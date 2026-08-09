import { auth } from "@clerk/nextjs/server";
import { OverviewStats, CoverageResponse, QuestionMeta, PlannerConfig } from "@/types/api";

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
  } catch (error: any) {
    throw new Error(`Fetch failed for ${BACKEND_URL}${endpoint}: ${error.message}`);
  }

  if (!response.ok) {
    throw new Error(`Server API error on ${BACKEND_URL}${endpoint}: ${response.status} ${response.statusText}`);
  }

  let data;
  try {
    const text = await response.text();
    try {
      data = JSON.parse(text);
    } catch (e: any) {
      console.error(`JSON Parse Error for ${BACKEND_URL}${endpoint}. Raw text: ${text.substring(0, 500)}`);
      throw new Error(`JSON parse error on ${BACKEND_URL}${endpoint}: ${e.message}`);
    }
  } catch (e: any) {
    throw new Error(`Failed to read response from ${BACKEND_URL}${endpoint}: ${e.message}`);
  }

  return data;
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
    generatePlan: (params: any) => serverFetch<any>("/api/planner/generate", {
      method: 'POST',
      body: JSON.stringify(params),
      cache: 'no-store'
    }),
    getProgress: () => serverFetch<any>("/api/planner/progress", { cache: 'no-store' }),
  }
};
