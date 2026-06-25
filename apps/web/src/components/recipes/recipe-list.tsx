"use client";

import { useState } from "react";
import Link from "next/link";
import { Layers, Plus, Trash2, Play } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { RecipeForm } from "./recipe-form";
import { useCreateRecipe, useDeleteRecipe, useRecipes } from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import type { RecipeCreate } from "@albumentations-dataset-augmentation/shared";

export function RecipeList() {
  const { data: recipes = [], isLoading, error, refetch } = useRecipes();
  const create = useCreateRecipe();
  const remove = useDeleteRecipe();
  const [open, setOpen] = useState(false);

  function handleCreate(payload: RecipeCreate) {
    create.mutate(payload, {
      onSuccess: () => {
        toast.success("Recipe created");
        setOpen(false);
      },
      onError: (e) => toast.error(e.message),
    });
  }

  function handleDelete(id: string) {
    remove.mutate(id, {
      onSuccess: () => toast.success("Recipe deleted (augmented output retained)"),
      onError: (e) => toast.error(e.message),
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="h-8">
              <Plus className="h-3.5 w-3.5" /> New recipe
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>New augmentation recipe</DialogTitle>
            </DialogHeader>
            <RecipeForm submitting={create.isPending} onSubmit={handleCreate} />
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="p-0">
            <ErrorState error={error} onRetry={() => refetch()} />
          </CardContent>
        </Card>
      ) : recipes.length === 0 ? (
        <Card>
          <CardContent className="p-0">
            <EmptyState
              icon={Layers}
              title="No recipes yet"
              description="Create your first Albumentations recipe to start expanding seed datasets."
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {recipes.map((recipe) => (
            <Card key={recipe.id} className="card-hover flex flex-col">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base">
                    <Link href={`/recipes/${recipe.id}`} className="hover:underline">
                      {recipe.name}
                    </Link>
                  </CardTitle>
                  <Badge variant="secondary">v{recipe.version}</Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col gap-3">
                <div className="flex flex-wrap gap-1">
                  {recipe.transforms.slice(0, 4).map((t, i) => (
                    <Badge key={i} variant="outline" className="text-[10px]">
                      {t.id}
                    </Badge>
                  ))}
                  {recipe.transforms.length > 4 && (
                    <Badge variant="outline" className="text-[10px]">
                      +{recipe.transforms.length - 4}
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  {recipe.variants_per_image}× variants · {recipe.run_count} run
                  {recipe.run_count === 1 ? "" : "s"} · updated{" "}
                  {formatDate(recipe.updated_at)}
                </div>
                <div className="mt-auto flex items-center gap-2 pt-2">
                  <Button asChild size="sm" variant="secondary" className="flex-1">
                    <Link href={`/recipes/${recipe.id}`}>
                      <Play className="h-3.5 w-3.5" /> Open & run
                    </Link>
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button size="icon" variant="ghost" className="h-8 w-8">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete this recipe?</AlertDialogTitle>
                        <AlertDialogDescription>
                          The recipe manifest <code>{recipe.id}</code> will be removed.
                          Augmented output already written to B2 is retained.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={() => handleDelete(recipe.id)}>
                          Delete recipe
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
