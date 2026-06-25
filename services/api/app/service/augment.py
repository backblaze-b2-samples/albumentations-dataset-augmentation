"""Albumentations augmentation engine — pure compute, NO B2 / no boto3.

Builds an `A.Compose` transform graph from a recipe and applies it to in-memory
images, emitting N augmented variants per source image. This is the local OSS
core of the sample: Albumentations runs entirely on the CPU with no API key and
no model download. All B2 I/O stays in `repo/`; this module only ever sees and
returns numpy arrays / bytes.
"""

import io
import os

# Disable Albumentations' network update check — the engine must run fully
# offline (no API key, no network), so we never want a background version ping.
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

import albumentations as A
import numpy as np
from PIL import Image

from app.service.transforms import is_known_transform


class RecipeBuildError(Exception):
    """Raised when a recipe cannot be compiled into an A.Compose."""


def build_compose(
    transforms: list[dict],
    bbox_format: str | None = None,
) -> A.Compose:
    """Compile a list of recipe transforms into an Albumentations pipeline.

    Each transform is ``{"id": <AlbumentationsClassName>, "params": {...},
    "p": <prob>}``. Unknown ids are rejected so a malformed recipe fails fast
    rather than silently dropping steps.
    """
    steps: list[A.BasicTransform] = []
    for t in transforms:
        tid = t.get("id")
        if not tid or not is_known_transform(tid):
            raise RecipeBuildError(f"Unknown transform id: {tid!r}")
        cls = getattr(A, tid, None)
        if cls is None:  # pragma: no cover - catalog guards this
            raise RecipeBuildError(f"Transform {tid!r} not available in albumentations")
        params = dict(t.get("params") or {})
        # Albumentations expects tuples where the catalog stores JSON lists.
        params = {k: tuple(v) if isinstance(v, list) else v for k, v in params.items()}
        params["p"] = float(t.get("p", 1.0))
        try:
            steps.append(cls(**params))
        except Exception as e:  # invalid param combo for this transform
            raise RecipeBuildError(f"Bad params for {tid!r}: {e}") from e

    compose_kwargs: dict = {}
    if bbox_format:
        compose_kwargs["bbox_params"] = A.BboxParams(
            format=bbox_format, label_fields=["class_labels"]
        )
    return A.Compose(steps, **compose_kwargs)


def decode_image(data: bytes) -> np.ndarray:
    """Decode image bytes to an RGB numpy array."""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return np.asarray(img)


def encode_image(arr: np.ndarray, fmt: str = "PNG") -> bytes:
    """Encode an RGB numpy array back to image bytes."""
    buf = io.BytesIO()
    Image.fromarray(arr.astype(np.uint8)).save(buf, format=fmt)
    return buf.getvalue()


def augment_image(
    compose: A.Compose,
    image: np.ndarray,
    n_variants: int,
    bboxes: list[list[float]] | None = None,
    class_labels: list | None = None,
) -> list[dict]:
    """Apply the compiled pipeline `n_variants` times to one image.

    Returns a list of ``{"image": np.ndarray, "bboxes": [...]}`` dicts. The
    same `compose` is re-applied, so probabilistic transforms produce distinct
    variants; determinism across whole runs is handled by the caller seeding
    numpy/random before invoking this.
    """
    # A bbox-aware compose (built with bbox_params) requires `bboxes` and its
    # declared label field on *every* call — even for a seed with no annotations.
    # Pass empty lists in that case so an un-annotated seed augments image-only
    # instead of tripping Albumentations' label_fields validation (would 500).
    bbox_aware = "bboxes" in getattr(compose, "processors", {})
    out: list[dict] = []
    for _ in range(n_variants):
        if bbox_aware:
            boxes = bboxes or []
            res = compose(
                image=image,
                bboxes=boxes,
                class_labels=class_labels or [0] * len(boxes),
            )
            out.append({"image": res["image"], "bboxes": res["bboxes"]})
        else:
            res = compose(image=image)
            out.append({"image": res["image"], "bboxes": None})
    return out


def library_versions() -> dict[str, str]:
    """Pin the library versions that define a reproducible run."""
    return {
        "albumentations": getattr(A, "__version__", "unknown"),
        "numpy": np.__version__,
    }
