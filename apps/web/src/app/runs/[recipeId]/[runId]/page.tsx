import { RunDetail } from "@/components/runs/run-detail";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ recipeId: string; runId: string }>;
}) {
  const { recipeId, runId } = await params;
  return (
    <div className="animate-fade-in">
      <RunDetail recipeId={recipeId} runId={runId} />
    </div>
  );
}
