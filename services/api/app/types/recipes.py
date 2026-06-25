from datetime import datetime

from pydantic import BaseModel, Field


class RecipeTransform(BaseModel):
    """One step in a recipe's transform graph: an Albumentations transform
    `id` from the catalog, its parameter overrides, and an apply probability."""

    id: str  # Albumentations class name, e.g. "HorizontalFlip"
    params: dict = {}
    p: float = Field(default=1.0, ge=0.0, le=1.0)


class RecipeCreate(BaseModel):
    """Inbound payload for create/edit. The recipe id + versioning are
    assigned server-side."""

    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    seed_prefix: str = Field(default="seeds/", min_length=1)
    transforms: list[RecipeTransform] = []
    variants_per_image: int = Field(default=5, ge=1, le=50)
    random_seed: int | None = None
    bbox_format: str | None = None  # None | "yolo" | "pascal_voc" | "coco"


class Recipe(BaseModel):
    """Persisted recipe manifest stored at recipes/<id>.json."""

    id: str
    version: int = 1
    name: str
    description: str = ""
    seed_prefix: str
    transforms: list[RecipeTransform] = []
    variants_per_image: int
    random_seed: int | None = None
    bbox_format: str | None = None
    created_at: datetime
    updated_at: datetime
    run_count: int = 0
