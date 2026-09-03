import {
  OverviewStats, CoverageResponse, TimelineStat, WeakTopic, Recommendation,
  BreakdownStat, DistractorStat, PlannerConfig, PlannerProgressMap, PlannerTopicProgressMap, PlannerPlanResponse,
  QuestionMeta, SubtemaItem, QuestionListItem, QuestionDetail, AttemptResult, SearchResult,
  BatchAttemptItem, BatchAttemptResult, BatchDetailResponse, Flashcard, FlashcardGenerateResponse,
  BatchFlashcardGenerateResponse, PredictiveScore, AtRiskTopic, LearningProfile, ExamReadiness,
  BenchmarkStat, BottleneckTopic, DomainSummaryResponse, ErrorNotebookSummary,
  NotificationConfig, NotificationConfigUpdate, PushSubscriptionPayload,
  InstitutionRadarResponse, FlashcardDecksResponse, AnkiImportResult
} from "@/types/api";


const API_BASE = process.env.NEXT_PUBLIC_APP_URL ||
  (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` :
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` :
  (typeof window !== "undefined" ? "" : "http://localhost:3000")));

import { syncManager } from "./sync";
import { localDb, getLocalOwnerId } from "./db";

export class OfflineQueuedError extends Error {
  public localId: string;
  constructor(localId: string) {
    super("Operação salva neste dispositivo e aguardando sincronização.");
    this.name = "OfflineQueuedError";
    this.localId = localId;
  }
}

