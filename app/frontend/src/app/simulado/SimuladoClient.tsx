"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { QuestionMeta, QuestionListItem, QuestionDetail, BatchAttemptItem, BatchAttemptResultItem, FlashcardGenerateResponse } from "@/types/api";
import { api, OfflineQueuedError } from "@/lib/api";
import { Play, Clock, ChevronLeft, ChevronRight, FileSignature, AlertTriangle, BookOpen, AlertCircle, RotateCcw, Flag, CloudOff, Sparkles, CheckCircle2 } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import Link from "next/link";

import { normalizeFlashcard } from "@/lib/normalizeFlashcard";
import { LEARNING_SESSION_VERSION, readLearningSession, writeLearningSession, removeLearningSession, deadlineFromNow } from "@/lib/sessionState";
import { motion, AnimatePresence } from "framer-motion";
import { ImageViewer } from "@/components/ImageViewer";
import { Grid as FixedSizeGrid, CellComponentProps } from "react-window";
import { AutoSizer } from "react-virtualized-auto-sizer";
import Image from "next/image";
type SimuladoState = "START" | "LOADING" | "PLAYING" | "SUBMITTING" | "RESULTS" | "OFFLINE_SUBMITTED";

interface SavedSimuladoState {
  version: number;
  state: SimuladoState;
  queue: QuestionListItem[];
  answers: Record<number, string>;
  deadlineAt: number;
  currentIndex: number;
  resultsMap: Record<number, BatchAttemptResultItem>;
  flagged: Record<number, boolean>;
  force4Options: boolean;
  queueId?: string;
  savedAt: number;
}

function isSavedSimuladoState(value: unknown): value is SavedSimuladoState {
  if (typeof value !== "object" || value === null) return false;
  const saved = value as Partial<SavedSimuladoState>;
  return saved.version === LEARNING_SESSION_VERSION &&
    (saved.state === "PLAYING" || saved.state === "RESULTS" || saved.state === "OFFLINE_SUBMITTED") &&
    Array.isArray(saved.queue) && saved.queue.length > 0 &&
    typeof saved.currentIndex === "number" && saved.currentIndex >= 0 &&
    saved.currentIndex < saved.queue.length &&
    typeof saved.answers === "object" && saved.answers !== null &&
    typeof saved.resultsMap === "object" && saved.resultsMap !== null &&
    typeof saved.flagged === "object" && saved.flagged !== null &&
    typeof saved.deadlineAt === "number" && Number.isFinite(saved.deadlineAt);
}

