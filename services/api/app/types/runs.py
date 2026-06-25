from datetime import datetime

from pydantic import BaseModel

from app.types.recipes import Recipe


class RunRequest(BaseModel):
    """Optional overrides when kicking off a run. Empty body = use the recipe
    as stored against its full seed prefix."""

    seed_prefix: str | None = None  # override the recipe's seed prefix
    random_seed: int | None = None  # override the recipe's pinned seed


class VariantPair(BaseModel):
    """A seed image and the augmented variant keys produced from it."""

    seed_key: str
    seed_filename: str
    variant_keys: list[str] = []


class RunManifest(BaseModel):
    """Reproducibility manifest stored at augmented/<recipe-id>/<run-id>/_run.json.

    Pins everything needed to reproduce the run bit-for-bit: a full snapshot of
    the recipe, the resolved seed list, the random seed, and library versions.
    """

    run_id: str
    recipe_id: str
    recipe_version: int
    recipe_snapshot: Recipe
    seed_prefix: str
    random_seed: int
    source_keys: list[str] = []
    variants_per_image: int
    bbox_format: str | None = None
    library_versions: dict[str, str] = {}
    created_at: datetime


class RunResult(BaseModel):
    """Outcome summary returned by POST /recipes/{id}/run."""

    run_id: str
    recipe_id: str
    source_count: int
    variants_written: int
    bytes_written: int
    bytes_written_human: str
    multiplication_factor: float
    truncated: bool  # True if source list was capped by max_run_source_images
    created_at: datetime


class RunSummary(BaseModel):
    """Lightweight run-history row for the recipe detail page."""

    run_id: str
    recipe_id: str
    source_count: int
    variants_written: int
    bytes_written: int
    bytes_written_human: str
    multiplication_factor: float
    created_at: datetime


class RunDetail(BaseModel):
    """Full run detail: the manifest plus the seed -> variant pairing and
    presigned thumbnail URLs for the gallery."""

    manifest: RunManifest
    pairs: list[VariantPair] = []
    variants_written: int
    bytes_written: int
    bytes_written_human: str
    multiplication_factor: float
