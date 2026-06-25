<!-- last_verified: 2026-06-24 -->
# Feature: Dashboard

## Purpose
Surface the augmentation pipeline's write amplification at a glance — how many seeds in, how many variants out, and how much data was written to B2.

## Used By
- UI: `/` page (dashboard home)
- API: `GET /augment/stats`

## Core Functions
- `apps/web/src/components/dashboard/stats-cards.tsx` — 5 stat cards (seeds, recipes, variants, multiplication, bytes written)
- `apps/web/src/components/dashboard/recent-uploads-table.tsx` — recent augmentation runs across all recipes
- `apps/web/src/components/dashboard/upload-chart.tsx` — "variants produced per run" bar chart
- `apps/web/src/lib/queries.ts` — `useAugmentStats()`
- `services/api/app/runtime/augment_stats.py` — `GET /augment/stats` handler
- `services/api/app/service/augment_stats.py` — aggregation logic
- `services/api/app/repo/b2_client.py` — `list_object_keys()` data access

## Canonical Files
- Dashboard stats: `apps/web/src/components/dashboard/stats-cards.tsx`
- Aggregation service: `services/api/app/service/augment_stats.py`

## Inputs
- None (dashboard loads data automatically)

## Outputs
- `GET /augment/stats` → `AugmentStats`:
  - `seed_images` — images under `seeds/`
  - `recipe_count` — recipe manifests under `recipes/`
  - `total_variants` — augmented images under `augmented/`
  - `multiplication_factor` — avg variants per seed
  - `bytes_written` / `bytes_written_human` — total bytes under `augmented/`
  - `recent_runs` — last 8 runs (summaries)
  - `variants_per_run` — last 10 runs for the chart

## Flow
- Page loads → single `useAugmentStats()` query
- Stats cards display seeds, recipe count, total variants, multiplication factor, bytes written
- Chart displays variants produced per recent run
- Recent-runs table links each run to its `/runs/{recipeId}/{runId}` detail page

## Edge Cases
- API unavailable → inline `ErrorState` with Retry (no misleading zeros)
- No runs yet → empty chart + empty table messaging
- Large object count → aggregation paginates via `list_object_keys`

## UX States
- Loading: skeleton placeholders for cards and table
- Empty: "No runs yet" messaging
- Loaded: populated cards, chart, table

## Verification
- Test files: `services/api/tests/test_recipes.py` (run/stats wiring via the repo fake), `services/api/tests/test_structure.py`
- Required cases: stats with runs, stats with empty bucket, API error fallback
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green, no ruff violations

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
- [Augmentation](augmentation.md)
