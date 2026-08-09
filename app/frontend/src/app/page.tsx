import { serverApi } from "@/lib/server-api";
import { BrainCircuit, Flame, Target, Trophy, Clock } from "lucide-react";
import Link from "next/link";
import { OverviewStats } from "@/types/api";

// This is a Server Component. Next.js 16.3 supports async server components naturally.
export default async function Dashboard() {
  const stats: OverviewStats = await serverApi.stats.getOverview();

  const accuracyFormatted = stats.accuracy_all_attempts != null 
    ? (stats.accuracy_all_attempts * 100).toFixed(1) + "%" 
    : "--";

  const coverageFormatted = stats.coverage_pct != null
    ? (stats.coverage_pct * 100).toFixed(1) + "%"
    : "--";

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500 pb-10">
      
      {/* Header section with Hero Number and Primary Action */}
      <section className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        {/* Subtle accent line */}
        <div className="absolute top-0 left-0 w-full h-1 bg-primary/80" />
        
        <div>
          <h1 className="text-display font-bold text-foreground tracking-tight mb-2 flex items-center gap-3">
            <span className="text-primary">{stats.srs_due_count}</span>
            <span className="text-h2 font-semibold text-muted-foreground">revisões hoje</span>
          </h1>
          <p className="text-muted-foreground text-body-l max-w-xl">
            O algoritmo de repetição espaçada separou {stats.srs_due_count} {stats.srs_due_count === 1 ? 'questão' : 'questões'} para fixação de longo prazo. A consistência diária é o fator número 1 de aprovação.
          </p>
        </div>

        <Link 
          href="/estudar?status=srs_due&limit=100"
          className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 py-4 rounded-lg font-medium text-lg shadow-1 transition-all hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-3 whitespace-nowrap shrink-0"
        >
          <BrainCircuit size={24} />
          Iniciar Revisão
        </Link>
      </section>

      {/* Secondary Grid */}
      <section>
        <h2 className="text-h2 font-semibold mb-4 text-foreground">Visão Geral</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          <div className="bg-card border border-border rounded-lg p-5 flex flex-col justify-between group hover:shadow-1 transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <span className="text-muted-foreground font-medium">Ofensiva</span>
              <Flame size={20} className={stats.streak_days > 0 ? "text-warning" : "text-muted-foreground"} />
            </div>
            <div className="flex items-baseline gap-2 mt-auto">
              <span className="text-h1 font-bold text-foreground">{stats.streak_days}</span>
              <span className="text-sm text-muted-foreground">dias</span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-5 flex flex-col justify-between group hover:shadow-1 transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <span className="text-muted-foreground font-medium">Acurácia Geral</span>
              <Target size={20} className="text-primary" />
            </div>
            <div className="flex items-baseline gap-2 mt-auto">
              <span className="text-h1 font-bold text-foreground">{accuracyFormatted}</span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-5 flex flex-col justify-between group hover:shadow-1 transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <span className="text-muted-foreground font-medium">Cobertura do Banco</span>
              <Trophy size={20} className="text-success" />
            </div>
            <div className="flex items-baseline gap-2 mt-auto">
              <span className="text-h1 font-bold text-foreground">{coverageFormatted}</span>
              <span className="text-sm text-muted-foreground">de {stats.total_questions} Qs</span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-5 flex flex-col justify-between group hover:shadow-1 transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <span className="text-muted-foreground font-medium">Questões Feitas</span>
              <Clock size={20} className="text-secondary" />
            </div>
            <div className="flex items-baseline gap-2 mt-auto">
              <span className="text-h1 font-bold text-foreground">{stats.distinct_answered}</span>
              <span className="text-sm text-muted-foreground">únicas</span>
            </div>
          </div>

        </div>
      </section>

    </div>
  );
}
