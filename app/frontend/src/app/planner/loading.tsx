export default function Loading() {
  return (
    <div className="flex flex-col gap-8 animate-pulse pb-10">
      <div className="space-y-2">
        <div className="h-10 w-64 bg-muted rounded-md" />
        <div className="h-5 w-96 bg-muted rounded-md" />
      </div>

      <div className="bg-card border border-border rounded-xl p-8 flex flex-col gap-6">
        <div className="h-8 w-48 bg-muted rounded-md mb-4" />
        <div className="h-12 w-full bg-muted rounded-md" />
        <div className="h-12 w-full bg-muted rounded-md" />
        <div className="h-12 w-full bg-muted rounded-md" />
      </div>
    </div>
  );
}
