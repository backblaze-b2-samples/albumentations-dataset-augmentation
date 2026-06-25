import { RecipeList } from "@/components/recipes/recipe-list";

export default function RecipesPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Recipes</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Versioned Albumentations augmentation recipes. Create, edit, run, and
          re-run them to expand seed datasets stored in B2.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <RecipeList />
      </div>
    </div>
  );
}
