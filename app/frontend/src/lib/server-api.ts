import { auth } from "@clerk/nextjs/server";
import { 
  OverviewStats, CoverageResponse, QuestionMeta, PlannerConfig,
  TimelineStat, WeakTopic, Recommendation, BreakdownStat, DistractorStat,
  PlannerPlanResponse, PlannerProgressMap
} from "@/types/api";

const BACKEND_URL = process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_FLASK_API_URL || "https://medquest-api.onrender.com";

async function serverFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const { getToken } = await auth();
  const token = await getToken();
  
  let response;
  try {
    response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options?.headers,
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    throw new Error(`Fetch failed for ${BACKEND_URL}${endpoint}: ${message}`);
  }

  if (!response.ok) {
    throw new Error(`Server API error on ${BACKEND_URL}${endpoint}: ${response.status} ${response.statusText}`);
  }

  let data;
  try {
    const text = await response.text();
    try {
      data = JSON.parse(text);
    } catch (e) {
      const message = e instanceof Error ? e.message : "Unknown parse error";
      console.error(`JSON Parse Error for ${BACKEND_URL}${endpoint}. Raw text: ${text.substring(0, 500)}`);
      throw new Error(`JSON parse error on ${BACKEND_URL}${endpoint}: ${message}`);
    }
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown read error";
    throw new Error(`Failed to read response from ${BACKEND_URL}${endpoint}: ${message}`);
  }

  return data;
}

export const serverApi = {
  stats: {
    getOverview: () => serverFetch<OverviewStats>("/api/stats/overview", { cache: 'no-store' }),
    getCoverage: () => serverFetch<CoverageResponse>("/api/coverage", { cache: 'no-store' }),
    getTimeline: () => serverFetch<TimelineStat[]>("/api/stats/timeline", { cache: 'no-store' }),
    getWeakTopics: () => serverFetch<WeakTopic[]>("/api/stats/weak-topics", { cache: 'no-store' }),
    getRecommendations: () => serverFetch<Recommendation[]>("/api/stats/recommendations", { cache: 'no-store' }),
    getDistractors: () => serverFetch<DistractorStat[]>("/api/stats/distractors", { cache: 'no-store' }),
    getBreakdown: (by: 'institution' | 'area' | 'year') => 
      serverFetch<BreakdownStat[]>(`/api/stats/breakdown?by=${by}`, { cache: 'no-store' }),
  },
  questions: {
    getMeta: () => serverFetch<QuestionMeta>("/api/meta", { next: { revalidate: 3600 } }),
  },
  planner: {
    getConfig: () => serverFetch<PlannerConfig>("/api/planner/config", { cache: 'no-store' }),
    generatePlan: (params: Record<string, unknown>) => serverFetch<PlannerPlanResponse>("/api/generate_plan", {
      method: 'POST',
      body: JSON.stringify(params),
      cache: 'no-store'
    }),
    getProgress: () => serverFetch<PlannerProgressMap>("/api/planner", { cache: 'no-store' }),
  }
};
