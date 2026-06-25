from fastapi import APIRouter, HTTPException

from app.service.runs import get_run_detail, list_runs, presign
from app.types.runs import RunDetail, RunSummary

router = APIRouter()


@router.get("/recipes/{recipe_id}/runs", response_model=list[RunSummary])
async def list_runs_endpoint(recipe_id: str):
    return list_runs(recipe_id)


@router.get("/recipes/{recipe_id}/runs/{run_id}", response_model=RunDetail)
async def run_detail_endpoint(recipe_id: str, run_id: str):
    detail = get_run_detail(recipe_id, run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return detail


@router.get("/objects/preview")
async def object_preview_endpoint(key: str):
    """Presigned inline GET URL for a single augmented variant / seed image.

    Scoped to image rendering in the gallery + run detail; the existing
    /files/{key}/preview endpoint still serves the full-bucket explorer.
    """
    if not key or ".." in key:
        raise HTTPException(status_code=400, detail="Invalid key")
    try:
        return {"url": presign(key)}
    except RuntimeError:
        raise HTTPException(status_code=502, detail="Failed to presign object") from None
