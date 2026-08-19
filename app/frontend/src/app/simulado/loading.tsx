import { Clock } from "lucide-react";

export default function LoadingSimulado() {
  return (
    <div className="flex flex-col lg:flex-row gap-6 w-full max-w-[1400px] mx-auto pb-12 lg:h-[calc(100vh-8rem)] animate-pulse">
      {/* Sidebar Skeleton */}
      <div className="w-full lg:w-72 shrink-0 flex flex-col gap-4 order-1 lg:order-1 h-auto lg:h-full lg:sticky lg:top-4 z-10 p-2 lg:p-0">
        <div className="bg-card border border-border shadow-1 rounded-xl p-4 lg:p-5 flex flex-row lg:flex-col items-center justify-between lg:justify-center gap-2">
          <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
            <Clock size={16} /> Tempo
          </span>
          <div className="h-10 w-24 bg-muted rounded-md mt-1" />
        </div>
        
        <div className="bg-card border border-border shadow-1 rounded-xl flex flex-col h-[200px] lg:h-auto lg:flex-1 p-4">
          <div className="h-4 w-32 bg-muted rounded mb-2" />
          <div className="h-3 w-48 bg-muted rounded mb-4" />
          <div className="flex flex-wrap gap-2">
            {[...Array(20)].map((_, i) => (
              <div key={i} className="w-8 h-8 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>

      {/* Main Area Skeleton */}
      <div className="flex-1 flex flex-col order-2 lg:order-2 h-full">
        <div className="flex flex-col h-full gap-4">
          {/* Header */}
          <div className="flex items-center justify-between bg-card border border-border shadow-sm rounded-xl p-3 shrink-0">
             <div className="h-8 w-24 bg-muted rounded" />
             <div className="h-6 w-32 bg-muted rounded" />
             <div className="h-8 w-24 bg-muted rounded" />
          </div>
          
          {/* Content */}
          <div className="bg-card border border-border shadow-1 rounded-xl p-8 flex-1 flex flex-col gap-6">
            <div className="h-6 w-32 bg-muted rounded" />
            <div className="h-40 bg-muted rounded-xl" />
            <div className="h-12 bg-muted rounded-xl" />
            <div className="h-12 bg-muted rounded-xl" />
            <div className="h-12 bg-muted rounded-xl" />
          </div>
        </div>
      </div>
    </div>
  );
}
