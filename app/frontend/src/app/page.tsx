import { serverApi } from "@/lib/server-api";
import { 
  OverviewStats, PlannerWeek, PlannerTopic, PlannerTopicProgressMap, PlannerProgressMap,
  BenchmarkStat, BottleneckTopic, DomainSummaryResponse, ErrorNotebookSummary 
} from "@/types/api";
import { currentUser } from '@clerk/nextjs/server';
import { DashboardClient } from "./DashboardClient";

export const dynamic = "force-dynamic";

export default async function Dashboard() {
  const stats: OverviewStats = await serverApi.stats.getOverview();
  const user = await currentUser();

  let currentPlannerWeek: PlannerWeek | null = null;
  let suggestedPlannerTopic: PlannerTopic | null = null;
  let remainingPlannerMetas: number = 0;
  let totalPlannerMetas: number = 0;
  let isPlanCompleted: boolean = false;
  let benchmarkStats: BenchmarkStat | null = null;
  let bottlenecks: BottleneckTopic[] = [];
  let domainSummary: DomainSummaryResponse | null = null;
  let errorNotebook: ErrorNotebookSummary | null = null;

  try {
    const [bench, bnecks, domain, errors, config, topicProgressMap, progressMap] = await Promise.all([
      serverApi.stats.getBenchmark().catch(() => null),
      serverApi.stats.getBottlenecks(3).catch(() => []),
      serverApi.stats.getDomainSummary().catch(() => null),
      serverApi.stats.getErrorNotebookSummary().catch(() => null),
      serverApi.planner.getConfig().catch(() => null),
      serverApi.planner.getTopicProgress().catch(() => ({} as PlannerTopicProgressMap)),
      serverApi.planner.getProgress().catch(() => ({} as PlannerProgressMap)),
    ]);
    benchmarkStats = bench;
    bottlenecks = bnecks;
    domainSummary = domain;
    errorNotebook = errors;

    if (config && config.exam_date && config.start_date) {
      const planResponse = await serverApi.planner.generatePlan({
        start_date: config.start_date,
        exam_date: config.exam_date,
        hours_per_week: Math.min(168, (config.days_per_week || 5) * (config.hours_per_day || 4)),
        intensive: false
      });

      if (planResponse.plan && planResponse.plan.length > 0) {
        const plan = planResponse.plan;

        // Encontra a primeira semana com metas ainda pendentes
        for (const week of plan) {
          if (progressMap[week.week.toString()]?.studied) {
            continue;
          }
          const pendingTopics = (week.topics || []).filter(
            (t) => !topicProgressMap[`${week.week}:${t.subtema}`]
          );
          if (pendingTopics.length > 0) {
            currentPlannerWeek = week;
            suggestedPlannerTopic = pendingTopics[0];
            remainingPlannerMetas = pendingTopics.length;
            totalPlannerMetas = (week.topics || []).length;
            break;
          }
        }

        // Se todas as semanas e tópicos foram concluídos
        if (!suggestedPlannerTopic && plan.length > 0) {
          isPlanCompleted = true;
          currentPlannerWeek = plan[plan.length - 1];
        }
      }
    }
  } catch (e) {
    console.error("Failed to fetch dashboard metrics", e);
  }

  const firstName = user?.firstName || "Doutor(a)";

  return (
    <DashboardClient 
      stats={stats} 
      currentPlannerWeek={currentPlannerWeek} 
      suggestedPlannerTopic={suggestedPlannerTopic}
      remainingPlannerMetas={remainingPlannerMetas}
      totalPlannerMetas={totalPlannerMetas}
      isPlanCompleted={isPlanCompleted}
      firstName={firstName} 
      benchmarkStats={benchmarkStats}
      bottlenecks={bottlenecks}
      domainSummary={domainSummary}
      errorNotebook={errorNotebook}
    />
  );
}

