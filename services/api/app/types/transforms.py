from pydantic import BaseModel


class TransformParam(BaseModel):
    """A single tunable parameter on an Albumentations transform."""

    name: str
    type: str  # "float" | "int" | "bool" | "tuple"
    default: float | int | bool | list | None = None
    min: float | int | None = None
    max: float | int | None = None
    description: str = ""


class TransformSpec(BaseModel):
    """Catalog entry describing one Albumentations transform the recipe
    builder can offer. `id` is the Albumentations class name (e.g.
    "HorizontalFlip") used verbatim when constructing the A.Compose."""

    id: str
    label: str
    category: str  # "geometric" | "color" | "blur" | "noise" | "crop"
    description: str
    supports_bbox: bool
    params: list[TransformParam] = []
