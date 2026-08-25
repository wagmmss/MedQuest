import { serverApi } from "@/lib/server-api";
import { PlannerWizard } from "./PlannerWizard";
import { PlannerClient } from "./PlannerClient";

export default async function PlannerPage({ searchParams }: { searchParams: Promise<{ intensive?: string }> }) {
  const config = await serverApi.planner.getConfig();
  const sp = await searchParams;
  const isIntensive = sp.intensive === 'true';

  // Se não houver configuração salva ou se faltar data da prova, força o Onboarding
  if (!config || !config.exam_date || !config.start_date) {
    return (
      <div className="animate-in fade-in duration-500 flex flex-col items-center justify-center min-h-[70vh]">
        <PlannerWizard />
      </div>
    );
  }

  // Fazemos fetch paralelo: Gerar o cronograma (on-the-fly) e carregar os ticks já feitos
  const [planResponse, progressMap, topicProgressMap] = await Promise.all([
    serverApi.planner.generatePlan({
      start_date: config.start_date,
      exam_date: config.exam_date,
      hours_per_week: Math.min(168, (config.days_per_week || 5) * (config.hours_per_day || 4)),
      intensive: isIntensive
    }),
    serverApi.planner.getProgress(),
    serverApi.planner.getTopicProgress(),
  ]);

  // Se a geração falhar ou retornar array vazio
  if (!planResponse.plan || planResponse.plan.length === 0) {
    return (
      <div className="animate-in fade-in duration-500 flex flex-col items-center justify-center min-h-[70vh]">
        <div className="bg-destructive/10 text-destructive text-center p-6 rounded-xl border border-destructive/20 max-w-md">
          A data da prova precisa ser no futuro (ou não há temas no modo intensivo).
        </div>
        <div className="mt-8">
          <PlannerWizard />
        </div>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in duration-500">
      <PlannerClient 
        plan={planResponse.plan}
        initialProgress={progressMap}
        initialTopicProgress={topicProgressMap}
        warning={planResponse.warning}
        isIntensive={isIntensive}
        config={config}
      />
    </div>
  );
}