export function SimuladoClient({
  initialFilters = {},
  meta
}: {
  initialFilters?: Record<string, string | string[]>;
  meta?: QuestionMeta;
}) {
  const [state, setState] = useState<SimuladoState>("START");
  const [queue, setQueue] = useState<QuestionListItem[]>([]);
  
  // Quiz State
  const [currentIndex, setCurrentIndex] = useState(0);
  const [detailsCache, setDetailsCache] = useState<Record<number, QuestionDetail>>({});
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState(false);
  const [showAreaSummary, setShowAreaSummary] = useState(false);
  const [showResultsSummary, setShowResultsSummary] = useState(false);
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);
  
  // Answers: question_id -> letter
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [resultsMap, setResultsMap] = useState<Record<number, BatchAttemptResultItem>>({});
  const [queueId, setQueueId] = useState<string | undefined>(undefined);
  const [isSyncingOffline, setIsSyncingOffline] = useState(false);
  
  // Flashcards
  const [generatingBatchFlashcards, setGeneratingBatchFlashcards] = useState(false);
  const [batchFlashcardsResult, setBatchFlashcardsResult] = useState<{ count: number } | null>(null);
  const [questionFlashcardsMap, setQuestionFlashcardsMap] = useState<Record<number, FlashcardGenerateResponse>>({});
  const [generatingSingleFlashcard, setGeneratingSingleFlashcard] = useState<number | null>(null);
  const [draftFlashcardsMap, setDraftFlashcardsMap] = useState<Record<number, { front: string; back: string; context: string }>>({});
  const [savingSingleFlashcard, setSavingSingleFlashcard] = useState<number | null>(null);
  
  // Marcar para revisar
  const [flagged, setFlagged] = useState<Record<number, boolean>>({});
  // Filtro da sidebar: 'all' | 'unanswered' | 'flagged'
  const [sidebarFilter, setSidebarFilter] = useState<'all' | 'unanswered' | 'flagged'>('all');
  
  // Duração proporcional: 3 min/questão (120 Qs = 6h), arredondado
  const [timeLeft, setTimeLeft] = useState(6 * 60 * 60);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const deadlineRef = useRef(0);
  const hasCustomFilters = Object.keys(initialFilters).length > 0;
  
  const [customConfig, setCustomConfig] = useState({
    institutions: [] as string[],
    years: [] as string[],
    questions_per_area: 20,
    duration_minutes: 180,
    force_4_options: false
  });

  const [hasSavedState, setHasSavedState] = useState(false);
  const [clientReady, setClientReady] = useState(false);
  const [storageReady, setStorageReady] = useState(false);
  const [force4Options, setForce4Options] = useState(false);
  const submitLockRef = useRef(false);
  const startLockRef = useRef(false);
  const detailRequestRef = useRef(0);
  const dialogInitialFocusRef = useRef<HTMLButtonElement>(null);
  const customConfigLoadedRef = useRef(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        const saved = localStorage.getItem("medquest_simulado_config");
        if (saved) {
          const parsed = JSON.parse(saved) as Partial<typeof customConfig>;
          setCustomConfig(prev => ({
            ...prev,
            institutions: Array.isArray(parsed.institutions) ? parsed.institutions.slice(0, 20) : prev.institutions,
            years: Array.isArray(parsed.years) ? parsed.years.slice(0, 20) : prev.years,
            questions_per_area: Math.max(1, Math.min(100, Number(parsed.questions_per_area) || prev.questions_per_area)),
            duration_minutes: Math.max(15, Math.min(600, Number(parsed.duration_minutes) || prev.duration_minutes)),
            force_4_options: Boolean(parsed.force_4_options),
          }));
        }
      } catch {
        localStorage.removeItem("medquest_simulado_config");
      } finally {
        customConfigLoadedRef.current = true;
      }
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (customConfigLoadedRef.current) {
      localStorage.setItem("medquest_simulado_config", JSON.stringify(customConfig));
    }
  }, [customConfig]);

  useEffect(() => {
    if (showAreaSummary) dialogInitialFocusRef.current?.focus();
  }, [showAreaSummary]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setHasSavedState(readLearningSession("simulado", isSavedSimuladoState) !== null);
      setStorageReady(true);
      setClientReady(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const resumeSimulado = () => {
    const saved = readLearningSession("simulado", isSavedSimuladoState);
    if (saved) {
      setState(saved.state);
      setQueue(saved.queue);
      setAnswers(saved.answers);
      deadlineRef.current = saved.deadlineAt;
      setTimeLeft(Math.max(0, Math.ceil((saved.deadlineAt - Date.now()) / 1000)));
      setCurrentIndex(saved.currentIndex);
      setResultsMap(saved.resultsMap);
      setFlagged(saved.flagged);
      setForce4Options(saved.force4Options);
      setQueueId(saved.queueId);
        
      const ids = saved.queue.map((question: QuestionListItem) => question.id);
      api.questions.getBatch(ids, saved.force4Options).then(batchRes => {
        const cache: Record<number, QuestionDetail> = {};
        for (const q of batchRes.questions) cache[q.id] = q;
        setDetailsCache(cache);
      }).catch(() => {
        toast.error("Erro ao carregar detalhes do simulado retomado.");
      });
      setHasSavedState(false);
      toast.success("Simulado retomado do ponto em que você parou.");
    }
  };

  useEffect(() => {
    if (!storageReady) return;
    if (state === "PLAYING" || state === "RESULTS" || state === "OFFLINE_SUBMITTED") {
      writeLearningSession("simulado", {
        version: LEARNING_SESSION_VERSION,
        state,
        queue,
        answers,
        deadlineAt: deadlineRef.current,
        currentIndex,
        resultsMap,
        flagged,
        force4Options,
        queueId,
        savedAt: Date.now(),
      } satisfies SavedSimuladoState);
    }
  }, [storageReady, state, queue, answers, currentIndex, resultsMap, flagged, force4Options, queueId]);

  // Load Simulado
  const startSimulado = async () => {
    if (startLockRef.current) return;
    startLockRef.current = true;
    if (hasSavedState) {
      removeLearningSession("simulado");
      setHasSavedState(false);
    }
    setState("LOADING");
    try {
      let qList: QuestionListItem[];
      let isForce4Options = false;
      let durationHours = 6;

      if (hasCustomFilters) {
        const limit = initialFilters.limit || "50";
        qList = await api.questions.getList({ ...initialFilters, limit });
        durationHours = (qList.length / 120) * 6;
      } else {
        qList = await api.questions.getCustomSimulado(customConfig);
        isForce4Options = customConfig.force_4_options;
        durationHours = customConfig.duration_minutes / 60;
      }

      if (qList.length === 0) {
        toast.error("Erro: Não há questões suficientes para montar o simulado com esses filtros.");
        setState("START");
        return;
      }
      
      const calcTime = Math.round(durationHours * 60 * 60);
      setTimeLeft(calcTime);
      deadlineRef.current = deadlineFromNow(calcTime);
      setForce4Options(isForce4Options);
      
      setQueue(qList);
      setCurrentIndex(0);
      setAnswers({});
      setResultsMap({});
      setFlagged({});
      setSidebarFilter('all');
      setState("PLAYING");
      
      // Batch prefetch all question details in one request
      const ids = qList.map(q => q.id);
      try {
        const batchRes = await api.questions.getBatch(ids, isForce4Options);
        const cache: Record<number, QuestionDetail> = {};
        for (const q of batchRes.questions) {
          cache[q.id] = q;
        }
        setDetailsCache(cache);
      } catch {
        // Fallback: load first question individually
        loadDetail(qList[0].id);
      }
    } catch {
      toast.error("Erro ao gerar simulado.");
      setState("START");
    } finally {
      startLockRef.current = false;
    }
  };

  const loadDetail = async (id: number) => {
    if (detailsCache[id]) return; // Already cached
    const requestId = ++detailRequestRef.current;
    setLoadingDetail(true);
    setDetailError(false);
    try {
      const detail = await api.questions.getDetail(id);
      setDetailsCache(prev => ({ ...prev, [id]: detail }));
    } catch {
      console.error("Erro ao carregar questão", id);
      if (detailRequestRef.current === requestId) setDetailError(true);
    } finally {
      if (detailRequestRef.current === requestId) setLoadingDetail(false);
    }
  };

  const submitSimulado = useCallback(async () => {
    if (submitLockRef.current) return;
    submitLockRef.current = true;
    setState("SUBMITTING");
    if (timerRef.current) clearInterval(timerRef.current);

    const attempts: BatchAttemptItem[] = Object.keys(answers).map(qIdStr => {
      const qId = parseInt(qIdStr);
      return {
        question_id: qId,
        selected_letter: answers[qId],
        confidence: "duvida" // We don't ask for confidence in Simulado, default to duvida
      };
    });

    try {
      const res = await api.questions.submitAttemptBatch(attempts);
      const rMap: Record<number, BatchAttemptResultItem> = {};
      res.results.forEach(r => {
        rMap[r.question_id] = r;
      });
      setResultsMap(rMap);
      setState("RESULTS");
      setCurrentIndex(0); // Go back to first question to review

      removeLearningSession("simulado");
    } catch (err) {
      if (err instanceof OfflineQueuedError) {
        toast("Respostas do simulado salvas no dispositivo; serão sincronizadas quando a conexão voltar.", { icon: "💾" });
        setQueueId(err.localId);
        setState("OFFLINE_SUBMITTED");
      } else {
        toast.error("Erro ao enviar simulado. Tente novamente.");
        setState("PLAYING");
      }
    } finally {
      submitLockRef.current = false;
    }
  }, [answers]);

  const handleGenerateSingleFlashcard = async (qid: number, wrongLetter: string) => {
    if (generatingSingleFlashcard) return;
    setGeneratingSingleFlashcard(qid);
    try {
      const res = await api.flashcards.preview(qid, wrongLetter || undefined);
      setDraftFlashcardsMap(prev => ({ ...prev, [qid]: res }));
    } catch {
      toast.error("Erro ao gerar prévia do flashcard.");
    } finally {
      setGeneratingSingleFlashcard(null);
    }
  };

  const handleSaveSingleFlashcard = async (qid: number) => {
    const draft = draftFlashcardsMap[qid];
    if (!draft || savingSingleFlashcard) return;
    setSavingSingleFlashcard(qid);
    try {
      const res = await api.flashcards.save(qid, draft.front, draft.back, draft.context);
      const qDetail = detailsCache[qid];
      const normalized = normalizeFlashcard({ ...res, stem: qDetail?.stem || "" });
      setQuestionFlashcardsMap(prev => ({ ...prev, [qid]: normalized }));
      setDraftFlashcardsMap(prev => {
        const next = { ...prev };
        delete next[qid];
        return next;
      });
      toast.success("Flashcard criado e inserido na sua Revisão Ativa!");
    } catch {
      toast.error("Erro ao salvar flashcard.");
    } finally {
      setSavingSingleFlashcard(null);
    }
  };

  const handleGenerateAllSimuladoWrongFlashcards = async () => {
    const wrongItems = queue
      .filter(q => resultsMap[q.id] && !resultsMap[q.id].is_correct && answers[q.id])
      .map(q => ({ question_id: q.id, wrong_letter: answers[q.id] }));

    if (wrongItems.length === 0) return;
    setGeneratingBatchFlashcards(true);
    try {
      const res = await api.flashcards.generateBatch(wrongItems);
      setBatchFlashcardsResult({ count: res.count });
      toast.success(`${res.count} flashcard(s) criado(s) e adicionado(s) à Revisão Ativa!`);
    } catch {
      toast.error("Erro ao gerar flashcards em lote.");
    } finally {
      setGeneratingBatchFlashcards(false);
    }
  };

  const submitSimuladoRef = useRef(submitSimulado);
  useEffect(() => {
    submitSimuladoRef.current = submitSimulado;
  }, [submitSimulado]);

  // Timer Effect
  useEffect(() => {
    if (state === "PLAYING") {
      timerRef.current = setInterval(() => {
        const remaining = Math.max(0, Math.ceil((deadlineRef.current - Date.now()) / 1000));
        setTimeLeft(remaining);
        if (remaining === 0) {
          if (timerRef.current) clearInterval(timerRef.current);
          setTimeout(() => submitSimuladoRef.current(), 0);
        }
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [state]);

  const handleManualSyncSimulado = useCallback(async () => {
    if (isSyncingOffline) return;
    setIsSyncingOffline(true);
    try {
      const attempts: BatchAttemptItem[] = Object.keys(answers).map(qIdStr => {
        const qId = parseInt(qIdStr, 10);
        return {
          question_id: qId,
          selected_letter: answers[qId],
          confidence: "duvida"
        };
      });

      if (attempts.length === 0) {
        removeLearningSession("simulado");
        setHasSavedState(false);
        setState("START");
        return;
      }

      if (navigator.onLine) {
        const res = await api.questions.submitAttemptBatch(attempts);
        if (res && res.results) {
          const rMap: Record<number, BatchAttemptResultItem> = {};
          res.results.forEach(r => {
            rMap[r.question_id] = r;
          });
          setResultsMap(rMap);
          removeLearningSession("simulado");
          setHasSavedState(false);
          setState("RESULTS");
          setCurrentIndex(0);
          toast.success("Simulado corrigido com sucesso!");
          return;
        }
      }

      const { syncManager } = await import("@/lib/sync");
      await syncManager.sync(true);
      toast.success("Tentativa de sincronização enviada.");
    } catch (err) {
      if (err instanceof OfflineQueuedError) {
        toast("Ainda sem conexão com a internet. Suas respostas permanecem salvas com segurança.", { icon: "💾" });
      } else {
        toast.error("Erro ao sincronizar. Verifique sua conexão e tente novamente.");
      }
    } finally {
      setIsSyncingOffline(false);
    }
  }, [answers, isSyncingOffline]);

  // Sincronização offline e ouvinte de sucesso
  useEffect(() => {
    if (state !== "OFFLINE_SUBMITTED") return;

    const handleSyncSuccess = (e: Event) => {
      const customEvent = e as CustomEvent<{
        id: string;
        endpoint: string;
        method: string;
        data: unknown;
      }>;
      const detail = customEvent.detail;
      if (detail && detail.endpoint.includes("/api/attempt/batch")) {
        const res = detail.data as { results?: BatchAttemptResultItem[] } | null;
        if (res && Array.isArray(res.results) && res.results.length > 0) {
          const rMap: Record<number, BatchAttemptResultItem> = {};
          res.results.forEach(r => {
            rMap[r.question_id] = r;
          });
          setResultsMap(rMap);
          removeLearningSession("simulado");
          setHasSavedState(false);
          setState("RESULTS");
          setCurrentIndex(0);
          toast.success("Simulado sincronizado e corrigido com sucesso!");
        } else {
          removeLearningSession("simulado");
          setHasSavedState(false);
          setState("START");
          toast.success("Simulado sincronizado!");
        }
      }
    };

    window.addEventListener("sync-item-success", handleSyncSuccess);

    const checkAndSync = async () => {
      try {
        const { syncManager } = await import('@/lib/sync');
        if (navigator.onLine) {
          await syncManager.sync();
        }
        if (queueId) {
          const failed = await syncManager.getFailedItems();
          if (failed.find(i => i.id === queueId)) {
            toast.error("A sincronização encontrou uma falha. Você pode tentar reenviar as respostas salvas.");
            setState("PLAYING");
            setQueueId(undefined);
            return;
          }
          const pending = await syncManager.getQueue();
          if (!pending.find(i => i.id === queueId)) {
            // Foi sincronizado
            removeLearningSession("simulado");
            setHasSavedState(false);
            setState("START");
          }
        }
      } catch (e) {
        console.error(e);
      }
    };

    const handleOnline = () => {
      void checkAndSync();
    };
    window.addEventListener("online", handleOnline);
    const interval = setInterval(checkAndSync, 5000);

    return () => {
      window.removeEventListener("sync-item-success", handleSyncSuccess);
      window.removeEventListener("online", handleOnline);
      clearInterval(interval);
    };
  }, [state, queueId]);

  const handleSelect = useCallback((letter: string) => {
    if (state !== "PLAYING") return;
    const currentQ = queue[currentIndex];
    setAnswers(prev => ({ ...prev, [currentQ.id]: letter }));
  }, [state, queue, currentIndex]);

  const toggleFlag = useCallback(() => {
    if (state !== "PLAYING") return;
    const currentQ = queue[currentIndex];
    setFlagged(prev => ({ ...prev, [currentQ.id]: !prev[currentQ.id] }));
  }, [state, queue, currentIndex]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      if (showAreaSummary) {
        if (e.key === "Escape") setShowAreaSummary(false);
        return;
      }

      if (state !== "PLAYING" && state !== "RESULTS") return;

      const key = e.key.toLowerCase();
      
      // Navigate
      if (key === 'arrowleft') {
        e.preventDefault();
        setCurrentIndex(prev => Math.max(0, prev - 1));
      } else if (key === 'arrowright') {
        e.preventDefault();
        setCurrentIndex(prev => Math.min(queue.length - 1, prev + 1));
      }

      if (state === "PLAYING") {
        // Toggle flag
        if (key === 'f') {
          e.preventDefault();
          toggleFlag();
        }

        // Select alternative (1-5 or a-e)
        const currentQ = queue[currentIndex];
        const detail = detailsCache[currentQ?.id];
        if (detail && detail.alternatives) {
          const idxMap: Record<string, number> = { '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, 'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4 };
          if (key in idxMap) {
            const idx = idxMap[key];
            if (idx < detail.alternatives.length) {
              handleSelect(detail.alternatives[idx].letter);
            }
          }
        }

        // Finish/submit
        if (key === 'enter') {
          e.preventDefault();
          setShowAreaSummary(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state, currentIndex, queue, detailsCache, handleSelect, toggleFlag, showAreaSummary]);


  // Filtro de questões visíveis na sidebar
  const filteredIndices = useMemo(() => {
    if (sidebarFilter === 'all') return queue.map((_, i) => i);
    if (sidebarFilter === 'unanswered') return queue.map((_, i) => i).filter(i => !answers[queue[i].id]);
    if (sidebarFilter === 'flagged') return queue.map((_, i) => i).filter(i => flagged[queue[i].id]);
    return queue.map((_, i) => i);
  }, [queue, answers, flagged, sidebarFilter]);

  // Resumo por área para modal de confirmação
  const areaSummary = useMemo(() => {
    const summary: Record<string, { total: number; answered: number; blank: number }> = {};
    for (const q of queue) {
      const area = q.area || "Sem área";
      if (!summary[area]) summary[area] = { total: 0, answered: 0, blank: 0 };
      summary[area].total++;
      if (answers[q.id]) summary[area].answered++;
      else summary[area].blank++;
    }
    return Object.entries(summary).map(([area, data]) => ({ area, ...data }));
  }, [queue, answers]);

  const navigateTo = (index: number) => {
    if (index >= 0 && index < queue.length) {
      setCurrentIndex(index);
      loadDetail(queue[index].id);
    }
  };

  const finishSimulado = () => {
    if (state !== "PLAYING") return;
    
    const unanswered = queue.length - Object.keys(answers).length;
    if (unanswered > 0) {
      setShowAreaSummary(true);
      return;
    }
    setShowAreaSummary(true);
  };

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (state === "START") {
    return (
      <div className="bg-card border border-border shadow-1 rounded-2xl p-6 md:p-8 max-w-4xl mx-auto w-full flex flex-col items-center">
        <div className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mb-6 ring-1 ring-primary/20">
          <FileSignature size={32} />
        </div>
        <h2 className="text-3xl font-bold text-foreground mb-3 text-center tracking-tight">
          {hasCustomFilters ? "Simulado Personalizado" : "Novo Simulado"}
        </h2>
        <p className="text-muted-foreground text-base mb-8 max-w-lg text-center">
          {hasCustomFilters 
            ? "Esta prova irá simular as condições reais de exame usando os filtros que você escolheu."
            : "Crie um simulado com as suas próprias configurações."}
        </p>

        {!hasCustomFilters && (
          <div className="w-full mb-8 bg-muted/30 p-6 rounded-2xl border border-border text-left flex flex-col gap-5 animate-in slide-in-from-top-4 fade-in duration-300">
            <div>
              <label className="block text-sm font-bold text-foreground mb-2">Bancas Incluídas (deixe vazio para todas)</label>
              <div className="flex flex-wrap gap-2">
                {(meta?.institutions.map(i => i.institution_code) || ['USP-SP', 'USP-RP', 'UNICAMP']).filter(i => !['SUS-SP', 'ENARE'].includes(i)).map(inst => (
                  <label key={inst} className="flex items-center gap-1.5 bg-background border border-border px-3 py-1.5 rounded-lg text-sm cursor-pointer hover:bg-muted transition-colors">
                    <input 
                      type="checkbox" 
                      checked={customConfig.institutions.includes(inst)}
                      onChange={(e) => {
                        setCustomConfig(prev => ({
                          ...prev,
                          institutions: e.target.checked 
                            ? [...prev.institutions, inst] 
                            : prev.institutions.filter(i => i !== inst)
                        }))
                      }}
                      className="rounded text-primary focus:ring-primary w-4 h-4"
                    />
                    {inst}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-foreground mb-2">Anos (deixe vazio para todos)</label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto pr-2 custom-scrollbar">
                {(meta?.years || []).map(year => String(year)).map(year => (
                  <label key={year} className="flex items-center gap-1.5 bg-background border border-border px-3 py-1.5 rounded-lg text-sm cursor-pointer hover:bg-muted transition-colors">
                    <input
                      type="checkbox"
                      checked={customConfig.years.includes(year)}
                      onChange={(event) => setCustomConfig(prev => ({
                        ...prev,
                        years: event.target.checked ? [...prev.years, year] : prev.years.filter(item => item !== year),
                      }))}
                      className="rounded text-primary focus:ring-primary w-4 h-4"
                    />
                    {year}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-5">
              <div className="flex-1">
                <label className="block text-sm font-bold text-foreground mb-2">Questões por Área</label>
                <div className="relative">
                  <input 
                    type="number" 
                    min="5" max="30" 
                    value={customConfig.questions_per_area}
                    onChange={(e) => setCustomConfig(prev => ({ ...prev, questions_per_area: parseInt(e.target.value) || 20 }))}
                    className="w-full bg-background border border-border rounded-xl p-3 text-foreground focus:ring-2 focus:ring-primary/50 transition-shadow outline-none"
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1.5 font-medium flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">info</span>
                  Multiplicado por 5 grandes áreas
                </p>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-bold text-foreground mb-2">Duração (minutos)</label>
                <div className="relative">
                  <input
                    type="number"
                    min="15" max="600" step="15"
                    value={customConfig.duration_minutes}
                    onChange={(event) => setCustomConfig(prev => ({ ...prev, duration_minutes: Math.max(15, Math.min(600, parseInt(event.target.value) || 180)) }))}
                    className="w-full bg-background border border-border rounded-xl p-3 text-foreground focus:ring-2 focus:ring-primary/50 transition-shadow outline-none"
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1.5 font-medium flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">info</span>
                  Entre 15 min e 10 horas
                </p>
              </div>
            </div>

            <label className="flex items-center gap-3 cursor-pointer border-t border-border/50 pt-5 mt-2 group">
              <input 
                type="checkbox" 
                checked={customConfig.force_4_options}
                onChange={(e) => setCustomConfig(prev => ({ ...prev, force_4_options: e.target.checked }))}
                className="rounded text-primary focus:ring-primary w-5 h-5 cursor-pointer"
              />
              <span className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">Forçar 4 Alternativas (Estilo Nova Prova USP)</span>
            </label>
          </div>
        )}
        
        <div className="grid grid-cols-2 gap-4 w-full max-w-lg mb-8 text-left">
          <div className="bg-muted/50 rounded-xl p-4 border border-border/50">
            <span className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground uppercase mb-1.5 tracking-wider">
              <span className="material-symbols-outlined text-[14px]">list_alt</span> Questões
            </span>
            <span className="text-lg font-bold text-foreground">
              {hasCustomFilters ? (initialFilters.limit || "Até 50") : (customConfig.questions_per_area * 5)} <span className="text-sm font-medium text-muted-foreground">un</span>
            </span>
          </div>
          <div className="bg-muted/50 rounded-xl p-4 border border-border/50">
            <span className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground uppercase mb-1.5 tracking-wider">
              <span className="material-symbols-outlined text-[14px]">timer</span> Duração
            </span>
            <span className="text-lg font-bold text-foreground">
              {hasCustomFilters 
                ? `${Math.round((Number(initialFilters.limit || 50) / 120) * 6 * 60)} min` 
                : `${customConfig.duration_minutes} min`
              }
            </span>
          </div>
          {!hasCustomFilters && (
            <div className="bg-muted/50 rounded-xl p-4 col-span-2 border border-border/50">
              <span className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground uppercase mb-1.5 tracking-wider">
                <span className="material-symbols-outlined text-[14px]">balance</span> Balanceamento
              </span>
              <span className="text-sm font-medium text-foreground">
                {`${customConfig.questions_per_area} Clínica • ${customConfig.questions_per_area} Cirurgia • ${customConfig.questions_per_area} Pediatria • ${customConfig.questions_per_area} GO • ${customConfig.questions_per_area} Preventiva`}
              </span>
            </div>
          )}
        </div>

        <div className="bg-warning/10 text-warning-foreground border border-warning/20 rounded-xl p-4 flex items-start gap-3 w-full max-w-lg mb-8 text-left text-sm shadow-sm">
          <AlertTriangle size={20} className="shrink-0 mt-0.5 text-warning" />
          <p className="font-medium text-warning-foreground/90">
            Você não receberá feedback imediato ao clicar nas alternativas. 
            O resultado e os comentários só serão exibidos ao finalizar a prova.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full max-w-lg">
          {hasSavedState && (
            <button 
              onClick={resumeSimulado}
              disabled={!clientReady}
              aria-label="Continuar Simulado em Andamento"
              className="flex-1 bg-secondary hover:bg-secondary/90 text-secondary-foreground font-bold py-3.5 px-6 rounded-xl transition-all flex items-center justify-center gap-2 shadow-sm hover:shadow-md disabled:opacity-60"
            >
              <RotateCcw size={20} />
              Continuar Andamento
            </button>
          )}
          <button 
            onClick={startSimulado}
            disabled={!clientReady}
            className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3.5 px-6 rounded-xl transition-all flex items-center justify-center gap-2 shadow-sm hover:shadow-md disabled:opacity-60"
          >
            <Play size={20} fill="currentColor" />
            {hasSavedState
              ? (hasCustomFilters ? "Novo Personalizado" : "Novo Simulado")
              : "Iniciar Simulado"}
          </button>
        </div>
      </div>
    );
  }

  if (state === "LOADING" || state === "SUBMITTING") {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p className="text-muted-foreground font-medium text-lg">
          {state === "LOADING" ? "Gerando cadernos e balanceando questões..." : "Corrigindo gabarito e calculando SRS..."}
        </p>
      </div>
    );
  }

  if (state === "OFFLINE_SUBMITTED") {
    return (
      <div className="max-w-2xl mx-auto py-16 px-6 text-center flex flex-col items-center gap-6 bg-card border border-border rounded-2xl shadow-1 mt-8 animate-in zoom-in-95 duration-200">
        <div className="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center">
          <CloudOff size={32} />
        </div>
        <div className="space-y-3">
          <h2 className="text-2xl font-bold text-foreground">Simulado Salvo Offline</h2>
          <p className="text-muted-foreground text-base">
            Todas as suas {Object.keys(answers).length} respostas foram salvas com segurança neste dispositivo.
          </p>
          <p className="text-sm text-muted-foreground leading-relaxed">
            A correção oficial, gabarito e atualização do seu algoritmo de repetição espaçada (FSRS) serão processados automaticamente assim que sua conexão com a internet for restabelecida.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 w-full max-w-md mt-2">
          <button
            onClick={handleManualSyncSimulado}
            disabled={isSyncingOffline}
            className="flex-1 bg-primary text-primary-foreground font-bold px-6 py-3.5 rounded-xl hover:bg-primary/90 disabled:opacity-50 transition-colors shadow-md text-sm flex items-center justify-center gap-2 cursor-pointer"
          >
            {isSyncingOffline ? (
              <>
                <RotateCcw className="animate-spin" size={18} />
                Sincronizando...
              </>
            ) : (
              <>
                <RotateCcw size={18} />
                Sincronizar e Ver Gabarito
              </>
            )}
          </button>
          <button
            onClick={() => {
              removeLearningSession("simulado");
              setHasSavedState(false);
              setState("START");
            }}
            className="flex-1 bg-muted hover:bg-muted/80 text-foreground font-semibold px-6 py-3.5 rounded-xl transition-colors text-sm cursor-pointer"
          >
            Concluir e Voltar ao Início
          </button>
        </div>
      </div>
    );
  }

  const currentQListItem = queue[currentIndex];
  const qDetail = detailsCache[currentQListItem?.id];
  const isReview = state === "RESULTS";
  const unansweredCount = queue.length - Object.keys(answers).length;

  return (
    <div className="flex flex-col lg:flex-row gap-6 w-full max-w-[1400px] mx-auto pb-12 lg:h-[calc(100vh-8rem)]">
      
      {/* Sidebar: Grid de Questões */}
      <div className="w-full lg:w-72 shrink-0 flex flex-col gap-4 order-1 lg:order-1 h-auto lg:h-full lg:sticky lg:top-4 z-10 bg-background/95 lg:bg-transparent backdrop-blur-md lg:backdrop-blur-none p-2 lg:p-0 rounded-xl shadow-sm lg:shadow-none mb-4 lg:mb-0 border lg:border-0 border-border">
        {/* Timer Box */}
        <div className="bg-card border border-border shadow-1 rounded-xl p-4 lg:p-5 flex flex-row lg:flex-col items-center justify-between lg:justify-center gap-2">
          {isReview ? (
            <>
              <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Nota Final</span>
              <div className="text-2xl lg:text-4xl font-black text-foreground">
                {Object.values(resultsMap).filter(r => r.is_correct).length} <span className="text-sm lg:text-lg text-muted-foreground">/ {queue.length}</span>
              </div>
              <div className="text-sm font-medium text-primary mt-1">
                {Math.round((Object.values(resultsMap).filter(r => r.is_correct).length / queue.length) * 100)}% de Acerto
              </div>
              {showResultsSummary && (
                <button 
                  onClick={() => setShowResultsSummary(false)}
                  className="mt-3 bg-primary text-primary-foreground font-bold px-4 py-2 rounded-lg text-sm w-full transition-colors hover:bg-primary/90"
                >
                  Revisar Questões
                </button>
              )}
            </>
          ) : (
            <>
              <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Clock size={16} /> Tempo
              </span>
              <div className={clsx(
                "text-2xl lg:text-3xl font-black font-mono",
                timeLeft < 1800 ? "text-destructive animate-pulse" : "text-foreground"
              )}>
                {formatTime(timeLeft)}
              </div>
            </>
          )}
        </div>

        {/* Grid Box */}
        <div className="bg-card border border-border shadow-1 rounded-xl flex flex-col h-[200px] lg:h-auto lg:flex-1 overflow-hidden">
          <div className="p-3 lg:p-4 border-b border-border bg-muted/30">
            <h3 className="font-bold text-foreground text-sm">Cartão Resposta</h3>
            {!isReview && (
              <p className="text-xs text-muted-foreground mt-1">
                {Object.keys(answers).length} respondidas, {queue.length - Object.keys(answers).length} em branco.
                {Object.values(flagged).filter(Boolean).length > 0 && (
                  <span className="text-warning ml-1">
                    · {Object.values(flagged).filter(Boolean).length} marcada(s)
                  </span>
                )}
              </p>
            )}
            {/* Filter buttons */}
            {!isReview && (
              <div className="flex gap-1.5 mt-2">
                {([
                  { key: 'all' as const, label: 'Todas' },
                  { key: 'unanswered' as const, label: 'Em branco' },
                  { key: 'flagged' as const, label: '🚩' },
                ] as const).map(f => (
                  <button
                    key={f.key}
                    onClick={() => setSidebarFilter(f.key)}
                    className={clsx(
                      "text-[10px] font-semibold px-2 py-1 rounded transition-colors",
                      sidebarFilter === f.key
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                    )}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex-1 overflow-hidden">
            <AutoSizer renderProp={({ height, width }) => {
                if (height === undefined || width === undefined) return null;
                const availableWidth = width;
                let columnCount = 5;
                if (availableWidth > 300) columnCount = 6;
                if (availableWidth > 400) columnCount = 8;
                if (availableWidth > 600) columnCount = 5;
                
                const gap = 8;
                const columnWidth = (availableWidth - gap * (columnCount - 1)) / columnCount;
                const rowHeight = columnWidth;
                const rowCount = Math.ceil(filteredIndices.length / columnCount);

                const Cell = ({ columnIndex, rowIndex, style, ariaAttributes }: CellComponentProps) => {
                  const index = rowIndex * columnCount + columnIndex;
                  if (index >= filteredIndices.length) return null;
                  
                  const idx = filteredIndices[index];
                  const q = queue[idx];
                  const isCurrent = idx === currentIndex;
                  const answeredLetter = answers[q.id];
                  const res = resultsMap[q.id];
                  const isFlagged = flagged[q.id];

                  let btnClass = "bg-muted text-muted-foreground hover:bg-muted/80";
                  
                  if (isReview) {
                    if (res?.is_correct) btnClass = "bg-success text-success-foreground font-bold";
                    else if (res && !res.is_correct) btnClass = "bg-destructive text-destructive-foreground font-bold";
                    else btnClass = "bg-card border border-dashed border-muted-foreground text-muted-foreground";
                  } else {
                    if (answeredLetter) btnClass = "bg-primary/20 text-primary font-bold";
                  }

                  if (isCurrent) {
                    btnClass += " ring-2 ring-foreground ring-offset-2 ring-offset-background";
                  }

                  const cellStyle = {
                    ...style,
                    left: Number(style.left) + gap / 2,
                    top: Number(style.top) + gap / 2,
                    width: Number(style.width) - gap,
                    height: Number(style.height) - gap
                  };

                  return (
                    <div {...ariaAttributes} style={cellStyle}>
                      <button
                        key={q.id}
                        onClick={() => navigateTo(idx)}
                        aria-label={`Ir para questão ${idx + 1}${answeredLetter ? `, resposta ${answeredLetter}` : ", em branco"}${isFlagged ? ", marcada para revisão" : ""}`}
                        aria-current={isCurrent ? "step" : undefined}
                        className={clsx(
                          "w-full h-full rounded flex flex-col items-center justify-center text-xs transition-all relative",
                          btnClass
                        )}
                      >
                        {isFlagged && (
                          <span className="absolute -top-0.5 -right-0.5 text-warning">
                            <Flag size={8} fill="currentColor" />
                          </span>
                        )}
                        <span className={clsx(!isReview && answeredLetter ? "text-[10px]" : "text-xs")}>{idx + 1}</span>
                        {!isReview && answeredLetter && <span className="text-[14px] leading-none">{answeredLetter}</span>}
                      </button>
                    </div>
                  );
                };

                return (
                  <FixedSizeGrid
                    columnCount={columnCount}
                    columnWidth={columnWidth + gap}
                    rowCount={rowCount}
                    rowHeight={rowHeight + gap}
                    cellComponent={Cell}
                    cellProps={{}}
                    style={{ overflowX: "hidden", height, width }}
                  />
                );
              }} />
          </div>
          
          {!isReview && (
            <div className="p-3 lg:p-4 border-t border-border bg-muted/30">
              <button 
                onClick={finishSimulado}
                className="w-full bg-foreground hover:bg-foreground/90 text-background font-bold py-2.5 lg:py-3 rounded-lg transition-colors text-sm lg:text-base"
              >
                Finalizar Simulado
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Area: Question View */}
      <div className="flex-1 flex flex-col order-2 lg:order-2 h-full">
        {showResultsSummary ? (
          <div className="bg-card border border-border shadow-1 rounded-xl p-8 flex-1 flex flex-col items-center justify-center animate-in zoom-in-95 duration-500 overflow-y-auto">
            <div className="w-24 h-24 bg-success/20 text-success rounded-full flex items-center justify-center mb-6">
              <span className="material-symbols-outlined text-5xl">trophy</span>
            </div>
            <h2 className="text-3xl font-black text-foreground mb-2">Simulado Finalizado!</h2>
            <p className="text-muted-foreground text-lg mb-8 text-center max-w-md">
              Você acertou <strong className="text-foreground">{Object.values(resultsMap).filter(r => r.is_correct).length}</strong> de <strong className="text-foreground">{queue.length}</strong> questões.
              O que representa um desempenho de <strong className="text-primary">{Math.round((Object.values(resultsMap).filter(r => r.is_correct).length / queue.length) * 100)}%</strong>.
            </p>

            <div className="w-full max-w-2xl bg-muted/30 rounded-xl p-6 border border-border mb-8">
              <h3 className="text-lg font-bold text-foreground mb-4">Desempenho por Área</h3>
              <div className="flex flex-col gap-4">
                {areaSummary.map(row => {
                  // Count corrects in this area
                  let correctInArea = 0;
                  queue.forEach(q => {
                    const area = q.area || "Sem área";
                    if (area === row.area && resultsMap[q.id]?.is_correct) {
                      correctInArea++;
                    }
                  });
                  const percentage = Math.round((correctInArea / row.total) * 100) || 0;
                  return (
                    <div key={row.area}>
                      <div className="flex justify-between text-sm font-medium mb-1">
                        <span>{row.area}</span>
                        <span className="text-muted-foreground">{correctInArea} / {row.total} ({percentage}%)</span>
                      </div>
                      <div className="w-full bg-border h-2 rounded-full overflow-hidden">
                        <div 
                          className={clsx(
                            "h-full rounded-full",
                            percentage >= 80 ? "bg-success" : percentage >= 60 ? "bg-warning" : "bg-destructive"
                          )}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {queue.filter(q => resultsMap[q.id] && !resultsMap[q.id].is_correct && answers[q.id]).length > 0 && (
              <div className="w-full max-w-2xl bg-purple-500/10 border border-purple-500/25 rounded-xl p-6 mb-8 text-left animate-in slide-in-from-bottom-2">
                <div className="flex items-center gap-2 text-purple-600 font-bold text-base mb-2">
                  <Sparkles size={20} />
                  Revisão Ativa & Flashcards das Erradas
                </div>
                <p className="text-sm text-foreground/80 leading-relaxed mb-4">
                  Você errou <strong className="text-foreground">{queue.filter(q => resultsMap[q.id] && !resultsMap[q.id].is_correct && answers[q.id]).length}</strong> questões neste simulado. Converta seus erros em flashcards com 1 clique para praticar repetição espaçada (FSRS).
                </p>

                {batchFlashcardsResult ? (
                  <div className="flex flex-col sm:flex-row items-center gap-3">
                    <div className="flex-1 bg-success/15 border border-success/30 text-success font-semibold px-4 py-2.5 rounded-xl text-sm flex items-center gap-2">
                      <CheckCircle2 size={18} /> {batchFlashcardsResult.count} flashcard(s) adicionado(s) à Revisão Ativa!
                    </div>
                    <Link
                      href="/revisao-ativa"
                      className="bg-purple-600 hover:bg-purple-700 text-white font-bold px-5 py-2.5 rounded-xl text-sm transition-all shadow-sm flex items-center gap-2 shrink-0"
                    >
                      <Sparkles size={16} /> Praticar Flashcards
                    </Link>
                  </div>
                ) : (
                  <button
                    onClick={handleGenerateAllSimuladoWrongFlashcards}
                    disabled={generatingBatchFlashcards}
                    className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer text-sm"
                  >
                    {generatingBatchFlashcards ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Gerando Flashcards dos seus Erros...
                      </>
                    ) : (
                      <>
                        <Sparkles size={18} />
                        Gerar Flashcards de Todas as Erradas ({queue.filter(q => resultsMap[q.id] && !resultsMap[q.id].is_correct && answers[q.id]).length})
                      </>
                    )}
                  </button>
                )}
              </div>
            )}

            <button 
              onClick={() => setShowResultsSummary(false)}
              className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 px-8 rounded-lg transition-all shadow-lg hover:-translate-y-0.5 flex items-center gap-2"
            >
              <BookOpen size={20} /> Iniciar Revisão Detalhada
            </button>
          </div>
        ) : detailError ? (
          <div className="bg-card border border-border shadow-1 rounded-xl p-8 flex-1 flex flex-col gap-4 items-center justify-center">
            <AlertCircle className="text-destructive w-10 h-10" />
            <p className="text-foreground font-semibold">Erro ao carregar a questão</p>
            <p className="text-muted-foreground text-sm text-center">Não foi possível carregar os detalhes desta questão. Verifique sua conexão.</p>
            <button 
              onClick={() => {
                if (queue[currentIndex]) {
                  loadDetail(queue[currentIndex].id);
                } else {
                  startSimulado();
                }
              }}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors font-medium text-sm mt-2"
            >
              <RotateCcw size={16} /> Tentar Novamente
            </button>
          </div>
        ) : loadingDetail || !qDetail ? (
          <div className="bg-card border border-border shadow-1 rounded-xl p-8 flex-1 flex flex-col gap-6 animate-pulse">
             <div className="h-6 w-32 bg-muted rounded" />
             <div className="h-40 bg-muted rounded-xl" />
             <div className="h-12 bg-muted rounded-xl" />
             <div className="h-12 bg-muted rounded-xl" />
             <div className="h-12 bg-muted rounded-xl" />
          </div>
        ) : (
          <div className="flex flex-col h-full gap-4">
            {/* Nav Header */}
            <div className="flex items-center justify-between bg-card border border-border shadow-sm rounded-xl p-3 shrink-0 relative overflow-hidden">
              <div 
                className="absolute bottom-0 left-0 h-1 bg-primary transition-all duration-300 ease-out" 
                style={{ width: `${(Object.keys(answers).length / queue.length) * 100}%` }} 
              />
              <button 
                onClick={() => navigateTo(currentIndex - 1)}
                disabled={currentIndex === 0}
                className="flex items-center gap-1 px-3 py-1.5 rounded hover:bg-muted disabled:opacity-50 text-sm font-medium z-10"
              >
                <ChevronLeft size={16} /> Anterior
              </button>
              <div className="flex items-center gap-2 z-10">
                <span className="font-bold text-foreground">
                  Questão {currentIndex + 1} de {queue.length}
                </span>
                {!isReview && (
                  <button
                    onClick={toggleFlag}
                    className={clsx(
                      "p-1.5 rounded transition-colors",
                      flagged[queue[currentIndex]?.id]
                        ? "text-warning bg-warning/10"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                    title={flagged[queue[currentIndex]?.id] ? "Desmarcar revisão" : "Marcar para revisar"}
                  >
                    <Flag size={16} fill={flagged[queue[currentIndex]?.id] ? "currentColor" : "none"} />
                  </button>
                )}
              </div>
              <button 
                onClick={() => navigateTo(currentIndex + 1)}
                disabled={currentIndex === queue.length - 1}
                className="flex items-center gap-1 px-3 py-1.5 rounded hover:bg-muted disabled:opacity-50 text-sm font-medium z-10"
              >
                Próxima <ChevronRight size={16} />
              </button>
            </div>

            <div className="hidden lg:flex items-center justify-center gap-2 px-3 py-1 bg-muted/50 rounded-full text-xs text-muted-foreground font-medium self-center">
              <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">A-E</kbd> ou <kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">1-5</kbd> Selecionar</span>
              <span className="w-1 h-1 rounded-full bg-border" />
              <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">F</kbd> Marcar p/ Revisão</span>
              <span className="w-1 h-1 rounded-full bg-border" />
              <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">➔</kbd> Navegar</span>
            </div>

            <div className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex-1 overflow-x-hidden overflow-y-auto custom-scrollbar relative">
              <AnimatePresence mode="wait">
                <motion.div 
                  key={currentIndex}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="w-full"
                >
                  {qDetail.technical_note && (
                <div className="bg-amber-500/15 border-2 border-amber-500/50 rounded-xl p-5 flex gap-4 text-foreground mb-6 shadow-sm">
                  <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={24} />
                  <div className="text-sm">
                    <p className="font-bold text-amber-600 dark:text-amber-500 mb-1 text-base uppercase tracking-wider">Atenção: Questão Histórica / Desatualizada</p>
                    <p className="leading-relaxed font-medium">{qDetail.technical_note}</p>
                  </div>
                </div>
              )}
              
              <ImageViewer 
                src={enlargedImage ? `/api/images/${enlargedImage}` : ""} 
                isOpen={!!enlargedImage} 
                onClose={() => setEnlargedImage(null)} 
              />
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-6">
                {qDetail.is_verified && (
                  <span className="bg-success/15 text-success border border-success/30 px-2 py-1 rounded flex items-center gap-1" title={qDetail.last_updated_at ? `Revisado em ${qDetail.last_updated_at}` : "Revisado por um médico"}>
                    <span className="material-symbols-outlined text-[14px]" data-icon="verified_user">verified_user</span> Revisado
                  </span>
                )}
                <span className="bg-muted px-2 py-1 rounded">{qDetail.institution_code} {qDetail.year}</span>
                <span className="bg-muted px-2 py-1 rounded">{qDetail.area}</span>
                <span className="bg-muted px-2 py-1 rounded">{qDetail.subtema}</span>
              </div>
              
              {/* Clinical Case */}
              {qDetail.clinical_case && (
                <div className="bg-muted/30 border-l-4 border-primary rounded-r-xl p-5 mb-6">
                  <h4 className="text-sm font-bold text-primary mb-3 uppercase tracking-wider">Caso Clínico</h4>
                  <div className="text-foreground text-lg leading-relaxed whitespace-pre-wrap">
                    {qDetail.clinical_case.stem}
                  </div>
                  {qDetail.clinical_case.images && qDetail.clinical_case.images.length > 0 && (
                    <div className="flex flex-col sm:flex-row flex-wrap gap-4 mt-4">
                      {qDetail.clinical_case.images.map((img, i) => (
                        <div 
                          key={i} 
                          className="relative group rounded-lg overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all sm:max-w-xs"
                          onClick={() => setEnlargedImage(img)}
                        >
                          <Image
                            src={`/api/images/${img}`} 
                            alt={`Imagem do Caso ${i+1}`} 
                            width={800}
                            height={600}
                            unoptimized
                            className="max-w-full h-auto object-cover hover:scale-[1.02] transition-transform duration-300" 
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              <div className="text-foreground text-lg leading-relaxed whitespace-pre-wrap mb-8">
                {qDetail.stem}
              </div>

              {qDetail.images && qDetail.images.length > 0 && (
                <div className="flex flex-col sm:flex-row flex-wrap gap-4 mb-8">
                  {qDetail.images.map((img, i) => (
                    <div 
                      key={i} 
                      className="relative group rounded-lg overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all sm:max-w-sm"
                      onClick={() => setEnlargedImage(img)}
                    >
                      <Image
                        src={`/api/images/${img}`} 
                        alt={`Imagem ${i+1}`} 
                        width={800}
                        height={600}
                        unoptimized
                        className="max-w-full h-auto object-cover hover:scale-[1.02] transition-transform duration-300" 
                      />
                    </div>
                  ))}
                </div>
              )}

              <div className="flex flex-col gap-3">
                {qDetail.alternatives.map((alt) => {
                  const isSelected = answers[qDetail.id] === alt.letter;
                  const res = resultsMap[qDetail.id];
                  
                  let altClass = "bg-card border-border hover:bg-muted/50 cursor-pointer";
                  
                  if (isReview) {
                    altClass = "bg-card border-border opacity-60 cursor-default"; // Default inactive
                    
                    if (res) {
                      if (alt.letter === res.correct_letter) {
                        altClass = "bg-success/20 border-success/50 cursor-default ring-2 ring-success";
                      } else if (isSelected && !res.is_correct) {
                        altClass = "bg-destructive/20 border-destructive/50 cursor-default";
                      }
                    } else if (isSelected) {
                      // Se não tivermos resultado por algum motivo de falha, marcamos a que ele clicou
                      altClass = "bg-primary/20 border-primary cursor-default";
                    }
                  } else {
                    if (isSelected) altClass = "bg-primary/10 border-primary cursor-pointer ring-1 ring-primary";
                  }

                  return (
                    <button
                      key={alt.letter}
                      onClick={() => !isReview && handleSelect(alt.letter)}
                      disabled={isReview}
                      aria-pressed={isSelected}
                      className={clsx(
                        "text-left p-4 rounded-xl border transition-all flex items-start gap-4 w-full",
                        altClass
                      )}
                    >
                      <div className={clsx(
                        "w-8 h-8 shrink-0 flex items-center justify-center rounded-lg font-bold text-sm border border-transparent",
                        isReview && alt.letter === res?.correct_letter ? "bg-success text-success-foreground" :
                        isReview && isSelected && !res?.is_correct ? "bg-destructive text-destructive-foreground" :
                        isSelected && !isReview ? "bg-primary text-primary-foreground" : 
                        "bg-muted text-muted-foreground"
                      )}>
                        {alt.letter}
                      </div>
                      <div className="pt-1.5 text-foreground leading-relaxed flex-1">
                        {alt.text}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Review Explanation */}
              {isReview && resultsMap[qDetail.id] && (
                <div className="mt-8 animate-in slide-in-from-bottom-4 fade-in duration-300">
                  <div className="rounded-xl border shadow-1 overflow-hidden bg-card">
                    <div className="p-6 md:p-8">
                      <h3 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                        <BookOpen size={20} className="text-primary" />
                        Comentário do Professor
                      </h3>
                      <div className="text-foreground text-lg leading-relaxed whitespace-pre-wrap">
                        {resultsMap[qDetail.id].explanation || "Nenhum comentário disponível para esta questão."}
                      </div>
                      
                      {qDetail.medical_references && (
                        <div className="mt-6 pt-5 border-t border-border">
                          <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">Referências e Diretrizes</h4>
                          <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap bg-muted/30 p-4 rounded-lg">
                            {qDetail.medical_references}
                          </div>
                        </div>
                      )}

                      {!questionFlashcardsMap[qDetail.id] && !draftFlashcardsMap[qDetail.id] && (
                        <div className="mt-6 pt-5 border-t border-border">
                          <button
                            onClick={() => handleGenerateSingleFlashcard(qDetail.id, answers[qDetail.id] || "")}
                            disabled={generatingSingleFlashcard === qDetail.id}
                            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-2.5 px-5 rounded-xl shadow-sm transition-all disabled:opacity-50 cursor-pointer text-sm"
                          >
                            {generatingSingleFlashcard === qDetail.id ? (
                              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                              <Sparkles size={16} />
                            )}
                            {generatingSingleFlashcard === qDetail.id ? "Gerando Flashcard com IA..." : "Criar Flashcard com IA"}
                          </button>
                        </div>
                      )}

                      {draftFlashcardsMap[qDetail.id] && (
                        <div className="mt-6 pt-5 border-t border-border">
                          <div className="bg-purple-500/10 border border-purple-500/25 rounded-2xl p-5 animate-in slide-in-from-bottom-2 text-left">
                            <div className="flex items-center gap-2 text-purple-600 font-bold text-sm mb-4">
                              <Sparkles size={16} /> Editar Flashcard
                            </div>
                            <div className="space-y-4">
                              <div>
                                <label className="text-xs font-bold text-muted-foreground uppercase block mb-1.5">Frente</label>
                                <textarea 
                                  value={draftFlashcardsMap[qDetail.id].front}
                                  onChange={(e) => setDraftFlashcardsMap(prev => ({ ...prev, [qDetail.id]: { ...prev[qDetail.id], front: e.target.value } }))}
                                  className="w-full bg-background border border-border rounded-lg p-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[100px]"
                                />
                              </div>
                              <div>
                                <label className="text-xs font-bold text-muted-foreground uppercase block mb-1.5">Verso</label>
                                <textarea 
                                  value={draftFlashcardsMap[qDetail.id].back}
                                  onChange={(e) => setDraftFlashcardsMap(prev => ({ ...prev, [qDetail.id]: { ...prev[qDetail.id], back: e.target.value } }))}
                                  className="w-full bg-background border border-border rounded-lg p-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[120px]"
                                />
                              </div>
                              <div className="flex justify-end gap-3 pt-2">
                                <button 
                                  onClick={() => setDraftFlashcardsMap(prev => { const next = {...prev}; delete next[qDetail.id]; return next; })}
                                  disabled={savingSingleFlashcard === qDetail.id}
                                  className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                                >
                                  Cancelar
                                </button>
                                <button 
                                  onClick={() => handleSaveSingleFlashcard(qDetail.id)}
                                  disabled={savingSingleFlashcard === qDetail.id}
                                  className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-5 rounded-lg transition-colors text-sm shadow-sm disabled:opacity-50"
                                >
                                  {savingSingleFlashcard === qDetail.id ? (
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                  ) : (
                                    <BookOpen size={16} />
                                  )}
                                  Salvar Flashcard
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {questionFlashcardsMap[qDetail.id] && (
                        <div className="mt-6 pt-5 border-t border-border">
                          <div className="bg-purple-500/10 border border-purple-500/25 rounded-2xl p-5 animate-in slide-in-from-bottom-2 text-left">
                            <div className="flex items-center justify-between gap-2 mb-3">
                              <div className="flex items-center gap-2 text-purple-600 font-bold text-sm">
                                <Sparkles size={16} /> Flashcard Salvo na Revisão Ativa!
                              </div>
                              <Link 
                                href="/revisao-ativa"
                                className="text-xs font-bold text-purple-600 hover:underline flex items-center gap-1"
                              >
                                Ir para Revisão Ativa →
                              </Link>
                            </div>
                            <div className="text-foreground text-sm space-y-2">
                              <div className="font-medium bg-background p-3.5 rounded-lg border border-border leading-relaxed whitespace-pre-line text-sm">
                                <span className="text-xs font-bold text-muted-foreground uppercase block mb-1.5">Frente:</span>
                                {questionFlashcardsMap[qDetail.id].front}
                              </div>
                              {questionFlashcardsMap[qDetail.id].back && (
                                <div className="text-muted-foreground bg-background p-3.5 rounded-lg border border-border leading-relaxed whitespace-pre-line text-sm">
                                  <span className="text-xs font-bold text-muted-foreground uppercase block mb-1.5">Verso:</span>
                                  {questionFlashcardsMap[qDetail.id].back}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Warning if missed */}
              {isReview && !answers[qDetail.id] && (
                <div className="mt-4 bg-destructive/10 text-destructive border border-destructive/20 rounded-lg p-4 flex items-center gap-3 w-full text-sm font-medium">
                  <AlertCircle size={20} className="shrink-0" />
                  Você não respondeu esta questão no simulado.
                </div>
              )}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        )}
      </div>

      {showAreaSummary && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="simulado-submit-title"
            className="bg-card border border-border shadow-lg rounded-xl p-6 max-w-md w-full flex flex-col gap-4 animate-in zoom-in-95 duration-200"
          >
            <h3 id="simulado-submit-title" className="font-bold text-lg text-foreground">Resumo por Área</h3>
            
            <div className="border border-border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Área</th>
                    <th className="text-center px-3 py-2 font-semibold text-muted-foreground">Resp.</th>
                    <th className="text-center px-3 py-2 font-semibold text-muted-foreground">Branco</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {areaSummary.map(row => (
                    <tr key={row.area}>
                      <td className="px-3 py-2 text-foreground font-medium">{row.area}</td>
                      <td className="px-3 py-2 text-center text-success font-semibold">{row.answered}</td>
                      <td className={clsx("px-3 py-2 text-center font-semibold", row.blank > 0 ? "text-destructive" : "text-muted-foreground")}>
                        {row.blank}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-muted/30 border-t border-border">
                  <tr>
                    <td className="px-3 py-2 font-bold text-foreground">Total</td>
                    <td className="px-3 py-2 text-center font-bold text-success">{Object.keys(answers).length}</td>
                    <td className={clsx("px-3 py-2 text-center font-bold", unansweredCount > 0 ? "text-destructive" : "text-muted-foreground")}>
                      {unansweredCount}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {unansweredCount > 0 && (
              <div className="bg-warning/10 text-warning border border-warning/20 rounded-lg p-3 flex items-start gap-2 text-sm">
                <AlertTriangle size={16} className="shrink-0 mt-0.5" />
                <span>Você ainda tem {unansweredCount} questão(ões) em branco.</span>
              </div>
            )}

            <div className="flex justify-end gap-3 mt-2">
              <button
                ref={dialogInitialFocusRef}
                onClick={() => setShowAreaSummary(false)}
                className="px-4 py-2 bg-muted text-muted-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors"
              >
                Voltar à Prova
              </button>
              <button
                onClick={() => {
                  setShowAreaSummary(false);
                  submitSimulado();
                }}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
              >
                Entregar Prova
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
