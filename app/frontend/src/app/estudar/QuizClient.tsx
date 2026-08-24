"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { QuestionMeta, QuestionListItem, QuestionDetail, AttemptResult, FlashcardGenerateResponse } from "@/types/api";
import { api, OfflineQueuedError } from "@/lib/api";
import { Play, Filter, Clock, CheckCircle2, XCircle, BookOpen, Heart, ArrowRight, Sparkles, BookOpenCheck, FileSignature, ArrowLeft, ImageOff, Maximize, Minimize, AlertTriangle, Search, X, CloudOff, RotateCcw } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { normalizeFlashcard } from "@/lib/normalizeFlashcard";

import { SubjectTreeSelector } from "@/components/SubjectTreeSelector";
import { ImageViewer } from "@/components/ImageViewer";
import { ExplanationViewer } from "@/components/ExplanationViewer";
import { useZenMode } from "@/hooks/useZenMode";
import Image from "next/image";
import {
  LEARNING_SESSION_VERSION,
  readLearningSession,
  removeLearningSession,
  writeLearningSession,
} from "@/lib/sessionState";

type QuizState = "FILTERS" | "LOADING_QUEUE" | "PLAYING" | "FINISHED";
type SessionAnswer = { letter: string; result?: AttemptResult | null; isOffline?: boolean };

interface SavedQuizState {
  version: number;
  state: "PLAYING" | "FINISHED";
  queue: QuestionListItem[];
  currentIndex: number;
  filters: Record<string, string | string[]>;
  currentDetail: QuestionDetail | null;
  sessionAnswers: Record<number, SessionAnswer>;
  selectedLetter: string | null;
  timeSpent: number;
  savedAt: number;
}

function isSavedQuizState(value: unknown): value is SavedQuizState {
  if (typeof value !== "object" || value === null) return false;
  const saved = value as Partial<SavedQuizState>;
  return saved.version === LEARNING_SESSION_VERSION &&
    (saved.state === "PLAYING" || saved.state === "FINISHED") &&
    Array.isArray(saved.queue) && saved.queue.length > 0 &&
    typeof saved.currentIndex === "number" && saved.currentIndex >= 0 &&
    saved.currentIndex < saved.queue.length &&
    typeof saved.filters === "object" && saved.filters !== null &&
    typeof saved.sessionAnswers === "object" && saved.sessionAnswers !== null;
}

const DEFAULT_META: QuestionMeta = {
  total_questions: 0,
  answered_questions: 0,
  institutions: [],
  years: [],
  areas: [],
  subtemas: [],
  sources: [],
  specialties: []
};

