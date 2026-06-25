"use client";

import { useMemo, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTransforms } from "@/lib/queries";
import type {
  Recipe,
  RecipeCreate,
  RecipeTransform,
} from "@albumentations-dataset-augmentation/shared";

const BBOX_FORMATS = ["none", "yolo", "pascal_voc", "coco"] as const;

interface RecipeFormProps {
  initial?: Recipe;
  submitting?: boolean;
  onSubmit: (payload: RecipeCreate) => void;
}

export function RecipeForm({ initial, submitting, onSubmit }: RecipeFormProps) {
  const { data: catalog = [], isLoading: catalogLoading } = useTransforms();

  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [seedPrefix, setSeedPrefix] = useState(initial?.seed_prefix ?? "seeds/");
  const [variants, setVariants] = useState(initial?.variants_per_image ?? 5);
  const [randomSeed, setRandomSeed] = useState<string>(
    initial?.random_seed !== null && initial?.random_seed !== undefined
      ? String(initial.random_seed)
      : ""
  );
  const [bboxFormat, setBboxFormat] = useState<string>(initial?.bbox_format ?? "none");
  const [steps, setSteps] = useState<RecipeTransform[]>(initial?.transforms ?? []);
  const [picker, setPicker] = useState<string>("");

  const byId = useMemo(
    () => Object.fromEntries(catalog.map((t) => [t.id, t])),
    [catalog]
  );

  function addStep() {
    if (!picker) return;
    const spec = byId[picker];
    if (!spec) return;
    const params: Record<string, unknown> = {};
    for (const p of spec.params) {
      if (p.default !== null && p.default !== undefined) params[p.name] = p.default;
    }
    setSteps((s) => [...s, { id: picker, params, p: 1.0 }]);
    setPicker("");
  }

  function removeStep(idx: number) {
    setSteps((s) => s.filter((_, i) => i !== idx));
  }

  function setStepParam(idx: number, key: string, value: number) {
    setSteps((s) =>
      s.map((step, i) =>
        i === idx ? { ...step, params: { ...step.params, [key]: value } } : step
      )
    );
  }

  function setStepProb(idx: number, value: number) {
    setSteps((s) => s.map((step, i) => (i === idx ? { ...step, p: value } : step)));
  }

  function submit() {
    if (!name.trim()) {
      toast.error("Give the recipe a name.");
      return;
    }
    if (steps.length === 0) {
      toast.error("Add at least one transform.");
      return;
    }
    const payload: RecipeCreate = {
      name: name.trim(),
      description,
      seed_prefix: seedPrefix.trim() || "seeds/",
      transforms: steps,
      variants_per_image: variants,
      random_seed: randomSeed === "" ? null : Number(randomSeed),
      bbox_format: bboxFormat === "none" ? null : bboxFormat,
    };
    onSubmit(payload);
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="name">Recipe name</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Flip + Color Jitter" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="seed">Seed prefix (B2)</Label>
          <Input id="seed" value={seedPrefix} onChange={(e) => setSeedPrefix(e.target.value)} placeholder="seeds/cats/" />
        </div>
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="desc">Description</Label>
          <Textarea id="desc" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="variants">Variants per image</Label>
          <Input
            id="variants"
            type="number"
            min={1}
            max={50}
            value={variants}
            onChange={(e) => setVariants(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="rseed">Random seed (optional)</Label>
          <Input id="rseed" type="number" value={randomSeed} onChange={(e) => setRandomSeed(e.target.value)} placeholder="leave blank for 42" />
        </div>
        <div className="space-y-2">
          <Label>Bounding-box format</Label>
          <Select value={bboxFormat} onValueChange={setBboxFormat}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {BBOX_FORMATS.map((f) => (
                <SelectItem key={f} value={f}>
                  {f}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-end gap-2">
          <div className="flex-1 space-y-2">
            <Label>Add a transform</Label>
            <Select value={picker} onValueChange={setPicker} disabled={catalogLoading}>
              <SelectTrigger>
                <SelectValue placeholder="Choose an Albumentations transform" />
              </SelectTrigger>
              <SelectContent>
                {catalog.map((t) => (
                  <SelectItem key={t.id} value={t.id}>
                    {t.label} · {t.category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button type="button" variant="secondary" onClick={addStep} disabled={!picker}>
            <Plus className="h-4 w-4" /> Add
          </Button>
        </div>

        {catalogLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : steps.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No transforms yet. Pick one above to start building the graph.
          </p>
        ) : (
          <div className="space-y-3">
            {steps.map((step, idx) => {
              const spec = byId[step.id];
              return (
                <Card key={`${step.id}-${idx}`}>
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge>{spec?.label ?? step.id}</Badge>
                        {spec && (
                          <span className="text-xs text-muted-foreground">
                            {spec.category}
                          </span>
                        )}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => removeStep(idx)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="space-y-1">
                        <Label className="text-xs">Probability (p)</Label>
                        <Input
                          type="number"
                          step="0.1"
                          min={0}
                          max={1}
                          value={step.p}
                          onChange={(e) => setStepProb(idx, Number(e.target.value))}
                        />
                      </div>
                      {(spec?.params ?? []).map((p) => (
                        <div key={p.name} className="space-y-1">
                          <Label className="text-xs">{p.name}</Label>
                          <Input
                            type="number"
                            value={Number(step.params[p.name] ?? p.default ?? 0)}
                            min={p.min ?? undefined}
                            max={p.max ?? undefined}
                            onChange={(e) =>
                              setStepParam(idx, p.name, Number(e.target.value))
                            }
                          />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button onClick={submit} disabled={submitting}>
          {submitting ? "Saving…" : initial ? "Save changes" : "Create recipe"}
        </Button>
      </div>
    </div>
  );
}
