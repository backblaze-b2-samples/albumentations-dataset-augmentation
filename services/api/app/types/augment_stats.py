from pydantic import BaseModel

from app.types.runs import RunSummary


class VariantsPerRun(BaseModel):
    """One bar in the "variants produced per run" dashboard chart."""

    run_label: str
    variants: int


class AugmentStats(BaseModel):
    """Augmentation dashboard aggregates (replaces the starter upload stats)."""

    seed_images: int
    recipe_count: int
    total_variants: int
    multiplication_factor: float  # avg variants / seed across all runs
    bytes_written: int
    bytes_written_human: str
    recent_runs: list[RunSummary] = []
    variants_per_run: list[VariantsPerRun] = []


class GalleryRun(BaseModel):
    """A run's worth of augmented output for the scoped /gallery explorer."""

    recipe_id: str
    recipe_name: str
    run_id: str
    variant_count: int
    created_at: str
    thumbnails: list[dict] = []  # [{key, url}] — first few variants
