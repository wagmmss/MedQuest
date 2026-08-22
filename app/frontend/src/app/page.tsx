import { serverApi } from "@/lib/server-api";
import { OverviewStats, PlannerWeek, TimelineStat, BreakdownStat } from "@/types/api";
import { currentUser } from '@clerk/nextjs/server';
import { DashboardClient } from "./DashboardClient";

export default async function Dashboard() {
  const stats: OverviewStats = await serverApi.stats.getOverview();
  const user = await currentUser();

  let currentPlannerWeek: PlannerWeek | null = null;
  let timelineStats: TimelineStat[] = [];
  let breakdownStats: BreakdownStat[] = [];
  try {
    const [timeline, breakdown] = await Promise.all([
      serverApi.stats.getTimeline(180),
      serverApi.stats.getBreakdown("area")
    ]);
    timelineStats = timeline;
    breakdownStats = breakdown;
  } catch (e) {
    console.error("Failed to fetch timeline or breakdown for dashboard", e);
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
      timelineStats={timelineStats}
      breakdownStats={breakdownStats}
    />
  );
}
