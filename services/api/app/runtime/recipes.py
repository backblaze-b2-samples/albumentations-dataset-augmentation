import logging

from fastapi import APIRouter, HTTPException

from app.service.recipes import (
    RecipeNotFoundError,
    RecipeValidationError,
    create_recipe,
    delete_recipe,
    get_recipe,
    list_recipes,
    update_recipe,
)
from app.service.runs import run_recipe
from app.types.recipes import Recipe, RecipeCreate
from app.types.runs import RunRequest, RunResult

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/recipes", response_model=list[Recipe])
async def list_recipes_endpoint():
    return list_recipes()


@router.post("/recipes", response_model=Recipe, status_code=201)
async def create_recipe_endpoint(payload: RecipeCreate):
    try:
        return create_recipe(payload)
    except RecipeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe_endpoint(recipe_id: str):
    try:
        return get_recipe(recipe_id)
    except RecipeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except RecipeNotFoundError:
        raise HTTPException(status_code=404, detail="Recipe not found") from None


@router.put("/recipes/{recipe_id}", response_model=Recipe)
async def update_recipe_endpoint(recipe_id: str, payload: RecipeCreate):
    try:
        return update_recipe(recipe_id, payload)
    except RecipeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except RecipeNotFoundError:
        raise HTTPException(status_code=404, detail="Recipe not found") from None


@router.delete("/recipes/{recipe_id}")
async def delete_recipe_endpoint(recipe_id: str):
    try:
        delete_recipe(recipe_id)
    except RecipeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except RecipeNotFoundError:
        raise HTTPException(status_code=404, detail="Recipe not found") from None
    return {"deleted": True, "id": recipe_id}


@router.post("/recipes/{recipe_id}/run", response_model=RunResult)
async def run_recipe_endpoint(recipe_id: str, body: RunRequest | None = None):
    body = body or RunRequest()
    try:
        return run_recipe(
            recipe_id,
            seed_prefix_override=body.seed_prefix,
            random_seed_override=body.random_seed,
        )
    except RecipeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except RecipeNotFoundError:
        raise HTTPException(status_code=404, detail="Recipe not found") from None
    except RuntimeError as e:
        logger.error("Run failed for recipe %s: %s", recipe_id, e)
        raise HTTPException(status_code=502, detail="Augmentation run failed") from None
    except Exception:
        # Surface engine errors as a real HTTP response (carries CORS headers so
        # the browser can read it) rather than a bare 500 the client sees only
        # as an opaque "network error".
        logger.exception("Unexpected error running recipe %s", recipe_id)
        raise HTTPException(status_code=500, detail="Augmentation run failed") from None
