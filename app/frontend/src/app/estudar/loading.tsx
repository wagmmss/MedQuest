export default function Loading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse pb-10 max-w-4xl mx-auto">
      <div className="h-10 w-48 bg-muted rounded-md mb-4" />
      
      <div className="bg-card border border-border rounded-xl p-6 md:p-8 flex flex-col gap-8">
        <div className="space-y-3">
          <div className="h-6 w-full bg-muted rounded-md" />
          <div className="h-6 w-11/12 bg-muted rounded-md" />
          <div className="h-6 w-4/5 bg-muted rounded-md" />
        </div>

        <div className="flex flex-col gap-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-14 w-full bg-muted rounded-lg border border-border" />
          ))}
        </div>
      </div>
    </div>
  );
}
