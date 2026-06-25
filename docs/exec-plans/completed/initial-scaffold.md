# Build plan — `albumentations-dataset-augmentation`

Source of truth (Phase 0 clone, the ONLY valid starter-kit source):
`.claude/scratch/vcsk-7a197566-dbb4-4f7f-8924-4990be3d60a4/`

## 1. Purpose

A reproducible, version-controlled **image dataset augmentation pipeline** on Backblaze B2.
Computer-vision engineers and ML researchers point it at a small labeled image
dataset stored in B2, define a configurable **Albumentations** transform graph (a
named, versioned *recipe*), and run it to generate **N augmented variants per source
image** — multiplying a few hundred seed images into thousands of training-ready
examples. Both the seed dataset and the expanded output live on B2, and every run
writes a manifest that pins the exact recipe + random seed + source list so the
augmentation can be reproduced bit-for-bit. The headline is deliberate **write
amplification**: 500 seeds × 10 variants = 5,000 images written to B2 in one run.
Runs entirely on local OSS (Albumentations) — **B2 credentials only, no second API key.**

## 2. Architecture delta from vibe-coding-starter-kit

The starter kit is the ceiling. Strip what augmentation doesn't need; reuse everything else.

### KEEP (as-is — starter contract, non-negotiable)
- `apps/web/src/components/ui/**` — shadcn primitives. Build new screens with these; never edit them.
- Design tokens in `apps/web/src/app/globals.css` + the `/design` reference page + its sidebar "Reference" link.
- **Full-bucket File Explorer** — `/files` route, `apps/web/src/app/files/`, `apps/web/src/components/files/**`. **NEVER removable** (skill rule). Sidebar "Files" entry stays.
- **Upload** — `/upload` route, `apps/web/src/app/upload/`, `apps/web/src/components/upload/**`. This is how seed datasets get into B2. Sidebar "Upload" entry stays.
- Backend layering `types → config → repo → service → runtime`, the structural tests (`tests/test_structure.py`), JSON logging, `/health`, `/metrics`, request-id middleware, the doctor/dev scripts, TanStack-Query data layer (`lib/queries.ts`, `lib/api-client.ts`), `refresh-context`, error/empty-state patterns.
- `repo/b2_client.py` as the single home for all boto3/S3 I/O (extended — see §3).

### TRIM (remove from starter)
- The default **Dashboard** widgets that are upload-generic (`components/dashboard/upload-chart.tsx`, `recent-uploads-table.tsx`, `stats-cards.tsx`) are **adapted, not deleted** — replaced with augmentation metrics (see ADD). The starter explicitly designates the dashboard as the per-app rewrite surface.
- Nothing else is removed. Metadata extraction (`service/metadata.py`, Pillow/EXIF) is KEPT — image dimensions are genuinely useful for seed images.

### ADD (new for this sample)
- **Primary entity = Recipe** (augmentation recipe / versioned manifest). Full UI lifecycle — see §4.
  - Backend: `service/recipes.py` (recipe manifest CRUD + validation), `service/augment.py` (the Albumentations engine — build `A.Compose` from a recipe, apply, emit N variants; pure compute, lives in `service/` like the existing Pillow code, NOT `repo/`), `service/runs.py` (run orchestration, run manifest, stats), `types/recipes.py`, `types/runs.py`, `types/transforms.py`.
  - Routes: `runtime/recipes.py` (CRUD + `POST /recipes/{id}/run`), `runtime/runs.py` (read run history + detail), `runtime/transforms.py` (`GET /transforms` catalog that drives the recipe-builder UI), `runtime/augment_stats.py` (dashboard aggregates) — each wired through `lib/api-client.ts` + `lib/queries.ts`.
  - Frontend pages: `/recipes` (list + create/edit/delete), `/recipes/[id]` (detail + Run + run history), `/runs/[recipeId]/[runId]` (run detail: seed→variant gallery, stats, reproducibility manifest, Re-run), and the recipe-builder form component.
