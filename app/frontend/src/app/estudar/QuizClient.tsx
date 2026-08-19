"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { QuestionMeta, QuestionListItem, QuestionDetail, AttemptResult, FlashcardGenerateResponse } from "@/types/api";
import { api } from "@/lib/api";
import { Play, Filter, Clock, CheckCircle2, XCircle, ChevronRight, BookOpen, Heart, ArrowRight, Sparkles, BookOpenCheck, FileSignature, ArrowLeft, ImageOff, Maximize, Minimize, AlertTriangle } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

type QuizState = "FILTERS" | "LOADING_QUEUE" | "PLAYING" | "FINISHED";

export function QuizClient({
  meta,
  initialFilters
}: {
  meta: QuestionMeta;
  initialFilters: Record<string, string>;
}) {
  const router = useRouter();
  const [state, setState] = useState<QuizState>(Object.keys(initialFilters).length > 0 ? "LOADING_QUEUE" : "FILTERS");
  const [filters, setFilters] = useState<Record<string, string | string[]>>({ limit: "50", ...initialFilters });
  const [localLimit, setLocalLimit] = useState<string>(
    typeof filters.limit === "string" ? filters.limit : "50"
  );
  const [zenMode, setZenMode] = useState(false);

  useEffect(() => {
    if (zenMode) {
      document.body.classList.add('zen-mode');
    } else {
      document.body.classList.remove('zen-mode');
    }
    return () => document.body.classList.remove('zen-mode');
  }, [zenMode]);

  const [studyMode, setStudyMode] = useState<"TUTOR" | "SIMULADO">("TUTOR");
  const [dynamicMeta, setDynamicMeta] = useState<QuestionMeta>(meta);
  const [isUpdatingMeta, setIsUpdatingMeta] = useState(false);
  
  const [queue, setQueue] = useState<QuestionListItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentDetail, setCurrentDetail] = useState<QuestionDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  // Quiz State
  const [selectedLetter, setSelectedLetter] = useState<string | null>(null);
  const [attemptResult, setAttemptResult] = useState<AttemptResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [generatingFlashcard, setGeneratingFlashcard] = useState(false);
  const [flashcardResult, setFlashcardResult] = useState<FlashcardGenerateResponse | null>(null);
  
  // Timer State
  const [timeSpent, setTimeSpent] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Image Modal
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);

  // AI Explanation Stream
  const [aiExplanation, setAiExplanation] = useState<string>("");
  const [isExplaining, setIsExplaining] = useState(false);

  // Confidence

  const [togglingFavorite, setTogglingFavorite] = useState(false);

  const loadQuestionDetail = useCallback(async (id: number) => {
    setLoadingDetail(true);
    setAttemptResult(null);
    setSelectedLetter(null);
    setFlashcardResult(null);
    setAiExplanation("");
    setIsExplaining(false);
    setTimeSpent(0);
    try {
      const detail = await api.questions.getDetail(id);
      setCurrentDetail(detail);
      // Removida a lógica de bloqueio por already_answered. Na revisão, o aluno tenta de novo!
    } catch (e) {
      toast.error("Erro ao carregar questão.");
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  const loadQueue = useCallback(async (activeFilters: Record<string, string | string[]>) => {
    setState("LOADING_QUEUE");
    try {
      const qList = await api.questions.getList(activeFilters);
      if (qList.length > 0) {
        setQueue(qList);
        setCurrentIndex(0);
        setState("PLAYING");
        loadQuestionDetail(qList[0].id);
      } else {
        toast.error("Nenhuma questão encontrada com esses filtros.");
        setState("FILTERS");
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Erro desconhecido";
      toast.error(`Erro ao buscar questões: ${message}`);
      setState("FILTERS");
    }
  }, [loadQuestionDetail]);

  useEffect(() => {
    if (Object.keys(initialFilters).length > 0 && queue.length === 0 && state === "LOADING_QUEUE") {
      const timer = setTimeout(() => {
        loadQueue({ limit: "50", ...initialFilters });
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [initialFilters, loadQueue, queue.length, state]);

  // Effect to fetch dynamic meta when filters change
  useEffect(() => {
    if (state !== "FILTERS") return;
    
    let isMounted = true;
    const fetchDynamicMeta = async () => {
      setIsUpdatingMeta(true);
      try {
        const newMeta = await api.questions.getMeta(filters);
        if (isMounted) setDynamicMeta(newMeta);
      } catch (e) {
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

  const handleAttempt = async () => {
    if (attemptResult || submitting || !currentDetail || !selectedLetter) return;
    
    setSubmitting(true);
    if (timerRef.current) clearInterval(timerRef.current);

    try {
      const res = await api.questions.submitAttempt(currentDetail.id, selectedLetter, timeSpent * 1000, "defer");
      setAttemptResult(res);
    } catch (e) {
      toast.error("Erro ao enviar resposta.");
      // O timer será reiniciado automaticamente pelo useEffect pois attemptResult continua null e state="PLAYING"
    } finally {
      setSubmitting(false);
    }
  };

  const handleGenerateFlashcard = async () => {
    if (!currentDetail || !selectedLetter) return;
    setGeneratingFlashcard(true);
    try {
      const res = await api.flashcards.generate(currentDetail.id, selectedLetter);
      setFlashcardResult(res);
    } catch (e) {
      toast.error("Erro ao gerar flashcard com IA.");
    } finally {
      setGeneratingFlashcard(false);
    }
  };

  const handleExplain = async () => {
    if (!currentDetail) return;
    setIsExplaining(true);
    setAiExplanation("");
    try {
      // Usamos fetch nativo porque a lib apiFetch geralmente espera JSON e não stream
      const response = await fetch(`/api/questions/${currentDetail.id}/explain`);
      if (!response.body) throw new Error("No body returned");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || "";
        
        for (const part of parts) {
          if (part.startsWith('data: ')) {
            const dataStr = part.slice(6);
            if (dataStr === '[DONE]') break;
            try {
              const data = JSON.parse(dataStr);
              if (data.text) {
                setAiExplanation(prev => prev + data.text);
              }
            } catch (e) {}
          }
        }
      }
    } catch (e) {
      toast.error("Erro ao carregar explicação com IA.");
    } finally {
      setIsExplaining(false);
    }
  };

  const nextQuestion = () => {
    if (currentIndex + 1 < queue.length) {
      setCurrentIndex(prev => prev + 1);
      loadQuestionDetail(queue[currentIndex + 1].id);
    } else {
      setState("FINISHED");
    }
  };

  const handleReviewFSRS = async (conf: string) => {
    if (!currentDetail) return;
    try {
      await api.questions.reviewFSRS(currentDetail.id, conf);
    } catch (e) {
      toast.error("Erro ao salvar revisão (FSRS).");
    } finally {
      nextQuestion();
    }
  };

  const prevQuestion = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
      loadQuestionDetail(queue[currentIndex - 1].id);
    }
  };

  const toggleFavorite = async () => {
    if (!currentDetail || togglingFavorite) return;
    setTogglingFavorite(true);
    setCurrentDetail({ ...currentDetail, is_favorite: !currentDetail.is_favorite });
    try {
      await api.questions.toggleFavorite(currentDetail.id);
    } catch (e) {
      setCurrentDetail({ ...currentDetail, is_favorite: currentDetail.is_favorite });
    } finally {
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
            setSelectedLetter(currentDetail.alternatives[idx].letter);
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
  }, [state, currentDetail, loadingDetail, attemptResult, currentIndex, queue, selectedLetter, submitting]);

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
                <option value="">Todas</option>
                <option value="unanswered">Não respondidas</option>
                <option value="srs_due">Para Revisão (Repetição Espaçada)</option>
                <option value="wrong">Errei anteriormente</option>
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
                <option value="">Todas as Áreas</option>
                {dynamicMeta.areas.map(a => (
                  <option key={a.area} value={a.area}>{a.area} ({a.n})</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground flex items-center justify-between">
                <span>Instituição</span>
                {isUpdatingMeta && <span className="text-xs text-muted-foreground animate-pulse">Atualizando...</span>}
              </label>
              <select 
                className="w-full bg-input border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={filters.institution || ""}
                onChange={(e) => setFilters({ ...filters, institution: e.target.value })}
              >
                <option value="">Todas as Instituições</option>
                {dynamicMeta.institutions.map(i => (
                  <option key={i.institution_code} value={i.institution_code}>{i.institution_code} ({i.n})</option>
                ))}
              </select>
            </div>
            
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-foreground flex items-center justify-between">
                <span>Subtemas (Múltipla Escolha)</span>
                {isUpdatingMeta && <span className="text-xs text-muted-foreground animate-pulse">Atualizando...</span>}
              </label>
              <div className="w-full bg-input border border-border rounded-md p-3 h-48 overflow-y-auto flex flex-col gap-1">
                {dynamicMeta.subtemas?.length === 0 && (
                  <p className="text-xs text-muted-foreground italic">Nenhum subtema encontrado para esta área.</p>
                )}
                {dynamicMeta.subtemas?.map(s => {
                  const isSelected = Array.isArray(filters.subtema) 
                    ? filters.subtema.includes(s.subtema) 
                    : filters.subtema === s.subtema;
                  
                  return (
                    <label key={s.subtema} className="flex items-center gap-3 text-sm text-foreground cursor-pointer hover:bg-muted/50 p-2 rounded border border-transparent hover:border-border transition-colors">
                      <input 
                        type="checkbox" 
                        checked={isSelected}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          let current = Array.isArray(filters.subtema) ? [...filters.subtema] : (filters.subtema ? [filters.subtema as string] : []);
                          if (checked) {
                            current.push(s.subtema);
                          } else {
                            current = current.filter(x => x !== s.subtema);
                          }
                          setFilters({ ...filters, subtema: current });
                        }}
                        className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                      />
                      <span className="flex-1 truncate">{s.subtema}</span>
                      <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-0.5 rounded-full">{s.n}</span>
                    </label>
                  );
                })}
              </div>
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

        <div className="mt-10 pt-8 border-t border-border">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <Sparkles size={16} className="text-primary" /> Sugestões Rápidas
          </h3>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => { setLocalLimit("20"); setFilters({ ...filters, area: "Clínica Médica", limit: "20" }); }} className="bg-muted/50 hover:bg-muted px-4 py-2 rounded-full text-xs font-medium text-foreground border border-border transition-colors">
              Revisar Clínica Médica (20 Qs)
            </button>
            <button type="button" onClick={() => { setLocalLimit("15"); setFilters({ ...filters, status: "wrong", limit: "15" }); }} className="bg-destructive/5 hover:bg-destructive/10 px-4 py-2 rounded-full text-xs font-medium text-destructive border border-destructive/20 transition-colors">
              Refazer Erros Recentes (15 Qs)
            </button>
            <button type="button" onClick={() => { setLocalLimit("30"); setFilters({ ...filters, status: "srs_due", limit: "30" }); }} className="bg-warning/5 hover:bg-warning/10 px-4 py-2 rounded-full text-xs font-medium text-warning border border-warning/20 transition-colors">
              Revisão Espaçada Diária (30 Qs)
            </button>
          </div>
        </div>
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
    return (
      <div className="bg-card border border-border shadow-1 rounded-xl p-10 max-w-2xl mx-auto w-full text-center">
        <div className="w-20 h-20 bg-success/20 text-success rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 size={40} />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-3">
          {studyMode === "TUTOR" ? "Sessão Concluída!" : "Simulado Concluído!"}
        </h2>
        <p className="text-muted-foreground mb-8">
          {studyMode === "TUTOR" ? "Você terminou de responder todas as questões desta sessão." : "Você terminou todas as questões da fila."}
        </p>
        <button 
          onClick={() => setState("FILTERS")}
          className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-2.5 px-6 rounded-md transition-colors cursor-pointer"
        >
          Voltar para Filtros
        </button>
      </div>
    );
  }

  // PLAYING STATE
  const q = currentDetail;

  return (
    <div className="max-w-4xl mx-auto w-full flex flex-col gap-6 pb-12 relative">
      {/* Fullscreen Image Modal */}
      {enlargedImage && (
        <div 
          className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex items-center justify-center p-4 sm:p-8 cursor-zoom-out"
          onClick={() => setEnlargedImage(null)}
        >
          <img 
            src={`/api/images/${enlargedImage}`} 
            alt="Imagem Ampliada" 
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
          />
          <button 
            className="absolute top-4 right-4 bg-surface/50 hover:bg-surface text-foreground p-2 rounded-full transition-colors"
            onClick={(e) => { e.stopPropagation(); setEnlargedImage(null); }}
          >
            <XCircle size={24} />
          </button>
        </div>
      )}
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-card border border-border shadow-1 rounded-xl p-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setState("FILTERS")}
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
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
            onClick={() => setZenMode(!zenMode)}
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

      {loadingDetail || !q ? (
        <div className="flex flex-col gap-6 animate-pulse">
          <div className="bg-card border border-border rounded-xl p-8 h-40" />
          <div className="flex flex-col gap-4">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-14 bg-card border border-border rounded-lg" />)}
          </div>
        </div>
      ) : (
        <>
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
                    <img 
                      src={`/api/images/${img}`} 
                      alt={`Imagem ${i+1}`} 
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
                <button
                  key={alt.letter}
                  onClick={() => !attemptResult && !submitting && setSelectedLetter(alt.letter)}
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
                </button>
              );
            })}
          </div>

          {!attemptResult && selectedLetter && (
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
                  <h3 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                    <BookOpen size={20} className="text-primary" />
                    Comentário do Professor
                  </h3>
                  <div className="text-foreground text-base md:text-lg leading-relaxed whitespace-pre-wrap">
                    {attemptResult.explanation || "Nenhum comentário disponível para esta questão."}
                  </div>

                  {currentDetail?.medical_references && (
                    <div className="mt-6 pt-5 border-t border-border">
                      <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">Referências e Diretrizes</h4>
                      <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap bg-muted/30 p-4 rounded-lg">
                        {currentDetail.medical_references}
                      </div>
                    </div>
                  )}

                  {currentDetail?.times_wrong && currentDetail.times_wrong > 0 ? (
                    <div className="mt-4 flex items-center gap-2 text-sm text-destructive font-semibold bg-destructive/10 px-3 py-1.5 rounded-full w-fit">
                      Você já errou esta questão {currentDetail.times_wrong} {currentDetail.times_wrong === 1 ? 'vez' : 'vezes'} no passado.
                    </div>
                  ) : null}
                  
                  {/* AI Explanation Stream Area */}
                  {aiExplanation && (
                    <div className="mt-6 p-5 bg-primary/5 border border-primary/20 rounded-xl">
                      <h4 className="text-sm font-bold text-primary flex items-center gap-2 mb-3">
                        <Sparkles size={16} /> Resposta do Tutor de IA
                      </h4>
                      <div className="text-foreground leading-relaxed whitespace-pre-wrap">
                        {aiExplanation}
                        {isExplaining && <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />}
                      </div>
                    </div>
                  )}

                  <div className="mt-6 flex flex-wrap gap-3">
                    {!aiExplanation && !isExplaining && (
                      <button 
                        onClick={handleExplain}
                        className="flex items-center gap-2 bg-primary/10 text-primary hover:bg-primary/20 font-bold py-2 px-4 rounded-lg shadow-sm transition-all"
                      >
                        <Sparkles size={18} />
                        Explicar com IA
                      </button>
                    )}
                    
                    {!attemptResult.is_correct && !flashcardResult && (
                      <button 
                        onClick={handleGenerateFlashcard}
                        disabled={generatingFlashcard}
                        className="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white font-bold py-2 px-4 rounded-lg shadow-sm transition-all disabled:opacity-50"
                      >
                        {generatingFlashcard ? (
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                          <Sparkles size={18} />
                        )}
                        {generatingFlashcard ? "Analisando seu erro..." : "Gerar Flashcard"}
                      </button>
                    )}
                  </div>

                  {flashcardResult && (
                    <div className="mt-6 bg-purple-500/10 border border-purple-500/20 rounded-xl p-5">
                      <div className="flex items-center gap-2 text-purple-500 font-bold mb-3">
                        <Sparkles size={18} /> Flashcard Salvo com Sucesso!
                      </div>
                      <div className="text-foreground text-sm space-y-2">
                        <p className="font-medium bg-background p-3 rounded border border-border">Frente: {flashcardResult.front}</p>
                        {flashcardResult.back && <p className="text-muted-foreground bg-background p-3 rounded border border-border">Verso: {flashcardResult.back}</p>}
                      </div>
                      <p className="text-xs text-muted-foreground mt-3">Ele foi automaticamente inserido na sua pilha de Revisão Ativa.</p>
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
        </>
      )}
    </div>
  );
}
