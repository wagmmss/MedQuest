"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { QuestionMeta, QuestionListItem, QuestionDetail, AttemptResult, FlashcardGenerateResponse } from "@/types/api";
import { api, OfflineQueuedError } from "@/lib/api";
import { Play, Filter, Clock, CheckCircle2, XCircle, BookOpen, Heart, ArrowRight, Sparkles, BookOpenCheck, FileSignature, ArrowLeft, ImageOff, Maximize, Minimize, AlertTriangle, Search, X, CloudOff, RotateCcw, Brain, SlidersHorizontal, RefreshCw, Pencil, Stethoscope } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { useUser } from "@clerk/nextjs";
import { normalizeFlashcard } from "@/lib/normalizeFlashcard";

import { SubjectTreeSelector } from "@/components/SubjectTreeSelector";
import { ImageViewer } from "@/components/ImageViewer";
import { ExplanationViewer } from "@/components/ExplanationViewer";
import { QuestionClassificationModal } from "@/components/QuestionClassificationModal";
import { FormattedContent, normalizeImageSrc, filterExtraImages } from "@/components/FormattedContent";
import { useZenMode } from "@/hooks/useZenMode";
import { QuizTimer, QuizTimerHandle } from "@/components/QuizTimer";
import Image from "next/image";
import { QuizFilters } from "./components/QuizFilters";
import {
  LEARNING_SESSION_VERSION,
  readLearningSession,
  removeLearningSession,
  writeLearningSession,

} from "@/lib/sessionState";
import { useQuizKeyboard } from "./hooks/useQuizKeyboard";

export type SessionAnswer = { 
  letter: string; 
  result?: AttemptResult | null; 
  isOffline?: boolean; 
  writtenAnswer?: string; 
  isDiscursive?: boolean; 
};

type QuizState = "FILTERS" | "LOADING_QUEUE" | "PLAYING" | "FINISHED";

function resolveImageUrl(img: string | null | undefined): string {
  return normalizeImageSrc(img);
}

export interface SavedQuizState {
  version: number;
  state: "PLAYING" | "FINISHED";
  queue: QuestionListItem[];
  currentIndex: number;
  filters: Record<string, string | string[]>;
  currentDetail: QuestionDetail | null;
  sessionAnswers: Record<number, SessionAnswer>;
  selectedLetter: string | null;
  userWrittenAnswer?: string;
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
  const { user } = useUser();
  const isCurator = user?.primaryEmailAddress?.emailAddress?.toLowerCase() === "moraes.wagg@gmail.com";
  const [isClassificationModalOpen, setIsClassificationModalOpen] = useState(false);
  const hasExplicitFilters = Object.keys(initialFilters).filter(k => k !== "resume").length > 0;
  const [state, setState] = useState<QuizState>(hasExplicitFilters ? "LOADING_QUEUE" : "FILTERS");
  const [filters, setFilters] = useState<Record<string, string | string[]>>({ limit: "50", ...initialFilters });
  const [localLimit, setLocalLimit] = useState<string>(
    typeof filters.limit === "string" ? filters.limit : "50"
  );
  const { isZenMode: zenMode, toggleZenMode } = useZenMode();
  const [subtemaSearch, setSubtemaSearch] = useState("");
  const [showCustomSession, setShowCustomSession] = useState(false);
  const [showTopicTree, setShowTopicTree] = useState(false);
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
  const [userWrittenAnswer, setUserWrittenAnswer] = useState<string>("");
  const [attemptResult, setAttemptResult] = useState<AttemptResult | null>(null);
  const [isOfflineSaved, setIsOfflineSaved] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [generatingFlashcard, setGeneratingFlashcard] = useState(false);
  const [savingFlashcard, setSavingFlashcard] = useState(false);
  const [flashcardResult, setFlashcardResult] = useState<FlashcardGenerateResponse | null>(null);
  const [draftFlashcard, setDraftFlashcard] = useState<{front: string; back: string; context: string} | null>(null);
  const [generatingBatchFlashcards, setGeneratingBatchFlashcards] = useState(false);
  const [batchFlashcardsResult, setBatchFlashcardsResult] = useState<{ count: number } | null>(null);
  const [preceptorResponse, setPreceptorResponse] = useState<{ answer: string; model: string; source: string } | null>(null);
  const [askingPreceptor, setAskingPreceptor] = useState(false);
  const [preceptorInput, setPreceptorInput] = useState("");
  
  // Timer State
  const quizTimerRef = useRef<QuizTimerHandle>(null);
  const [initialTime, setInitialTime] = useState(0);

