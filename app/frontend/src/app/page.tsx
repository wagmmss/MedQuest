import { serverApi } from "@/lib/server-api";
import { 
  OverviewStats, PlannerWeek,
  BenchmarkStat, BottleneckTopic, DomainSummaryResponse, ErrorNotebookSummary 
} from "@/types/api";
import { currentUser } from '@clerk/nextjs/server';
import { DashboardClient } from "./DashboardClient";

export default async function Dashboard() {
  const stats: OverviewStats = await serverApi.stats.getOverview();
  const user = await currentUser();

  let currentPlannerWeek: PlannerWeek | null = null;
  let benchmarkStats: BenchmarkStat | null = null;
  let bottlenecks: BottleneckTopic[] = [];
  let domainSummary: DomainSummaryResponse | null = null;
  let errorNotebook: ErrorNotebookSummary | null = null;

  try {
    const [bench, bnecks, domain, errors] = await Promise.all([
      serverApi.stats.getBenchmark().catch(() => null),
      serverApi.stats.getBottlenecks(3).catch(() => []),
      serverApi.stats.getDomainSummary().catch(() => null),
      serverApi.stats.getErrorNotebookSummary().catch(() => null),
    ]);
    benchmarkStats = bench;
    bottlenecks = bnecks;
    domainSummary = domain;
    errorNotebook = errors;
  } catch (e) {
    console.error("Failed to fetch dashboard metrics", e);
  }

  try {
    const config = await serverApi.planner.getConfig();
    if (config && config.exam_date && config.start_date) {
      const planResponse = await serverApi.planner.generatePlan({
        start_date: config.start_date,
        exam_date: config.exam_date,
        hours_per_week: (config.days_per_week || 5) * (config.hours_per_day || 4),
        intensive: false
      });
      if (planResponse.plan && planResponse.plan.length > 0) {
        const now = new Date();
        const start = new Date(config.start_date);
        const diffTime = now.getTime() - start.getTime();
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        const weekIndex = Math.floor(diffDays / 7);
        if (weekIndex >= 0 && weekIndex < planResponse.plan.length) {
          currentPlannerWeek = planResponse.plan[weekIndex];
        } else if (weekIndex >= planResponse.plan.length) {
           currentPlannerWeek = planResponse.plan[planResponse.plan.length - 1];
        } else if (weekIndex < 0) {
           currentPlannerWeek = planResponse.plan[0];
        }
      }
    }
  } catch (e) {
    console.error("Failed to fetch planner info for dashboard", e);
  }

  const firstName = user?.firstName || "Doutor(a)";

  return (
    <DashboardClient 
      stats={stats} 
      currentPlannerWeek={currentPlannerWeek} 
      firstName={firstName} 
      benchmarkStats={benchmarkStats}
      bottlenecks={bottlenecks}
      domainSummary={domainSummary}
      errorNotebook={errorNotebook}
    />
  );
}

