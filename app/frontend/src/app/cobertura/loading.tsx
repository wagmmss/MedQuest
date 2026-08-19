import { Target } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500">
      {/* Header Skeleton */}
      <section className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-muted" />
        
        <div className="flex-1">
          <h1 className="text-h1 font-bold text-foreground tracking-tight mb-2 flex items-center gap-3">
            <Target className="text-muted" size={28} />
            Cobertura do Banco
          </h1>
          <div className="h-4 bg-muted rounded w-3/4 animate-pulse mb-2" />
          <div className="h-4 bg-muted rounded w-1/2 animate-pulse" />
        </div>

        <div className="bg-muted/50 p-4 rounded-lg flex flex-col min-w-[200px] shrink-0">
          <div className="h-4 bg-muted rounded w-24 mb-2 animate-pulse" />
          <div className="h-8 bg-muted rounded w-16 mb-2 animate-pulse" />
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden" />
        </div>
      </section>

      {/* Main Content Skeleton */}
      <section className="flex flex-col gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-5 shadow-1 flex items-center justify-between">
            <div className="flex items-center gap-4 w-full">
              <div className="w-2 h-10 rounded-full shrink-0 bg-muted animate-pulse" />
              <div className="flex-1">
                <div className="h-5 bg-muted rounded w-48 mb-2 animate-pulse" />
                <div className="h-3 bg-muted rounded w-32 animate-pulse" />
              </div>
              <div className="hidden sm:flex flex-col items-end gap-2 w-64">
                <div className="h-3 bg-muted rounded w-full animate-pulse" />
                <div className="h-2 bg-muted rounded w-full animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
