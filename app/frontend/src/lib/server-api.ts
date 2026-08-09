import { auth } from "@clerk/nextjs/server";
import { OverviewStats, CoverageResponse, QuestionMeta, PlannerConfig } from "@/types/api";

const BACKEND_URL = process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_FLASK_API_URL || "http://127.0.0.1:5000";

async function serverFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const { getToken } = await auth();
  const token = await getToken();
  
  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`Server API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export const serverApi = {
  stats: {
    getOverview: () => serverFetch<OverviewStats>("/api/stats/overview", { cache: 'no-store' }),
    getCoverage: () => serverFetch<CoverageResponse>("/api/coverage", { cache: 'no-store' }),
  },
  questions: {
    getMeta: () => serverFetch<QuestionMeta>("/api/meta", { next: { revalidate: 3600 } }),
  },
  planner: {
    getConfig: () => serverFetch<PlannerConfig>("/api/planner/config", { cache: 'no-store' }),
  }
};
