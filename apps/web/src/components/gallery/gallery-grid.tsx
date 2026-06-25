"use client";

import Link from "next/link";
import { Images, ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useGallery } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function GalleryGrid() {
  const { data: runs = [], isLoading, error, refetch } = useGallery();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
    );
  }
  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }
  if (runs.length === 0) {
    return (
      <Card>
        <CardContent className="p-0">
          <EmptyState
            icon={Images}
            title="No augmented output yet"
            description="Run a recipe to populate the augmented/ prefix and see thumbnails here."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {runs.map((run) => (
        <Card key={`${run.recipe_id}-${run.run_id}`} className="card-hover">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-base">{run.recipe_name}</CardTitle>
              <Badge variant="secondary">{run.variant_count} variants</Badge>
            </div>
            <div className="text-xs text-muted-foreground">
              run <span className="font-mono">{run.run_id.slice(0, 8)}</span> ·{" "}
              {formatDate(run.created_at)}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {run.thumbnails.map((t) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={t.key}
                  src={t.url}
                  alt={t.key}
                  className="aspect-square w-full rounded-md object-cover"
                />
              ))}
            </div>
            <Link
              href={`/runs/${run.recipe_id}/${run.run_id}`}
              className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              View run detail <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
