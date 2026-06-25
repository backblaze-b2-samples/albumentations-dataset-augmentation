<!-- last_verified: 2026-06-24 -->
# App Workflows

The end-to-end journey: **ingest → configure → augment → store → serve.**

## 1. Ingest seed images

- User navigates to `/upload`
- Drops or selects seed images in the dropzone
- Client validates file size (max 100MB) and type
- Files land in B2 under `uploads/`; users can also stage images anywhere under their chosen seed prefix (e.g. `seeds/cats/`)
- See: [File Upload](features/file-upload.md)

## 2. Configure a recipe

- User navigates to `/recipes` and clicks **New recipe**
- In the builder: pick Albumentations transforms from the catalog (`GET /transforms`), set each transform's params and apply probability `p`, choose N variants per image, a seed prefix, an optional pinned random seed, and an optional bounding-box format
- Save → `POST /recipes` writes `recipes/<id>.json` to B2
- Edit (`PUT`) bumps the manifest version; Delete (`DELETE`) removes the manifest only (output retained)
- See: [Recipes](features/recipes.md)

## 3. Augment (run the recipe)

- On `/recipes/[id]`, the user clicks **Run**
- The backend lists seed images, reads each one's bytes, builds the `A.Compose` once, and applies it N times per seed
- A toast reports the run: variants written, multiplication factor, and whether the source list was capped for the demo
- See: [Augmentation](features/augmentation.md)

## 4. Store (write amplification + reproducibility)

- Each variant is written to `augmented/<recipe-id>/<run-id>/<img>__aug<k>.<ext>`
- A `_run.json` manifest pins the recipe snapshot, seed list, random seed, and library versions
- The dashboard (`/`) shows seeds in, variants out, multiplication factor, and bytes written — the headline write amplification
- See: [Dashboard](features/dashboard.md)

## 5. Serve (browse + reproduce)

- `/gallery` — the augmented output library, scoped to `augmented/` and grouped by run, with thumbnails
- `/runs/[recipeId]/[runId]` — seed→variant gallery, run stats, the full reproducibility manifest, and a **Re-run** button that reproduces identical output
- `/files` — the full-bucket explorer (seeds, recipes, and augmented output)
- See: [Gallery](features/gallery.md), [File Browser](features/file-browser.md)
