export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Image-specific
  image_width: number | null;
  image_height: number | null;
  exif: Record<string, string> | null;
  // PDF-specific
  pdf_pages: number | null;
  pdf_author: string | null;
  pdf_title: string | null;
  // Audio/Video
  duration_seconds: number | null;
  codec: string | null;
  bitrate: number | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
}

// ----- Augmentation pipeline -----

export interface TransformParam {
  name: string;
  type: string;
  default: number | boolean | number[] | null;
  min: number | null;
  max: number | null;
  description: string;
}

export interface TransformSpec {
  id: string;
  label: string;
  category: string;
  description: string;
  supports_bbox: boolean;
  params: TransformParam[];
}

export interface RecipeTransform {
  id: string;
  params: Record<string, unknown>;
  p: number;
}

export interface RecipeCreate {
  name: string;
  description: string;
  seed_prefix: string;
  transforms: RecipeTransform[];
  variants_per_image: number;
  random_seed: number | null;
  bbox_format: string | null;
}

export interface Recipe {
  id: string;
  version: number;
  name: string;
  description: string;
  seed_prefix: string;
  transforms: RecipeTransform[];
  variants_per_image: number;
  random_seed: number | null;
  bbox_format: string | null;
  created_at: string;
  updated_at: string;
  run_count: number;
}

export interface RunResult {
  run_id: string;
  recipe_id: string;
  source_count: number;
  variants_written: number;
  bytes_written: number;
  bytes_written_human: string;
  multiplication_factor: number;
  truncated: boolean;
  created_at: string;
}

export interface RunSummary {
  run_id: string;
  recipe_id: string;
  source_count: number;
  variants_written: number;
  bytes_written: number;
  bytes_written_human: string;
  multiplication_factor: number;
  created_at: string;
}

export interface VariantPair {
  seed_key: string;
  seed_filename: string;
  variant_keys: string[];
}

export interface RunManifest {
  run_id: string;
  recipe_id: string;
  recipe_version: number;
  recipe_snapshot: Recipe;
  seed_prefix: string;
  random_seed: number;
  source_keys: string[];
  variants_per_image: number;
  bbox_format: string | null;
  library_versions: Record<string, string>;
  created_at: string;
}

export interface RunDetail {
  manifest: RunManifest;
  pairs: VariantPair[];
  variants_written: number;
  bytes_written: number;
  bytes_written_human: string;
  multiplication_factor: number;
}

export interface VariantsPerRun {
  run_label: string;
  variants: number;
}

export interface AugmentStats {
  seed_images: number;
  recipe_count: number;
  total_variants: number;
  multiplication_factor: number;
  bytes_written: number;
  bytes_written_human: string;
  recent_runs: RunSummary[];
  variants_per_run: VariantsPerRun[];
}

export interface GalleryThumbnail {
  key: string;
  url: string;
}

export interface GalleryRun {
  recipe_id: string;
  recipe_name: string;
  run_id: string;
  variant_count: number;
  created_at: string;
  thumbnails: GalleryThumbnail[];
}