- **Sample-specific scoped asset explorer (mandatory add):** a **`/gallery`** page — an "Augmented Output" library scoped to the `augmented/` prefix only, showing the expanded dataset grouped by recipe/run with image thumbnails and seed→variant pairing. This is distinct from and additional to the kept full-bucket Files explorer (which is never removed). Sidebar "Gallery" entry added.
- **Dashboard rewrite** — augmentation metrics: total seed images, recipe count, total augmented variants produced, dataset multiplication factor (avg N×), bytes written to B2, recent runs table, "variants produced per run" chart. All aggregations flow `runtime → service → repo` and surface via TanStack-Query hooks (no bare `useEffect+fetch`).
- Sidebar nav (`app-sidebar.tsx`) gains **Recipes**, **Gallery** (and the Dashboard stays Home `/`). Files + Upload + Settings + Design System stay.

**Bucket-explorer tension note:** none — the full-bucket explorer is kept verbatim AND the scoped `/gallery` explorer is added alongside it. No conflict.

### B2 object layout
```
seeds/<dataset>/...                          seed images (uploaded via /upload, browsed via /files)
recipes/<recipe-id>.json                     versioned recipe manifest (Albumentations A.to_dict() + meta)
augmented/<recipe-id>/<run-id>/_run.json     run manifest: recipe snapshot + seed list + seed value + versions
augmented/<recipe-id>/<run-id>/<img>__aug<k>.<ext>   the N× augmented variants
augmented/<recipe-id>/<run-id>/<img>__aug<k>.txt     (optional) transformed YOLO/bbox sidecar where annotations exist
```

## 3. B2 surface (S3-compatible API only — no b2-native, no deviation)
- `put_object` — write augmented images, recipe manifests, run manifests.
- `get_object` — **NEW repo helper `get_object_bytes(key) -> bytes`** (starter lacks a download helper) to read seed image bytes for augmentation + read manifests.
- `list_objects_v2` (prefix-scoped) — list seeds, recipes, runs, gallery.
- `head_object` — object metadata.
- `delete_object` — delete a recipe manifest (scoped to `recipes/<id>.json`; outputs under `augmented/<id>/` are NOT auto-purged — documented, optional explicit purge only).
- `generate_presigned_url` — serve/download augmented images, manifests, seed previews.
All via the existing S3 client in `repo/b2_client.py` with `user_agent_extra` set and `region_name=settings.b2_region`. **No b2-native API use anywhere.**

## 4. Key features (seed README + `docs/features/*.md`)
1. **Recipes (primary entity, full CRUD + run from the UI).**
2. **Albumentations augmentation engine** — configurable transform graph, N variants/image, deterministic via pinned seed.
3. **Reproducible run manifests** — every run pins recipe + seed + source list + library versions on B2; "Re-run" reproduces identical output.
4. **Write amplification at a glance** — dashboard shows N× dataset growth and bytes written.
5. **Scoped output Gallery** — browse the expanded dataset by run, seed→variant pairs.
6. **Optional bounding-box/mask transforms** — when a seed has a YOLO/COCO sidecar annotation, transforms apply to the geometry too and write a transformed sidecar next to each variant.

**External API provider:** NONE. Albumentations is a local pure-Python OSS library (`pip install albumentations`), no API key, no model download, no network. No provider cost. **No Genblaze** — the description does not mention Genblaze/`genblaze-*`/`genblaze-s3`, so provider-orchestration routing does not apply.

**Primary-entity lifecycle — Recipe (all five verbs built in the UI; nothing omitted):**
| Verb | UI surface | Backend |
|------|-----------|---------|
| **create** | "New Recipe" form (name, transforms from catalog w/ params + probability `p`, N variants, seed prefix, optional random seed, optional bbox format) | `POST /recipes` → write `recipes/<id>.json` |
| **read** | `/recipes` list + `/recipes/[id]` detail (transforms, params, run history) | `GET /recipes`, `GET /recipes/{id}` |
| **edit** | Edit form (pre-filled); save bumps manifest version | `PUT /recipes/{id}` |
| **delete** | Delete action w/ confirm (alert-dialog) | `DELETE /recipes/{id}` (scoped to manifest) |
| **run** | "Run" button on recipe detail → augment seed prefix, write N× variants + run manifest; "Re-run" on run detail | `POST /recipes/{id}/run` |

