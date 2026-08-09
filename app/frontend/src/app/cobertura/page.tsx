import { CoverageResponse } from "@/types/api";
import { CoverageClient } from "./CoverageClient";
import { serverApi } from "@/lib/server-api";
import { Target } from "lucide-react";

export default async function CoberturaPage() {
  const data: CoverageResponse = await serverApi.stats.getCoverage();

  const totalQuestions = data.areas.reduce((acc, a) => acc + a.n_questions, 0);
  const totalAnswered = data.areas.reduce((acc, a) => acc + a.answered_questions, 0);
  const globalProgress = totalQuestions > 0 ? (totalAnswered / totalQuestions) * 100 : 0;

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <section className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-success/80" />
        
        <div>
          <h1 className="text-h1 font-bold text-foreground tracking-tight mb-2 flex items-center gap-3">
            <Target className="text-success" size={28} />
            Cobertura do Banco
          </h1>
          <p className="text-muted-foreground text-body-l max-w-2xl">
            Acompanhe o seu domínio em cada subtema. O status é calculado com base no número de tentativas e acurácia. Subtemas com mais de 70% de acerto em pelo menos 2 questões atestam domínio.
          </p>
        </div>

        <div className="bg-muted p-4 rounded-lg flex flex-col min-w-[200px] shrink-0">
          <span className="text-sm font-medium text-muted-foreground mb-1">Progresso Global</span>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-display font-bold text-foreground leading-none">{globalProgress.toFixed(1)}%</span>
          </div>
          <div className="h-2 w-full bg-border rounded-full overflow-hidden">
            <div className="h-full bg-success" style={{ width: `${globalProgress}%` }} />
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section>
        <CoverageClient areas={data.areas} />
      </section>

    </div>
  );
}
