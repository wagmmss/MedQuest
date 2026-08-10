export default function Loading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex flex-col md:flex-row gap-6 md:items-end justify-between mb-2">
        <div className="space-y-2">
          <div className="h-10 w-48 bg-muted rounded-md" />
          <div className="h-5 w-64 bg-muted rounded-md" />
        </div>
        <div className="h-12 w-40 bg-muted rounded-md" />
      </div>

      {/* Grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Stats section */}
        <div className="md:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-5 flex flex-col justify-between h-32">
              <div className="h-5 w-24 bg-muted rounded-md" />
              <div className="h-8 w-16 bg-muted rounded-md mt-auto" />
            </div>
          ))}
        </div>
        
        {/* Quick access section */}
        <div className="md:col-span-4 bg-card border border-border rounded-lg p-5 flex flex-col gap-4">
          <div className="h-6 w-32 bg-muted rounded-md mb-2" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 w-full bg-muted rounded-md" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
