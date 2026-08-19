import { serverApi } from "@/lib/server-api";
import { Activity } from "lucide-react";
import { AnalysisClient } from "./AnalysisClient";

export default async function AnalisePage() {
  // Fazemos fetch paralelo de todos os dados do dashboard analítico
  const results = await Promise.allSettled([
    serverApi.stats.getTimeline(),
    serverApi.stats.getWeakTopics(),
    serverApi.stats.getRecommendations(),
    serverApi.stats.getBreakdown("institution"),
    serverApi.stats.getDistractors(),
    serverApi.stats.getPredictiveScore(),
    serverApi.stats.getAtRiskTopics(),
  ]);

  const timeline = results[0].status === 'fulfilled' ? results[0].value : [];
  const weakTopics = results[1].status === 'fulfilled' ? results[1].value : [];
  const recommendations = results[2].status === 'fulfilled' ? results[2].value : [];
  const breakdown = results[3].status === 'fulfilled' ? results[3].value : [];
  const distractors = results[4].status === 'fulfilled' ? results[4].value : [];
  const predictiveScore = results[5].status === 'fulfilled' ? results[5].value : { projected_score: 0, target_score: null, areas: [] };
  const atRiskTopics = results[6].status === 'fulfilled' ? results[6].value : [];

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <section className="bg-card border border-border shadow-sm rounded-2xl p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden isolation-auto">
        <div className="absolute top-0 right-0 w-64 h-64 bg-secondary/10 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-0 left-0 w-40 h-40 bg-primary/10 rounded-full blur-3xl -z-10" />
        
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/10 text-secondary text-sm font-semibold mb-4 border border-secondary/20">
            <Activity size={16} />
            Inteligência Artificial
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight mb-3">
            Análise de Desempenho
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl leading-relaxed">
            Inteligência de dados sobre a sua jornada. Acompanhe a sua evolução ao longo do tempo, receba recomendações personalizadas e ataque ativamente seus pontos fracos.
          </p>
        </div>
      </section>

      {/* Main Content Dashboard */}
      <AnalysisClient 
        timeline={timeline}
        weakTopics={weakTopics}
        recommendations={recommendations}
        breakdown={breakdown}
        distractors={distractors}
        predictiveScore={predictiveScore}
        atRiskTopics={atRiskTopics}
      />

    </div>
  );
}
