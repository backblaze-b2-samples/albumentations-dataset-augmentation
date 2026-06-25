"""Catalog of Albumentations transforms exposed to the recipe builder.

Pure data — no B2, no compute. The `id` of each entry is the exact
Albumentations class name, so `service/augment.py` can construct the transform
by looking the class up on the `albumentations` module. Keeping the catalog
curated (rather than reflecting over the whole library) gives the UI a stable,
documented set with sane parameter ranges.
"""

from app.types.transforms import TransformParam, TransformSpec

_CATALOG: list[TransformSpec] = [
    TransformSpec(
        id="HorizontalFlip",
        label="Horizontal Flip",
        category="geometric",
        description="Mirror the image left-to-right.",
        supports_bbox=True,
        params=[],
    ),
    TransformSpec(
        id="VerticalFlip",
        label="Vertical Flip",
        category="geometric",
        description="Mirror the image top-to-bottom.",
        supports_bbox=True,
        params=[],
    ),
    TransformSpec(
        id="RandomRotate90",
        label="Random 90° Rotate",
        category="geometric",
        description="Rotate by a random multiple of 90 degrees.",
        supports_bbox=True,
        params=[],
    ),
    TransformSpec(
        id="Rotate",
        label="Rotate",
        category="geometric",
        description="Rotate by a random angle within +/- limit degrees.",
        supports_bbox=True,
        params=[
            TransformParam(
                name="limit", type="int", default=30, min=0, max=180,
                description="Max rotation angle (degrees).",
            ),
        ],
    ),
    TransformSpec(
        id="RandomBrightnessContrast",
        label="Brightness / Contrast",
        category="color",
        description="Jitter brightness and contrast.",
        supports_bbox=True,
        params=[
            TransformParam(
                name="brightness_limit", type="float", default=0.2,
                min=0.0, max=1.0, description="Max brightness shift.",
            ),
            TransformParam(
                name="contrast_limit", type="float", default=0.2,
                min=0.0, max=1.0, description="Max contrast shift.",
            ),
        ],
    ),
    TransformSpec(
        id="HueSaturationValue",
        label="Hue / Saturation",
        category="color",
        description="Shift hue, saturation, and value channels.",
        supports_bbox=True,
        params=[
            TransformParam(
                name="hue_shift_limit", type="int", default=20,
                min=0, max=180, description="Max hue shift.",
            ),
            TransformParam(
                name="sat_shift_limit", type="int", default=30,
                min=0, max=255, description="Max saturation shift.",
            ),
        ],
    ),
    TransformSpec(
        id="RGBShift",
        label="RGB Shift",
        category="color",
        description="Independently shift the R, G, B channels.",
        supports_bbox=True,
        params=[
            TransformParam(
                name="r_shift_limit", type="int", default=20,
                min=0, max=255, description="Max red shift.",
            ),
        ],
    ),
    TransformSpec(
        id="GaussianBlur",
        label="Gaussian Blur",
        category="blur",
        description="Apply a Gaussian blur.",
        supports_bbox=True,
        params=[
            TransformParam(
                name="blur_limit", type="int", default=7,
                min=3, max=31, description="Max kernel size (odd).",
            ),
        ],
    ),
    TransformSpec(
        id="MotionBlur",
        label="Motion Blur",
        category="blur",
        description="Simulate camera motion blur.",
        supports_bbox=True,
        params=[
            TransformParam(
                name="blur_limit", type="int", default=7,
                min=3, max=31, description="Max kernel size (odd).",
            ),
        ],
    ),
    TransformSpec(
        id="GaussNoise",
        label="Gaussian Noise",
        category="noise",
        description="Add Gaussian sensor noise.",
        supports_bbox=True,
        params=[],
    ),
    TransformSpec(
        id="RandomResizedCrop",
        label="Random Resized Crop",
        category="crop",
        description="Crop a random region and resize back to a fixed size.",
        supports_bbox=True,
        params=[
            TransformParam(
                name="size", type="tuple", default=[256, 256],
                description="Output [height, width].",
            ),
        ],
    ),
]

_BY_ID = {t.id: t for t in _CATALOG}


def get_transform_catalog() -> list[TransformSpec]:
    """Return the full curated transform catalog for the recipe builder."""
    return list(_CATALOG)


def is_known_transform(transform_id: str) -> bool:
    return transform_id in _BY_ID


def transform_supports_bbox(transform_id: str) -> bool:
    spec = _BY_ID.get(transform_id)
    return bool(spec and spec.supports_bbox)
