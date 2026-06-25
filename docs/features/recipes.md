<!-- last_verified: 2026-06-24 -->
# Feature: Recipes

## Purpose
Recipes are the primary entity: named, versioned Albumentations transform graphs with a full create / read / edit / delete / run lifecycle from the UI.

## Used By
- UI: `/recipes` (list + create/delete), `/recipes/[id]` (detail + edit + run)
- API: `GET/POST /recipes`, `GET/PUT/DELETE /recipes/{id}`, `POST /recipes/{id}/run`, `GET /transforms`

## Core Functions
- `apps/web/src/components/recipes/recipe-form.tsx` — builder (transforms from catalog, params, `p`, N variants, seed prefix, random seed, bbox format)
- `apps/web/src/components/recipes/recipe-list.tsx` — list + create dialog + delete confirm
- `apps/web/src/components/recipes/recipe-detail.tsx` — detail, edit dialog, Run, run history
- `services/api/app/service/recipes.py` — manifest CRUD + validation
- `services/api/app/service/transforms.py` — curated transform catalog
- `services/api/app/runtime/recipes.py`, `runtime/transforms.py` — route handlers

## Canonical Files
- Recipe CRUD: `services/api/app/service/recipes.py`
- Recipe builder UI: `apps/web/src/components/recipes/recipe-form.tsx`

## Inputs
- `RecipeCreate`: name, description, seed_prefix, transforms[] (id + params + p), variants_per_image (1–50), random_seed?, bbox_format?

## Outputs
- `Recipe` manifest persisted at `recipes/<id>.json` (B2)
- `version` bumps on every edit; `run_count` increments after a successful run
- Delete removes the manifest only — augmented output under `augmented/<id>/` is retained

## Flow
- **Create** → "New Recipe" form → `POST /recipes` → write `recipes/<id>.json`
- **Read** → `/recipes` list and `/recipes/[id]` detail (transforms, params, run history)
- **Edit** → pre-filled form → `PUT /recipes/{id}` → version bumped
- **Delete** → alert-dialog confirm → `DELETE /recipes/{id}` (manifest only)
- **Run** → "Run" on detail → augment seed prefix → write N× variants + run manifest (see [Augmentation](augmentation.md))

## Edge Cases
- Empty transform list → 400 validation error
- Unknown transform id → 400 (validated against the catalog)
- Unknown recipe id → 404
- Delete a recipe with existing output → manifest removed, output kept (documented, not auto-purged)

## UX States
- Loading: skeleton cards
- Empty: "No recipes yet"
- Error: inline `ErrorState` with Retry

## Verification
- Test files: `services/api/tests/test_recipes.py`
- Required cases: create+read, edit bumps version, delete keeps output, reject empty/unknown transforms
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green; all five verbs reachable from the UI

## Related Docs
- [Augmentation](augmentation.md)
- [Gallery](gallery.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
