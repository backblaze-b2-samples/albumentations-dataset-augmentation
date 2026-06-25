from fastapi import APIRouter

from app.service.transforms import get_transform_catalog
from app.types.transforms import TransformSpec

router = APIRouter()


@router.get("/transforms", response_model=list[TransformSpec])
async def list_transforms_endpoint():
    """Curated Albumentations transform catalog that drives the recipe builder."""
    return get_transform_catalog()
