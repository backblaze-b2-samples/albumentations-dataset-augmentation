import { GalleryGrid } from "@/components/gallery/gallery-grid";

export default function GalleryPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Gallery</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Augmented output library — scoped to the <code>augmented/</code> prefix
          and grouped by run. For the full bucket, see Files.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <GalleryGrid />
      </div>
    </div>
  );
}
