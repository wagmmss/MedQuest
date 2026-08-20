export default function LoadingBuscar() {
  return (
    <div className="max-w-4xl mx-auto w-full flex flex-col gap-6 pb-12 animate-pulse">
      {/* Top Search Header Skeleton */}
      <div className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex flex-col gap-6 text-center">
        <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-2" />
        
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-48 bg-muted rounded-md" />
          <div className="h-4 w-64 bg-muted rounded-md" />
        </div>
        
        <div className="flex items-center justify-center gap-3 mt-2">
          <div className="h-6 w-11 bg-muted rounded-full" />
          <div className="h-4 w-32 bg-muted rounded-md" />
        </div>
        
        <div className="relative max-w-2xl w-full mx-auto mt-2">
          <div className="w-full h-16 bg-muted rounded-full" />
        </div>
      </div>
      
      {/* Results Skeleton (simulating a few results if there was a query) */}
      <div className="flex flex-col gap-4">
        <div className="h-4 w-40 bg-muted rounded px-2" />
        <div className="flex flex-col gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-card border border-border shadow-sm rounded-xl p-5 flex flex-col gap-3 h-32">
              <div className="flex gap-2">
                <div className="h-5 w-16 bg-muted rounded" />
                <div className="h-5 w-20 bg-muted rounded" />
                <div className="h-5 w-24 bg-muted rounded" />
              </div>
              <div className="h-4 w-full bg-muted rounded mt-2" />
              <div className="h-4 w-3/4 bg-muted rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
