"""Recipe manifest CRUD + validation.

Recipes are the primary entity: versioned Albumentations manifests stored at
``recipes/<id>.json`` in B2. All persistence goes through the `repo` layer —
this module owns validation, id/version assignment, and JSON (de)serialization.
"""

import json
import logging
import re
import uuid
from datetime import UTC, datetime

from app.repo import (
    delete_file,
    get_object_bytes,
    list_object_keys,
    put_bytes,
)
from app.service.transforms import is_known_transform
from app.types.recipes import Recipe, RecipeCreate

logger = logging.getLogger(__name__)

RECIPE_PREFIX = "recipes/"
_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_VALID_BBOX_FORMATS = {None, "yolo", "pascal_voc", "coco", "albumentations"}


class RecipeNotFoundError(Exception):
    """Raised when a recipe id does not resolve to a stored manifest."""


class RecipeValidationError(Exception):
    """Raised when a recipe payload fails validation."""


def _recipe_key(recipe_id: str) -> str:
    return f"{RECIPE_PREFIX}{recipe_id}.json"


def _validate(payload: RecipeCreate) -> None:
    if not payload.transforms:
        raise RecipeValidationError("A recipe needs at least one transform.")
    for t in payload.transforms:
        if not is_known_transform(t.id):
            raise RecipeValidationError(f"Unknown transform: {t.id}")
    if payload.bbox_format not in _VALID_BBOX_FORMATS:
        raise RecipeValidationError(f"Unsupported bbox format: {payload.bbox_format}")


def create_recipe(payload: RecipeCreate) -> Recipe:
    _validate(payload)
    now = datetime.now(UTC)
    recipe = Recipe(
        id=uuid.uuid4().hex[:12],
        version=1,
        name=payload.name,
        description=payload.description,
        seed_prefix=payload.seed_prefix,
        transforms=payload.transforms,
        variants_per_image=payload.variants_per_image,
        random_seed=payload.random_seed,
        bbox_format=payload.bbox_format,
        created_at=now,
        updated_at=now,
        run_count=0,
    )
    _write(recipe)
    logger.info("Recipe created: id=%s name=%s", recipe.id, recipe.name)
    return recipe


def _write(recipe: Recipe) -> None:
    body = recipe.model_dump_json(indent=2).encode("utf-8")
    put_bytes(body, _recipe_key(recipe.id), "application/json")


def get_recipe(recipe_id: str) -> Recipe:
    if not _ID_RE.match(recipe_id):
        raise RecipeValidationError("Invalid recipe id.")
    try:
        raw = get_object_bytes(_recipe_key(recipe_id))
    except RuntimeError as e:
        raise RecipeNotFoundError(str(e)) from e
    return Recipe(**json.loads(raw))


def list_recipes() -> list[Recipe]:
    recipes: list[Recipe] = []
    for obj in list_object_keys(prefix=RECIPE_PREFIX, max_keys=1000):
        key = obj["key"]
        if not key.endswith(".json"):
            continue
        try:
            raw = get_object_bytes(key)
            recipes.append(Recipe(**json.loads(raw)))
        except Exception:
            logger.warning("Skipping unreadable recipe manifest: %s", key)
    recipes.sort(key=lambda r: r.updated_at, reverse=True)
    return recipes


def update_recipe(recipe_id: str, payload: RecipeCreate) -> Recipe:
    _validate(payload)
    existing = get_recipe(recipe_id)
    updated = existing.model_copy(
        update={
            "name": payload.name,
            "description": payload.description,
            "seed_prefix": payload.seed_prefix,
            "transforms": payload.transforms,
            "variants_per_image": payload.variants_per_image,
            "random_seed": payload.random_seed,
            "bbox_format": payload.bbox_format,
            "version": existing.version + 1,
            "updated_at": datetime.now(UTC),
        }
    )
    _write(updated)
    logger.info("Recipe updated: id=%s version=%d", updated.id, updated.version)
    return updated


def bump_run_count(recipe_id: str) -> None:
    """Increment the recipe's run counter after a successful run."""
    try:
        recipe = get_recipe(recipe_id)
    except RecipeNotFoundError:
        return
    recipe = recipe.model_copy(update={"run_count": recipe.run_count + 1})
    _write(recipe)


def delete_recipe(recipe_id: str) -> None:
    """Delete the recipe manifest only.

    Augmented outputs under ``augmented/<id>/`` are intentionally NOT purged —
    they are reproducible training assets and deletion is documented as an
    explicit, separate action.
    """
    if not _ID_RE.match(recipe_id):
        raise RecipeValidationError("Invalid recipe id.")
    # Confirm it exists so a 404 surfaces rather than a silent no-op.
    get_recipe(recipe_id)
    delete_file(_recipe_key(recipe_id))
    logger.info("Recipe manifest deleted: id=%s (outputs retained)", recipe_id)
