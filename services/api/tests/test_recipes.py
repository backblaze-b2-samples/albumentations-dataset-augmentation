"""Recipe CRUD service tests — repo layer mocked, no B2 / no boto3."""

import json

import pytest

from app.service import recipes as recipes_service
from app.service.recipes import (
    RecipeValidationError,
    create_recipe,
)
from app.types.recipes import RecipeCreate, RecipeTransform


@pytest.fixture
def fake_b2(monkeypatch):
    """In-memory object store standing in for B2 in the repo layer."""
    store: dict[str, bytes] = {}

    def put_bytes(data, key, content_type):
        store[key] = data
        return len(data)

    def get_object_bytes(key):
        if key not in store:
            raise RuntimeError(f"B2 object not found: '{key}'")
        return store[key]

    def list_object_keys(prefix="", max_keys=1000):
        return [
            {"key": k, "size_bytes": len(v), "last_modified": None}
            for k, v in store.items()
            if k.startswith(prefix)
        ]

    def delete_file(key):
        store.pop(key, None)

    monkeypatch.setattr(recipes_service, "put_bytes", put_bytes)
    monkeypatch.setattr(recipes_service, "get_object_bytes", get_object_bytes)
    monkeypatch.setattr(recipes_service, "list_object_keys", list_object_keys)
    monkeypatch.setattr(recipes_service, "delete_file", delete_file)
    return store


def _valid_payload(name="Flip + Jitter") -> RecipeCreate:
    return RecipeCreate(
        name=name,
        seed_prefix="seeds/cats/",
        transforms=[
            RecipeTransform(id="HorizontalFlip", params={}, p=1.0),
            RecipeTransform(id="RandomBrightnessContrast", params={}, p=0.8),
        ],
        variants_per_image=8,
        random_seed=7,
    )


def test_create_read_recipe(fake_b2):
    recipe = create_recipe(_valid_payload())
    assert recipe.id
    assert recipe.version == 1
    assert recipe.variants_per_image == 8

    fetched = recipes_service.get_recipe(recipe.id)
    assert fetched.name == "Flip + Jitter"
    # Manifest is real JSON on the (fake) B2 store.
    raw = json.loads(fake_b2[f"recipes/{recipe.id}.json"])
    assert raw["name"] == "Flip + Jitter"


def test_update_bumps_version(fake_b2):
    recipe = create_recipe(_valid_payload())
    updated = recipes_service.update_recipe(
        recipe.id, _valid_payload(name="Renamed")
    )
    assert updated.version == 2
    assert updated.name == "Renamed"


def test_delete_removes_manifest_only(fake_b2):
    recipe = create_recipe(_valid_payload())
    # Simulate augmented output existing under the recipe.
    fake_b2[f"augmented/{recipe.id}/run1/img__aug0.png"] = b"x"
    recipes_service.delete_recipe(recipe.id)
    assert f"recipes/{recipe.id}.json" not in fake_b2
    # Outputs are intentionally retained.
    assert f"augmented/{recipe.id}/run1/img__aug0.png" in fake_b2


def test_create_rejects_empty_transforms(fake_b2):
    payload = _valid_payload()
    payload.transforms = []
    with pytest.raises(RecipeValidationError):
        create_recipe(payload)


def test_create_rejects_unknown_transform(fake_b2):
    payload = _valid_payload()
    payload.transforms = [RecipeTransform(id="Bogus", params={}, p=1.0)]
    with pytest.raises(RecipeValidationError):
        create_recipe(payload)
