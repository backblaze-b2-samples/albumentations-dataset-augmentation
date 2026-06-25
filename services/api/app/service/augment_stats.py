"""Dashboard + gallery aggregations for the augmentation pipeline.

Replaces the starter's upload-centric stats. Aggregates flow strictly
runtime -> service -> repo; no boto3 here.
"""

import logging

from app.repo import list_object_keys
from app.service.recipes import list_recipes
from app.service.runs import (
    AUGMENTED_PREFIX,
    presign,
    read_run_manifest,
    summarize_run,
)
from app.types.augment_stats import AugmentStats, GalleryRun, VariantsPerRun
from app.types.formatting import humanize_bytes

logger = logging.getLogger(__name__)

_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def _is_variant(key: str) -> bool:
    return key.lower().endswith(_IMAGE_EXTS) and not key.endswith("_run.json")


def _count_seeds() -> int:
    """Count seed images across the conventional seeds/ prefix."""
    return sum(
        1
        for o in list_object_keys(prefix="seeds/", max_keys=1000)
        if o["key"].lower().endswith(_IMAGE_EXTS)
    )


def get_augment_stats() -> AugmentStats:
    recipes = list_recipes()
    objs = list_object_keys(prefix=AUGMENTED_PREFIX, max_keys=1000)

    total_variants = sum(1 for o in objs if _is_variant(o["key"]))
    bytes_written = sum(o["size_bytes"] for o in objs)
    seed_images = _count_seeds()

    summaries = []
    for o in objs:
        parts = o["key"].split("/")
        if len(parts) >= 4 and parts[3] == "_run.json":
            recipe_id, run_id = parts[1], parts[2]
            run_objs = [
                x for x in objs if x["key"].startswith(f"{AUGMENTED_PREFIX}{recipe_id}/{run_id}/")
            ]
            s = summarize_run(recipe_id, run_id, run_objs)
            if s:
                summaries.append(s)
    summaries.sort(key=lambda s: s.created_at, reverse=True)

    factor = (
        round(total_variants / seed_images, 2) if seed_images else 0.0
    )
    per_run = [
        VariantsPerRun(run_label=s.run_id[:8], variants=s.variants_written)
        for s in summaries[:10]
    ][::-1]

    return AugmentStats(
        seed_images=seed_images,
        recipe_count=len(recipes),
        total_variants=total_variants,
        multiplication_factor=factor,
        bytes_written=bytes_written,
        bytes_written_human=humanize_bytes(bytes_written),
        recent_runs=summaries[:8],
        variants_per_run=per_run,
    )


def list_gallery(limit_thumbs: int = 6) -> list[GalleryRun]:
    """List augmented output grouped by run for the scoped /gallery explorer."""
    objs = list_object_keys(prefix=AUGMENTED_PREFIX, max_keys=1000)
    recipe_names = {r.id: r.name for r in list_recipes()}
    grouped: dict[tuple[str, str], list[dict]] = {}
    for o in objs:
        parts = o["key"].split("/")
        if len(parts) >= 4:
            grouped.setdefault((parts[1], parts[2]), []).append(o)

    gallery: list[GalleryRun] = []
    for (recipe_id, run_id), items in grouped.items():
        manifest = read_run_manifest(recipe_id, run_id)
        if not manifest:
            continue
        variants = sorted(i["key"] for i in items if _is_variant(i["key"]))
        thumbs = [
            {"key": k, "url": presign(k)} for k in variants[:limit_thumbs]
        ]
        gallery.append(
            GalleryRun(
                recipe_id=recipe_id,
                recipe_name=recipe_names.get(recipe_id, recipe_id),
                run_id=run_id,
                variant_count=len(variants),
                created_at=manifest.created_at.isoformat(),
                thumbnails=thumbs,
            )
        )
    gallery.sort(key=lambda g: g.created_at, reverse=True)
    return gallery