export function QuizClient({
  meta = DEFAULT_META,
  initialFilters = {}
}: {
  meta?: QuestionMeta;
  initialFilters?: Record<string, string>;
}) {
  const router = useRouter();
  const hasExplicitFilters = Object.keys(initialFilters).filter(k => k !== "resume").length > 0;
  const [state, setState] = useState<QuizState>(hasExplicitFilters ? "LOADING_QUEUE" : "FILTERS");
  const [filters, setFilters] = useState<Record<string, string | string[]>>({ limit: "50", ...initialFilters });
  const [localLimit, setLocalLimit] = useState<string>(
    typeof filters.limit === "string" ? filters.limit : "50"
  );
  const { isZenMode: zenMode, toggleZenMode } = useZenMode();
  const [subtemaSearch, setSubtemaSearch] = useState("");
  const [hasSavedState, setHasSavedState] = useState(false);
  const [savedSessionData, setSavedSessionData] = useState<SavedQuizState | null>(null);

  const [studyMode, setStudyMode] = useState<"TUTOR" | "SIMULADO">("TUTOR");
  const [dynamicMeta, setDynamicMeta] = useState<QuestionMeta>(meta || DEFAULT_META);
  const [isUpdatingMeta, setIsUpdatingMeta] = useState(false);
  
  const [queue, setQueue] = useState<QuestionListItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentDetail, setCurrentDetail] = useState<QuestionDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  
  const [sessionAnswers, setSessionAnswers] = useState<Record<number, SessionAnswer>>({});
  
  // Quiz State
  const [selectedLetter, setSelectedLetter] = useState<string | null>(null);
  const [attemptResult, setAttemptResult] = useState<AttemptResult | null>(null);
  const [isOfflineSaved, setIsOfflineSaved] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [generatingFlashcard, setGeneratingFlashcard] = useState(false);
  const [savingFlashcard, setSavingFlashcard] = useState(false);
  const [flashcardResult, setFlashcardResult] = useState<FlashcardGenerateResponse | null>(null);
  const [draftFlashcard, setDraftFlashcard] = useState<{front: string; back: string; context: string} | null>(null);
  const [generatingBatchFlashcards, setGeneratingBatchFlashcards] = useState(false);
  const [batchFlashcardsResult, setBatchFlashcardsResult] = useState<{ count: number } | null>(null);
  
  // Timer State
  const [timeSpent, setTimeSpent] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const timeSpentSnapshotRef = useRef(0);

  useEffect(() => {
    timeSpentSnapshotRef.current = timeSpent;
  }, [timeSpent]);
  
  // Image Modal
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);

  const detailsCacheRef = useRef<Record<number, QuestionDetail>>({});
  const prefetchingRef = useRef<Set<number>>(new Set());

  const [togglingFavorite, setTogglingFavorite] = useState(false);
  const detailRequestRef = useRef(0);
  const attemptLockRef = useRef(false);
  const reviewLockRef = useRef(false);
  const favoriteLockRef = useRef(false);

  const loadQuestionDetail = useCallback(async (id: number) => {
    const requestId = ++detailRequestRef.current;
    setDetailError(null);
    setAttemptResult(null);
    setSelectedLetter(null);
    setIsOfflineSaved(false);
    setFlashcardResult(null);
    setDraftFlashcard(null);
    setTimeSpent(0);

    // Se já estiver no cache, carrega instantaneamente sem tela de loading
    const cached = detailsCacheRef.current[id];
    if (cached) {
      setCurrentDetail(cached);
      setLoadingDetail(false);
      return;
    }

    setLoadingDetail(true);
    setCurrentDetail(null);
    try {
      const detail = await api.questions.getDetail(id);
      detailsCacheRef.current[id] = detail;
      if (detailRequestRef.current === requestId) {
        setCurrentDetail(detail);
      }
    } catch {
      if (detailRequestRef.current === requestId) {
        setDetailError("Não foi possível carregar esta questão. Verifique sua conexão e tente novamente.");
      }
    } finally {
      if (detailRequestRef.current === requestId) setLoadingDetail(false);
    }
  }, []);

  // Pré-carregamento em segundo plano das próximas questões
  useEffect(() => {
    if (state !== "PLAYING" || queue.length === 0) return;

    const nextIds = [
      queue[currentIndex + 1]?.id,
      queue[currentIndex + 2]?.id,
    ].filter((id): id is number => typeof id === "number" && !detailsCacheRef.current[id] && !prefetchingRef.current.has(id));

    if (nextIds.length === 0) return;

    for (const nextId of nextIds) {
      prefetchingRef.current.add(nextId);
      api.questions.getDetail(nextId)
        .then((detail) => {
          detailsCacheRef.current[nextId] = detail;
        })
        .catch(() => {
          // Ignora falhas de prefetch em segundo plano
        })
        .finally(() => {
          prefetchingRef.current.delete(nextId);
        });
    }
  }, [state, queue, currentIndex]);

  const loadQueue = useCallback(async (activeFilters: Record<string, string | string[]>) => {
    removeLearningSession("quiz");
    setHasSavedState(false);
    setSavedSessionData(null);
    if (typeof window !== "undefined") {
      sessionStorage.setItem("medquest_active_quiz", "1");
    }
    setState("LOADING_QUEUE");
    try {
      const qList = await api.questions.getList(activeFilters);
      if (qList.length > 0) {
        setQueue(qList);
        setCurrentIndex(0);
        setSessionAnswers({});
        setSelectedLetter(null);
        setAttemptResult(null);
        setState("PLAYING");
        loadQuestionDetail(qList[0].id);
      } else {
        if (typeof window !== "undefined") {
          sessionStorage.removeItem("medquest_active_quiz");
        }
        toast.error("Nenhuma questão encontrada com esses filtros.");
        setState("FILTERS");
      }
    } catch (e) {
      if (typeof window !== "undefined") {
        sessionStorage.removeItem("medquest_active_quiz");
      }
      const message = e instanceof Error ? e.message : "Erro desconhecido";
      toast.error(`Erro ao buscar questões: ${message}`);
      setState("FILTERS");
    }
  }, [loadQuestionDetail]);

  useEffect(() => {
    if (currentDetail && sessionAnswers[currentDetail.id]) {
      const ans = sessionAnswers[currentDetail.id];
      const timer = setTimeout(() => {
        setSelectedLetter(ans.letter);
        setAttemptResult(ans.result || null);
        setIsOfflineSaved(!!ans.isOffline);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [currentDetail, sessionAnswers]);

  useEffect(() => {
    const handleSyncSuccess = (e: Event) => {
      const customEvent = e as CustomEvent<{
        id: string;
        endpoint: string;
        method: string;
        data: unknown;
      }>;
      const detail = customEvent.detail;
      if (detail && detail.endpoint.includes("/api/questions/") && detail.endpoint.includes("/attempt")) {
        const attemptRes = detail.data as AttemptResult | null;
        if (attemptRes && typeof attemptRes.is_correct === "boolean") {
          const match = detail.endpoint.match(/\/api\/questions\/(\d+)\/attempt/);
          if (match && currentDetail && Number(match[1]) === currentDetail.id) {
            setAttemptResult(attemptRes);
            setIsOfflineSaved(false);
            setSessionAnswers(prev => ({
              ...prev,
              [currentDetail.id]: { letter: selectedLetter || attemptRes.correct_letter || "", result: attemptRes }
            }));
            toast.success("Resposta sincronizada com sucesso!");
          }
        }
      }
    };

    window.addEventListener("sync-item-success", handleSyncSuccess);
    return () => {
      window.removeEventListener("sync-item-success", handleSyncSuccess);
    };
  }, [currentDetail, selectedLetter]);

  const hasRestored = useRef(false);
  const [storageReady, setStorageReady] = useState(false);

  useEffect(() => {
    if (hasRestored.current) return;
    hasRestored.current = true;

    const saved = readLearningSession("quiz", isSavedQuizState);
    const isExplicitResume = initialFilters.resume === "true" || initialFilters.resume === "1";
    const isActiveInSession = typeof window !== "undefined" && sessionStorage.getItem("medquest_active_quiz") === "1";
    const filterKeys = Object.keys(initialFilters).filter(k => k !== "resume");

    if (saved && (isExplicitResume || isActiveInSession)) {
      setQueue(saved.queue);
      setCurrentIndex(saved.currentIndex);
      setFilters(saved.filters);
      setCurrentDetail(saved.currentDetail);
      setSessionAnswers(saved.sessionAnswers);
      setSelectedLetter(saved.selectedLetter);
      setTimeSpent(saved.timeSpent || 0);
      setState(saved.state);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("medquest_active_quiz", "1");
      }
      if (saved.currentDetail) {
        detailsCacheRef.current[saved.currentDetail.id] = saved.currentDetail;
      } else if (saved.queue[saved.currentIndex]) {
        loadQuestionDetail(saved.queue[saved.currentIndex].id);
      }
      toast.success("Sessão de estudo retomada.");
    } else if (saved && filterKeys.length === 0) {
      // Sessão salva existente: exibe banner na tela de filtros sem forçar entrada nas questões
      setHasSavedState(true);
      setSavedSessionData(saved);
      setState("FILTERS");
    } else if (filterKeys.length > 0) {
      loadQueue({ limit: "50", ...initialFilters });
    }
    setStorageReady(true);
  }, [initialFilters, loadQueue, loadQuestionDetail]);

  const resumeSavedQuiz = useCallback(() => {
    const saved = savedSessionData || readLearningSession("quiz", isSavedQuizState);
    if (saved) {
      setQueue(saved.queue);
      setCurrentIndex(saved.currentIndex);
      setFilters(saved.filters);
      setCurrentDetail(saved.currentDetail);
      setSessionAnswers(saved.sessionAnswers);
      setSelectedLetter(saved.selectedLetter);
      setTimeSpent(saved.timeSpent || 0);
      setState(saved.state);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("medquest_active_quiz", "1");
      }
      if (saved.currentDetail) {
        detailsCacheRef.current[saved.currentDetail.id] = saved.currentDetail;
      } else if (saved.queue[saved.currentIndex]) {
        loadQuestionDetail(saved.queue[saved.currentIndex].id);
      }
      setHasSavedState(false);
      toast.success("Sessão de estudo retomada.");
    }
  }, [savedSessionData, loadQuestionDetail]);

  const discardSavedQuiz = useCallback(() => {
    removeLearningSession("quiz");
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("medquest_active_quiz");
    }
    setHasSavedState(false);
    setSavedSessionData(null);
    toast("Sessão anterior descartada.", { icon: "🗑️" });
  }, []);

  const handleBackToFilters = useCallback(() => {
    removeLearningSession("quiz");
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("medquest_active_quiz");
      window.history.replaceState(null, "", window.location.pathname);
    }
    setQueue([]);
    setCurrentIndex(0);
    setCurrentDetail(null);
    setSelectedLetter(null);
    setAttemptResult(null);
    setSessionAnswers({});
    setTimeSpent(0);
    setHasSavedState(false);
    setSavedSessionData(null);
    setState("FILTERS");
  }, []);

  const handleNewSession = useCallback(() => {
    setBatchFlashcardsResult(null);
    handleBackToFilters();
  }, [handleBackToFilters]);

  const persistSession = useCallback((nextSelectedLetter = selectedLetter) => {
    if (!storageReady) return;
    if (state === "PLAYING" || state === "FINISHED") {
      writeLearningSession("quiz", {
        version: LEARNING_SESSION_VERSION,
        state,
        queue,
        currentIndex,
        filters,
        currentDetail,
        sessionAnswers,
        selectedLetter: nextSelectedLetter,
        timeSpent: timeSpentSnapshotRef.current,
        savedAt: Date.now(),
      } satisfies SavedQuizState);
    } else if (state === "FILTERS") {
      removeLearningSession("quiz");
    }
  }, [storageReady, state, queue, currentIndex, filters, currentDetail, sessionAnswers, selectedLetter]);

  useEffect(() => {
    persistSession();
  }, [persistSession]);

  const selectAlternative = useCallback((letter: string) => {
    if (attemptResult || submitting) return;
    // Persist synchronously so a reload immediately after selecting an answer
    // can still restore the in-progress session.
    persistSession(letter);
    setSelectedLetter(letter);
  }, [attemptResult, submitting, persistSession]);

  // Effect to fetch dynamic meta when filters change
  useEffect(() => {
    if (state !== "FILTERS") return;
    
    let isMounted = true;
    const fetchDynamicMeta = async () => {
      setIsUpdatingMeta(true);
      try {
        // Keep topic options stable while the user selects several of them.
        // Otherwise each selected subtema narrows the metadata response and
        // makes the remaining specialties disappear from the tree.
        const metaFilters = { ...filters };
        delete metaFilters.subtema;
        delete metaFilters.topic;
        const newMeta = await api.questions.getMeta(metaFilters);
        if (isMounted) setDynamicMeta(newMeta);
      } catch {
        console.error("Failed to load dynamic meta");
      } finally {
        if (isMounted) setIsUpdatingMeta(false);
      }
    };
    
    // Debounce to prevent spamming
    const timeout = setTimeout(fetchDynamicMeta, 300);
    return () => {
      isMounted = false;
      clearTimeout(timeout);
    };
  }, [filters, state]);

  // Timer Control
  useEffect(() => {
    if (state === "PLAYING" && currentDetail && !attemptResult) {
      timerRef.current = setInterval(() => {
        setTimeSpent(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [state, currentDetail, attemptResult]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Sanitize limit before submitting
    let finalLimit = "50";
    if (typeof filters.limit === "string" && filters.limit.trim() !== "") {
      const parsed = parseInt(filters.limit, 10);
      if (!isNaN(parsed)) {
        if (parsed < 1) finalLimit = "1";
        else if (parsed > 200) finalLimit = "200";
        else finalLimit = parsed.toString();
      }
    }
    const finalFilters = { ...filters, limit: finalLimit };

    if (studyMode === "SIMULADO") {
      const params = new URLSearchParams();
      for (const [key, value] of Object.entries(finalFilters)) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v));
        } else if (value !== undefined && value !== "") {
          params.append(key, value as string);
        }
      }
      router.push(`/simulado?${params.toString()}`);
    } else {
      loadQueue(finalFilters);
    }
  };

  const handleAttempt = useCallback(async () => {
    if (attemptLockRef.current || attemptResult || isOfflineSaved || submitting || !currentDetail || !selectedLetter) return;
    attemptLockRef.current = true;
    
    setSubmitting(true);
    if (timerRef.current) clearInterval(timerRef.current);

    try {
      const res = await api.questions.submitAttempt(currentDetail.id, selectedLetter, timeSpent * 1000, "defer");
      setAttemptResult(res);
      setIsOfflineSaved(false);
      setSessionAnswers(prev => ({
        ...prev,
        [currentDetail.id]: { letter: selectedLetter, result: res }
      }));

    } catch (err) {
      if (err instanceof OfflineQueuedError) {
        toast("Resposta salva neste dispositivo; será sincronizada quando a conexão voltar.", { icon: "💾" });
        setIsOfflineSaved(true);
        setSessionAnswers(prev => ({
          ...prev,
          [currentDetail.id]: { letter: selectedLetter, isOffline: true }
        }));
      } else {
        toast.error("Erro ao enviar resposta.");
      }
    } finally {
      attemptLockRef.current = false;
      setSubmitting(false);
    }
  }, [attemptResult, isOfflineSaved, submitting, currentDetail, selectedLetter, timeSpent]);

  const handleGenerateFlashcard = async () => {
    if (!currentDetail) return;
    setGeneratingFlashcard(true);
    setDraftFlashcard(null);
    try {
      const res = await api.flashcards.preview(currentDetail.id, selectedLetter || undefined);
      setDraftFlashcard({
        front: res.front,
        back: res.back,
        context: res.context
      });
    } catch {
      toast.error("Erro ao gerar prévia do flashcard.");
    } finally {
      setGeneratingFlashcard(false);
    }
  };

  const handleSaveFlashcard = async () => {
    if (!currentDetail || !draftFlashcard) return;
    setSavingFlashcard(true);
    try {
      const res = await api.flashcards.save(
        currentDetail.id, 
        draftFlashcard.front, 
        draftFlashcard.back, 
        draftFlashcard.context
      );
      const normalized = normalizeFlashcard({ ...res, stem: currentDetail.stem });
      setFlashcardResult(normalized);
      setDraftFlashcard(null);
      toast.success("Flashcard criado e inserido na sua Revisão Ativa!");
    } catch {
      toast.error("Erro ao salvar flashcard.");
    } finally {
      setSavingFlashcard(false);
    }
  };

  const handleGenerateAllWrongFlashcards = async () => {
    const wrongItems = Object.entries(sessionAnswers)
      .filter(([, ans]) => ans.result && !ans.result.is_correct)
      .map(([qid, ans]) => ({ question_id: Number(qid), wrong_letter: ans.letter }));

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

  const nextQuestion = useCallback(() => {
    if (currentIndex + 1 < queue.length) {
      setCurrentIndex(prev => prev + 1);
      loadQuestionDetail(queue[currentIndex + 1].id);
    } else {
      setState("FINISHED");
    }
  }, [currentIndex, queue, loadQuestionDetail]);

  const handleReviewFSRS = useCallback(async (conf: string) => {
    if (!currentDetail || reviewLockRef.current) return;
    reviewLockRef.current = true;
    try {
      await api.questions.reviewFSRS(currentDetail.id, conf);
    } catch {
      toast.error("Erro ao salvar revisão (FSRS).");
    } finally {
      reviewLockRef.current = false;
      nextQuestion();
    }
  }, [currentDetail, nextQuestion]);

  const prevQuestion = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
      loadQuestionDetail(queue[currentIndex - 1].id);
    }
  }, [currentIndex, queue, loadQuestionDetail]);

  const toggleFavorite = async () => {
    if (!currentDetail || togglingFavorite || favoriteLockRef.current) return;
    favoriteLockRef.current = true;
    setTogglingFavorite(true);
    const updated = { ...currentDetail, is_favorite: !currentDetail.is_favorite };
    setCurrentDetail(updated);
    detailsCacheRef.current[updated.id] = updated;
    try {
      await api.questions.toggleFavorite(currentDetail.id);
    } catch {
      setCurrentDetail(currentDetail);
      detailsCacheRef.current[currentDetail.id] = currentDetail;
    } finally {
      favoriteLockRef.current = false;
      setTogglingFavorite(false);
    }
  };

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      
      const isButton = tag === 'BUTTON';
      const target = e.target as HTMLButtonElement;
      
      if (isButton && !target.disabled && (e.key === "Enter" || e.key === " ")) {
        return;
      }

      if (state !== "PLAYING" || !currentDetail || loadingDetail) return;

      const key = e.key.toUpperCase();
      
      if (!attemptResult) {
        // Alternatives 1-5 or A-E
        const altIndexMap: Record<string, number> = { '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, 'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4 };
        if (key in altIndexMap) {
          const idx = altIndexMap[key];
          if (idx < currentDetail.alternatives.length) {
            selectAlternative(currentDetail.alternatives[idx].letter);
          }
        } else if (key === "ENTER" || key === " ") {
          if (selectedLetter && !submitting) {
            e.preventDefault();
            handleAttempt();
          }
        }
      } else {
        if (!attemptResult.next_review_date) {
          if (key === "1") handleReviewFSRS("chutei");
          else if (key === "2" || key === "ENTER" || key === " ") { e.preventDefault(); handleReviewFSRS("duvida"); }
          else if (key === "3") handleReviewFSRS("certeza");
        } else {
          if (key === "ENTER" || key === " " || key === "3" || key === "2" || key === "1") {
            e.preventDefault();
            nextQuestion();
          }
        }
      }

      // Free navigation with arrows (Requires Ctrl or Alt to prevent accidental jumps while scrolling)
      if (e.key === "ArrowLeft" && (e.ctrlKey || e.altKey)) {
        e.preventDefault();
        prevQuestion();
      } else if (e.key === "ArrowRight" && (e.ctrlKey || e.altKey)) {
        e.preventDefault();
        nextQuestion();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [state, currentDetail, loadingDetail, attemptResult, currentIndex, queue, selectedLetter, submitting, handleAttempt, handleReviewFSRS, nextQuestion, prevQuestion, selectAlternative]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (state === "FILTERS") {
    return (
      <div className="bg-card border border-border shadow-1 rounded-xl p-8 max-w-2xl mx-auto w-full">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 bg-primary/20 text-primary rounded-xl flex items-center justify-center shrink-0">
            <Filter size={24} />
          </div>
          <div>
            <h2 className="text-h2 font-bold text-foreground">Filtros de Estudo</h2>
            <p className="text-muted-foreground text-sm">Monte sua sessão de estudos escolhendo os filtros.</p>
          </div>
        </div>

        {hasSavedState && savedSessionData && (
          <div className="bg-primary/10 border border-primary/30 rounded-xl p-5 mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary text-primary-foreground flex items-center justify-center shrink-0 shadow-sm">
                <RotateCcw size={20} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-foreground">Sessão de Estudos em Andamento</h3>
                <p className="text-xs text-muted-foreground">
                  Você tem uma sessão salva com {savedSessionData.queue.length} questões (Questão {savedSessionData.currentIndex + 1} de {savedSessionData.queue.length}).
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                type="button"
                onClick={discardSavedQuiz}
                className="flex-1 sm:flex-initial px-3 py-2 text-xs font-semibold text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors cursor-pointer"
              >
                Descartar
              </button>
              <button
                type="button"
                onClick={resumeSavedQuiz}
                className="flex-1 sm:flex-initial px-4 py-2 text-xs font-bold bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-all shadow-sm flex items-center justify-center gap-1.5 cursor-pointer hover:scale-[1.02]"
              >
                <Play size={14} fill="currentColor" />
                Continuar Sessão
              </button>
            </div>
          </div>
        )}

        <form onSubmit={handleFilterSubmit} className="flex flex-col gap-6">
          <div className="bg-muted/30 border border-border p-4 rounded-lg flex flex-col sm:flex-row gap-4">
            <button 
              type="button"
              onClick={() => setStudyMode("TUTOR")}
              className={clsx(
                "flex-1 flex flex-col items-center justify-center gap-2 p-4 rounded-md border transition-all",
                studyMode === "TUTOR" ? "bg-primary/10 border-primary text-primary shadow-sm" : "bg-card border-border text-muted-foreground hover:bg-muted/50"
              )}
            >
              <BookOpenCheck size={24} />
              <span className="font-bold">Modo Tutor</span>
              <span className="text-xs text-center">Feedback imediato após cada resposta. Ideal para aprender.</span>
            </button>
            <button 
              type="button"
              onClick={() => setStudyMode("SIMULADO")}
              className={clsx(
                "flex-1 flex flex-col items-center justify-center gap-2 p-4 rounded-md border transition-all",
                studyMode === "SIMULADO" ? "bg-primary/10 border-primary text-primary shadow-sm" : "bg-card border-border text-muted-foreground hover:bg-muted/50"
              )}
            >
              <FileSignature size={24} />
              <span className="font-bold">Modo Simulado</span>
              <span className="text-xs text-center">Foco e resistência. Feedback e correção apenas no final.</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Status</label>
              <select 
                className="w-full bg-input border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={filters.status || ""}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <option className="bg-background text-foreground" value="">Todas</option>
                <option className="bg-background text-foreground" value="unanswered">Não respondidas</option>
                <option className="bg-background text-foreground" value="srs_due">Para Revisão (Repetição Espaçada)</option>
                <option className="bg-background text-foreground" value="wrong">Errei anteriormente</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Quantidade de Questões</label>
              <input 
                type="number"
                min="1"
                max="200"
                className="w-full bg-input border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={localLimit}
                onChange={(e) => {
                  const val = e.target.value;
                  setLocalLimit(val);
                  setFilters((prev) => ({ ...prev, limit: val }));
                }}
              />
              <p className="text-xs text-muted-foreground">Máximo de 200 questões por sessão.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground flex items-center justify-between">
                <span>Área</span>
                {isUpdatingMeta && <span className="text-xs text-muted-foreground animate-pulse">Atualizando...</span>}
              </label>
              <select 
                className="w-full bg-input border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={filters.area || ""}
                onChange={(e) => setFilters({ ...filters, area: e.target.value })}
              >
                <option className="bg-background text-foreground" value="">Todas as Áreas</option>
                {dynamicMeta.areas.map(a => (
                  <option className="bg-background text-foreground" key={a.area} value={a.area}>{a.area} ({a.n})</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground flex items-center justify-between">
                <span>Ano</span>
                {isUpdatingMeta && <span className="text-xs text-muted-foreground animate-pulse">Atualizando...</span>}
              </label>
              <select 
                className="w-full bg-input border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={filters.year || ""}
                onChange={(e) => setFilters({ ...filters, year: e.target.value })}
              >
                <option className="bg-background text-foreground" value="">Todos os Anos</option>
                {(dynamicMeta.years || []).map(y => (
                  <option className="bg-background text-foreground" key={y} value={String(y)}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-3 mt-6">
            <label className="text-sm font-medium text-foreground flex items-center justify-between">
              <span>Instituição / Banca</span>
              {isUpdatingMeta && <span className="text-xs text-muted-foreground animate-pulse">Atualizando...</span>}
            </label>

            {/* Quick-select interactive chips */}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => {
                  const newFilters = { ...filters };
                  delete newFilters.institution;
                  setFilters(newFilters);
                }}
                className={clsx(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border",
                  !filters.institution
                    ? "bg-primary text-primary-foreground border-primary shadow-sm"
                    : "bg-background border-border text-muted-foreground hover:bg-muted"
                )}
              >
                Todas ({dynamicMeta.total_questions})
              </button>
              {dynamicMeta.institutions.map(inst => {
                const isSelected = filters.institution === inst.institution_code;
                return (
                  <button
                    key={inst.institution_code}
                    type="button"
                    onClick={() => {
                      if (isSelected) {
                        const newFilters = { ...filters };
                        delete newFilters.institution;
                        setFilters(newFilters);
                      } else {
                        setFilters({ ...filters, institution: inst.institution_code });
                      }
                    }}
                    className={clsx(
                      "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border flex items-center gap-1.5",
                      isSelected
                        ? "bg-primary text-primary-foreground border-primary shadow-sm"
                        : "bg-background border-border text-foreground hover:bg-muted hover:border-border/80"
                    )}
                    title={inst.institution_label}
                  >
                    <span>{inst.institution_code}</span>
                    <span className={clsx(
                      "text-[10px] px-1.5 py-0.2 rounded-full font-normal",
                      isSelected ? "bg-primary-foreground/20 text-primary-foreground" : "bg-muted text-muted-foreground"
                    )}>
                      {inst.n}
                    </span>
                  </button>
                );
              })}
            </div>

            <select 
              className="w-full bg-input border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              value={filters.institution || ""}
              onChange={(e) => setFilters({ ...filters, institution: e.target.value })}
            >
              <option className="bg-background text-foreground" value="">Todas as Instituições ({dynamicMeta.total_questions})</option>
              {dynamicMeta.institutions.map(i => (
                <option className="bg-background text-foreground" key={i.institution_code} value={i.institution_code}>
                  {i.institution_code} • {i.institution_label || i.institution_code} ({i.n})
                </option>
              ))}
            </select>
          </div>
            
            <div className="space-y-2 md:col-span-2 relative">
              <label className="text-sm font-medium text-foreground flex items-center justify-between">
                <span>Subtemas (Múltipla Escolha)</span>
                {isUpdatingMeta && <span className="text-xs text-muted-foreground animate-pulse">Atualizando...</span>}
              </label>
              
              {/* Chips of selected subtemas */}
              {Array.isArray(filters.subtema) && filters.subtema.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {filters.subtema.map(sub => (
                    <span key={sub} className="bg-primary/10 text-primary border border-primary/20 px-3 py-1.5 rounded-full text-sm flex items-center gap-1.5 animate-in zoom-in-95 duration-200">
                      <span className="max-w-[200px] truncate">{sub}</span>
                      <button 
                        type="button" 
                        onClick={() => {
                          const current = (filters.subtema as string[]).filter(x => x !== sub);
                          const newFilters = { ...filters };
                          if (current.length > 0) newFilters.subtema = current;
                          else delete newFilters.subtema;
                          setFilters(newFilters);
                        }} 
                        className="hover:text-destructive hover:bg-destructive/10 rounded-full p-0.5 transition-colors"
                        aria-label="Remover"
                      >
                        <X size={14} />
                      </button>
                    </span>
                  ))}
                  <button 
                    type="button" 
                    onClick={() => {
                      const newFilters = { ...filters };
                      delete newFilters.subtema;
                      setFilters(newFilters);
                    }}
                    className="text-xs text-muted-foreground hover:text-foreground underline px-2 py-1.5"
                  >
                    Limpar todos
                  </button>
                </div>
              )}
              
              <div className="relative">
                <input
                  type="text"
                  placeholder="Buscar subtema para adicionar..."
                  value={subtemaSearch}
                  onChange={(e) => setSubtemaSearch(e.target.value)}
                  className="w-full bg-input border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary pl-9"
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                  <Search size={16} />
                </div>
              </div>
              
              {subtemaSearch.trim().length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-md shadow-lg max-h-60 overflow-y-auto">
                  {dynamicMeta.subtemas
                    ?.filter(s => s.subtema.toLowerCase().includes(subtemaSearch.toLowerCase()))
                    .filter(s => !(Array.isArray(filters.subtema) && filters.subtema.includes(s.subtema)))
                    .length === 0 && (
                      <div className="px-4 py-3 text-sm text-muted-foreground italic">
                        Nenhum subtema disponível encontrado.
                      </div>
                  )}
                  {dynamicMeta.subtemas
                    ?.filter(s => s.subtema.toLowerCase().includes(subtemaSearch.toLowerCase()))
                    .filter(s => !(Array.isArray(filters.subtema) && filters.subtema.includes(s.subtema)))
                    .slice(0, 50)
                    .map(s => (
                      <button 
                        key={s.subtema} 
                        type="button"
                        onClick={() => {
                          const current = Array.isArray(filters.subtema) ? [...filters.subtema] : (filters.subtema ? [filters.subtema as string] : []);
                          current.push(s.subtema);
                          setFilters({ ...filters, subtema: current });
                          setSubtemaSearch("");
                        }}
                        className="w-full text-left flex items-center justify-between px-4 py-2.5 hover:bg-muted text-sm border-b border-border/50 last:border-0"
                      >
                        <span className="truncate pr-4">{s.subtema}</span>
                        <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-0.5 rounded-full shrink-0">{s.n}</span>
                      </button>
                  ))}
                </div>
              )}
              
              <div className="mt-6 pt-4 border-t border-border">
                <label className="text-sm font-medium text-foreground mb-3 flex items-center justify-between">
                  <span>Subtópicos / Árvore de Temas</span>
                </label>
                <SubjectTreeSelector
                  selectedSubtemas={Array.isArray(filters.subtema) ? filters.subtema : (filters.subtema ? [filters.subtema] : [])}
                  onChange={(newSelection) => {
                    const newFilters = { ...filters };
                    if (newSelection.length > 0) newFilters.subtema = newSelection;
                    else delete newFilters.subtema;
                    setFilters(newFilters);
                  }}
                  availableSubtemas={dynamicMeta.subtemas}
                />
              </div>
            </div>

          <button 
            type="submit"
            className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3.5 rounded-md transition-colors flex items-center justify-center gap-2 w-full mt-2 shadow-sm"
          >
            <Play size={18} fill="currentColor" />
            {studyMode === "TUTOR" ? "Iniciar Sessão de Estudos" : "Iniciar Simulado Personalizado"}
          </button>
        </form>
      </div>
    );
  }

  if (state === "LOADING_QUEUE") {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p className="text-muted-foreground font-medium">Montando seu simulado...</p>
      </div>
    );
  }

  if (state === "FINISHED") {
    const totalAnswered = Object.keys(sessionAnswers).length;
    const correctCount = Object.values(sessionAnswers).filter(a => a.result?.is_correct).length;
    const wrongItems = Object.entries(sessionAnswers)
      .filter(([, ans]) => ans.result && !ans.result.is_correct)
      .map(([qid, ans]) => ({ question_id: Number(qid), wrong_letter: ans.letter }));
    const accuracy = totalAnswered > 0 ? Math.round((correctCount / totalAnswered) * 100) : 0;

    return (
      <div className="bg-card border border-border shadow-1 rounded-2xl p-8 md:p-10 max-w-2xl mx-auto w-full text-center flex flex-col items-center animate-in zoom-in-95 duration-300">
        <div className="w-20 h-20 bg-success/20 text-success rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 size={40} />
        </div>
        <h2 className="text-2xl md:text-3xl font-black text-foreground mb-3 tracking-tight">
          {studyMode === "TUTOR" ? "Sessão Concluída!" : "Simulado Concluído!"}
        </h2>
        <p className="text-muted-foreground text-base md:text-lg mb-6">
          Você respondeu <strong className="text-foreground">{totalAnswered}</strong> {totalAnswered === 1 ? 'questão' : 'questões'} com <strong className="text-primary">{accuracy}%</strong> de acerto ({correctCount} acertos).
        </p>

        {wrongItems.length > 0 && (
          <div className="w-full bg-purple-500/10 border border-purple-500/25 rounded-2xl p-6 mb-8 text-left animate-in slide-in-from-bottom-2">
            <div className="flex items-center gap-2.5 text-purple-600 font-bold text-base mb-2">
              <Sparkles size={20} />
              Revisão Ativa & Repetição Espaçada (FSRS)
            </div>
            <p className="text-sm text-foreground/80 leading-relaxed mb-5">
              Você errou <strong className="text-foreground">{wrongItems.length}</strong> {wrongItems.length === 1 ? 'questão' : 'questões'} nesta sessão. Transforme seus erros em flashcards com 1 clique para consolidar a memória e não esquecer mais.
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
                onClick={handleGenerateAllWrongFlashcards}
                disabled={generatingBatchFlashcards}
                className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                {generatingBatchFlashcards ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Gerando Flashcards dos seus Erros...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Gerar Flashcards de Todas as Erradas ({wrongItems.length})
                  </>
                )}
              </button>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-center gap-3 w-full">
          <button 
            onClick={handleNewSession}
            className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 px-8 rounded-xl transition-colors cursor-pointer text-sm shadow-md"
          >
            Nova Sessão de Estudos
          </button>
        </div>
      </div>
    );
  }

  // PLAYING STATE
  const q = currentDetail;

  return (
    <div className="max-w-4xl mx-auto w-full flex flex-col gap-6 pb-12 relative">
      {/* Fullscreen Image Modal */}
      {enlargedImage && (
        <ImageViewer 
          src={`/api/images/${enlargedImage}`} 
          isOpen={!!enlargedImage} 
          onClose={() => setEnlargedImage(null)} 
        />
      )}
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-card border border-border shadow-1 rounded-xl p-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={handleBackToFilters}
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            ← Voltar
          </button>
          <div className="h-6 w-px bg-border hidden sm:block" />
          <div className="text-sm font-semibold text-foreground">
            Questão {currentIndex + 1} de {queue.length}
          </div>
          <div className="hidden lg:flex items-center gap-2 ml-4 px-3 py-1 bg-muted/50 rounded-full text-xs text-muted-foreground font-medium">
            <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">A-E</kbd> ou <kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">1-5</kbd> Alternativas</span>
            <span className="w-1 h-1 rounded-full bg-border" />
              <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">Enter</kbd> Confirmar</span>
            <span className="w-1 h-1 rounded-full bg-border" />
            <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">➔</kbd> Próxima</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button 
            onClick={toggleZenMode}
            className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-muted/80 text-muted-foreground rounded-lg transition-colors border border-border text-xs font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 focus-visible:ring-offset-background"
            title={zenMode ? "Sair do Modo Zen" : "Entrar no Modo Zen (Foco Absoluto)"}
            aria-label={zenMode ? "Sair do Modo Zen" : "Entrar no Modo Zen"}
          >
            {zenMode ? (
              <>
                <Minimize size={14} /> Sair do Modo Zen
              </>
            ) : (
              <>
                <Maximize size={14} /> Modo Zen
              </>
            )}
          </button>
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground w-16">
            <Clock size={16} />
            <span className={clsx(timeSpent > 120 && !attemptResult && "text-warning")}>
              {formatTime(timeSpent)}
            </span>
          </div>
          {q && (
            <button 
              onClick={toggleFavorite}
              className={clsx(
                "p-2 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 focus-visible:ring-offset-background", 
                q.is_favorite ? "bg-destructive/10 text-destructive" : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
              )}
              title={q.is_favorite ? "Remover dos Favoritos" : "Favoritar"}
              aria-label={q.is_favorite ? "Remover dos Favoritos" : "Adicionar aos Favoritos"}
              aria-pressed={q.is_favorite}
            >
              <Heart size={18} fill={q.is_favorite ? "currentColor" : "none"} aria-hidden="true" />
            </button>
          )}
        </div>
      </div>

      {detailError ? (
        <div className="bg-card border border-border shadow-1 rounded-xl p-8 min-h-64 flex flex-col gap-4 items-center justify-center text-center" role="alert">
          <AlertTriangle className="text-destructive" size={36} />
          <p className="font-bold text-foreground">Erro ao carregar a questão</p>
          <p className="text-sm text-muted-foreground max-w-md">{detailError}</p>
          <button
            onClick={() => queue[currentIndex] && loadQuestionDetail(queue[currentIndex].id)}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors font-semibold"
          >
            <RotateCcw size={16} /> Tentar novamente
          </button>
        </div>
      ) : loadingDetail || !q ? (
        <div className="flex flex-col gap-6 animate-pulse">
          <div className="bg-card border border-border rounded-xl p-8 h-40" />
          <div className="flex flex-col gap-4">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-14 bg-card border border-border rounded-lg" />)}
          </div>
        </div>
      ) : (
        <div className={clsx("grid gap-6 items-start", q.clinical_case ? "lg:grid-cols-2" : "grid-cols-1")}>
          {q.clinical_case && (
            <div className="lg:sticky lg:top-24 h-fit bg-muted/30 border-l-4 border-primary shadow-sm rounded-r-xl rounded-l-md p-6 flex flex-col gap-6">
              <h4 className="text-sm font-bold text-primary uppercase tracking-wider flex items-center gap-2">
                <BookOpen size={18} /> Caso Clínico
              </h4>
              <div className="text-foreground text-lg leading-relaxed whitespace-pre-wrap">
                {q.clinical_case.stem}
              </div>
              {q.clinical_case.images && q.clinical_case.images.length > 0 && (
                <div className="flex flex-col sm:flex-row flex-wrap gap-4 mt-2">
                  {q.clinical_case.images.map((img, i) => (
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

          <div className="flex flex-col gap-6">
            {/* Question Stem */}
            <div className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex flex-col gap-6">
            {q.technical_note && (
              <div className="bg-amber-500/15 border-2 border-amber-500/50 rounded-xl p-5 flex gap-4 text-foreground mb-2 shadow-sm">
                <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={24} />
                <div className="text-sm">
                  <p className="font-bold text-amber-600 dark:text-amber-500 mb-1 text-base uppercase tracking-wider">Atenção: Questão Histórica / Desatualizada</p>
                  <p className="leading-relaxed font-medium">{q.technical_note}</p>
                </div>
              </div>
            )}
            <div className="flex items-start md:items-center justify-between flex-col md:flex-row gap-4">
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {q.is_verified && (
                  <span className="bg-success/15 text-success border border-success/30 px-2 py-1 rounded flex items-center gap-1" title={q.last_updated_at ? `Revisado em ${q.last_updated_at}` : "Revisado por um médico"}>
                    <span className="material-symbols-outlined text-[14px]" data-icon="verified_user">verified_user</span> Revisado
                  </span>
                )}
                <span className="bg-muted px-2 py-1 rounded">{q.institution_code} {q.year}</span>
                <span className="bg-muted px-2 py-1 rounded">{q.area}</span>
                <span className="bg-muted px-2 py-1 rounded">{q.subtema}</span>
              </div>
              
              <div className="flex items-center gap-3 bg-muted/30 px-3 py-1.5 rounded-lg border border-border">
                <button 
                  onClick={prevQuestion} 
                  disabled={currentIndex === 0 || loadingDetail}
                  className="p-1 hover:bg-background rounded transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                  title="Questão Anterior (Seta Esquerda)"
                  aria-label="Questão Anterior"
                >
                  <ArrowLeft size={18} aria-hidden="true" />
                </button>
                <span className="text-sm font-bold text-foreground min-w-[3rem] text-center">
                  {currentIndex + 1} / {queue.length}
                </span>
                <button 
                  onClick={nextQuestion} 
                  disabled={currentIndex === queue.length - 1 || loadingDetail}
                  className="p-1 hover:bg-background rounded transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                  title="Próxima Questão (Seta Direita)"
                  aria-label="Próxima Questão"
                >
                  <ArrowRight size={18} aria-hidden="true" />
                </button>
              </div>
            </div>
            

            <div className="text-foreground text-lg md:text-xl font-medium leading-relaxed whitespace-pre-wrap">
              {q.stem}
            </div>

            {q.images && q.images.length > 0 && (
              <div className="flex flex-col sm:flex-row flex-wrap gap-4 mt-6">
                {q.images.map((img, i) => (
                  <div 
                    key={i} 
                    className="relative group rounded-xl overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all sm:max-w-sm"
                    onClick={() => setEnlargedImage(img)}
                  >
                    <Image
                      src={`/api/images/${img}`} 
                      alt={`Imagem ${i+1}`} 
                      width={800}
                      height={600}
                      unoptimized
                      className="max-w-full h-auto object-cover hover:scale-[1.02] transition-transform duration-300" 
                      onError={(e) => { 
                        e.currentTarget.style.display = 'none'; 
                        if (e.currentTarget.nextElementSibling) {
                          (e.currentTarget.nextElementSibling as HTMLElement).style.display = 'flex';
                        }
                      }} 
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center pointer-events-none">
                      <Maximize size={24} className="text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-md" />
                    </div>
                    <div className="hidden flex-col items-center justify-center p-8 text-muted-foreground gap-2">
                      <ImageOff size={32} />
                      <span className="text-sm font-medium">Imagem indisponível</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Alternatives */}
          <div className="flex flex-col gap-3">
            {q.alternatives.map((alt) => {
              const isSelected = selectedLetter === alt.letter;
              const isCorrect = attemptResult?.correct_letter === alt.letter || (attemptResult && isSelected && attemptResult.is_correct);
              const isWrong = attemptResult && isSelected && !attemptResult.is_correct;
              
              let altClass = "bg-card border-border hover:bg-muted/50 hover:border-primary/30 cursor-pointer shadow-sm hover:shadow";
              if (isSelected && !attemptResult) altClass = "bg-primary/5 border-primary/50 cursor-pointer shadow ring-1 ring-primary/20";
              if (attemptResult) {
                if (isCorrect) altClass = "bg-success/10 border-success/50 shadow-sm cursor-default ring-1 ring-success/20";
                else if (isWrong) altClass = "bg-destructive/10 border-destructive/50 shadow-sm cursor-default ring-1 ring-destructive/20";
                else altClass = "bg-card border-border opacity-40 cursor-default";
              }

              return (
                <motion.button
                  whileTap={!attemptResult ? { scale: 0.98 } : {}}
                  animate={
                    attemptResult && isWrong ? { x: [-5, 5, -5, 5, 0], transition: { duration: 0.4 } } : 
                    attemptResult && isCorrect ? { scale: [1, 1.02, 1], transition: { duration: 0.4 } } : 
                    {}
                  }
                  key={alt.letter}
                  onClick={() => selectAlternative(alt.letter)}
                  disabled={!!attemptResult || submitting}
                  className={clsx(
                    "text-left p-4 rounded-xl border transition-all flex items-start gap-4 w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
                    altClass
                  )}
                  aria-pressed={isSelected}
                >
                  <div className={clsx(
                    "w-8 h-8 shrink-0 flex items-center justify-center rounded-lg font-bold text-sm",
                    isSelected && !attemptResult ? "bg-primary text-primary-foreground" : 
                    isCorrect ? "bg-success text-success-foreground" : 
                    isWrong ? "bg-destructive text-destructive-foreground" : 
                    "bg-muted text-muted-foreground"
                  )}>
                    {submitting && isSelected ? (
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    ) : (
                      alt.letter
                    )}
                  </div>
                  <div className="pt-1.5 text-foreground leading-relaxed flex-1">
                    {alt.text}
                  </div>
                </motion.button>
              );
            })}
          </div>

          {!attemptResult && !isOfflineSaved && selectedLetter && (
            <button
              onClick={handleAttempt}
              disabled={submitting}
              className="mt-2 w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3.5 rounded-xl transition-all flex items-center justify-center shadow-md animate-in slide-in-from-bottom-2 fade-in duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              {submitting ? (
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                "Confirmar Resposta"
              )}
            </button>
          )}

          {/* Offline Saved Banner */}
          {isOfflineSaved && (
            <div className="bg-primary/10 border border-primary/30 rounded-xl p-6 flex flex-col gap-4 text-foreground animate-in slide-in-from-bottom-2 duration-200 shadow-sm mt-2">
              <div className="flex items-center gap-3">
                <CloudOff className="text-primary shrink-0" size={24} />
                <div>
                  <p className="font-bold text-base">Resposta Salva Offline</p>
                  <p className="text-sm text-muted-foreground">Sua resposta foi salva neste dispositivo e será sincronizada automaticamente assim que a conexão for restabelecida.</p>
                </div>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-primary/20">
                <button
                  type="button"
                  onClick={async () => {
                    if (!navigator.onLine) {
                      toast("Ainda sem conexão com a internet. Sua resposta segue gravada localmente.", { icon: "💾" });
                      return;
                    }
                    try {
                      const { syncManager } = await import("@/lib/sync");
                      await syncManager.sync(true);
                      if (currentDetail && selectedLetter) {
                        const res = await api.questions.submitAttempt(currentDetail.id, selectedLetter, timeSpent * 1000, "defer");
                        setAttemptResult(res);
                        setIsOfflineSaved(false);
                        setSessionAnswers(prev => ({
                          ...prev,
                          [currentDetail.id]: { letter: selectedLetter, result: res }
                        }));
                        toast.success("Resposta sincronizada com sucesso!");
                      }
                    } catch (e) {
                      if (e instanceof OfflineQueuedError) {
                        toast("Sem conexão com a internet no momento.", { icon: "💾" });
                      } else {
                        toast.error("Erro ao sincronizar.");
                      }
                    }
                  }}
                  className="flex items-center gap-1.5 text-xs font-bold text-primary hover:text-primary/80 transition-colors bg-card border border-border px-3 py-2 rounded-lg"
                >
                  <RotateCcw size={14} /> Sincronizar Gabarito Agora
                </button>
                <button
                  onClick={nextQuestion}
                  disabled={currentIndex === queue.length - 1}
                  className="flex items-center gap-2 bg-primary text-primary-foreground font-bold px-4 py-2 rounded-lg transition-colors text-sm hover:bg-primary/90 disabled:opacity-50"
                >
                  Próxima Questão <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* Explanation Block */}
          {attemptResult && (
            <div className="animate-in slide-in-from-bottom-4 fade-in duration-300">
              <div className={clsx(
                "rounded-xl border shadow-1 overflow-hidden",
                attemptResult.is_correct ? "bg-success/5 border-success/20" : "bg-destructive/5 border-destructive/20"
              )}>
                <div className={clsx(
                  "p-4 border-b flex items-center justify-between",
                  attemptResult.is_correct ? "border-success/20 bg-success/10" : "border-destructive/20 bg-destructive/10"
                )}>
                  <div className="flex items-center gap-2 font-bold">
                    {attemptResult.is_correct ? (
                      <><CheckCircle2 className="text-success" /> <span className="text-success">Resposta Correta!</span></>
                    ) : (
                      <><XCircle className="text-destructive" /> <span className="text-destructive">Resposta Incorreta</span></>
                    )}
                  </div>
                  {!attemptResult.is_correct && attemptResult.next_review_date && (
                    <button
                      onClick={nextQuestion}
                      className="flex items-center gap-2 bg-background border border-border hover:bg-muted font-bold px-4 py-2 rounded-md transition-colors text-sm"
                    >
                      Próxima <ArrowRight size={16} />
                    </button>
                  )}
                </div>
                
                <div className="p-6 md:p-8">
                  <h3 className="text-lg font-bold text-foreground mb-5 flex items-center gap-2">
                    <BookOpen size={20} className="text-primary" />
                    Comentário do Professor
                  </h3>
                  <ExplanationViewer 
                    explanation={attemptResult.explanation} 
                    medicalReferences={currentDetail?.medical_references}
                    correctLetter={attemptResult.correct_letter}
                    questionId={currentDetail?.id}
                    userLetter={selectedLetter || attemptResult.correct_letter || undefined}
                  />

                  {currentDetail?.times_wrong && currentDetail.times_wrong > 0 ? (
                    <div className="mt-4 flex items-center gap-2 text-sm text-destructive font-semibold bg-destructive/10 px-3 py-1.5 rounded-full w-fit">
                      Você já errou esta questão {currentDetail.times_wrong} {currentDetail.times_wrong === 1 ? 'vez' : 'vezes'} no passado.
                    </div>
                  ) : null}
                  
                  {!flashcardResult && !draftFlashcard && (
                    <div className="mt-6">
                      <button 
                        onClick={handleGenerateFlashcard}
                        disabled={generatingFlashcard}
                        className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-2.5 px-5 rounded-xl shadow-sm transition-all disabled:opacity-50 cursor-pointer text-sm"
                      >
                        {generatingFlashcard ? (
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                          <Sparkles size={16} />
                        )}
                        {generatingFlashcard ? "Gerando Flashcard com IA..." : "Criar Flashcard com IA"}
                      </button>
                    </div>
                  )}

                  {draftFlashcard && (
                    <div className="mt-6 bg-purple-500/10 border border-purple-500/25 rounded-2xl p-5 animate-in slide-in-from-bottom-2">
                      <div className="flex items-center gap-2 text-purple-600 font-bold text-sm mb-4">
                        <Sparkles size={16} /> Editar Flashcard
                      </div>
                      <div className="space-y-4">
                        <div>
                          <label className="text-xs font-bold text-muted-foreground uppercase block mb-1.5">Frente</label>
                          <textarea 
                            value={draftFlashcard.front}
                            onChange={(e) => setDraftFlashcard({ ...draftFlashcard, front: e.target.value })}
                            className="w-full bg-background border border-border rounded-lg p-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[100px]"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-bold text-muted-foreground uppercase block mb-1.5">Verso</label>
                          <textarea 
                            value={draftFlashcard.back}
                            onChange={(e) => setDraftFlashcard({ ...draftFlashcard, back: e.target.value })}
                            className="w-full bg-background border border-border rounded-lg p-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[120px]"
                          />
                        </div>
                        <div className="flex justify-end gap-3 pt-2">
                          <button 
                            onClick={() => setDraftFlashcard(null)}
                            disabled={savingFlashcard}
                            className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                          >
                            Cancelar
                          </button>
                          <button 
                            onClick={handleSaveFlashcard}
                            disabled={savingFlashcard}
                            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-5 rounded-lg transition-colors text-sm shadow-sm disabled:opacity-50"
                          >
                            {savingFlashcard ? (
                              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                              <BookOpen size={16} />
                            )}
                            Salvar Flashcard
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {flashcardResult && (
                    <div className="mt-6 bg-purple-500/10 border border-purple-500/25 rounded-2xl p-5 animate-in slide-in-from-bottom-2">
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
                          {flashcardResult.front}
                        </div>
                        {flashcardResult.back && (
                          <div className="text-muted-foreground bg-background p-3.5 rounded-lg border border-border leading-relaxed whitespace-pre-line text-sm">
                            <span className="text-xs font-bold text-muted-foreground uppercase block mb-1.5">Verso:</span>
                            {flashcardResult.back}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {attemptResult.next_review_date ? (
                    <div className="mt-8 pt-4 border-t border-border flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <Clock size={16} />
                      Próxima revisão agendada para: {new Date(attemptResult.next_review_date).toLocaleDateString('pt-BR')}
                    </div>
                  ) : (
                    <div className="mt-8 pt-4 border-t border-border flex flex-col gap-4">
                      <span className="text-sm font-bold text-foreground">
                        {attemptResult.is_correct 
                          ? "Como foi lembrar dessa resposta? (FSRS)" 
                          : "Qual era o seu grau de certeza antes de ver o resultado? (FSRS)"}
                      </span>
                      <div className="flex flex-col sm:flex-row gap-3">
                        {attemptResult.is_correct ? (
                          <>
                            <button title="O algoritmo agendará a revisão desta questão para um intervalo curto (geralmente no dia seguinte) já que você não dominava o conceito original." onClick={() => handleReviewFSRS("chutei")} className="flex-1 bg-destructive/10 text-destructive hover:bg-destructive/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1">
                              <span>🔴 Acertei no Chute</span>
                              <span className="text-[10px] font-normal opacity-80">Volta amanhã (Difícil) • Atalho: 1</span>
                            </button>
                            <button title="O algoritmo agendará a revisão com um multiplicador moderado de dias, reforçando a memória sem sobrecarregar sua fila." onClick={() => handleReviewFSRS("duvida")} className="flex-1 bg-warning/10 text-warning hover:bg-warning/20 font-bold py-3 rounded-lg transition-colors text-sm border-2 border-warning/50 shadow-sm flex flex-col items-center justify-center gap-1">
                              <span>🟡 Pensei um Pouco</span>
                              <span className="text-[10px] font-normal opacity-80">Bom tempo • Atalho: 2 / Enter</span>
                            </button>
                            <button title="O algoritmo entenderá que você domina este assunto e agendará a revisão para o mais longe possível (maior estabilidade de memória)." onClick={() => handleReviewFSRS("certeza")} className="flex-1 bg-success/10 text-success hover:bg-success/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1">
                              <span>🟢 Tinha Certeza</span>
                              <span className="text-[10px] font-normal opacity-80">Revisa mais tarde (Fácil) • Atalho: 3</span>
                            </button>
                          </>
                        ) : (
                          <>
                            <button title="Você não sabia a resposta e foi pego de surpresa. A revisão ocorrerá o mais breve possível (amanhã)." onClick={() => handleReviewFSRS("chutei")} className="flex-1 bg-destructive/10 text-destructive hover:bg-destructive/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1">
                              <span>🔴 Errei no Chute</span>
                              <span className="text-[10px] font-normal opacity-80">Volta amanhã • Atalho: 1</span>
                            </button>
                            <button title="O algoritmo entenderá que você cometeu um erro que exige reforço imediato e agendará a revisão mais próxima para consertar a falha de memória." onClick={() => handleReviewFSRS("duvida")} className="flex-1 bg-warning/10 text-warning hover:bg-warning/20 font-bold py-3 rounded-lg transition-colors text-sm border-2 border-warning/50 shadow-sm flex flex-col items-center justify-center gap-1">
                              <span>🟡 Fiquei em Dúvida</span>
                              <span className="text-[10px] font-normal opacity-80">Bom tempo • Atalho: 2 / Enter</span>
                            </button>
                            <button title="Você sentiu firmeza, mas se confundiu numa 'pegadinha'. O algoritmo agendará a revisão com certa urgência, mas espaçada o suficiente para testar se a confusão persiste." onClick={() => handleReviewFSRS("certeza")} className="flex-1 bg-success/10 text-success hover:bg-success/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1">
                              <span>🟢 Errei com Certeza</span>
                              <span className="text-[10px] font-normal opacity-80">Preciso fixar • Atalho: 3</span>
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          </div>
        </div>
      )}
    </div>
  );
}
