"use client";

import { useState } from "react";
import Link from "next/link";
import { Play, Pencil, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RecipeForm } from "./recipe-form";
import {
  useRecipe,
  useRuns,
  useRunRecipe,
  useUpdateRecipe,
} from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import type { RecipeCreate } from "@albumentations-dataset-augmentation/shared";

export function RecipeDetail({ recipeId }: { recipeId: string }) {
  const { data: recipe, isLoading, error, refetch } = useRecipe(recipeId);
  const { data: runs = [] } = useRuns(recipeId);
  const run = useRunRecipe(recipeId);
  const update = useUpdateRecipe(recipeId);
  const [editOpen, setEditOpen] = useState(false);

  function handleRun() {
    run.mutate(
      {},
      {
        onSuccess: (res) => {
          toast.success(
            `Run complete — ${res.variants_written} variants (${res.multiplication_factor}×)` +
              (res.truncated ? " · source list was capped for the demo" : "")
          );
        },
        onError: (e) => toast.error(e.message),
      }
    );
  }

  function handleEdit(payload: RecipeCreate) {
    update.mutate(payload, {
      onSuccess: () => {
        toast.success("Recipe updated — version bumped");
        setEditOpen(false);
      },
      onError: (e) => toast.error(e.message),
    });
  }

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (error) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!recipe) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-5">
        <div>
          <Link
            href="/recipes"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3 w-3" /> All recipes
          </Link>
          <h1 className="page-title mt-1">{recipe.name}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {recipe.description || "No description"} · seeds at{" "}
            <code className="text-xs">{recipe.seed_prefix}</code>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => setEditOpen(true)}>
            <Pencil className="h-4 w-4" /> Edit
          </Button>
          <Button onClick={handleRun} disabled={run.isPending}>
            <Play className="h-4 w-4" /> {run.isPending ? "Running…" : "Run"}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Variants per image</CardTitle>
          </CardHeader>
          <CardContent className="stat-value">{recipe.variants_per_image}×</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Random seed</CardTitle>
          </CardHeader>
          <CardContent className="stat-value">{recipe.random_seed ?? 42}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Bounding boxes</CardTitle>
          </CardHeader>
          <CardContent className="stat-value">{recipe.bbox_format ?? "none"}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">Transform graph</CardTitle>
        </CardHeader>
        <CardContent className="p-5 space-y-2">
          {recipe.transforms.map((t, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Badge variant="secondary">{i + 1}</Badge>
                <span className="font-medium">{t.id}</span>
                <span className="text-xs text-muted-foreground">
                  {Object.entries(t.params)
                    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                    .join(", ")}
                </span>
              </div>
              <Badge variant="outline">p={t.p}</Badge>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">Run history</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {runs.length === 0 ? (
            <EmptyState
              icon={Play}
              title="No runs yet"
              description="Hit Run to augment the seed prefix and write variants to B2."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40 hover:bg-muted/40">
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Run</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Seeds</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Variants</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Factor</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Bytes</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((r) => (
                  <TableRow key={r.run_id} className="table-row-hover">
                    <TableCell>
                      <Link
                        href={`/runs/${recipeId}/${r.run_id}`}
                        className="font-mono text-xs hover:underline"
                      >
                        {r.run_id.slice(0, 8)}
                      </Link>
                    </TableCell>
                    <TableCell className="tabular-nums">{r.source_count}</TableCell>
                    <TableCell className="tabular-nums">{r.variants_written}</TableCell>
                    <TableCell className="font-mono text-xs">{r.multiplication_factor}×</TableCell>
                    <TableCell className="text-muted-foreground">{r.bytes_written_human}</TableCell>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {formatDate(r.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit recipe</DialogTitle>
          </DialogHeader>
          <RecipeForm initial={recipe} submitting={update.isPending} onSubmit={handleEdit} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