`omitted_ui_verbs = []` — every verb the app supports is user-accessible. Run is bounded for the demo (configurable max source images per synchronous run) and surfaces the multiplication factor; document the bound, don't silently cap.

## 5. Doc transforms
- **Rewrite:** `README.md` (full rebrand, augmentation framing, B2 layout, standard env vars), `docs/features/dashboard.md` (augmentation metrics), `docs/app-workflows.md` (ingest→configure→augment→store→serve journey), `ARCHITECTURE.md` (augment service + recipe/run layout + B2 layout).
- **Keep (light touch):** `docs/features/file-upload.md` (frame as seed ingest), `docs/features/file-browser.md` (full-bucket explorer), `docs/features/metadata-extraction.md`, `docs/SECURITY.md`, `docs/RELIABILITY.md`, `docs/dev-workflows.md`, `docs/design-system.md`, `AGENTS.md` (update repo map + commands only).
- **Add (from `docs/features/_template.md`):** `docs/features/recipes.md`, `docs/features/augmentation.md`, `docs/features/gallery.md`.
- Move this plan to `docs/exec-plans/completed/initial-scaffold.md` on PASS (Phase 5).

## 6. Rename table
| From (starter) | To (this sample) |
|---|---|
| `vibe-coding-starter-kit` (kebab, repo + pkg name + `@vibe-coding-starter-kit/*` scopes + clone URL + commit msg) | `albumentations-dataset-augmentation` |
| `OSS Starter Kit` / `Vibe Coding Starter Kit` (Title Case, `APP_NAME`, README H1) | `Albumentations Augmentation Pipeline` |
| `APP_DESCRIPTION` "File management dashboard powered by Backblaze B2" | "Reproducible image dataset augmentation pipeline powered by Backblaze B2" |
| FastAPI `title="OSS Starter Kit API"` / description | `Albumentations Augmentation Pipeline API` / augmentation-focused desc |
| `user_agent_extra="b2ai-oss-start"` | `user_agent_extra="albumentations-dataset-augmentation"` |
| `utm_content=b2ai-oss-start` (all README + sidebar B2 links) | `utm_content=albumentations-dataset-augmentation` |
| header `pageTitles` map | add `/recipes`→"Recipes", `/gallery`→"Gallery", `/runs`→"Runs" (dynamic `[id]` segments derive automatically; verify no stale-name/"Page" fallback in any breadcrumb) |
| **Env vars → parent CLAUDE.md Standard #3 (b2-doctor):** | |
| `B2_KEY_ID` → | `B2_APPLICATION_KEY_ID` |
| `B2_ENDPOINT` (full URL) → | `B2_REGION` (default `us-west-004`); derive endpoint via `@property b2_endpoint = f"https://s3.{b2_region}.backblazeb2.com"` |
| `B2_PUBLIC_URL` → | `B2_PUBLIC_URL_BASE` |
| `B2_APPLICATION_KEY`, `B2_BUCKET_NAME` | unchanged (already standard) |

Apply env renames in `.env.example`, `config/settings.py` (attr names + `b2_region` + derived endpoint property + pass `region_name`), `services/api/main.py` (`REQUIRED_B2_SETTINGS`, `PLACEHOLDER_VALUES`), `repo/b2_client.py` (attr refs), README setup steps, and `scripts/doctor.mjs` if it checks env names. Custom user agent must remain set on the S3 client (Standard #2). S3-compatible API is the only path (Standard #1).

## 7. Build acceptance (must pass before commit)
`pnpm install` clean · `pnpm lint` · `pnpm build` (no unused-import/type errors) · `pnpm lint:api` (ruff) · `pnpm test:api` (incl. new augment/recipe tests + the structural boundary tests still green: no boto3 outside `repo/`, files <300 lines, layers intact) · all new routes reachable from the sidebar · header breadcrumb shows the new app name + correct page titles on every route. Add `albumentations` (and `numpy`) to `services/api/requirements.txt`; add a no-network unit test that builds an `A.Compose` from a sample recipe and asserts N variants are produced from one in-memory image (use a generated numpy array, no B2).
