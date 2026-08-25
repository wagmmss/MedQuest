import { auth } from "@clerk/nextjs/server";
import { getGuestSession } from "./session";
import { 
  OverviewStats, CoverageResponse, QuestionMeta, PlannerConfig,
  TimelineStat, WeakTopic, Recommendation, BreakdownStat, DistractorStat,
  PlannerPlanResponse, PlannerProgressMap, PlannerTopicProgressMap, PredictiveScore, AtRiskTopic, LearningProfile, ExamReadiness,
  BenchmarkStat, BottleneckTopic, DomainSummaryResponse, ErrorNotebookSummary
} from "@/types/api";

export type { QuestionMeta };

const BACKEND_URL = process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_FLASK_API_URL || "https://medquest-api.onrender.com";
const API_REQUEST_TIMEOUT_MS = process.env.PLAYWRIGHT_TEST ? 1_000 : 5_000;

export function isDynamicServerUsageError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const digest = "digest" in error && typeof error.digest === "string" ? error.digest : "";
  return error.message.includes("DYNAMIC_SERVER_USAGE") || digest.includes("DYNAMIC_SERVER_USAGE");
}

async function serverFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  if (process.env.PLAYWRIGHT_TEST === "true") {
    throw new Error("E2E test environment: SSR fetch bypassed in favor of client mocking.");
  }
  const proxySecret = process.env.FLASK_API_PROXY_SECRET;
  if (!proxySecret) {
    throw new Error("FLASK_API_PROXY_SECRET is not configured on server.");
  }
  const { getToken } = await auth();
  const token = await getToken();
  const guestId = await getGuestSession();
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> || {}),
  };
  
  if (token) headers["Authorization"] = `Bearer ${token}`;
  else if (guestId) headers["X-Guest-ID"] = guestId;
  
  headers["X-Internal-Proxy-Token"] = proxySecret;

  let response;
  try {
    response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      headers,
      // A stalled upstream must not leave the App Router streaming its loading
      // UI forever. Callers can still provide a stricter signal when needed.
      signal: options?.signal ?? AbortSignal.timeout(API_REQUEST_TIMEOUT_MS),
    });
  } catch (error) {
    if (isDynamicServerUsageError(error)) {
      throw error; // Re-throw to allow Next.js to handle it
    }
    const message = error instanceof Error ? error.message : "Unknown error";
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new Error(`Backend timeout after ${API_REQUEST_TIMEOUT_MS / 1000}s for ${endpoint}`);
    }
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
    getOverview: () => serverFetch<OverviewStats>("/api/stats/overview", { next: { tags: ['stats'] } }),
    getCoverage: () => serverFetch<CoverageResponse>("/api/coverage", { next: { tags: ['stats'] } }),
    getTimeline: (days: number = 14) => serverFetch<TimelineStat[]>(`/api/stats/timeline?days=${days}`, { next: { tags: ['stats'] } }),
    getWeakTopics: () => serverFetch<WeakTopic[]>("/api/stats/weak-topics", { next: { tags: ['stats'] } }),
    getRecommendations: () => serverFetch<Recommendation[]>("/api/stats/recommendations", { next: { tags: ['stats'] } }),
    getDistractors: () => serverFetch<DistractorStat[]>("/api/stats/distractors", { next: { tags: ['stats'] } }),
    getPredictiveScore: () => serverFetch<PredictiveScore>("/api/stats/predictive-score", { next: { tags: ['stats'] } }),
    getAtRiskTopics: () => serverFetch<AtRiskTopic[]>("/api/stats/at-risk", { next: { tags: ['stats'] } }),
    getLearningProfile: () => serverFetch<LearningProfile>("/api/stats/learning-profile", { next: { tags: ['stats'] } }),
    getExamReadiness: (institution?: string) => serverFetch<ExamReadiness>(`/api/stats/exam-readiness${institution ? `?institution=${encodeURIComponent(institution)}` : ""}`, { next: { tags: ['stats'] } }),
    getBreakdown: (by: 'institution' | 'area' | 'year') => 
      serverFetch<BreakdownStat[]>(`/api/stats/breakdown?by=${by}`, { next: { tags: ['stats'] } }),
    getBenchmark: () => serverFetch<BenchmarkStat>("/api/stats/benchmark", { next: { tags: ['stats'] } }),
    getBottlenecks: (limit: number = 3) => serverFetch<BottleneckTopic[]>(`/api/stats/bottlenecks?limit=${limit}`, { next: { tags: ['stats'] } }),
    getDomainSummary: () => serverFetch<DomainSummaryResponse>("/api/stats/domain-summary", { next: { tags: ['stats'] } }),
    getErrorNotebookSummary: () => serverFetch<ErrorNotebookSummary>("/api/stats/error-notebook-summary", { next: { tags: ['stats'] } }),
  },
  questions: {
    getMeta: () => serverFetch<QuestionMeta>("/api/meta", { cache: 'no-store' }),
  },
  planner: {
    getConfig: () => serverFetch<PlannerConfig>("/api/planner/config", { cache: 'no-store' }),
    generatePlan: (params: Record<string, unknown>) => serverFetch<PlannerPlanResponse>("/api/generate_plan", {
      method: 'POST',
      body: JSON.stringify(params),
      cache: 'no-store'
    }),
    getProgress: () => serverFetch<PlannerProgressMap>("/api/planner", { cache: 'no-store' }),
    getTopicProgress: () => serverFetch<PlannerTopicProgressMap>("/api/planner/topics", { cache: 'no-store' }),
  }
};