  // Expose current time without causing re-renders
  const getCurrentTime = () => quizTimerRef.current?.getTime() ?? initialTime;
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
    setUserWrittenAnswer("");
    setIsOfflineSaved(false);
    setFlashcardResult(null);
    setDraftFlashcard(null);
    setPreceptorResponse(null);
    setPreceptorInput("");
    setInitialTime(0);

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
    } catch (err) {
      console.error(`[QUIZ] Erro ao carregar questão ${id}:`, err);
      if (detailRequestRef.current === requestId) {
        const msg = err instanceof Error ? err.message : "Verifique sua conexão";
        setDetailError(`Não foi possível carregar esta questão (${msg}). Clique abaixo para tentar novamente.`);
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
    setFilters(activeFilters);
    if (typeof activeFilters.limit === "string") setLocalLimit(activeFilters.limit);
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

  // Salvaguarda: garante que, se estiver no estado PLAYING sem questão carregada ou em erro, carrega a questão atual
  useEffect(() => {
    if (state === "PLAYING" && !currentDetail && !loadingDetail && !detailError && queue[currentIndex]) {
      loadQuestionDetail(queue[currentIndex].id);
    }
  }, [state, currentDetail, loadingDetail, detailError, queue, currentIndex, loadQuestionDetail]);

  useEffect(() => {
    if (currentDetail && sessionAnswers[currentDetail.id]) {
      const ans = sessionAnswers[currentDetail.id];
      const timer = setTimeout(() => {
        setSelectedLetter(ans.letter);
        setAttemptResult(ans.result || null);
        setIsOfflineSaved(!!ans.isOffline);
        setUserWrittenAnswer(ans.writtenAnswer || "");
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
              [currentDetail.id]: { letter: selectedLetter || attemptRes.correct_letter || "", result: attemptRes, writtenAnswer: userWrittenAnswer }
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
  }, [currentDetail, selectedLetter, userWrittenAnswer]);

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
      setTimeout(() => {
        setQueue(saved.queue);
        setCurrentIndex(saved.currentIndex);
        setFilters(saved.filters);
        setSessionAnswers(saved.sessionAnswers);
        setSelectedLetter(saved.selectedLetter);
        setUserWrittenAnswer(saved.userWrittenAnswer || "");
        setInitialTime(saved.timeSpent || 0);
        setState(saved.state);
        if (typeof window !== "undefined") {
          sessionStorage.setItem("medquest_active_quiz", "1");
        }
        const targetQ = saved.queue[saved.currentIndex];
        if (targetQ && saved.currentDetail && saved.currentDetail.id === targetQ.id) {
          setCurrentDetail(saved.currentDetail);
          detailsCacheRef.current[saved.currentDetail.id] = saved.currentDetail;
        } else if (targetQ) {
          setCurrentDetail(null);
          loadQuestionDetail(targetQ.id);
        }
        toast.success("Sessão de estudo retomada.");
        setStorageReady(true);
      }, 0);
    } else if (saved && filterKeys.length === 0) {
      setTimeout(() => {
        // Sessão salva existente: exibe banner na tela de filtros sem forçar entrada nas questões
        setHasSavedState(true);
        setSavedSessionData(saved);
        setState("FILTERS");
        setStorageReady(true);
      }, 0);
    } else if (filterKeys.length > 0) {
      setTimeout(() => {
        loadQueue({ limit: "50", ...initialFilters });
        setStorageReady(true);
      }, 0);
    } else {
      setTimeout(() => {
        setStorageReady(true);
      }, 0);
    }
  }, [initialFilters, loadQueue, loadQuestionDetail]);

  const resumeSavedQuiz = useCallback(() => {
    const saved = savedSessionData || readLearningSession("quiz", isSavedQuizState);
    if (saved) {
      setQueue(saved.queue);
      setCurrentIndex(saved.currentIndex);
      setFilters(saved.filters);
      setSessionAnswers(saved.sessionAnswers);
      setSelectedLetter(saved.selectedLetter);
      setUserWrittenAnswer(saved.userWrittenAnswer || "");
      setInitialTime(saved.timeSpent || 0);
      setState(saved.state);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("medquest_active_quiz", "1");
      }
      const targetQ = saved.queue[saved.currentIndex];
      if (targetQ && saved.currentDetail && saved.currentDetail.id === targetQ.id) {
        setCurrentDetail(saved.currentDetail);
        detailsCacheRef.current[saved.currentDetail.id] = saved.currentDetail;
      } else if (targetQ) {
        setCurrentDetail(null);
        loadQuestionDetail(targetQ.id);
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
    setUserWrittenAnswer("");
    setAttemptResult(null);
    setSessionAnswers({});
    setInitialTime(0);
    setFilters({ limit: "50" });
    setLocalLimit("50");
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
        userWrittenAnswer,
        timeSpent: getCurrentTime(),
        savedAt: Date.now(),
      } satisfies SavedQuizState);
    } else if (state === "FILTERS" && !hasSavedState) {
      removeLearningSession("quiz");
    }
  }, [storageReady, state, queue, currentIndex, filters, currentDetail, sessionAnswers, selectedLetter, userWrittenAnswer, hasSavedState]);

  useEffect(() => {
    persistSession();
  }, [persistSession]);

  // Persist session before unmounting to prevent losing progress if user navigates away
  const stateRef = useRef({ state, queue, currentIndex, filters, currentDetail, sessionAnswers, selectedLetter, userWrittenAnswer, storageReady });
  useEffect(() => {
    stateRef.current = { state, queue, currentIndex, filters, currentDetail, sessionAnswers, selectedLetter, userWrittenAnswer, storageReady };
  }, [state, queue, currentIndex, filters, currentDetail, sessionAnswers, selectedLetter, userWrittenAnswer, storageReady]);

  useEffect(() => {
    return () => {
      const s = stateRef.current;
      if (s.storageReady && (s.state === "PLAYING" || s.state === "FINISHED")) {
        writeLearningSession("quiz", {
          version: LEARNING_SESSION_VERSION,
          state: s.state,
          queue: s.queue,
          currentIndex: s.currentIndex,
          filters: s.filters,
          currentDetail: s.currentDetail,
          sessionAnswers: s.sessionAnswers,
          selectedLetter: s.selectedLetter,
          userWrittenAnswer: s.userWrittenAnswer,
          timeSpent: getCurrentTime(),
          savedAt: Date.now(),
        } satisfies SavedQuizState);
      }
    };
  }, []);

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



  const updateUrlWithFilters = (finalFilters: Record<string, string | string[]>) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(finalFilters)) {
      if (Array.isArray(value)) {
        value.forEach(v => params.append(key, v));
      } else if (value !== undefined && value !== "") {
        params.append(key, value as string);
      }
    }
    window.history.replaceState(null, "", `/estudar?${params.toString()}`);
  };

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
      updateUrlWithFilters(finalFilters);
      loadQueue(finalFilters);
    }
  };

  const startRecommendedSession = useCallback((kind: "adaptive" | "review") => {
    const limit = kind === "review" ? "20" : "30";
    setStudyMode("TUTOR");
    const activeFilters = { limit, ...(kind === "adaptive" ? { mode: "adaptive" } : { status: "srs_due" }) };
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(activeFilters)) {
      params.append(key, value as string);
    }
    window.history.replaceState(null, "", `/estudar?${params.toString()}`);
    loadQueue(activeFilters);
  }, [loadQueue]);

  const handleAttempt = useCallback(async () => {
    if (attemptLockRef.current || attemptResult || isOfflineSaved || submitting || !currentDetail || !selectedLetter) return;
    attemptLockRef.current = true;
    
    setSubmitting(true);

    try {
      const res = await api.questions.submitAttempt(currentDetail.id, selectedLetter, getCurrentTime() * 1000, "defer");
      setAttemptResult(res);
      setIsOfflineSaved(false);
      setSessionAnswers(prev => ({
        ...prev,
        [currentDetail.id]: { letter: selectedLetter, result: res, writtenAnswer: userWrittenAnswer }
      }));

    } catch (err) {
      if (err instanceof OfflineQueuedError) {
        toast("Resposta salva neste dispositivo; será sincronizada quando a conexão voltar.", { icon: "💾" });
        setIsOfflineSaved(true);
        setSessionAnswers(prev => ({
          ...prev,
          [currentDetail.id]: { letter: selectedLetter, isOffline: true, writtenAnswer: userWrittenAnswer }
        }));
      } else {
        toast.error("Erro ao enviar resposta.");
      }
    } finally {
      attemptLockRef.current = false;
      setSubmitting(false);
    }
  }, [attemptResult, isOfflineSaved, submitting, currentDetail, selectedLetter, userWrittenAnswer]);

  const handleDiscursiveReveal = useCallback(async () => {
    if (attemptLockRef.current || attemptResult || isOfflineSaved || submitting || !currentDetail) return;
    attemptLockRef.current = true;
    
    setSubmitting(true);

    try {
      const res = await api.questions.submitAttempt(
        currentDetail.id, 
        "A", 
        getCurrentTime() * 1000, 
        "defer", 
        null,
        userWrittenAnswer
      );
      setAttemptResult(res);
      setIsOfflineSaved(false);
      setSessionAnswers(prev => ({
        ...prev,
        [currentDetail.id]: { letter: "A", result: res, writtenAnswer: userWrittenAnswer, isDiscursive: true }
      }));
    } catch (e: unknown) {
      if (e instanceof OfflineQueuedError) {
        setIsOfflineSaved(true);
        setSessionAnswers(prev => ({
          ...prev,
          [currentDetail.id]: { letter: "A", isOffline: true, writtenAnswer: userWrittenAnswer, isDiscursive: true }
        }));
        toast("Resposta salva neste dispositivo; será sincronizada quando a conexão voltar.", { icon: "💾" });
      } else {
        toast.error("Erro ao enviar resposta.");
      }
    } finally {
      attemptLockRef.current = false;
      setSubmitting(false);
    }
  }, [attemptResult, isOfflineSaved, submitting, currentDetail, userWrittenAnswer]);

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
      .map(([qid, ans]) => ({ question_id: Number(qid), wrong_letter: ans.letter || "A" }));

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

  const handleAskPreceptor = async () => {
    if (!currentDetail) return;
    setAskingPreceptor(true);
    try {
      const res = await api.questions.askAI(
        currentDetail.id,
        preceptorInput || undefined,
        selectedLetter || undefined
      );
      setPreceptorResponse(res);
    } catch (e: any) {
      toast.error(e.message || "Erro ao perguntar ao preceptor.");
    } finally {
      setAskingPreceptor(false);
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

  const handleReviewFSRS = useCallback(async (conf: string, explicitIsCorrect?: boolean) => {
    if (!currentDetail || reviewLockRef.current) return;
    reviewLockRef.current = true;

    // Snapshot variables for background request
    const questionId = currentDetail.id;
    const currentAttemptResult = attemptResult;
    const currentSelectedLetter = selectedLetter;
    const currentWrittenAnswer = userWrittenAnswer;
    const isDiscursive = Boolean(currentDetail.is_discursive || (currentDetail.alternatives || []).length <= 1);
    const institutionCode = currentDetail.institution_code;

    // Optimistic UI updates - Advance immediately
    reviewLockRef.current = false;
    nextQuestion();

    // Call API in background
    try {
      const res = await api.questions.reviewFSRS(questionId, conf, explicitIsCorrect);
      const isCorr = explicitIsCorrect !== undefined ? explicitIsCorrect : (currentAttemptResult?.is_correct ?? false);
      const updatedResult: AttemptResult = {
        ...(currentAttemptResult || {
          correct_letter: institutionCode || "A",
          explanation: null,
          next_review_date: res.next_review_date,
        }),
        is_correct: isCorr,
        next_review_date: res.next_review_date,
      };

      // Only update sessionAnswers (don't update attemptResult to avoid overwriting the next question's state)
      setSessionAnswers(prev => ({
        ...prev,
        [questionId]: {
          letter: currentSelectedLetter || "A",
          result: updatedResult,
          writtenAnswer: currentWrittenAnswer,
          isDiscursive: isDiscursive
        }
      }));
    } catch {
      toast.error("Erro ao salvar revisão (FSRS) em background.");
    }
  }, [currentDetail, attemptResult, selectedLetter, userWrittenAnswer, nextQuestion]);

  const prevQuestion = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
      loadQuestionDetail(queue[currentIndex - 1].id);
    }
  }, [currentIndex, queue, loadQuestionDetail]);

  const navigateQuestion = useCallback((direction: "next" | "previous") => {
    if (direction === "previous") {
      prevQuestion();
      return;
    }
    if (!attemptResult && !isOfflineSaved && !window.confirm("Pular esta questão? Ela ficará pendente e não contará como respondida na sessão.")) {
      return;
    }
    nextQuestion();
  }, [attemptResult, isOfflineSaved, nextQuestion, prevQuestion]);

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

  useQuizKeyboard({
    state,
    currentDetail,
    loadingDetail,
    attemptResult,
    currentIndex,
    queue,
    selectedLetter,
    submitting,
    handleAttempt,
    handleDiscursiveReveal,
    handleReviewFSRS,
    nextQuestion,
    prevQuestion,
    navigateQuestion,
    selectAlternative
  });

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (state === "FILTERS") {
    return (
      <QuizFilters
        hasSavedState={hasSavedState}
        savedSessionData={savedSessionData}
        discardSavedQuiz={discardSavedQuiz}
        resumeSavedQuiz={resumeSavedQuiz}
        showCustomSession={showCustomSession}
        setShowCustomSession={setShowCustomSession}
        startRecommendedSession={startRecommendedSession}
        handleFilterSubmit={handleFilterSubmit}
        studyMode={studyMode}
        setStudyMode={setStudyMode}
        filters={filters}
        setFilters={setFilters}
        localLimit={localLimit}
        setLocalLimit={setLocalLimit}
        isUpdatingMeta={isUpdatingMeta}
        dynamicMeta={dynamicMeta}
        subtemaSearch={subtemaSearch}
        setSubtemaSearch={setSubtemaSearch}
        showTopicTree={showTopicTree}
        setShowTopicTree={setShowTopicTree}
      />
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
  const completedCount = Object.values(sessionAnswers).filter(answer => answer.result || answer.isOffline).length;
  const extraCaseImages = filterExtraImages(q?.clinical_case?.images, q?.clinical_case?.stem);
  const extraStemImages = filterExtraImages(q?.images, q?.stem);

  return (
    <div className="max-w-4xl mx-auto w-full flex flex-col gap-6 pb-12 relative">
      {/* Fullscreen Image Modal */}
      {enlargedImage && (
        <ImageViewer 
          src={resolveImageUrl(enlargedImage)} 
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
             Respondidas {completedCount}/{queue.length}
          </div>
          <div className="hidden lg:flex items-center gap-2 ml-4 px-3 py-1 bg-muted/50 rounded-full text-xs text-muted-foreground font-medium">
            <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">A-E</kbd> ou <kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">1-5</kbd> Alternativas</span>
            <span className="w-1 h-1 rounded-full bg-border" />
              <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">Enter</kbd> Confirmar</span>
            <span className="w-1 h-1 rounded-full bg-border" />
              <span className="flex items-center gap-1"><kbd className="bg-background border border-border px-1.5 py-0.5 rounded text-[10px]">Ctrl + ➔</kbd> Navegar</span>
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
          <QuizTimer 
            ref={quizTimerRef}
            isRunning={state === "PLAYING" && !!currentDetail && !attemptResult}
            initialTime={initialTime}
            className={clsx("text-sm font-medium w-16", getCurrentTime() > 120 && !attemptResult ? "text-warning" : "text-muted-foreground")}
          />
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
              <FormattedContent 
                content={q.clinical_case.stem} 
                onImageClick={setEnlargedImage} 
                className="text-foreground text-lg leading-relaxed" 
              />
              {extraCaseImages.length > 0 && (
                <div className="flex flex-col sm:flex-row flex-wrap gap-4 mt-2">
                  {extraCaseImages.map((img, i) => (
                    <div 
                      key={i} 
                      className="relative group rounded-lg overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all sm:max-w-xs"
                      onClick={() => setEnlargedImage(img)}
                    >
                      <Image
                        src={resolveImageUrl(img)} 
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
                {Boolean(q.is_discursive || (q.alternatives || []).length <= 1) && (
                  <span className="bg-primary/15 text-primary border border-primary/30 px-2 py-1 rounded flex items-center gap-1 font-bold">
                    Discursiva
                  </span>
                )}
                <span className="bg-muted px-2 py-1 rounded">{q.institution_code}{q.is_autoral ? " (A)" : ""} {q.year}</span>
                <span className="bg-muted px-2 py-1 rounded">{q.area}</span>
                <span className="bg-muted px-2 py-1 rounded">{q.subtema}</span>
                {isCurator && (
                  <button
                    type="button"
                    onClick={() => setIsClassificationModalOpen(true)}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-primary/10 hover:bg-primary/20 text-primary border border-primary/25 transition-colors font-bold text-[11px] cursor-pointer shadow-xs"
                    title="Editar Classificação da Questão (Curadoria)"
                  >
                    <Pencil size={11} /> Editar Tema
                  </button>
                )}
              </div>
              
              <div className="flex items-center gap-3 bg-muted/30 px-3 py-1.5 rounded-lg border border-border">
                <button 
                  onClick={() => navigateQuestion("previous")}
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
                  onClick={() => navigateQuestion("next")}
                  disabled={loadingDetail}
                  className="p-1 hover:bg-background rounded transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                  title="Próxima questão (Ctrl + Seta Direita)"
                  aria-label="Próxima Questão"
                >
                  <ArrowRight size={18} aria-hidden="true" />
                </button>
              </div>
            </div>
            

            <FormattedContent 
              content={q.stem} 
              onImageClick={setEnlargedImage} 
              className="text-foreground text-lg md:text-xl font-medium leading-relaxed" 
            />

            {extraStemImages.length > 0 && (
              <div className="flex flex-col sm:flex-row flex-wrap gap-4 mt-6">
                {extraStemImages.map((img, i) => (
                  <div 
                    key={i} 
                    className="relative group rounded-xl overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all sm:max-w-sm"
                    onClick={() => setEnlargedImage(img)}
                  >
                    <Image
                      src={resolveImageUrl(img)} 
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

          {/* Alternatives or Discursive Response */}
          {Boolean(q.is_discursive || (q.alternatives || []).length <= 1) ? (
            !attemptResult && (
              <div className="bg-card border border-border shadow-1 rounded-2xl p-6 md:p-7 flex flex-col gap-4 animate-in fade-in duration-200">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-primary font-bold text-base">
                    <span className="material-symbols-outlined text-[20px]">edit_document</span>
                    <span>Questão Discursiva (Resposta Aberta)</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Atalho: <kbd className="bg-muted px-1.5 py-0.5 rounded border border-border text-[10px]">Ctrl+Enter</kbd> para confirmar
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Anote seus achados clínicos, hipótese diagnóstica ou conduta antes de revelar o gabarito e padrão oficial da banca:
                </p>
                <textarea
                  value={userWrittenAnswer}
                  onChange={(e) => setUserWrittenAnswer(e.target.value)}
                  placeholder="Escreva sua resposta ou hipótese aqui..."
                  rows={4}
                  className="w-full bg-input/40 border border-border focus:border-primary/50 focus:bg-background rounded-xl p-4 text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-y text-base font-normal leading-relaxed min-h-[110px]"
                  onKeyDown={(e) => {
                    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                      e.preventDefault();
                      handleDiscursiveReveal();
                    }
                  }}
                />
                <button
                  onClick={handleDiscursiveReveal}
                  disabled={submitting}
                  className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 shadow-md cursor-pointer text-sm disabled:opacity-50"
                >
                  {submitting ? (
                    <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <CheckCircle2 size={18} />
                      Confirmar Resposta & Ver Padrão da Banca
                    </>
                  )}
                </button>
              </div>
            )
          ) : (
            <div className="flex flex-col gap-3">
              {(q.alternatives || []).map((alt) => {
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
            </div>
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
                      // The queue dispatches sync-item-success with the original
                      // idempotency key. Sending a second request here would create
                      // a duplicate attempt after the queued one succeeds.
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
            <div className="animate-in slide-in-from-bottom-4 fade-in duration-300 flex flex-col gap-6">
              {/* If user had written an answer on discursive question, show it prominently */}
              {Boolean(q.is_discursive || (q.alternatives || []).length <= 1) && userWrittenAnswer && (
                <div className="bg-card border border-border shadow-1 rounded-2xl p-6 flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-primary uppercase tracking-wider">
                    <span className="material-symbols-outlined text-[16px]">draw</span>
                    <span>Sua Resposta Anotada</span>
                  </div>
                  <div className="text-foreground text-base leading-relaxed whitespace-pre-wrap bg-muted/40 p-4 rounded-xl border border-border font-medium">
                    {userWrittenAnswer}
                  </div>
                </div>
              )}

              <div className={clsx(
                "rounded-xl border shadow-1 overflow-hidden",
                attemptResult.is_correct === true ? "bg-success/5 border-success/20" :
                attemptResult.is_correct === false ? "bg-destructive/5 border-destructive/20" :
                "bg-card border-border"
              )}>
                <div className={clsx(
                  "p-4 border-b flex items-center justify-between",
                  attemptResult.is_correct === true ? "border-success/20 bg-success/10" :
                  attemptResult.is_correct === false ? "border-destructive/20 bg-destructive/10" :
                  "border-border bg-muted/50"
                )}>
                  <div className="flex items-center gap-2 font-bold">
                    {attemptResult.is_correct === true ? (
                      <><CheckCircle2 className="text-success" /> <span className="text-success">Resposta Correta!</span></>
                    ) : attemptResult.is_correct === false ? (
                      <><XCircle className="text-destructive" /> <span className="text-destructive">Resposta Incorreta</span></>
                    ) : (
                      <><span className="material-symbols-outlined text-primary text-[20px]">fact_check</span> <span className="text-foreground">Padrão de Resposta Oficial</span></>
                    )}
                  </div>
                  {attemptResult.is_correct !== null && attemptResult.next_review_date && (
                    <button
                      onClick={nextQuestion}
                      className="flex items-center gap-2 bg-background border border-border hover:bg-muted font-bold px-4 py-2 rounded-md transition-colors text-sm cursor-pointer"
                    >
                      Próxima <ArrowRight size={16} />
                    </button>
                  )}
                </div>
                
                <div className="p-6 md:p-8">
                  <h3 className="text-lg font-bold text-foreground mb-5 flex items-center gap-2">
                    <BookOpen size={20} className="text-primary" />
                    {Boolean(q.is_discursive || (q.alternatives || []).length <= 1) ? "Padrão de Resposta da Banca & Comentário" : "Comentário do Professor"}
                  </h3>
                  <ExplanationViewer 
                    explanation={attemptResult.explanation} 
                    correctLetter={Boolean(q.is_discursive || (q.alternatives || []).length <= 1) ? null : attemptResult.correct_letter}
                    questionId={currentDetail?.id}
                    userLetter={selectedLetter || attemptResult.correct_letter || undefined}
                    isDiscursive={Boolean(q.is_discursive || (q.alternatives || []).length <= 1)}
                  />

                  {currentDetail?.times_wrong && currentDetail.times_wrong > 0 ? (
                    <div className="mt-4 flex items-center gap-2 text-sm text-destructive font-semibold bg-destructive/10 px-3 py-1.5 rounded-full w-fit">
                      Você já errou esta questão {currentDetail.times_wrong} {currentDetail.times_wrong === 1 ? 'vez' : 'vezes'} no passado.
                    </div>
                  ) : null}
                  
                  {/* Flashcard Generation: Available when marked wrong, or on demand */}
                  {attemptResult.is_correct === false && !flashcardResult && !draftFlashcard && (
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

                  {/* Preceptor AI Section */}
                  <div className="mt-8 bg-blue-500/5 border border-blue-500/20 rounded-2xl p-5 md:p-6">
                    <h4 className="text-blue-700 dark:text-blue-400 font-bold flex items-center gap-2 mb-3 uppercase tracking-wider text-sm">
                      <Stethoscope size={18} /> Perguntar ao Preceptor (IA)
                    </h4>
                    {!preceptorResponse ? (
                      <div className="flex flex-col gap-3">
                        <textarea
                          className="w-full bg-background border border-border rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none min-h-[80px]"
                          placeholder="Ficou com alguma dúvida sobre esta questão? Pergunte ao preceptor virtual..."
                          value={preceptorInput}
                          onChange={(e) => setPreceptorInput(e.target.value)}
                        />
                        <div className="flex justify-end">
                          <button
                            onClick={handleAskPreceptor}
                            disabled={askingPreceptor || !preceptorInput.trim()}
                            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-xl shadow-sm transition-all flex items-center gap-2 text-sm"
                          >
                            {askingPreceptor ? (
                              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                              <Sparkles size={16} />
                            )}
                            {askingPreceptor ? "Consultando..." : "Enviar Pergunta"}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="bg-background rounded-xl p-4 border border-border relative">
                          <button 
                            onClick={() => { setPreceptorResponse(null); setPreceptorInput(""); }}
                            className="absolute top-2 right-2 text-muted-foreground hover:text-foreground"
                          >
                            <X size={16} />
                          </button>
                          <div className="text-sm md:text-base text-foreground leading-relaxed">
                            <FormattedContent content={preceptorResponse.answer} />
                          </div>
                          <div className="mt-3 text-xs text-muted-foreground font-mono bg-muted/50 w-fit px-2 py-1 rounded">
                            Respondido por: {preceptorResponse.model} ({preceptorResponse.source})
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

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
                            className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                          >
                            Cancelar
                          </button>
                          <button 
                            onClick={handleSaveFlashcard}
                            disabled={savingFlashcard}
                            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-5 rounded-lg transition-colors text-sm shadow-sm disabled:opacity-50 cursor-pointer"
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

                  {/* Self-Assessment / FSRS Block */}
                  {attemptResult.is_correct === null ? (
                    <div className="mt-8 pt-6 border-t border-border flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-primary text-[20px]">how_to_reg</span>
                          <span className="text-base font-bold text-foreground">
                            Autoavaliação da Resposta Discursiva
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          Compare sua hipótese com o padrão acima e declare:
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-1">
                        {/* Acertei */}
                        <div className="bg-success/5 border border-success/30 rounded-xl p-4 flex flex-col gap-3">
                          <div className="flex items-center gap-2 font-bold text-success text-sm">
                            <CheckCircle2 size={18} /> Acertei a Questão
                          </div>
                          <div className="flex flex-col gap-2">
                            <button
                              onClick={() => handleReviewFSRS("certeza", true)}
                              className="w-full text-left bg-card hover:bg-success/15 border border-success/30 hover:border-success text-foreground font-semibold px-3.5 py-2.5 rounded-lg text-xs flex items-center justify-between transition-colors shadow-sm cursor-pointer"
                            >
                              <span>🟢 Tinha Certeza</span>
                              <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded font-normal">Fácil • Atalho: 3</span>
                            </button>
                            <button
                              onClick={() => handleReviewFSRS("duvida", true)}
                              className="w-full text-left bg-card hover:bg-success/15 border border-success/30 hover:border-success text-foreground font-semibold px-3.5 py-2.5 rounded-lg text-xs flex items-center justify-between transition-colors shadow-sm cursor-pointer"
                            >
                              <span>🟡 Pensei um Pouco</span>
                              <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded font-normal">Bom tempo • Atalho: 2</span>
                            </button>
                            <button
                              onClick={() => handleReviewFSRS("chutei", true)}
                              className="w-full text-left bg-card hover:bg-success/15 border border-success/30 hover:border-success text-foreground font-semibold px-3.5 py-2.5 rounded-lg text-xs flex items-center justify-between transition-colors shadow-sm cursor-pointer"
                            >
                              <span>🔴 Acertei no Chute</span>
                              <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded font-normal">Difícil • Atalho: 1</span>
                            </button>
                          </div>
                        </div>

                        {/* Errei */}
                        <div className="bg-destructive/5 border border-destructive/30 rounded-xl p-4 flex flex-col gap-3">
                          <div className="flex items-center gap-2 font-bold text-destructive text-sm">
                            <XCircle size={18} /> Errei a Questão
                          </div>
                          <div className="flex flex-col gap-2">
                            <button
                              onClick={() => handleReviewFSRS("chutei", false)}
                              className="w-full text-left bg-card hover:bg-destructive/15 border border-destructive/30 hover:border-destructive text-foreground font-semibold px-3.5 py-2.5 rounded-lg text-xs flex items-center justify-between transition-colors shadow-sm cursor-pointer"
                            >
                              <span>🔴 Errei no Chute / Não sabia</span>
                              <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded font-normal">Volta amanhã</span>
                            </button>
                            <button
                              onClick={() => handleReviewFSRS("duvida", false)}
                              className="w-full text-left bg-card hover:bg-destructive/15 border border-destructive/30 hover:border-destructive text-foreground font-semibold px-3.5 py-2.5 rounded-lg text-xs flex items-center justify-between transition-colors shadow-sm cursor-pointer"
                            >
                              <span>🟡 Fiquei em Dúvida</span>
                              <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded font-normal">Volta em breve • Atalho: E</span>
                            </button>
                            <button
                              onClick={() => handleReviewFSRS("certeza", false)}
                              className="w-full text-left bg-card hover:bg-destructive/15 border border-destructive/30 hover:border-destructive text-foreground font-semibold px-3.5 py-2.5 rounded-lg text-xs flex items-center justify-between transition-colors shadow-sm cursor-pointer"
                            >
                              <span>🟢 Errei com Certeza</span>
                              <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded font-normal">Preciso fixar</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : attemptResult.next_review_date ? (
                    <div className="mt-8 pt-4 border-t border-border flex items-center justify-between flex-wrap gap-2 text-sm font-medium text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Clock size={16} />
                        Próxima revisão agendada para: {new Date(attemptResult.next_review_date).toLocaleDateString('pt-BR')}
                      </div>
                      {Boolean(q.is_discursive || (q.alternatives || []).length <= 1) && (
                        <button
                          onClick={() => setAttemptResult(prev => prev ? { ...prev, is_correct: null } : null)}
                          className="text-xs text-primary hover:underline font-semibold cursor-pointer"
                        >
                          Alterar autoavaliação
                        </button>
                      )}
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
                            <button title="O algoritmo agendará a revisão desta questão para um intervalo curto (geralmente no dia seguinte) já que você não dominava o conceito original." onClick={() => handleReviewFSRS("chutei")} className="flex-1 bg-destructive/10 text-destructive hover:bg-destructive/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1 cursor-pointer">
                              <span>🔴 Acertei no Chute</span>
                              <span className="text-[10px] font-normal opacity-80">Volta amanhã (Difícil) • Atalho: 1</span>
                            </button>
                            <button title="O algoritmo agendará a revisão com um multiplicador moderado de dias, reforçando a memória sem sobrecarregar sua fila." onClick={() => handleReviewFSRS("duvida")} className="flex-1 bg-warning/10 text-warning hover:bg-warning/20 font-bold py-3 rounded-lg transition-colors text-sm border-2 border-warning/50 shadow-sm flex flex-col items-center justify-center gap-1 cursor-pointer">
                              <span>🟡 Pensei um Pouco</span>
                              <span className="text-[10px] font-normal opacity-80">Bom tempo • Atalho: 2 / Enter</span>
                            </button>
                            <button title="O algoritmo entenderá que você domina este assunto e agendará a revisão para o mais longe possível (maior estabilidade de memória)." onClick={() => handleReviewFSRS("certeza")} className="flex-1 bg-success/10 text-success hover:bg-success/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1 cursor-pointer">
                              <span>🟢 Tinha Certeza</span>
                              <span className="text-[10px] font-normal opacity-80">Revisa mais tarde (Fácil) • Atalho: 3</span>
                            </button>
                          </>
                        ) : (
                          <>
                            <button title="Você não sabia a resposta e foi pego de surpresa. A revisão ocorrerá o mais breve possível (amanhã)." onClick={() => handleReviewFSRS("chutei")} className="flex-1 bg-destructive/10 text-destructive hover:bg-destructive/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1 cursor-pointer">
                              <span>🔴 Errei no Chute</span>
                              <span className="text-[10px] font-normal opacity-80">Volta amanhã • Atalho: 1</span>
                            </button>
                            <button title="O algoritmo entenderá que você cometeu um erro que exige reforço imediato e agendará a revisão mais próxima para consertar a falha de memória." onClick={() => handleReviewFSRS("duvida")} className="flex-1 bg-warning/10 text-warning hover:bg-warning/20 font-bold py-3 rounded-lg transition-colors text-sm border-2 border-warning/50 shadow-sm flex flex-col items-center justify-center gap-1 cursor-pointer">
                              <span>🟡 Fiquei em Dúvida</span>
                              <span className="text-[10px] font-normal opacity-80">Bom tempo • Atalho: 2 / Enter</span>
                            </button>
                            <button title="Você sentiu firmeza, mas se confundiu numa 'pegadinha'. O algoritmo agendará a revisão com certa urgência, mas espaçada o suficiente para testar se a confusão persiste." onClick={() => handleReviewFSRS("certeza")} className="flex-1 bg-success/10 text-success hover:bg-success/20 font-bold py-3 rounded-lg transition-colors text-sm flex flex-col items-center justify-center gap-1 cursor-pointer">
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

      {isCurator && q && (
        <QuestionClassificationModal
          isOpen={isClassificationModalOpen}
          onClose={() => setIsClassificationModalOpen(false)}
          questionId={q.id}
          currentArea={q.area}
          currentSubtema={q.subtema}
          currentTopic={q.topic}
          onSuccess={(updated) => {
            setCurrentDetail((prev) => (prev ? { ...prev, area: updated.area, subtema: updated.subtema, topic: updated.topic } : prev));
            setQueue((prevQueue) =>
              prevQueue.map((item, idx) =>
                idx === currentIndex ? { ...item, area: updated.area, subtema: updated.subtema, topic: updated.topic } : item
              )
            );
            toast.success("Tema da questão atualizado com sucesso!");
          }}
        />
      )}
    </div>
  );
}
