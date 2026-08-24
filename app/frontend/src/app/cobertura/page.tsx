import { CoverageResponse } from "@/types/api";
import { CoverageClient } from "./CoverageClient";
import { serverApi } from "@/lib/server-api";
import { Target, Flame, CheckCircle2, BookOpen } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function CoberturaPage() {
  const data: CoverageResponse = await serverApi.stats.getCoverage();

  const totalQuestions = data.areas.reduce((acc, a) => acc + a.n_questions, 0);
  const totalAnswered = data.areas.reduce((acc, a) => acc + a.answered_questions, 0);
  const globalProgress = totalQuestions > 0 ? (totalAnswered / totalQuestions) * 100 : 0;

  const totalSubtemas = data.areas.reduce((acc, a) => acc + a.n_subtemas, 0);
  const totalHighYield = data.areas.reduce((acc, a) => acc + (a.high_yield_count || 0), 0);
  const highYieldMastered = data.areas.reduce((acc, a) => acc + (a.high_yield_mastered || 0), 0);
  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500 max-w-7xl mx-auto w-full">
      
      {/* Header Banner */}
      <section className="bg-card border border-border shadow-sm rounded-2xl p-6 md:p-8 flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-orange-500 to-success" />
        
        <div className="flex-1">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-2 flex items-center gap-3">
            <Target className="text-primary" size={30} />
            Cobertura do Banco por Temas e Módulos
          </h1>
          <p className="text-muted-foreground text-sm md:text-base max-w-3xl leading-relaxed">
            Acompanhe o seu domínio em cada um dos <span className="font-semibold text-foreground">{totalSubtemas} módulos estruturados</span> das 5 grandes áreas. 
            Identifique lacunas e priorize os <span className="font-semibold text-orange-500 inline-flex items-center gap-0.5"><Flame size={14} className="fill-current" /> {totalHighYield} temas de alta prevalência (USP-SP / USP-RP)</span>.
          </p>
        </div>

        {/* Global Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 shrink-0">
          <div className="bg-muted/40 border border-border p-3.5 rounded-xl flex flex-col">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1">
              <BookOpen size={12} /> Temas do Curso
            </span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-foreground">{totalSubtemas}</span>
              <span className="text-xs text-muted-foreground">módulos</span>
            </div>
            <span className="text-[11px] text-muted-foreground mt-1">{totalQuestions.toLocaleString()} questões</span>
          </div>

          <div className="bg-orange-500/5 border border-orange-500/20 p-3.5 rounded-xl flex flex-col">
            <span className="text-[11px] font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wider mb-1 flex items-center gap-1">
              <Flame size={12} className="fill-current" /> Foco USP
            </span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">{totalHighYield}</span>
              <span className="text-xs text-muted-foreground">temas</span>
            </div>
            <span className="text-[11px] text-muted-foreground mt-1">{highYieldMastered} dominados</span>
          </div>

          <div className="bg-muted/40 border border-border p-3.5 rounded-xl flex flex-col col-span-2 sm:col-span-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1">
              <CheckCircle2 size={12} /> Cobertura Geral
            </span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-foreground">{globalProgress.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 w-full bg-border rounded-full overflow-hidden mt-2">
              <div className="h-full bg-success transition-all duration-500" style={{ width: `${globalProgress}%` }} />
            </div>
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