/**
 * Base fetch function with default headers and resilient timeout
 */
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const isMutation = options?.method && ["POST", "PUT", "PATCH", "DELETE"].includes(options.method.toUpperCase());
  const isIdempotentEndpoint = isMutation && (
    endpoint.includes("/attempt") ||
    endpoint.includes("/review") ||
    endpoint.includes("/favorite") ||
    endpoint.includes("/planner/")
  );

  let idempotencyKey: string | undefined;
  const headers = new Headers(options?.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (!headers.has("X-Request-ID") && typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    headers.set("X-Request-ID", crypto.randomUUID());
  }

  if (isIdempotentEndpoint) {
    idempotencyKey = crypto.randomUUID();
    headers.set("X-Idempotency-Key", idempotencyKey);
  }

  // Falha rápida se o navegador já estiver sabidamente offline
  if (typeof window !== "undefined" && typeof navigator !== "undefined" && !navigator.onLine) {
    if (isIdempotentEndpoint) {
      console.warn("[API] Offline imediato detectado, enfileirando:", endpoint);
      const localId = await syncManager.enqueue(url, { ...options, headers }, idempotencyKey!);
      throw new OfflineQueuedError(localId);
    }
    throw new TypeError("Falha de rede: navegador está offline");
  }

  const timeoutMs = endpoint.includes("/batch") || endpoint.includes("/generate") ? 8000 : 4500;
  const controller = new AbortController();
  let isInternalTimeout = false;
  const timeoutId = setTimeout(() => {
    isInternalTimeout = true;
    controller.abort(new Error("Timeout de conexão"));
  }, timeoutMs);

  if (options?.signal) {
    if (options.signal.aborted) {
      clearTimeout(timeoutId);
      controller.abort(options.signal.reason);
    } else {
      options.signal.addEventListener("abort", () => {
        clearTimeout(timeoutId);
        controller.abort(options.signal!.reason);
      }, { once: true });
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      let errMsg = `${response.status} ${response.statusText}`;
      try {
        const errorJson = await response.json();
        if (errorJson?.error) errMsg = errorJson.error;
      } catch {
        // use status text
      }
      throw new Error(errMsg);
    }

    return await response.json();
  } catch (error) {
    // Aborto intencional iniciado pelo chamador
    if (options?.signal?.aborted) {
      throw error;
    }

    const isNetworkOrTimeout = isInternalTimeout ||
      error instanceof TypeError ||
      (typeof navigator !== "undefined" && !navigator.onLine);

    if (typeof window !== "undefined" && isIdempotentEndpoint && isNetworkOrTimeout) {
      console.warn("[API] Erro de rede ou timeout detectado, adicionando à fila offline:", endpoint);
      const localId = await syncManager.enqueue(url, { ...options, headers }, idempotencyKey!);
      throw new OfflineQueuedError(localId);
    }

    if (isInternalTimeout) {
      throw new TypeError("Tempo limite de conexão excedido");
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * API endpoints
 */
export const api = {
  stats: {
    getOverview: () => apiFetch<OverviewStats>("/api/stats/overview", { cache: 'no-store' }),
    getCoverage: () => apiFetch<CoverageResponse>("/api/coverage", { cache: 'no-store' }),
    getTimeline: (days: number = 14, signal?: AbortSignal) =>
      apiFetch<TimelineStat[]>(`/api/stats/timeline?days=${days}`, { cache: 'no-store', signal }),
    getWeakTopics: () => apiFetch<WeakTopic[]>("/api/stats/weak-topics", { cache: 'no-store' }),
    getRecommendations: () => apiFetch<Recommendation[]>("/api/stats/recommendations", { cache: 'no-store' }),
    getDistractors: () => apiFetch<DistractorStat[]>("/api/stats/distractors", { cache: 'no-store' }),
    getPredictiveScore: () => apiFetch<PredictiveScore>("/api/stats/predictive-score", { cache: 'no-store' }),
    getAtRiskTopics: () => apiFetch<AtRiskTopic[]>("/api/stats/at-risk", { cache: 'no-store' }),
    getLearningProfile: () => apiFetch<LearningProfile>("/api/stats/learning-profile", { cache: 'no-store' }),
    getExamReadiness: (institution?: string) => apiFetch<ExamReadiness>(`/api/stats/exam-readiness${institution ? `?institution=${encodeURIComponent(institution)}` : ""}`, { cache: 'no-store' }),
    getBreakdown: (by: 'institution' | 'area' | 'year') =>
      apiFetch<BreakdownStat[]>(`/api/stats/breakdown?by=${by}`, { cache: 'no-store' }),
    getBenchmark: () => apiFetch<BenchmarkStat>("/api/stats/benchmark", { cache: 'no-store' }),
    getBottlenecks: (limit: number = 3) => apiFetch<BottleneckTopic[]>(`/api/stats/bottlenecks?limit=${limit}`, { cache: 'no-store' }),
    getDomainSummary: () => apiFetch<DomainSummaryResponse>("/api/stats/domain-summary", { cache: 'no-store' }),
    getErrorNotebookSummary: () => apiFetch<ErrorNotebookSummary>("/api/stats/error-notebook-summary", { cache: 'no-store' }),
    getInstitutionRadar: (institution?: string, compareInstitution?: string, signal?: AbortSignal) => {
      const params = new URLSearchParams();
      if (institution) params.append("institution", institution);
      if (compareInstitution) params.append("compare_institution", compareInstitution);
      const qs = params.toString();
      return apiFetch<InstitutionRadarResponse>(`/api/stats/institution-radar${qs ? `?${qs}` : ""}`, { cache: 'no-store', signal });
    },
    logRadarAction: (action: "study" | "simulado" | "review") =>
      apiFetch<{success: boolean}>("/api/stats/institution-radar/action", {
        method: "POST",
        body: JSON.stringify({ action }),
      }),
    resetProgress: () =>
      apiFetch<{success: boolean}>("/api/stats/reset", {
        method: "DELETE",
      }),


  },
  sessions: {
    get: (sessionType: string) =>
      apiFetch<{data: unknown, updated_at: string} | {data: null}>(`/api/sessions/${sessionType}`, { cache: 'no-store' }),
    save: (sessionType: string, data: unknown) =>
      apiFetch<{success: boolean}>(`/api/sessions/${sessionType}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (sessionType: string) =>
      apiFetch<{success: boolean}>(`/api/sessions/${sessionType}`, {
        method: "DELETE",
      }),
    saveSimulado: async (payload: {
      client_session_id: string;
      planned_duration_seconds: number;
      elapsed_seconds: number;
      total_questions: number;
      answered_count: number;
      correct_count: number;
      filters?: Record<string, unknown>;
      area_results?: Array<Record<string, unknown>>;
    }) => {
      try {
        return await apiFetch<{ success: boolean }>(`/api/sessions/simulado`, {
          method: "POST",
          body: JSON.stringify(payload)
        });
      } catch (err) {
        console.warn("Falha ao salvar sessao de simulado no backend:", err);
        return { success: false };
      }
    }
  },
  planner: {
    getConfig: () => apiFetch<PlannerConfig>("/api/planner/config", { cache: 'no-store' }),
    saveConfig: async (config: PlannerConfig) => {
      try {
        return await apiFetch<{success: boolean}>("/api/planner/config", {
          method: "POST",
          body: JSON.stringify(config),
        });
      } catch (error) {
        const usesProfileFields = config.target_institution !== undefined ||
          config.target_institutions !== undefined ||
          config.target_specialty !== undefined;

        // Older API instances only accept the original planner fields. Retry
        // without the optional profile metadata so they do not block the user
        // from creating a study plan during a rolling deployment.
        if (!usesProfileFields || !(error instanceof Error) || !error.message.includes("400")) {
          throw error;
        }

        const legacyConfig: PlannerConfig = {
          exam_date: config.exam_date,
          start_date: config.start_date,
          days_per_week: config.days_per_week,
          hours_per_day: config.hours_per_day,
          target_score: config.target_score,
        };
        return apiFetch<{success: boolean}>("/api/planner/config", {
          method: "POST",
          body: JSON.stringify(legacyConfig),
        });
      }
    },
    resetConfig: () => apiFetch<{success: boolean}>("/api/planner/config/reset", {
      method: "POST",
    }),
    getProgress: () => apiFetch<PlannerProgressMap>("/api/planner", { cache: 'no-store' }),
    getTopicProgress: () => apiFetch<PlannerTopicProgressMap>("/api/planner/topics", { cache: 'no-store' }),
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
    markTopic: (week: number, subtema: string, completed: boolean) =>
      apiFetch<{success: boolean}>(`/api/planner/${week}/topic`, {
        method: "POST",
        body: JSON.stringify({ subtema, completed }),
      }),
    markRevision: (week: number, type: 'rev24h' | 'rev7d' | 'rev30d', checked: boolean) =>
      apiFetch<{success: boolean}>(`/api/planner/${week}/revision`, {
        method: "POST",
        body: JSON.stringify({ type, checked }),
      }),
    exportIcs: async () => {
      const url = `${API_BASE}/api/planner/export/ics`;
      const token = typeof window !== "undefined" ? (window as unknown as { __medquest_token?: string }).__medquest_token : undefined;
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error("Falha ao exportar cronograma para agenda");
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `medquest_cronograma_${new Date().toISOString().split("T")[0]}.ics`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    },
    getCalendarFeedUrl: () => {
      const base = typeof window !== "undefined" ? (API_BASE || window.location.origin) : API_BASE;
      return `${base}/api/planner/calendar/feed`;
    },
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
      params.delete("limit");
      const qs = params.toString();
      return apiFetch<QuestionMeta>(`/api/meta${qs ? `?${qs}` : ''}`, { cache: 'no-store' });
    },
    getTaxonomy: () => apiFetch<Record<string, Record<string, string>>>("/api/taxonomy", { cache: 'force-cache' }),
    updateClassification: (qid: number, data: { area: string; subtema: string; topic?: string }) =>
      apiFetch<{ success: boolean; question: { id: number; area: string; subtema: string; subtema_id: string; topic: string } }>(
        `/api/questions/${qid}/classification`,
        {
          method: "PATCH",
          body: JSON.stringify(data),
        }
      ),
    getSubtemas: (area?: string, q?: string) => {
      const params = new URLSearchParams();
      if (area) params.append("area", area);
      if (q) params.append("q", q);
      return apiFetch<SubtemaItem[]>(`/api/subtemas?${params.toString()}`, { next: { revalidate: 60 } });
    },
    getList: async (filters: Record<string, string | string[]>) => {
      const getLocalFallback = async () => {
        if (typeof window !== "undefined" && localDb) {
          const uid = getLocalOwnerId();
          let cached = await localDb.questions.where('_owner_id').equals(uid).toArray();

          if (filters.area) {
            const area = Array.isArray(filters.area) ? filters.area[0] : filters.area;
            cached = cached.filter(q => q.area === area);
          }
          if (filters.subtema) {
            const subtema = Array.isArray(filters.subtema) ? filters.subtema[0] : filters.subtema;
            cached = cached.filter(q => q.subtema === subtema);
          }
          if (filters.institution) {
            const inst = Array.isArray(filters.institution) ? filters.institution[0] : filters.institution;
            cached = cached.filter(q => q.institution_code === inst);
          }
          if (cached.length > 0) {
            const limit = typeof filters.limit === "string" ? parseInt(filters.limit, 10) : 50;
            return cached.slice(0, isNaN(limit) ? 50 : limit).map(q => ({
              id: q.id,
              source_file: q.source_file,
              source_number: q.source_number,
              year: q.year,
              institution_code: q.institution_code,
              institution_label: q.institution_label,
              topic: q.topic,
              area: q.area,
              subtema: q.subtema,
            }));
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      const params = new URLSearchParams();
      for (const [key, value] of Object.entries(filters)) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v));
        } else if (value !== undefined && value !== "") {
          params.append(key, value);
        }
      }
      try {
        return await apiFetch<QuestionListItem[]>(`/api/questions?${params.toString()}`, { cache: 'no-store' });
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    getDetail: async (id: number) => {
      const getLocalFallback = async () => {
        if (typeof window !== "undefined" && localDb) {
          const uid = getLocalOwnerId();
          const cached = await localDb.questions.where('_owner_id').equals(uid).filter(q => q.id === id).first();

          if (cached) return cached;
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        return await apiFetch<QuestionDetail>(`/api/questions/${id}`, { cache: 'no-store' });
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    submitAttempt: (id: number, selected_letter: string, time_spent_ms: number, confidence: string = "defer", is_correct?: boolean | null, user_answer_text?: string) =>
      apiFetch<AttemptResult>(`/api/questions/${id}/attempt`, {
        method: "POST",
        body: JSON.stringify({
          selected_letter,
          time_spent_ms,
          confidence,
          ...(is_correct !== undefined && is_correct !== null ? { is_correct } : {}),
          ...(user_answer_text ? { user_answer_text } : {})
        }),
      }),
    reviewFSRS: (id: number, confidence: string, is_correct?: boolean) =>
      apiFetch<{success: boolean, next_review_date: string, is_correct?: boolean}>(`/api/questions/${id}/review`, {
        method: "POST",
        body: JSON.stringify({
          confidence,
          ...(is_correct !== undefined ? { is_correct } : {})
        })
      }),
    toggleFavorite: (id: number) => apiFetch<{is_favorite: boolean}>(`/api/questions/${id}/favorite`, {
      method: "POST"
    }),
    search: (q: string, semantic: boolean = false, signal?: AbortSignal) =>
      apiFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}&semantic=${semantic}`, { cache: 'no-store', signal }),
    askAI: (id: number, user_question?: string, user_letter?: string) =>
      apiFetch<{ answer: string; model: string; source: string }>(`/api/questions/${id}/ask_ai`, {
        method: "POST",
        body: JSON.stringify({ user_question, user_letter })
      }),
    getSimuladoUSP: async () => {
      const getLocalFallback = async () => {
        if (typeof window !== "undefined" && localDb) {
          const uid = getLocalOwnerId();
          const cached = await localDb.questions.where('_owner_id').equals(uid).toArray();
          if (cached.length > 0) {
            return cached.map(q => ({
              id: q.id,
              source_file: q.source_file,
              source_number: q.source_number,
              year: q.year,
              institution_code: q.institution_code,
              institution_label: q.institution_label,
              topic: q.topic,
              area: q.area,
              subtema: q.subtema,
            }));
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        return await apiFetch<QuestionListItem[]>("/api/simulado/usp", { cache: 'no-store' });
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    getCustomSimulado: async (config: { institutions?: string[], years?: string[], questions_per_area?: number, duration_minutes?: number, force_4_options?: boolean }) => {
      const getLocalFallback = async () => {
        if (typeof window !== "undefined" && localDb) {
          const uid = getLocalOwnerId();
          const cached = await localDb.questions.where('_owner_id').equals(uid).toArray();

          if (cached.length > 0) {
            return cached.map(q => ({
              id: q.id,
              source_file: q.source_file,
              source_number: q.source_number,
              year: q.year,
              institution_code: q.institution_code,
              institution_label: q.institution_label,
              topic: q.topic,
              area: q.area,
              subtema: q.subtema,
            }));
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        return await apiFetch<QuestionListItem[]>("/api/simulado/custom", {
          method: "POST",
          body: JSON.stringify(config)
        });
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    saveSimuladoSession: (data: {
      client_session_id: string; planned_duration_seconds: number; elapsed_seconds: number;
      total_questions: number; answered_count: number; correct_count: number;
      filters: Record<string, unknown>; area_results: Array<Record<string, unknown>>;
    }) => apiFetch<{success: boolean}>("/api/simulado/sessions", {
      method: "POST", body: JSON.stringify(data),
    }),
    submitAttemptBatch: (attempts: BatchAttemptItem[]) => apiFetch<BatchAttemptResult>(`/api/attempt/batch`, {
      method: "POST",
      body: JSON.stringify({ attempts })
    }),
    getBatch: async (ids: number[], force_4_options: boolean = false) => {
      const getLocalFallback = async () => {
        if (typeof window !== "undefined" && localDb) {
          try {
            const uid = getLocalOwnerId();
            const cached = await localDb.questions.where('_owner_id').equals(uid).filter(q => ids.includes(q.id)).toArray();
            // A partial batch would make a resumed simulado render questions
            // without their alternatives. Fall back to the network instead.
            if (cached.length === ids.length) {
              return { questions: cached } as unknown as BatchDetailResponse;
            }
          } catch (e) {
            console.error("Dexie error loading batch", e);
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        return await apiFetch<BatchDetailResponse>(`/api/questions/batch`, {
          method: "POST",
          body: JSON.stringify({ ids, force_4_options })
        });
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
  },
  flashcards: {
    preview: async (question_id: number, wrong_letter?: string) => {
      const getLocalFallback = async (): Promise<{ front: string; back: string; context: string } | null> => {
        // Simple local fallback just to avoid breaking offline mode,
        // ideally we would format it similarly to backend.
        if (typeof window !== "undefined" && localDb) {
           // We can mock a simple preview
           return { front: "[Draft] Pergunta...", back: "Gabarito...", context: "Local" };
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        const res = await apiFetch<{ front: string; back: string; context: string }>(`/api/flashcards/preview`, {
          method: "POST",
          body: JSON.stringify({ question_id, wrong_letter: wrong_letter || "" })
        });
        return res;
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    save: async (question_id: number, front: string, back: string, context: string) => {
      const getLocalFallback = async (): Promise<FlashcardGenerateResponse | null> => {
        if (typeof window !== "undefined" && localDb) {
          try {
            const uid = getLocalOwnerId();
            const q = await localDb.questions.where('_owner_id').equals(uid).filter(item => item.id === question_id).first();
            if (q) {
              const mockCard: Flashcard & { _owner_id: string } = {
                id: Date.now(),
                question_id,
                front,
                back,
                next_review_date: new Date().toISOString(),
                stem: q.stem,
                is_ai_generated: true,
                source_context: context,
                _owner_id: uid,
              };
              await localDb.flashcards.put(mockCard);
              return {
                id: mockCard.id,
                question_id,
                front: mockCard.front,
                back: mockCard.back,
                context: mockCard.source_context
              };
            }
          } catch (e) {
            console.error("Dexie error saving local flashcard", e);
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        const res = await apiFetch<FlashcardGenerateResponse>(`/api/flashcards/save`, {
          method: "POST",
          body: JSON.stringify({ question_id, front, back, context })
        });
        if (typeof window !== "undefined" && localDb && res) {
          const uid = getLocalOwnerId();
          const cardToPut: Flashcard & { _owner_id: string } = {
            id: res.id,
            question_id: res.question_id,
            front: res.front,
            back: res.back,
            next_review_date: new Date().toISOString(),
            is_ai_generated: true,
            source_context: res.context,
            _owner_id: uid,
          };
          await localDb.flashcards.put(cardToPut);
        }
        return res;
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    generate: async (question_id: number, wrong_letter: string) => {
      const formatLocalCard = (q: QuestionDetail, wrongLetter: string) => {
        const correctAlt = q.alternatives?.find(a => "letter" in a && (a as { letter: string; is_correct?: boolean }).is_correct);
        const wrongAlt = q.alternatives?.find(a => a.letter === wrongLetter);
        const correctClean = (correctAlt?.text || "").replace(/^[A-Ea-e][\)\.\:\-]\s*/, "").trim();
        const wrongClean = (wrongAlt?.text || "").replace(/^[A-Ea-e][\)\.\:\-]\s*/, "").trim();
        const tag = `[${q.subtema || q.topic || q.area || "Caso Clínico"}]`;

        let scenario = (q.stem || "").trim();
        const endMatch = scenario.match(/(?:Diante disso|Diante do exposto|Diante desse quadro|Nesse momento|Nesse caso|Considerando o caso|Em relação ao caso|Sobre o caso descrito|Qual a conduta|Qual o diagnóstico|A melhor conduta|A conduta mais adequada).*$/i);
        if (endMatch && endMatch.index && endMatch.index > 30) {
          scenario = scenario.substring(0, endMatch.index).trim();
        }
        if (scenario && !scenario.endsWith(".")) scenario += ".";

        const front = scenario && scenario.length > 20
          ? `${tag} ${scenario}\n\n👉 Decisão / Conduta indicada: {{c1::${correctClean}}}`
          : `${tag}\n\n👉 Decisão / Conduta indicada: {{c1::${correctClean}}}`;

        const back = wrongClean && wrongClean.toLowerCase() !== correctClean.toLowerCase()
          ? `💡 Gabarito Oficial:\n${correctClean}\n\n⚠️ Atenção ao distrator:\nA opção '${wrongClean}' é incorreta para este quadro clínico.`
          : `💡 Gabarito Oficial:\n${correctClean}`;

        return { front, back, context: `${q.area || ""} > ${q.subtema || ""}`.trim() };
      };

      const getLocalFallback = async (): Promise<FlashcardGenerateResponse | null> => {
        if (typeof window !== "undefined" && localDb) {
          try {
            const uid = getLocalOwnerId();
            const q = await localDb.questions.where('_owner_id').equals(uid).filter(item => item.id === question_id).first();
            if (q) {
              const { front, back, context } = formatLocalCard(q, wrong_letter);
              const mockCard: Flashcard & { _owner_id: string } = {
                id: Date.now(),
                question_id,
                front,
                back,
                next_review_date: new Date().toISOString(),
                stem: q.stem,
                is_ai_generated: true,
                source_context: context,
                _owner_id: uid,
              };
              await localDb.flashcards.put(mockCard);
              return {
                id: mockCard.id,
                question_id,
                front: mockCard.front,
                back: mockCard.back,
                context: mockCard.source_context
              };
            }
          } catch (e) {
            console.error("Dexie error creating local flashcard", e);
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        const res = await apiFetch<FlashcardGenerateResponse>(`/api/flashcards/generate`, {
          method: "POST",
          body: JSON.stringify({ question_id, wrong_letter })
        });
        if (typeof window !== "undefined" && localDb && res) {
          const uid = getLocalOwnerId();
          const cardToPut: Flashcard & { _owner_id: string } = {
            id: res.id,
            question_id: res.question_id,
            front: res.front,
            back: res.back,
            next_review_date: new Date().toISOString(),
            is_ai_generated: true,
            source_context: res.context,
            _owner_id: uid,
          };
          await localDb.flashcards.put(cardToPut);
        }
        return res;
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    generateBatch: async (items: Array<{ question_id: number; wrong_letter: string }>) => {
      const formatLocalCard = (q: QuestionDetail, wrongLetter: string) => {
        const correctAlt = q.alternatives?.find(a => "letter" in a && (a as { letter: string; is_correct?: boolean }).is_correct);
        const wrongAlt = q.alternatives?.find(a => a.letter === wrongLetter);
        const correctClean = (correctAlt?.text || "").replace(/^[A-Ea-e][\)\.\:\-]\s*/, "").trim();
        const wrongClean = (wrongAlt?.text || "").replace(/^[A-Ea-e][\)\.\:\-]\s*/, "").trim();
        const tag = `[${q.subtema || q.topic || q.area || "Caso Clínico"}]`;

        let scenario = (q.stem || "").trim();
        const endMatch = scenario.match(/(?:Diante disso|Diante do exposto|Diante desse quadro|Nesse momento|Nesse caso|Considerando o caso|Em relação ao caso|Sobre o caso descrito|Qual a conduta|Qual o diagnóstico|A melhor conduta|A conduta mais adequada).*$/i);
        if (endMatch && endMatch.index && endMatch.index > 30) {
          scenario = scenario.substring(0, endMatch.index).trim();
        }
        if (scenario && !scenario.endsWith(".")) scenario += ".";

        const front = scenario && scenario.length > 20
          ? `${tag} ${scenario}\n\n👉 Decisão / Conduta indicada: {{c1::${correctClean}}}`
          : `${tag}\n\n👉 Decisão / Conduta indicada: {{c1::${correctClean}}}`;

        const back = wrongClean && wrongClean.toLowerCase() !== correctClean.toLowerCase()
          ? `💡 Gabarito Oficial:\n${correctClean}\n\n⚠️ Atenção ao distrator:\nA opção '${wrongClean}' é incorreta para este quadro clínico.`
          : `💡 Gabarito Oficial:\n${correctClean}`;

        return { front, back, context: `${q.area || ""} > ${q.subtema || ""}`.trim() };
      };

      const getLocalFallback = async (): Promise<BatchFlashcardGenerateResponse | null> => {
        if (typeof window !== "undefined" && localDb) {
          try {
            const uid = getLocalOwnerId();
            const created: FlashcardGenerateResponse[] = [];
            for (const item of items) {
              const q = await localDb.questions.where('_owner_id').equals(uid).filter(qItem => qItem.id === item.question_id).first();
              if (q) {
                const { front, back, context } = formatLocalCard(q, item.wrong_letter);
                const cardId = Date.now() + Math.floor(Math.random() * 1000);
                const mockCard: Flashcard & { _owner_id: string } = {
                  id: cardId,
                  question_id: item.question_id,
                  front,
                  back,
                  next_review_date: new Date().toISOString(),
                  stem: q.stem,
                  is_ai_generated: true,
                  source_context: context,
                  _owner_id: uid,
                };
                await localDb.flashcards.put(mockCard);
                created.push({
                  id: mockCard.id,
                  question_id: item.question_id,
                  front: mockCard.front,
                  back: mockCard.back,
                  context: mockCard.source_context
                });
              }
            }
            if (created.length > 0) {
              return { success: true, count: created.length, flashcards: created };
            }
          } catch (e) {
            console.error("Dexie error creating batch local flashcards", e);
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        const res = await apiFetch<BatchFlashcardGenerateResponse>(`/api/flashcards/generate-batch`, {
          method: "POST",
          body: JSON.stringify({ items })
        });
        if (typeof window !== "undefined" && localDb && res.flashcards) {
          const uid = getLocalOwnerId();
          const cardsToPut: Array<Flashcard & { _owner_id: string }> = res.flashcards.map(f => ({
            id: f.id,
            question_id: f.question_id,
            front: f.front,
            back: f.back,
            next_review_date: new Date().toISOString(),
            is_ai_generated: true,
            _owner_id: uid,
          }));
          await localDb.flashcards.bulkPut(cardsToPut);
        }
        return res;
      } catch (err) {
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    getDecks: () => apiFetch<FlashcardDecksResponse>("/api/flashcards/decks", { cache: "no-store" }),
    getDue: async (includeAll: boolean = false, signal?: AbortSignal, deck?: string) => {
      const getLocalFallback = async () => {
        if (typeof window !== "undefined" && localDb) {
          try {
            const uid = getLocalOwnerId();
            let cards = await localDb.flashcards.where('_owner_id').equals(uid).toArray();
            if (deck && deck !== "all") {
              cards = cards.filter(c => (c.deck_name || "Geral").toLowerCase() === deck.toLowerCase());
            }

            if (includeAll) return cards;
            const now = Date.now();
            return cards.filter(card => !card.next_review_date || new Date(card.next_review_date).getTime() <= now);
          } catch (e) {
            console.error("Dexie error loading flashcards", e);
            return [];
          }
        }
        return null;
      };

      if (typeof window !== "undefined" && !navigator.onLine) {
        const local = await getLocalFallback();
        if (local) return local;
      }

      try {
        const params = new URLSearchParams();
        if (includeAll) params.append("all", "true");
        if (deck && deck !== "all") params.append("deck", deck);
        const qs = params.toString();
        return await apiFetch<Flashcard[]>(`/api/flashcards/review${qs ? `?${qs}` : ""}`, { cache: 'no-store', signal });
      } catch (err) {
        if (signal?.aborted) throw err;
        const local = await getLocalFallback();
        if (local) return local;
        throw err;
      }
    },
    getUpcoming: async (signal?: AbortSignal, deck?: string) => {
      try {
        const params = new URLSearchParams();
        params.append("scope", "upcoming");
        if (deck && deck !== "all") params.append("deck", deck);
        const qs = params.toString();
        return await apiFetch<Flashcard[]>(`/api/flashcards/review?${qs}`, { cache: 'no-store', signal });
      } catch (err) {
        if (signal?.aborted) throw err;
        if (typeof window !== "undefined" && localDb) {
          try {
            const uid = getLocalOwnerId();
            let cards = await localDb.flashcards.where('_owner_id').equals(uid).toArray();
            if (deck && deck !== "all") {
              cards = cards.filter(c => (c.deck_name || "Geral").toLowerCase() === deck.toLowerCase());
            }
            const now = Date.now();
            return cards.filter(card => card.next_review_date && new Date(card.next_review_date).getTime() > now);
          } catch {
            return [];
          }
        }
        return [];
      }
    },

    importFile: async (file: File, deckName?: string): Promise<AnkiImportResult> => {
      const formData = new FormData();
      formData.append("file", file);
      if (deckName) formData.append("deck_name", deckName);

      const url = `${API_BASE}/api/flashcards/import/file`;
      const token = typeof window !== "undefined" ? (window as unknown as { __medquest_token?: string }).__medquest_token : undefined;
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(url, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!res.ok) {
        let errMsg = "Falha ao importar arquivo";
        try {
          const json = await res.json();
          if (json?.error) errMsg = json.error;
        } catch {
          // ignore
        }
        throw new Error(errMsg);
      }

      return await res.json();
    },

    importBatch: async (
      cards: Array<{ front: string; back: string; deck_name?: string; tags?: string[]; anki_nid?: number; anki_cid?: number }>,
      deckName?: string
    ): Promise<AnkiImportResult> => {
      return apiFetch<AnkiImportResult>("/api/flashcards/import/batch", {
        method: "POST",
        body: JSON.stringify({ cards, deck_name: deckName }),
      });
    },

    syncAnkiStates: async (cards: Array<{ anki_cid: number; anki_nid?: number; interval: number; reps: number; lapses: number }>) => {
      if (!cards.length) return { success: true, updated: 0 };
      return apiFetch<{ success: boolean; updated: number }>("/api/flashcards/anki/sync-state", {
        method: "POST",
        body: JSON.stringify({ cards }),
      });
    },

    deleteDeck: async (deckName: string): Promise<{ success: boolean; deck_name: string; deleted_count: number }> => {
      return apiFetch<{ success: boolean; deck_name: string; deleted_count: number }>("/api/flashcards/deck", {
        method: "DELETE",
        body: JSON.stringify({ deck_name: deckName }),
      });
    },

    review: (id: number, confidence: string) => apiFetch<{id: number, next_review_date: string}>(`/api/flashcards/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ confidence })
    }),
    report: (id: number, reason: string) => apiFetch<{success: boolean}>(`/api/flashcards/${id}/report`, {
      method: "POST",
      body: JSON.stringify({ reason })
    }),
    exportAnki: async (dueOnly: boolean = false) => {
      const url = `${API_BASE}/api/flashcards/export/anki${dueOnly ? "?due_only=true" : ""}`;
      const token = typeof window !== "undefined" ? (window as unknown as { __medquest_token?: string }).__medquest_token : undefined;
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error("Falha ao exportar flashcards para o Anki");
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `medquest_flashcards_anki_${new Date().toISOString().split("T")[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    },
  },
  notifications: {
    getConfig: () => apiFetch<NotificationConfig>("/api/notifications/config", { cache: "no-store" }),
    updateConfig: (config: NotificationConfigUpdate) =>
      apiFetch<NotificationConfigUpdate & { updated_at: string }>("/api/notifications/config", {
        method: "PUT",
        body: JSON.stringify(config),
      }),
    subscribe: (sub: PushSubscriptionPayload) =>
      apiFetch<{ success: boolean }>("/api/notifications/subscribe", {
        method: "POST",
        body: JSON.stringify(sub),
      }),
    unsubscribe: (endpoint?: string) =>
      apiFetch<{ success: boolean }>("/api/notifications/subscribe", {
        method: "DELETE",
        body: JSON.stringify({ endpoint }),
      }),
  },
};
