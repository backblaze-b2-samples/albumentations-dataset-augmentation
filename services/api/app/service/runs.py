"""Run orchestration: augment a recipe's seed prefix and persist the output.

Wires the pure `service/augment.py` engine to B2 via the `repo` layer: list
seeds, read bytes (+ optional YOLO sidecar), build the A.Compose once, apply it
N times per seed, write variants to ``augmented/<recipe-id>/<run-id>/``, and
write a reproducibility manifest pinning recipe + seed + versions. No boto3
here — all I/O is through repo helpers.
"""

import json
import logging
import random
import uuid
from datetime import UTC, datetime

import numpy as np

from app.config import settings
from app.repo import (
    get_object_bytes,
    get_presigned_get_url,
    list_object_keys,
    put_bytes,
)
from app.service.augment import (
    augment_image,
    build_compose,
    decode_image,
    encode_image,
    library_versions,
)
from app.service.recipes import bump_run_count, get_recipe
from app.types.formatting import humanize_bytes
from app.types.recipes import Recipe
from app.types.runs import (
    RunDetail,
    RunManifest,
    RunResult,
    RunSummary,
    VariantPair,
)

logger = logging.getLogger(__name__)

AUGMENTED_PREFIX = "augmented/"
_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def _is_image(key: str) -> bool:
    return key.lower().endswith(_IMAGE_EXTS)


def _basename(key: str) -> str:
    return key.rsplit("/", 1)[-1]


def _stem_ext(filename: str) -> tuple[str, str]:
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        return stem, ext
    return filename, "png"


def _run_prefix(recipe_id: str, run_id: str) -> str:
    return f"{AUGMENTED_PREFIX}{recipe_id}/{run_id}/"


def run_recipe(
    recipe_id: str,
    seed_prefix_override: str | None = None,
    random_seed_override: int | None = None,
) -> RunResult:
    """Execute a recipe against its seed prefix and write the expanded dataset."""
    recipe = get_recipe(recipe_id)
    seed_prefix = seed_prefix_override or recipe.seed_prefix
    random_seed = (
        random_seed_override
        if random_seed_override is not None
        else (recipe.random_seed if recipe.random_seed is not None else 42)
    )

    seeds = [
        o["key"]
        for o in list_object_keys(prefix=seed_prefix, max_keys=1000)
        if _is_image(o["key"])
    ]
    seeds.sort()
    truncated = len(seeds) > settings.max_run_source_images
    if truncated:
        seeds = seeds[: settings.max_run_source_images]

    run_id = uuid.uuid4().hex[:12]
    run_prefix = _run_prefix(recipe_id, run_id)

    # Deterministic ordering + seeding so a "Re-run" reproduces bit-for-bit.
    random.seed(random_seed)
    np.random.seed(random_seed % (2**32))
    compose = build_compose(
        [t.model_dump() for t in recipe.transforms], recipe.bbox_format
    )

    variants_written = 0
    bytes_written = 0
    for seed_key in seeds:
        bytes_written += _augment_one(
            seed_key, recipe, run_prefix, compose
        )[0]
        variants_written += recipe.variants_per_image

    now = datetime.now(UTC)
    manifest = RunManifest(
        run_id=run_id,
        recipe_id=recipe_id,
        recipe_version=recipe.version,
        recipe_snapshot=recipe,
        seed_prefix=seed_prefix,
        random_seed=random_seed,
        source_keys=seeds,
        variants_per_image=recipe.variants_per_image,
        bbox_format=recipe.bbox_format,
        library_versions=library_versions(),
        created_at=now,
    )
    bytes_written += put_bytes(
        manifest.model_dump_json(indent=2).encode("utf-8"),
        f"{run_prefix}_run.json",
        "application/json",
    )
    bump_run_count(recipe_id)

    factor = round(variants_written / len(seeds), 2) if seeds else 0.0
    logger.info(
        "Run complete: recipe=%s run=%s seeds=%d variants=%d bytes=%d",
        recipe_id, run_id, len(seeds), variants_written, bytes_written,
    )
    return RunResult(
        run_id=run_id,
        recipe_id=recipe_id,
        source_count=len(seeds),
        variants_written=variants_written,
        bytes_written=bytes_written,
        bytes_written_human=humanize_bytes(bytes_written),
        multiplication_factor=factor,
        truncated=truncated,
        created_at=now,
    )


