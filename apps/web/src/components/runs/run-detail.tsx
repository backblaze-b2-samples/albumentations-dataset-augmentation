"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { getObjectPreview } from "@/lib/api-client";
import { useRunDetail, useRunRecipe } from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import type { VariantPair } from "@albumentations-dataset-augmentation/shared";

// Resolves presigned image URLs for a key, rendering an <img> once ready.
function PreviewImage({ objectKey, alt }: { objectKey: string; alt: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    getObjectPreview(objectKey)
      .then((r) => active && setUrl(r.url))
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, [objectKey]);

  if (failed) {
    return (
      <div className="aspect-square rounded-md bg-muted flex items-center justify-center text-[10px] text-muted-foreground">
        n/a
      </div>
    );
  }
  if (!url) return <Skeleton className="aspect-square rounded-md" />;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={url} alt={alt} className="aspect-square w-full rounded-md object-cover" />
  );
}

function SeedRow({ pair }: { pair: VariantPair }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm">
        <Badge variant="secondary">seed</Badge>
        <span className="font-mono text-xs truncate">{pair.seed_filename}</span>
        <span className="text-xs text-muted-foreground">
          → {pair.variant_keys.length} variants
        </span>
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        <PreviewImage objectKey={pair.seed_key} alt={pair.seed_filename} />
        {pair.variant_keys.slice(0, 5).map((k) => (
          <PreviewImage key={k} objectKey={k} alt={k} />
        ))}
      </div>
    </div>
  );
}

export function RunDetail({
  recipeId,
  runId,
}: {
  recipeId: string;
  runId: string;
}) {
  const { data: detail, isLoading, error, refetch } = useRunDetail(recipeId, runId);
  const rerun = useRunRecipe(recipeId);

  function handleRerun() {
    if (!detail) return;
    rerun.mutate(
      {
        seed_prefix: detail.manifest.seed_prefix,
        random_seed: detail.manifest.random_seed,
      },
      {
        onSuccess: (res) =>
          toast.success(
            `Re-run complete — reproduced ${res.variants_written} variants (seed ${detail.manifest.random_seed})`
          ),
        onError: (e) => toast.error(e.message),
      }
    );
  }

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (error) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!detail) return null;

  const m = detail.manifest;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-5">
        <div>
          <Link
            href={`/recipes/${recipeId}`}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3 w-3" /> Back to recipe
          </Link>
          <h1 className="page-title mt-1 font-mono">{runId.slice(0, 12)}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {m.recipe_snapshot.name} (v{m.recipe_version}) · {formatDate(m.created_at)}
          </p>
        </div>
        <Button onClick={handleRerun} disabled={rerun.isPending}>
          <RefreshCw className="h-4 w-4" /> {rerun.isPending ? "Re-running…" : "Re-run"}
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Seeds</CardTitle>
          </CardHeader>
          <CardContent className="stat-value">{m.source_keys.length}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Variants</CardTitle>
          </CardHeader>
          <CardContent className="stat-value">{detail.variants_written}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Multiplication</CardTitle>
          </CardHeader>
          <CardContent className="stat-value">{detail.multiplication_factor}×</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Written to B2</CardTitle>
          </CardHeader>
          <CardContent className="stat-value">{detail.bytes_written_human}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">Reproducibility manifest</CardTitle>
        </CardHeader>
        <CardContent className="p-5 grid gap-2 sm:grid-cols-2 text-sm">
          <div>
            <span className="text-muted-foreground">Seed prefix:</span>{" "}
            <code className="text-xs">{m.seed_prefix}</code>
          </div>
          <div>
            <span className="text-muted-foreground">Random seed:</span> {m.random_seed}
          </div>
          <div>
            <span className="text-muted-foreground">Variants/image:</span> {m.variants_per_image}
          </div>
          <div>
            <span className="text-muted-foreground">Bbox format:</span> {m.bbox_format ?? "none"}
          </div>
          <div className="sm:col-span-2">
            <span className="text-muted-foreground">Library versions:</span>{" "}
            {Object.entries(m.library_versions).map(([lib, v]) => (
              <Badge key={lib} variant="outline" className="ml-1 text-[10px]">
                {lib} {v}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">Seed → variant gallery</CardTitle>
        </CardHeader>
        <CardContent className="p-5 space-y-6">
          {detail.pairs.map((pair) => (
            <SeedRow key={pair.seed_key} pair={pair} />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
