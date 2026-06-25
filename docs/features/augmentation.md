<!-- last_verified: 2026-06-24 -->
# Feature: Augmentation

## Purpose
Apply a recipe's Albumentations transform graph to each seed image N times, writing the expanded dataset to B2 along with a reproducibility manifest.

## Used By
- UI: "Run" on `/recipes/[id]`, "Re-run" on `/runs/[recipeId]/[runId]`
- API: `POST /recipes/{id}/run`, `GET /recipes/{id}/runs`, `GET /recipes/{id}/runs/{run_id}`

## Core Functions
- `services/api/app/service/augment.py` — **pure engine**: `build_compose()`, `augment_image()`, `decode_image()`/`encode_image()`, `library_versions()`. No B2, no boto3.
- `services/api/app/service/runs.py` — orchestration: list seeds, read bytes, apply engine, write variants + `_run.json`, summarize/detail
- `services/api/app/repo/b2_client.py` — `get_object_bytes()`, `put_bytes()`, `list_object_keys()`, `get_presigned_get_url()`

## Canonical Files
- Augmentation engine (pure compute): `services/api/app/service/augment.py`
- Run orchestration: `services/api/app/service/runs.py`

## Inputs
- A stored `Recipe` (transforms, variants_per_image, seed_prefix, random_seed, bbox_format)
- Optional `RunRequest` overrides (seed_prefix, random_seed) — Re-run passes the original run's manifest values

## Outputs
- `augmented/<recipe-id>/<run-id>/<img>__aug<k>.<ext>` — N variants per seed
- `augmented/<recipe-id>/<run-id>/<img>__aug<k>.txt` — transformed YOLO sidecar (when a seed has one and the recipe sets `bbox_format: yolo`)
- `augmented/<recipe-id>/<run-id>/_run.json` — `RunManifest`: recipe snapshot, seed list, random seed, library versions
- `RunResult`: source_count, variants_written, bytes_written, multiplication_factor, truncated flag

## Flow
1. Load recipe; resolve seed prefix + random seed (override or recipe default, falling back to 42)
2. List seed images under the prefix; cap at `max_run_source_images` (default 50) — `truncated` is surfaced, never silent
3. Seed `random`/`numpy`; build `A.Compose` once
4. For each seed: read bytes → decode → apply N× → write each variant (+ sidecar) to B2
5. Write `_run.json` and bump the recipe's run count

## Reproducibility
- The manifest pins recipe snapshot + seed list + random seed + `albumentations`/`numpy` versions.
- "Re-run" replays the same seed + prefix → identical output (deterministic seeding).

## Edge Cases
- No seeds under the prefix → run completes with 0 variants (factor 0)
- Unknown transform → engine raises `RecipeBuildError` → 502 from the route
- Bad transform params → `RecipeBuildError`
- Missing/absent YOLO sidecar → variant written without a sidecar (graceful), even when the recipe sets `bbox_format: yolo` (bbox-aware compose augments the un-annotated seed image-only)
- Unexpected engine error → route returns a 500 with a JSON `detail` (not a bare crash), so the client shows the error instead of an opaque network failure

## Verification
- Test files: `services/api/tests/test_augment.py` (no-network: builds `A.Compose` from a recipe and asserts N variants from one in-memory numpy image; bbox geometry carried through)
- Required cases: N variants produced, unknown-transform rejection, encode/decode roundtrip, every catalog id constructible, bbox transform, version pinning
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: augment tests green; `test_boto3_only_in_repo` green (engine stays B2-free)

## Related Docs
- [Recipes](recipes.md)
- [Gallery](gallery.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
