import { 
  OverviewStats, CoverageResponse, TimelineStat, WeakTopic, Recommendation, 
  BreakdownStat, DistractorStat, PlannerConfig, PlannerProgressMap, PlannerPlanResponse,
  QuestionMeta, SubtemaItem, QuestionListItem, QuestionDetail, AttemptResult, SearchResult,
  BatchAttemptItem, BatchAttemptResult, Flashcard, FlashcardGenerateResponse
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_APP_URL || 
  (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : 
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 
  (typeof window !== "undefined" ? "" : "http://localhost:3000")));

/**
 * Base fetch function with default headers
 */
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * API endpoints
 */
export const api = {
  stats: {
    getOverview: () => apiFetch<OverviewStats>("/api/stats/overview", { cache: 'no-store' }),
    getCoverage: () => apiFetch<CoverageResponse>("/api/coverage", { cache: 'no-store' }),
    getTimeline: () => apiFetch<TimelineStat[]>("/api/stats/timeline", { cache: 'no-store' }),
    getWeakTopics: () => apiFetch<WeakTopic[]>("/api/stats/weak-topics", { cache: 'no-store' }),
    getRecommendations: () => apiFetch<Recommendation[]>("/api/stats/recommendations", { cache: 'no-store' }),
    getDistractors: () => apiFetch<DistractorStat[]>("/api/stats/distractors", { cache: 'no-store' }),
    getBreakdown: (by: 'institution' | 'area' | 'year') => 
      apiFetch<BreakdownStat[]>(`/api/stats/breakdown?by=${by}`, { cache: 'no-store' }),
  },
  planner: {
    getConfig: () => apiFetch<PlannerConfig>("/api/planner/config", { cache: 'no-store' }),
    saveConfig: (config: PlannerConfig) => apiFetch<{success: boolean}>("/api/planner/config", {
      method: "POST",
      body: JSON.stringify(config),
    }),
    resetConfig: () => apiFetch<{success: boolean}>("/api/planner/config/reset", {
      method: "POST",
    }),
    getProgress: () => apiFetch<PlannerProgressMap>("/api/planner", { cache: 'no-store' }),
    generatePlan: (data: { start_date?: string; exam_date: string; hours_per_week: number; intensive?: boolean }) => 
      apiFetch<PlannerPlanResponse>("/api/generate_plan", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    markStudy: (week: number, studied: boolean) => 
      apiFetch<{success: boolean}>(`/api/planner/${week}/study`, {
        method: "POST",
        body: JSON.stringify({ studied }),
      }),
    markRevision: (week: number, type: 'rev24h' | 'rev7d' | 'rev30d', checked: boolean) => 
      apiFetch<{success: boolean}>(`/api/planner/${week}/revision`, {
        method: "POST",
        body: JSON.stringify({ type, checked }),
      })
  },
  questions: {
    getMeta: (filters?: Record<string, string | string[]>) => {
      const params = new URLSearchParams();
      if (filters) {
        for (const [key, value] of Object.entries(filters)) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v));
          } else if (value !== undefined && value !== "") {
            params.append(key, value);
          }
        }
      }
      // Remove limit from meta request so it returns accurate totals
      params.delete("limit");
      const qs = params.toString();
      return apiFetch<QuestionMeta>(`/api/meta${qs ? `?${qs}` : ''}`, { next: { revalidate: 3600 } });
    },
    getSubtemas: (area?: string, q?: string) => {
      const params = new URLSearchParams();
      if (area) params.append("area", area);
      if (q) params.append("q", q);
      return apiFetch<SubtemaItem[]>(`/api/subtemas?${params.toString()}`, { next: { revalidate: 3600 } });
    },
    getList: (filters: Record<string, string | string[]>) => {
      const params = new URLSearchParams();
      for (const [key, value] of Object.entries(filters)) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v));
        } else if (value !== undefined && value !== "") {
          params.append(key, value);
        }
      }
      return apiFetch<QuestionListItem[]>(`/api/questions?${params.toString()}`, { cache: 'no-store' });
    },
    getDetail: (id: number) => apiFetch<QuestionDetail>(`/api/questions/${id}`, { cache: 'no-store' }),
    submitAttempt: (id: number, selected_letter: string, time_spent_ms: number, confidence: string = "certeza") => 
      apiFetch<AttemptResult>(`/api/questions/${id}/attempt`, {
        method: "POST",
        body: JSON.stringify({ selected_letter, time_spent_ms, confidence }),
      }),
    toggleFavorite: (id: number) => apiFetch<{is_favorite: boolean}>(`/api/questions/${id}/favorite`, {
      method: "POST"
    }),
    search: (q: string, semantic: boolean = false) => apiFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}&semantic=${semantic}`, { cache: 'no-store' }),
    getSimuladoUSP: () => apiFetch<QuestionListItem[]>("/api/questions/simulado/usp", { cache: 'no-store' }),
    submitAttemptBatch: (attempts: BatchAttemptItem[]) => apiFetch<BatchAttemptResult>(`/api/questions/attempt/batch`, {
      method: "POST",
      body: JSON.stringify({ attempts })
    }),
  },
  flashcards: {
    generate: (question_id: number, wrong_letter: string) => apiFetch<FlashcardGenerateResponse>(`/api/flashcards/generate`, {
      method: "POST",
      body: JSON.stringify({ question_id, wrong_letter })
    }),
    getDue: () => apiFetch<Flashcard[]>("/api/flashcards/review", { cache: 'no-store' }),
    review: (id: number, confidence: string) => apiFetch<{id: number, next_review_date: string}>(`/api/flashcards/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ confidence })
    })
  }
};
