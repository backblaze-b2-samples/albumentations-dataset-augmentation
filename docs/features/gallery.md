<!-- last_verified: 2026-06-24 -->
# Feature: Gallery

## Purpose
A scoped "Augmented Output" explorer — browse the expanded dataset grouped by recipe/run, with thumbnails and seed→variant pairing. Distinct from (and additional to) the full-bucket File browser.

## Used By
- UI: `/gallery` (library), `/runs/[recipeId]/[runId]` (seed→variant pairing)
- API: `GET /gallery`, `GET /recipes/{id}/runs/{run_id}`, `GET /objects/preview`

## Core Functions
- `apps/web/src/components/gallery/gallery-grid.tsx` — runs grid with thumbnails
- `apps/web/src/components/runs/run-detail.tsx` — per-run seed→variant gallery + manifest + Re-run
- `services/api/app/service/augment_stats.py` — `list_gallery()` (scoped to `augmented/`)
- `services/api/app/service/runs.py` — `get_run_detail()`, `presign()`
- `services/api/app/runtime/augment_stats.py`, `runtime/runs.py` — route handlers

## Canonical Files
- Gallery aggregation: `services/api/app/service/augment_stats.py`
- Run detail UI: `apps/web/src/components/runs/run-detail.tsx`

## Inputs
- None for the grid; `recipeId` + `runId` for run detail

## Outputs
- `GET /gallery` → `GalleryRun[]` (recipe_id, recipe_name, run_id, variant_count, created_at, thumbnails[])
- `GET /recipes/{id}/runs/{run}` → `RunDetail` (manifest, seed→variant pairs, stats)
- `GET /objects/preview?key=...` → `{ url }` presigned inline GET URL for `<img>` rendering

## Scope (mandatory)
- The gallery is scoped to the **`augmented/` prefix only** — it never lists the rest of the bucket.
- The full-bucket explorer remains at `/files`, unchanged.

## Flow
- `/gallery` → `useGallery()` lists runs under `augmented/`, grouped by `(recipe, run)`, with a few presigned thumbnails each
- A run card links to `/runs/{recipeId}/{runId}`
- Run detail pairs each seed key to its `__aug<k>` variants and renders presigned previews

## Edge Cases
- No augmented output → empty state directing the user to run a recipe
- A presigned thumbnail that fails to load → per-image "n/a" placeholder
- Run manifest missing → that run is skipped in aggregation

## UX States
- Loading: skeleton tiles
- Empty: "No augmented output yet"
- Error: inline `ErrorState` with Retry

## Verification
- Test files: backend aggregation exercised via `services/api/tests/test_recipes.py` repo fake; route shapes typed end-to-end through `packages/shared`
- Required cases: gallery grouping by run, run detail pairing, scoped to `augmented/`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm build && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: `/gallery` and run detail render; full-bucket `/files` untouched

## Related Docs
- [Augmentation](augmentation.md)
- [File Browser](file-browser.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
