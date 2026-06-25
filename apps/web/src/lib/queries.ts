"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  createRecipe,
  deleteFile,
  deleteRecipe,
  getAugmentStats,
  getFiles,
  getFileStats,
  getGallery,
  getPreviewUrl,
  getRecipe,
  getRecipes,
  getRunDetail,
  getRuns,
  getTransforms,
  getUploadActivity,
  runRecipe,
  updateRecipe,
} from "@/lib/api-client";
import type {
  FileMetadata,
  RecipeCreate,
} from "@albumentations-dataset-augmentation/shared";

// Single source of truth for query keys. Keep these tightly scoped so that
// invalidating "files" doesn't blow away unrelated caches, and so an IDE
// "find usages" of `qk.files` reveals every consumer.
export const qk = {
  all: ["b2"] as const,
  files: (prefix?: string, limit?: number) =>
    [...qk.all, "files", prefix ?? "", limit ?? 100] as const,
  stats: () => [...qk.all, "stats"] as const,
  uploadActivity: (days: number) =>
    [...qk.all, "stats", "activity", days] as const,
  preview: (key: string) => [...qk.all, "preview", key] as const,
  transforms: () => [...qk.all, "transforms"] as const,
  recipes: () => [...qk.all, "recipes"] as const,
  recipe: (id: string) => [...qk.all, "recipes", id] as const,
  runs: (recipeId: string) => [...qk.all, "runs", recipeId] as const,
  runDetail: (recipeId: string, runId: string) =>
    [...qk.all, "runs", recipeId, runId] as const,
  augmentStats: () => [...qk.all, "augment-stats"] as const,
  gallery: () => [...qk.all, "gallery"] as const,
};

export function useFiles(prefix = "", limit = 100) {
  return useQuery<FileMetadata[], ApiError>({
    queryKey: qk.files(prefix, limit),
    queryFn: () => getFiles(prefix, limit),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: qk.stats(),
    queryFn: getFileStats,
  });
}

export function useUploadActivity(days = 7) {
  return useQuery({
    queryKey: qk.uploadActivity(days),
    queryFn: () => getUploadActivity(days),
  });
}

// Presigned preview URL — only fetched when `enabled` is true (e.g., when
// the dialog opens for a specific file). Kept short-lived (60s) because
// the URL itself has a presigned expiry and is cheap to regenerate.
export function usePreviewUrl(key: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.preview(key ?? ""),
    queryFn: () => getPreviewUrl(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileKey: string) => deleteFile(fileKey),
    // After delete, blow away every cached file list + stats. Cheap and
    // correct — the dashboard re-fetches lazily as components remount.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

// ----- Augmentation pipeline -----

export function useTransforms() {
  return useQuery({
    queryKey: qk.transforms(),
    queryFn: getTransforms,
    staleTime: Infinity, // catalog is static
  });
}

export function useRecipes() {
  return useQuery({
    queryKey: qk.recipes(),
    queryFn: getRecipes,
  });
}

export function useRecipe(id: string | undefined) {
  return useQuery({
    queryKey: qk.recipe(id ?? ""),
    queryFn: () => getRecipe(id as string),
    enabled: !!id,
  });
}

export function useRuns(recipeId: string | undefined) {
  return useQuery({
    queryKey: qk.runs(recipeId ?? ""),
    queryFn: () => getRuns(recipeId as string),
    enabled: !!recipeId,
  });
}

export function useRunDetail(
  recipeId: string | undefined,
  runId: string | undefined
) {
  return useQuery({
    queryKey: qk.runDetail(recipeId ?? "", runId ?? ""),
    queryFn: () => getRunDetail(recipeId as string, runId as string),
    enabled: !!recipeId && !!runId,
  });
}

export function useAugmentStats() {
  return useQuery({
    queryKey: qk.augmentStats(),
    queryFn: getAugmentStats,
  });
}

export function useGallery() {
  return useQuery({
    queryKey: qk.gallery(),
    queryFn: getGallery,
  });
}

export function useCreateRecipe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RecipeCreate) => createRecipe(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.recipes() }),
  });
}

export function useUpdateRecipe(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RecipeCreate) => updateRecipe(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.recipes() });
      qc.invalidateQueries({ queryKey: qk.recipe(id) });
    },
  });
}

export function useDeleteRecipe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteRecipe(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.recipes() }),
  });
}

export function useRunRecipe(recipeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { seed_prefix?: string | null; random_seed?: number | null }) =>
      runRecipe(recipeId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.runs(recipeId) });
      qc.invalidateQueries({ queryKey: qk.recipe(recipeId) });
      qc.invalidateQueries({ queryKey: qk.augmentStats() });
      qc.invalidateQueries({ queryKey: qk.gallery() });
    },
  });
}
