export default function Loading() {
  return (
    <div className="flex flex-col gap-8 animate-pulse pb-10">
      <div className="space-y-2">
        <div className="h-10 w-64 bg-muted rounded-md" />
        <div className="h-5 w-96 bg-muted rounded-md" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-xl h-64 p-6" />
          <div className="bg-card border border-border rounded-xl h-80 p-6" />
        </div>
        <div className="flex flex-col gap-6">
          <div className="bg-card border border-border rounded-xl h-48 p-6" />
          <div className="bg-card border border-border rounded-xl h-96 p-6" />
        </div>
      </div>
    </div>
  );
}
