import { 
  OverviewStats, CoverageResponse, TimelineStat, WeakTopic, Recommendation, 
  BreakdownStat, DistractorStat, PlannerConfig, PlannerProgressMap, PlannerPlanResponse,
  QuestionMeta, SubtemaItem, QuestionListItem, QuestionDetail, AttemptResult, SearchResult,
  BatchAttemptItem, BatchAttemptResult, BatchDetailResponse, Flashcard, FlashcardGenerateResponse,
  PredictiveScore, AtRiskTopic
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_APP_URL || 
  (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : 
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 
  (typeof window !== "undefined" ? "" : "http://localhost:3000")));

import { syncManager } from "./sync";
import { localDb } from "./db";

/**
 * Base fetch function with default headers
 */
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
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

    return await response.json();
  } catch (error) {
    if (typeof window !== "undefined" && options?.method && ["POST", "PUT"].includes(options.method.toUpperCase())) {
      const isNetworkError = error instanceof TypeError && error.message.includes("Failed to fetch");
      if (isNetworkError || !navigator.onLine) {
        console.warn("[API] Network error detected, adding to offline queue:", endpoint);
        syncManager.enqueue(url, options);
        // Retornamos um objeto mock com sucesso true para não travar a UI (útil para tentativas de questões)
        return { success: true, offline: true } as any;
      }
    }
    throw error;
  }
}

/**
 * API endpoints
 */
export const api = {
  stats: {
    getOverview: () => apiFetch<OverviewStats>("/api/stats/overview", { cache: 'no-store' }),
    getCoverage: () => apiFetch<CoverageResponse>("/api/coverage", { cache: 'no-store' }),
    getTimeline: (days: number = 14) => apiFetch<TimelineStat[]>(`/api/stats/timeline?days=${days}`, { cache: 'no-store' }),
    getWeakTopics: () => apiFetch<WeakTopic[]>("/api/stats/weak-topics", { cache: 'no-store' }),
    getRecommendations: () => apiFetch<Recommendation[]>("/api/stats/recommendations", { cache: 'no-store' }),
    getDistractors: () => apiFetch<DistractorStat[]>("/api/stats/distractors", { cache: 'no-store' }),
    getPredictiveScore: () => apiFetch<PredictiveScore>("/api/stats/predictive-score", { cache: 'no-store' }),
    getAtRiskTopics: () => apiFetch<AtRiskTopic[]>("/api/stats/at-risk", { cache: 'no-store' }),
    getBreakdown: (by: 'institution' | 'area' | 'year') => 
      apiFetch<BreakdownStat[]>(`/api/stats/breakdown?by=${by}`, { cache: 'no-store' }),
    resetProgress: () => 
      apiFetch<{success: boolean}>("/api/stats/reset", {
        method: "DELETE",
      }),
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
    submitAttempt: (id: number, selected_letter: string, time_spent_ms: number, confidence: string = "defer") => 
      apiFetch<AttemptResult>(`/api/questions/${id}/attempt`, {
        method: "POST",
        body: JSON.stringify({ selected_letter, time_spent_ms, confidence }),
      }),
    reviewFSRS: (id: number, confidence: string) => 
      apiFetch<{success: boolean, next_review_date: string}>(`/api/questions/${id}/review`, {
        method: "POST",
        body: JSON.stringify({ confidence })
      }),
    toggleFavorite: (id: number) => apiFetch<{is_favorite: boolean}>(`/api/questions/${id}/favorite`, {
      method: "POST"
    }),
    search: (q: string, semantic: boolean = false) => apiFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}&semantic=${semantic}`, { cache: 'no-store' }),
    getSimuladoUSP: () => apiFetch<QuestionListItem[]>("/api/simulado/usp", { cache: 'no-store' }),
    getCustomSimulado: (config: { institutions?: string[], years?: string[], questions_per_area?: number }) => apiFetch<QuestionListItem[]>("/api/simulado/custom", {
      method: "POST",
      body: JSON.stringify(config)
    }),
    submitAttemptBatch: (attempts: BatchAttemptItem[]) => apiFetch<BatchAttemptResult>(`/api/questions/attempt/batch`, {
      method: "POST",
      body: JSON.stringify({ attempts })
    }),
    getBatch: async (ids: number[], force_4_options: boolean = false) => {
      if (typeof window !== "undefined" && !navigator.onLine && localDb) {
        console.warn("[API] Offline mode: loading questions from localDb");
        try {
          const cached = await localDb.questions.where('id').anyOf(ids).toArray();
          const map = cached.reduce((acc, q) => { acc[q.id] = q; return acc; }, {} as Record<number, QuestionDetail>);
          return { questions: map } as BatchDetailResponse;
        } catch (e) {
          console.error("Dexie error", e);
        }
      }
      return apiFetch<BatchDetailResponse>(`/api/questions/batch`, {
        method: "POST",
        body: JSON.stringify({ ids, force_4_options })
      });
    },
  },
  flashcards: {
    generate: (question_id: number, wrong_letter: string) => apiFetch<FlashcardGenerateResponse>(`/api/flashcards/generate`, {
      method: "POST",
      body: JSON.stringify({ question_id, wrong_letter })
    }),
    getDue: async () => {
      if (typeof window !== "undefined" && !navigator.onLine && localDb) {
        console.warn("[API] Offline mode: loading flashcards from localDb");
        try {
          return await localDb.flashcards.toArray();
        } catch (e) {
          console.error("Dexie error", e);
          return [];
        }
      }
      return apiFetch<Flashcard[]>("/api/flashcards/review", { cache: 'no-store' });
    },
    review: (id: number, confidence: string) => apiFetch<{id: number, next_review_date: string}>(`/api/flashcards/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ confidence })
    }),
    report: (id: number, reason: string) => apiFetch<{success: boolean}>(`/api/flashcards/${id}/report`, {
      method: "POST",
      body: JSON.stringify({ reason })
    })
  }
};
