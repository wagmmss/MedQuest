import { Sparkles, BrainCircuit } from "lucide-react";

export default function LoadingFlashcards() {
  return (
    <div className="max-w-3xl mx-auto w-full flex flex-col items-center gap-6 pb-12 animate-in fade-in duration-500">
      <div className="w-full flex items-center justify-between mb-2 opacity-50">
        <div className="flex items-center gap-2 text-purple-500 font-bold">
          <Sparkles size={20} /> Revisão Ativa (IA)
        </div>
        <div className="text-sm font-medium text-muted-foreground">
          Buscando...
        </div>
      </div>
      <div className="w-full min-h-[300px] bg-card border border-border shadow-1 rounded-2xl p-8 flex flex-col items-center justify-center gap-6 animate-pulse">
        <div className="w-3/4 h-6 bg-muted rounded-md mb-4" />
        <div className="w-full h-24 bg-muted rounded-md" />
        <div className="w-2/3 h-6 bg-muted rounded-md mt-4" />
      </div>
    </div>
  );
}
