"""No-network unit tests for the Albumentations augmentation engine.

These exercise the pure-compute core (`service/augment.py` + the transform
catalog) with an in-memory numpy image — no B2, no boto3, no model download.
"""

import numpy as np

from app.service.augment import (
    RecipeBuildError,
    augment_image,
    build_compose,
    decode_image,
    encode_image,
    library_versions,
)
from app.service.transforms import get_transform_catalog, is_known_transform


def _sample_recipe_transforms() -> list[dict]:
    return [
        {"id": "HorizontalFlip", "params": {}, "p": 1.0},
        {"id": "RandomBrightnessContrast",
         "params": {"brightness_limit": 0.2, "contrast_limit": 0.2}, "p": 1.0},
        {"id": "Rotate", "params": {"limit": 15}, "p": 1.0},
    ]


def test_build_compose_from_recipe_produces_n_variants():
    """Core acceptance test: build A.Compose from a recipe and assert N
    variants are produced from one in-memory numpy image."""
    compose = build_compose(_sample_recipe_transforms())
    image = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)

    n = 10
    variants = augment_image(compose, image, n_variants=n)

    assert len(variants) == n
    for v in variants:
        assert isinstance(v["image"], np.ndarray)
        assert v["image"].shape[2] == 3  # RGB preserved


def test_build_compose_rejects_unknown_transform():
    try:
        build_compose([{"id": "NotARealTransform", "params": {}, "p": 1.0}])
    except RecipeBuildError:
        return
    raise AssertionError("Expected RecipeBuildError for unknown transform id")


def test_encode_decode_roundtrip():
    image = (np.random.rand(32, 48, 3) * 255).astype(np.uint8)
    data = encode_image(image, "PNG")
    restored = decode_image(data)
    assert restored.shape == (32, 48, 3)


def test_catalog_ids_are_constructible():
    """Every catalog id must resolve to a real Albumentations transform so the
    recipe builder never offers something the engine can't build."""
    catalog = get_transform_catalog()
    assert catalog, "Transform catalog is empty"
    for spec in catalog:
        assert is_known_transform(spec.id)
        defaults = [
            {"id": spec.id,
             "params": {p.name: p.default for p in spec.params if p.default is not None},
             "p": 1.0}
        ]
        # Should not raise.
        build_compose(defaults)


def test_bbox_compose_transforms_geometry():
    """With a YOLO bbox format, the compose carries boxes through transforms."""
    compose = build_compose(
        [{"id": "HorizontalFlip", "params": {}, "p": 1.0}], bbox_format="yolo"
    )
    image = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
    bboxes = [[0.25, 0.25, 0.2, 0.2]]
    variants = augment_image(
        compose, image, n_variants=3, bboxes=bboxes, class_labels=[0]
    )
    assert len(variants) == 3
    for v in variants:
        assert v["bboxes"] is not None
        # HorizontalFlip mirrors x-center to ~0.75.
        assert abs(v["bboxes"][0][0] - 0.75) < 0.01


def test_library_versions_pinned():
    versions = library_versions()
    assert "albumentations" in versions
    assert "numpy" in versions
