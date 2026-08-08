export default function Loading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse pb-10">
      <div className="space-y-2">
        <div className="h-10 w-64 bg-muted rounded-md" />
        <div className="h-5 w-96 bg-muted rounded-md" />
      </div>

      <div className="flex flex-col gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-5 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <div className="h-6 w-48 bg-muted rounded-md" />
              <div className="h-6 w-16 bg-muted rounded-md" />
            </div>
            <div className="h-2 w-full bg-muted rounded-full overflow-hidden" />
          </div>
        ))}
      </div>
    </div>
  );
}
