<!-- last_verified: 2026-06-24 -->
# Architecture

The app is an **image dataset augmentation pipeline**: seed images in B2 are
expanded into N augmented variants per image by a local Albumentations engine,
and the expanded dataset plus a reproducibility manifest are written back to B2.

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - Dashboard with augmentation metrics (seeds, recipes, variants, multiplication factor, bytes written) + a variants-per-run chart
  - Recipes — the primary entity, with full create / read / edit / delete / run from the UI
  - Run detail — seed→variant gallery, run stats, reproducibility manifest, Re-run
  - Gallery — a scoped explorer of the `augmented/` prefix, grouped by run
  - File upload (seed ingest) with drag-and-drop, and the full-bucket file browser
  - Dark mode via `next-themes`
- **services/api/** — FastAPI backend (layered architecture)
  - REST API for recipe CRUD, runs, transform catalog, augmentation stats, gallery, plus the kept upload / files / health / metrics
  - **Albumentations augmentation engine** (`service/augment.py`) — pure compute, builds an `A.Compose` from a recipe and applies it to in-memory numpy images; no B2, no boto3
  - B2 S3 integration via boto3, confined to `repo/b2_client.py` (S3-compatible API only)
  - Health check endpoint with B2 connectivity verification
  - Structured JSON logging with request tracing; Prometheus-format metrics endpoint
- **packages/shared/** — TypeScript type definitions
  - Mirrors Pydantic models from the API (recipes, runs, transforms, augment stats, gallery, files)
  - Consumed by `apps/web/` as workspace dependency

## Backend Layering

The API follows a strict layered architecture:

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Data access (boto3 B2 client) — no business logic
  |
service/   Business logic — calls repo, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules

1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports (e.g., service must not import from runtime)
3. `boto3` only allowed in `repo/` layer
4. All boundary data uses Pydantic models (no raw dicts across layers)
5. Each file stays under 300 lines

### Directory Structure

```
services/api/
  main.py                  App entrypoint, middleware, router registration
  app/
    types/                 Pydantic models (files, upload, stats, recipes, runs, transforms, augment_stats)
    config/                Settings loaded from environment (incl. b2_region + derived endpoint, max_run_source_images)
    repo/                  B2 S3 client (data access layer) — incl. get_object_bytes / put_bytes / list_object_keys
    service/               Business logic: augment (pure engine), recipes, runs, augment_stats, transforms, upload, files, metadata
    runtime/               FastAPI route handlers (recipes, runs, transforms, augment_stats, upload, files, health, metrics)
  tests/                   pytest tests (structural + augment engine + recipe CRUD)
```

### Compute vs. I/O split

`service/augment.py` is the **pure augmentation engine**: it builds an
`A.Compose` from a recipe and applies it to numpy images, returning arrays and
bytes. It performs **no** B2 access. `service/runs.py` orchestrates a run —
listing seeds, reading bytes, invoking the engine, and writing variants — but
every byte in/out of B2 goes through `repo/b2_client.py`. This keeps the
`boto3`-only-in-`repo/` invariant intact while the heavy lifting stays testable
without network (see `tests/test_augment.py`).

## Boundary Invariants

- **No external SDK leakage**: `boto3` is only imported in `app/repo/`. All other layers interact with B2 through the repo interface.
- **No raw dicts at boundaries**: All data crossing layer boundaries uses typed Pydantic models.
- **No mutable globals**: Configuration is read-only after init. No module-level mutable state shared between layers.
- **Validated inputs**: All HTTP inputs validated by FastAPI/Pydantic. All file keys validated against prefix allowlist.

## Deployment

- **Local dev** — `pnpm dev` runs both services via `concurrently`
  - Web: `localhost:3000`
  - API: `localhost:8000`
- **Railway** — two services from the same repo
  - See `infra/railway/README.md` for configuration

## Data Stores

- **Backblaze B2** — object storage (S3-compatible API), the sole data store. No application database — recipes and runs are JSON manifests in B2.

### B2 object layout

```
seeds/<dataset>/...                                  seed images (uploaded via /upload, browsed via /files)
uploads/<file>                                       default landing prefix for the Upload page
recipes/<recipe-id>.json                             versioned recipe manifest (transforms + meta)
augmented/<recipe-id>/<run-id>/_run.json             run manifest: recipe snapshot + seed list + seed value + library versions
augmented/<recipe-id>/<run-id>/<img>__aug<k>.<ext>   the N× augmented variants
augmented/<recipe-id>/<run-id>/<img>__aug<k>.txt     (optional) transformed YOLO/bbox sidecar where annotations exist
```

- The endpoint is **derived from `B2_REGION`** (`https://s3.{region}.backblazeb2.com`) — no region literal appears in source.
- Listing/metadata via S3 `list_objects_v2` / `head_object`; reads via `get_object`; writes via `put_object`; serving via presigned URLs.

## External Services

- **Backblaze B2 S3 API** — file storage, retrieval, deletion, presigned URLs

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md) for full security documentation.

- **Frontend -> API** — CORS-restricted to configured origins
- **API -> B2** — authenticated via application keys, signature v4
- **Client -> B2** — presigned URLs for download (10-min expiry, forced attachment)

## Data Flows

- **Create recipe**: Browser -> `POST /recipes` -> `service/recipes` validates against the transform catalog + assigns id/version -> repo writes `recipes/<id>.json`
- **Run recipe**: Browser -> `POST /recipes/{id}/run` -> `service/runs` lists seeds (repo) -> reads seed bytes (repo `get_object_bytes`) -> `service/augment` builds `A.Compose` + applies N× -> repo writes each variant + `_run.json` -> returns a `RunResult` with the multiplication factor
- **Re-run**: same flow, seeded with the original run's `random_seed` + `seed_prefix` from its manifest -> reproduces identical output
- **Run detail / Gallery**: Browser -> `GET /recipes/{id}/runs/{run}` or `GET /gallery` -> `service` aggregates `list_object_keys` under `augmented/` + reads manifests -> presigned thumbnail URLs
- **Dashboard stats**: Browser -> `GET /augment/stats` -> `service/augment_stats` aggregates seeds + recipes + variants + bytes
- **Upload / List / Download / Delete** (kept from the starter): multipart upload to `uploads/`; `GET /files`; presigned download; `DELETE /files/{key}`

## Observability

- Structured JSON logging on all requests with `request_id`
- Request timing middleware (logs duration per request)
- `/metrics` endpoint (Prometheus format: request count, latency, upload count)
- `/health` endpoint (B2 connectivity check)

## Canonical Files

- Augmentation engine (pure compute): `services/api/app/service/augment.py`
- Run orchestration: `services/api/app/service/runs.py`
- Recipe CRUD: `services/api/app/service/recipes.py`
- Transform catalog: `services/api/app/service/transforms.py`
- Augmentation/gallery aggregation: `services/api/app/service/augment_stats.py`
- B2 data access (repo layer): `services/api/app/repo/b2_client.py`
- Pydantic models: `services/api/app/types/` (`recipes.py`, `runs.py`, `transforms.py`, `augment_stats.py`, `files.py`, `upload.py`, `stats.py`, `formatting.py`)
- Config (pydantic-settings): `services/api/app/config/settings.py`
- Structural + engine tests: `services/api/tests/test_structure.py`, `test_augment.py`, `test_recipes.py`
- Recipe builder UI: `apps/web/src/components/recipes/recipe-form.tsx`
- Frontend API client: `apps/web/src/lib/api-client.ts`
- Shared TypeScript types: `packages/shared/src/types.ts`

## Core Features

- [Recipes](docs/features/recipes.md)
- [Augmentation](docs/features/augmentation.md)
- [Gallery](docs/features/gallery.md)
- [File Upload](docs/features/file-upload.md)
- [File Browser](docs/features/file-browser.md)
- [Dashboard](docs/features/dashboard.md)
- [Metadata Extraction](docs/features/metadata-extraction.md)

## References

- [docs/SECURITY.md](docs/SECURITY.md) — security principles and implementation
- [docs/RELIABILITY.md](docs/RELIABILITY.md) — reliability expectations
- [AGENTS.md](AGENTS.md) — architectural invariants and agent instructions