def _augment_one(seed_key, recipe: Recipe, run_prefix: str, compose) -> tuple[int, int]:
    """Augment a single seed image, writing N variants. Returns (bytes, count)."""
    data = get_object_bytes(seed_key)
    image = decode_image(data)
    filename = _basename(seed_key)
    stem, ext = _stem_ext(filename)
    fmt = "PNG" if ext.lower() not in ("jpg", "jpeg") else "JPEG"

    bboxes, labels = _load_sidecar(seed_key, recipe.bbox_format)
    results = augment_image(
        compose,
        image,
        recipe.variants_per_image,
        bboxes=bboxes,
        class_labels=labels,
    )

    total_bytes = 0
    for k, res in enumerate(results):
        out_key = f"{run_prefix}{stem}__aug{k}.{ext.lower()}"
        total_bytes += put_bytes(
            encode_image(res["image"], fmt), out_key, f"image/{fmt.lower()}"
        )
        if res["bboxes"] is not None and labels is not None:
            sidecar = _dump_yolo(res["bboxes"], labels)
            total_bytes += put_bytes(
                sidecar.encode("utf-8"),
                f"{run_prefix}{stem}__aug{k}.txt",
                "text/plain",
            )
    return total_bytes, len(results)


def _load_sidecar(seed_key, bbox_format):
    """Read an optional YOLO sidecar (.txt next to the image). Returns
    (bboxes, class_labels) or (None, None) when none / unsupported."""
    if bbox_format != "yolo":
        return None, None
    txt_key = seed_key.rsplit(".", 1)[0] + ".txt"
    try:
        raw = get_object_bytes(txt_key).decode("utf-8")
    except RuntimeError:
        return None, None
    bboxes, labels = [], []
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) == 5:
            labels.append(int(float(parts[0])))
            bboxes.append([float(p) for p in parts[1:5]])
    return (bboxes, labels) if bboxes else (None, None)


def _dump_yolo(bboxes, labels) -> str:
    lines = []
    for label, box in zip(labels, bboxes, strict=False):
        coords = " ".join(f"{c:.6f}" for c in box)
        lines.append(f"{label} {coords}")
    return "\n".join(lines) + "\n"


def list_runs(recipe_id: str) -> list[RunSummary]:
    """Return run-history summaries for one recipe, newest first."""
    prefix = f"{AUGMENTED_PREFIX}{recipe_id}/"
    objs = list_object_keys(prefix=prefix, max_keys=1000)
    summaries: list[RunSummary] = []
    for run_id, items in _group_by_run(objs).items():
        summary = summarize_run(recipe_id, run_id, items)
        if summary:
            summaries.append(summary)
    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def _group_by_run(objs: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for o in objs:
        parts = o["key"].split("/")
        # augmented/<recipe>/<run>/<file>
        if len(parts) >= 4:
            grouped.setdefault(parts[2], []).append(o)
    return grouped


def summarize_run(recipe_id: str, run_id: str, items: list[dict]) -> RunSummary | None:
    manifest = read_run_manifest(recipe_id, run_id)
    if not manifest:
        return None
    variants = sum(1 for i in items if _is_image(i["key"]))
    bytes_written = sum(i["size_bytes"] for i in items)
    source_count = len(manifest.source_keys)
    factor = round(variants / source_count, 2) if source_count else 0.0
    return RunSummary(
        run_id=run_id,
        recipe_id=recipe_id,
        source_count=source_count,
        variants_written=variants,
        bytes_written=bytes_written,
        bytes_written_human=humanize_bytes(bytes_written),
        multiplication_factor=factor,
        created_at=manifest.created_at,
    )


def read_run_manifest(recipe_id: str, run_id: str) -> RunManifest | None:
    try:
        raw = get_object_bytes(f"{_run_prefix(recipe_id, run_id)}_run.json")
    except RuntimeError:
        return None
    return RunManifest(**json.loads(raw))


def get_run_detail(recipe_id: str, run_id: str) -> RunDetail | None:
    manifest = read_run_manifest(recipe_id, run_id)
    if not manifest:
        return None
    objs = list_object_keys(prefix=_run_prefix(recipe_id, run_id), max_keys=1000)
    variant_keys = sorted(i["key"] for i in objs if _is_image(i["key"]))
    bytes_written = sum(i["size_bytes"] for i in objs)

    pairs = _pair_seeds_to_variants(manifest.source_keys, variant_keys)
    source_count = len(manifest.source_keys)
    factor = round(len(variant_keys) / source_count, 2) if source_count else 0.0
    return RunDetail(
        manifest=manifest,
        pairs=pairs,
        variants_written=len(variant_keys),
        bytes_written=bytes_written,
        bytes_written_human=humanize_bytes(bytes_written),
        multiplication_factor=factor,
    )


def _pair_seeds_to_variants(
    source_keys: list[str], variant_keys: list[str]
) -> list[VariantPair]:
    pairs: list[VariantPair] = []
    for seed_key in source_keys:
        stem, _ = _stem_ext(_basename(seed_key))
        matched = [v for v in variant_keys if _basename(v).startswith(stem + "__aug")]
        pairs.append(
            VariantPair(
                seed_key=seed_key,
                seed_filename=_basename(seed_key),
                variant_keys=matched,
            )
        )
    return pairs


def presign(key: str) -> str:
    """Presigned inline GET URL for rendering a variant / seed thumbnail."""
    return get_presigned_get_url(key)
