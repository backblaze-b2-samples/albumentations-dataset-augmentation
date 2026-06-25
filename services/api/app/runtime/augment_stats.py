from fastapi import APIRouter

from app.service.augment_stats import get_augment_stats, list_gallery
from app.types.augment_stats import AugmentStats, GalleryRun

router = APIRouter()


@router.get("/augment/stats", response_model=AugmentStats)
async def augment_stats_endpoint():
    """Dashboard aggregates: seeds, recipes, variants, multiplication factor."""
    return get_augment_stats()


@router.get("/gallery", response_model=list[GalleryRun])
async def gallery_endpoint():
    """Scoped augmented-output library (augmented/ prefix only), grouped by run."""
    return list_gallery()
