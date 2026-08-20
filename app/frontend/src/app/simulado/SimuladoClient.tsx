"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { QuestionMeta, QuestionListItem, QuestionDetail, BatchAttemptItem, BatchAttemptResultItem } from "@/types/api";
import { api } from "@/lib/api";
import { Play, Clock, CheckCircle2, XCircle, ChevronLeft, ChevronRight, FileSignature, AlertTriangle, BookOpen, AlertCircle, RotateCcw, Flag, Filter } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import confetti from "canvas-confetti";
import { motion, AnimatePresence } from "framer-motion";
import { ImageViewer } from "@/components/ImageViewer";
import { Grid as FixedSizeGrid } from "react-window";
import { AutoSizer } from "react-virtualized-auto-sizer";

type SimuladoState = "START" | "LOADING" | "PLAYING" | "SUBMITTING" | "RESULTS";

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
  const [showFinishConfirm, setShowFinishConfirm] = useState(false);
  const [showAreaSummary, setShowAreaSummary] = useState(false);
  const [showResultsSummary, setShowResultsSummary] = useState(false);
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);
  
  // Answers: question_id -> letter
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [resultsMap, setResultsMap] = useState<Record<number, BatchAttemptResultItem>>({});
  
  // Marcar para revisar
  const [flagged, setFlagged] = useState<Record<number, boolean>>({});
  // Filtro da sidebar: 'all' | 'unanswered' | 'flagged'
  const [sidebarFilter, setSidebarFilter] = useState<'all' | 'unanswered' | 'flagged'>('all');
  
  // Duração proporcional: 3 min/questão (120 Qs = 6h), arredondado
  const [totalTime, setTotalTime] = useState(6 * 60 * 60);
  const [timeLeft, setTimeLeft] = useState(6 * 60 * 60);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const hasCustomFilters = Object.keys(initialFilters).length > 0;
  const [simuladoProfile, setSimuladoProfile] = useState<'usp_2026' | 'usp_history' | 'unicamp' | 'sus_sp' | 'custom'>(
    hasCustomFilters ? 'custom' : 'usp_2026'
  );
  
  const [customConfig, setCustomConfig] = useState({
    institutions: [] as string[],
    years: [] as string[],
    questions_per_area: 20,
    force_4_options: false
  });

  const [hasSavedState, setHasSavedState] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    const saved = localStorage.getItem("medquest_simulado_state");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.state === "PLAYING" || parsed.state === "RESULTS") {
          timer = setTimeout(() => {
            setHasSavedState(true);
          }, 0);
        }
      } catch {
        localStorage.removeItem("medquest_simulado_state");
      }
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, []);

  const resumeSimulado = () => {
    const saved = localStorage.getItem("medquest_simulado_state");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setState(parsed.state);
        setQueue(parsed.queue);
        setAnswers(parsed.answers);
        setTimeLeft(parsed.timeLeft);
        setCurrentIndex(parsed.currentIndex);
        setResultsMap(parsed.resultsMap);
        
        // Re-fetch details batch
        const ids = parsed.queue.map((q: any) => q.id);
        const force4 = parsed.queue.length === 120 || parsed.queue.length === 80; // Heuristica simples para resume
        api.questions.getBatch(ids, force4).then(batchRes => {
          const cache: Record<number, QuestionDetail> = {};
          for (const q of batchRes.questions) {
            cache[q.id] = q;
          }
          setDetailsCache(cache);
        }).catch(() => {
          toast.error("Erro ao carregar detalhes no resumo.");
        });
        
      } catch {
        toast.error("Erro ao restaurar simulado.");
        localStorage.removeItem("medquest_simulado_state");
      }
    }
  };

  useEffect(() => {
    if (state === "PLAYING" || state === "RESULTS") {
      localStorage.setItem("medquest_simulado_state", JSON.stringify({
        state, queue, answers, timeLeft, currentIndex, resultsMap
      }));
    }
  }, [state, queue, answers, timeLeft, currentIndex, resultsMap]);

  // Load Simulado
  const startSimulado = async () => {
    if (hasSavedState) {
      localStorage.removeItem("medquest_simulado_state");
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
        if (simuladoProfile === 'usp_2026') {
          qList = await api.questions.getSimuladoUSP();
          isForce4Options = true;
          durationHours = 6; // 120 questões, 6 horas
        } else if (simuladoProfile === 'usp_history') {
          qList = await api.questions.getSimuladoUSP();
          durationHours = 6;
        } else if (simuladoProfile === 'unicamp') {
          qList = await api.questions.getList({ institution_code: "UNICAMP", limit: "80" });
          isForce4Options = true;
          durationHours = 4; // 80 questões, 4 horas
        } else if (simuladoProfile === 'sus_sp') {
          qList = await api.questions.getList({ institution_code: "SUS-SP", limit: "100" });
          durationHours = 5; // 100 questões, 5 horas
        } else if (simuladoProfile === 'custom' && !hasCustomFilters) {
          qList = await api.questions.getCustomSimulado(customConfig);
          isForce4Options = customConfig.force_4_options;
          durationHours = (qList.length / 120) * 6; // roughly 3 minutes per question
        } else {
          qList = await api.questions.getSimuladoUSP();
        }
      }

      if (qList.length === 0) {
        toast.error("Erro: Não há questões suficientes para montar o simulado com esses filtros.");
        setState("START");
        return;
      }
      
      const calcTime = Math.round(durationHours * 60 * 60);
      setTotalTime(calcTime);
      setTimeLeft(calcTime);
      
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
    }
  };

  const loadDetail = async (id: number) => {
    if (detailsCache[id]) return; // Already cached
    setLoadingDetail(true);
    setDetailError(false);
    try {
      const detail = await api.questions.getDetail(id);
      setDetailsCache(prev => ({ ...prev, [id]: detail }));
    } catch {
      console.error("Erro ao carregar questão", id);
      setDetailError(true);
    } finally {
      setLoadingDetail(false);
    }
  };

  const submitSimulado = useCallback(async () => {
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
      setResultsMap(rMap);
      setState("RESULTS");
      setCurrentIndex(0); // Go back to first question to review
      setShowResultsSummary(true);
      
      confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#0EA5E9', '#38BDF8', '#7DD3FC', '#F472B6']
      });
      
      localStorage.removeItem("medquest_simulado_state");
    } catch {
      toast.error("Erro ao enviar simulado. Tente novamente.");
      setState("PLAYING");
    }
  }, [answers]);

  const submitSimuladoRef = useRef(submitSimulado);
  useEffect(() => {
    submitSimuladoRef.current = submitSimulado;
  }, [submitSimulado]);

  // Timer Effect
  useEffect(() => {
    if (state === "PLAYING") {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            if (timerRef.current) clearInterval(timerRef.current);
            setTimeout(() => submitSimuladoRef.current(), 0);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [state]);

  const handleSelect = (letter: string) => {
    if (state !== "PLAYING") return;
    const currentQ = queue[currentIndex];
    setAnswers(prev => ({ ...prev, [currentQ.id]: letter }));
  };

  const toggleFlag = () => {
    if (state !== "PLAYING") return;
    const currentQ = queue[currentIndex];
    setFlagged(prev => ({ ...prev, [currentQ.id]: !prev[currentQ.id] }));
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

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
          setShowFinishConfirm(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state, currentIndex, queue, detailsCache]);


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
    const isCustom = Object.keys(initialFilters).length > 0;
    
    return (
      <div className="bg-card border border-border shadow-1 rounded-xl p-8 max-w-2xl mx-auto w-full text-center flex flex-col items-center">
        <div className="w-20 h-20 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mb-6">
          <FileSignature size={40} />
        </div>
        <h2 className="text-h2 font-bold text-foreground mb-4">
          {hasCustomFilters ? "Simulado Personalizado" : "Novo Simulado"}
        </h2>
        <p className="text-muted-foreground text-body-m mb-6 max-w-md">
          {hasCustomFilters 
            ? "Esta prova irá simular as condições reais de exame usando os filtros que você escolheu."
            : "Selecione o perfil de prova desejado para simular as condições reais do exame."}
        </p>

        {!hasCustomFilters && (
          <div className="w-full max-w-md mb-6">
            <select
              value={simuladoProfile}
              onChange={(e) => setSimuladoProfile(e.target.value as any)}
              className="w-full bg-background border border-border rounded-lg p-3 text-foreground font-medium focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option className="bg-background text-foreground" value="usp_2026">USP 2026 (120 Qs, 4 Alternativas)</option>
              <option className="bg-background text-foreground" value="usp_history">Histórico USP (120 Qs, 5 Alternativas)</option>
              <option className="bg-background text-foreground" value="unicamp">UNICAMP (80 Qs, 4 Alternativas)</option>
              <option className="bg-background text-foreground" value="sus_sp">SUS-SP (100 Qs, 5 Alternativas)</option>
              <option className="bg-background text-foreground" value="custom">Configuração Personalizada</option>
            </select>
          </div>
        )}

        {simuladoProfile === 'custom' && !hasCustomFilters && (
          <div className="w-full max-w-md mb-6 bg-muted/30 p-4 rounded-xl border border-border text-left flex flex-col gap-4 animate-in slide-in-from-top-2">
            <div>
              <label className="block text-sm font-bold text-foreground mb-2">Bancas Incluídas (deixe vazio para todas)</label>
              <div className="flex flex-wrap gap-2">
                {(meta?.institutions.map(i => i.institution_code) || ['USP-SP', 'USP-RP', 'UNICAMP', 'SUS-SP', 'ENARE']).map(inst => (
                  <label key={inst} className="flex items-center gap-1.5 bg-background border border-border px-2 py-1 rounded text-sm cursor-pointer hover:bg-muted">
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
                      className="rounded text-primary focus:ring-primary"
                    />
                    {inst}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm font-bold text-foreground mb-2">Questões por Área</label>
                <input 
                  type="number" 
                  min="5" max="30" 
                  value={customConfig.questions_per_area}
                  onChange={(e) => setCustomConfig(prev => ({ ...prev, questions_per_area: parseInt(e.target.value) || 20 }))}
                  className="w-full bg-background border border-border rounded-lg p-2 text-foreground focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-muted-foreground mt-1">Multiplicado por 5 áreas</p>
              </div>
            </div>

            <label className="flex items-center gap-2 cursor-pointer border-t border-border pt-4 mt-2">
              <input 
                type="checkbox" 
                checked={customConfig.force_4_options}
                onChange={(e) => setCustomConfig(prev => ({ ...prev, force_4_options: e.target.checked }))}
                className="rounded text-primary focus:ring-primary w-4 h-4"
              />
              <span className="text-sm font-bold text-foreground">Forçar 4 Alternativas (Estilo USP 2026)</span>
            </label>
          </div>
        )}
        
        <div className="grid grid-cols-2 gap-4 w-full max-w-md mb-8 text-left">
          <div className="bg-muted rounded-lg p-4">
            <span className="block text-xs font-bold text-muted-foreground uppercase mb-1">Questões</span>
            <span className="text-lg font-bold text-foreground">
              {hasCustomFilters ? (initialFilters.limit || "Até 50") : (
                simuladoProfile === 'unicamp' ? '80' :
                simuladoProfile === 'sus_sp' ? '100' :
                simuladoProfile === 'custom' ? (customConfig.questions_per_area * 5) : '120'
              )} (Múltipla Escolha)
            </span>
          </div>
          <div className="bg-muted rounded-lg p-4">
            <span className="block text-xs font-bold text-muted-foreground uppercase mb-1">Duração</span>
            <span className="text-lg font-bold text-foreground">
              {hasCustomFilters 
                ? `${Math.round((Number(initialFilters.limit || 50) / 120) * 6 * 60)} min` 
                : (
                    simuladoProfile === 'unicamp' ? '4 Horas' : 
                    simuladoProfile === 'sus_sp' ? '5 Horas' : 
                    simuladoProfile === 'custom' ? `${Math.round(((customConfig.questions_per_area * 5) / 120) * 6)} Horas` : '6 Horas'
                  )}
            </span>
          </div>
          {!hasCustomFilters && (simuladoProfile === 'usp_2026' || simuladoProfile === 'usp_history' || simuladoProfile === 'custom') && (
            <div className="bg-muted rounded-lg p-4 col-span-2">
              <span className="block text-xs font-bold text-muted-foreground uppercase mb-1">Balanceamento</span>
              <span className="text-sm font-medium text-foreground">
                {simuladoProfile === 'custom' 
                  ? `${customConfig.questions_per_area} Clínica • ${customConfig.questions_per_area} Cirurgia • ${customConfig.questions_per_area} Pediatria • ${customConfig.questions_per_area} GO • ${customConfig.questions_per_area} Preventiva`
                  : '24 Clínica • 24 Cirurgia • 24 Pediatria • 24 GO • 24 Preventiva'}
              </span>
            </div>
          )}
        </div>

        <div className="bg-warning/10 text-warning border border-warning/20 rounded-lg p-4 flex items-start gap-3 w-full max-w-md mb-8 text-left text-sm">
          <AlertTriangle size={20} className="shrink-0 mt-0.5" />
          <p>
            Você não receberá feedback imediato ao clicar nas alternativas. 
            O resultado e os comentários só serão exibidos ao finalizar a prova.
          </p>
        </div>

        <div className="flex flex-col gap-3 w-full max-w-md">
          {hasSavedState && (
            <button 
              onClick={resumeSimulado}
              className="bg-secondary hover:bg-secondary/90 text-secondary-foreground font-bold py-4 px-8 rounded-lg transition-colors flex items-center justify-center gap-2 w-full shadow-lg hover:-translate-y-0.5"
            >
              <RotateCcw size={20} />
              Continuar Simulado em Andamento
            </button>
          )}
          <button 
            onClick={startSimulado}
            className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-4 px-8 rounded-lg transition-colors flex items-center justify-center gap-2 w-full shadow-lg hover:-translate-y-0.5"
          >
            <Play size={20} fill="currentColor" />
            {hasSavedState
              ? (hasCustomFilters ? "Iniciar Novo Personalizado" : "Iniciar Novo Simulado")
              : "Iniciar Simulado Agora"}
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
            {/* @ts-ignore */}
            <AutoSizer>
              {({ height, width }: { height: number; width: number }) => {
                const availableWidth = width;
                let columnCount = 5;
                if (availableWidth > 300) columnCount = 6;
                if (availableWidth > 400) columnCount = 8;
                if (availableWidth > 600) columnCount = 5;
                
                const gap = 8;
                const columnWidth = (availableWidth - gap * (columnCount - 1)) / columnCount;
                const rowHeight = columnWidth;
                const rowCount = Math.ceil(filteredIndices.length / columnCount);

                const Cell = ({ columnIndex, rowIndex, style }: any) => {
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
                    <div style={cellStyle}>
                      <button
                        key={q.id}
                        onClick={() => navigateTo(idx)}
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
                  // @ts-ignore
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
              }}
            </AutoSizer>
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
                          <img 
                            src={`/api/images/${img}`} 
                            alt={`Imagem do Caso ${i+1}`} 
                            className="max-w-full h-auto object-cover hover:scale-[1.02] transition-transform duration-300" 
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              <div className="text-foreground text-body-l leading-relaxed whitespace-pre-wrap mb-8">
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
                      <img 
                        src={`/api/images/${img}`} 
                        alt={`Imagem ${i+1}`} 
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
                      <div className="text-foreground text-body-l leading-relaxed whitespace-pre-wrap">
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
          <div className="bg-card border border-border shadow-lg rounded-xl p-6 max-w-md w-full flex flex-col gap-4 animate-in zoom-in-95 duration-200">
            <h3 className="font-bold text-lg text-foreground">Resumo por Área</h3>
            
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
