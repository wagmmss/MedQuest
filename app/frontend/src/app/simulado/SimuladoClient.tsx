"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { QuestionListItem, QuestionDetail, BatchAttemptItem, BatchAttemptResultItem } from "@/types/api";
import { api } from "@/lib/api";
import { Play, Clock, CheckCircle2, XCircle, ChevronLeft, ChevronRight, FileSignature, AlertTriangle, BookOpen, AlertCircle, RotateCcw } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import confetti from "canvas-confetti";

type SimuladoState = "START" | "LOADING" | "PLAYING" | "SUBMITTING" | "RESULTS";

export function SimuladoClient({
  initialFilters = {}
}: {
  initialFilters?: Record<string, string | string[]>;
}) {
  const [state, setState] = useState<SimuladoState>("START");
  const [queue, setQueue] = useState<QuestionListItem[]>([]);
  
  // Quiz State
  const [currentIndex, setCurrentIndex] = useState(0);
  const [detailsCache, setDetailsCache] = useState<Record<number, QuestionDetail>>({});
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState(false);
  const [showFinishConfirm, setShowFinishConfirm] = useState(false);
  
  // Answers: question_id -> letter
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [resultsMap, setResultsMap] = useState<Record<number, BatchAttemptResultItem>>({});
  
  // Timer State (5 hours = 18000 seconds)
  const TOTAL_TIME = 5 * 60 * 60;
  const [timeLeft, setTimeLeft] = useState(TOTAL_TIME);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

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
        setCurrentIndex(parsed.currentIndex);
        setAnswers(parsed.answers);
        setResultsMap(parsed.resultsMap);
        setTimeLeft(parsed.timeLeft);
        if (parsed.queue.length > 0) {
          loadDetail(parsed.queue[parsed.currentIndex].id);
        }
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
      const hasCustomFilters = Object.keys(initialFilters).length > 0;
      
      let qList: QuestionListItem[];
      if (hasCustomFilters) {
        const limit = initialFilters.limit || "50";
        qList = await api.questions.getList({ ...initialFilters, limit });
      } else {
        qList = await api.questions.getSimuladoUSP();
      }

      if (qList.length === 0) {
        toast.error("Erro: Não há questões suficientes para montar o simulado com esses filtros.");
        setState("START");
        return;
      }
      
      setQueue(qList);
      setCurrentIndex(0);
      setTimeLeft(TOTAL_TIME);
      setAnswers({});
      setResultsMap({});
      setState("PLAYING");
      loadDetail(qList[0].id);
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
      setState("RESULTS");
      setCurrentIndex(0); // Go back to first question to review
      
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

  // Timer Effect
  useEffect(() => {
    if (state === "PLAYING") {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
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

  useEffect(() => {
    if (state === "PLAYING" && timeLeft === 0) {
      if (timerRef.current) clearInterval(timerRef.current);
      submitSimulado();
    }
  }, [timeLeft, state, submitSimulado]);

  const handleSelect = (letter: string) => {
    if (state !== "PLAYING") return;
    const currentQ = queue[currentIndex];
    setAnswers(prev => ({ ...prev, [currentQ.id]: letter }));
  };

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
      setShowFinishConfirm(true);
      return;
    }
    submitSimulado();
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
          {isCustom ? "Simulado Personalizado" : "Simulado Fiel da USP"}
        </h2>
        <p className="text-muted-foreground text-body-m mb-8 max-w-md">
          {isCustom 
            ? "Esta prova irá simular as condições reais de exame usando os filtros que você escolheu."
            : "Esta prova irá simular as condições reais de um exame de acesso direto da USP-SP / USP-RP."}
        </p>
        
        <div className="grid grid-cols-2 gap-4 w-full max-w-md mb-8 text-left">
          <div className="bg-muted rounded-lg p-4">
            <span className="block text-xs font-bold text-muted-foreground uppercase mb-1">Questões</span>
            <span className="text-lg font-bold text-foreground">
              {isCustom ? (initialFilters.limit || "Até 50") : "120"} (Múltipla Escolha)
            </span>
          </div>
          <div className="bg-muted rounded-lg p-4">
            <span className="block text-xs font-bold text-muted-foreground uppercase mb-1">Duração</span>
            <span className="text-lg font-bold text-foreground">5 Horas</span>
          </div>
          {!isCustom && (
            <div className="bg-muted rounded-lg p-4 col-span-2">
              <span className="block text-xs font-bold text-muted-foreground uppercase mb-1">Balanceamento</span>
              <span className="text-sm font-medium text-foreground">
                24 Clínica • 24 Cirurgia • 24 Pediatria • 24 GO • 24 Preventiva
              </span>
            </div>
          )}
        </div>

        <div className="bg-warning/10 text-warning border border-warning/20 rounded-lg p-4 flex items-start gap-3 w-full max-w-md mb-8 text-left text-sm">
          <AlertTriangle size={20} className="shrink-0 mt-0.5" />
          <p>
            Você não receberá feedback imediato ao clicar nas alternativas. 
            O resultado e os comentários dos professores só serão exibidos ao finalizar a prova.
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
            {hasSavedState ? "Iniciar Novo Simulado USP (120 Qs)" : "Iniciar Simulado USP Agora"}
          </button>

          {!isCustom && (
            <div className="mt-4 pt-4 border-t border-border w-full flex flex-col gap-3">
              <span className="text-xs font-bold text-muted-foreground uppercase text-center mb-1">Simulados Temáticos (50 Qs)</span>
              <div className="grid grid-cols-2 gap-3">
                <button 
                  onClick={() => { window.location.href = "/simulado?area=Clínica Médica&limit=50" }}
                  className="bg-muted hover:bg-muted/80 text-foreground font-semibold py-3 px-4 rounded-lg transition-colors text-sm border border-border"
                >
                  Clínica Médica
                </button>
                <button 
                  onClick={() => { window.location.href = "/simulado?area=Cirurgia&limit=50" }}
                  className="bg-muted hover:bg-muted/80 text-foreground font-semibold py-3 px-4 rounded-lg transition-colors text-sm border border-border"
                >
                  Cirurgia Geral
                </button>
                <button 
                  onClick={() => { window.location.href = "/simulado?area=Pediatria&limit=50" }}
                  className="bg-muted hover:bg-muted/80 text-foreground font-semibold py-3 px-4 rounded-lg transition-colors text-sm border border-border"
                >
                  Pediatria
                </button>
                <button 
                  onClick={() => { window.location.href = "/simulado?area=Medicina Preventiva e Social&limit=50" }}
                  className="bg-muted hover:bg-muted/80 text-foreground font-semibold py-3 px-4 rounded-lg transition-colors text-sm border border-border"
                >
                  Preventiva
                </button>
              </div>
            </div>
          )}
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
                {Object.values(resultsMap).filter(r => r.is_correct).length} <span className="text-sm lg:text-lg text-muted-foreground">/ 120</span>
              </div>
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
              </p>
            )}
          </div>
          <div className="p-3 lg:p-4 overflow-y-auto flex-1">
            <div className="grid grid-cols-6 sm:grid-cols-8 lg:grid-cols-5 gap-2">
              {queue.map((q, idx) => {
                const isCurrent = idx === currentIndex;
                const answeredLetter = answers[q.id];
                const res = resultsMap[q.id];

                let btnClass = "bg-muted text-muted-foreground hover:bg-muted/80";
                
                if (isReview) {
                  if (res?.is_correct) btnClass = "bg-success text-success-foreground font-bold";
                  else if (res && !res.is_correct) btnClass = "bg-destructive text-destructive-foreground font-bold";
                  else btnClass = "bg-card border border-dashed border-muted-foreground text-muted-foreground"; // Não respondida/errada
                } else {
                  if (answeredLetter) btnClass = "bg-primary/20 text-primary font-bold";
                }

                if (isCurrent) {
                  btnClass += " ring-2 ring-foreground ring-offset-2 ring-offset-background";
                }

                return (
                  <button
                    key={q.id}
                    onClick={() => navigateTo(idx)}
                    className={clsx(
                      "aspect-square rounded flex flex-col items-center justify-center text-xs transition-all",
                      btnClass
                    )}
                  >
                    <span className={clsx(!isReview && answeredLetter ? "text-[10px]" : "text-xs")}>{idx + 1}</span>
                    {!isReview && answeredLetter && <span className="text-[14px] leading-none">{answeredLetter}</span>}
                  </button>
                );
              })}
            </div>
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
        {detailError ? (
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
            <div className="flex items-center justify-between bg-card border border-border shadow-sm rounded-xl p-3 shrink-0">
              <button 
                onClick={() => navigateTo(currentIndex - 1)}
                disabled={currentIndex === 0}
                className="flex items-center gap-1 px-3 py-1.5 rounded hover:bg-muted disabled:opacity-50 text-sm font-medium"
              >
                <ChevronLeft size={16} /> Anterior
              </button>
              <span className="font-bold text-foreground">
                Questão {currentIndex + 1}
              </span>
              <button 
                onClick={() => navigateTo(currentIndex + 1)}
                disabled={currentIndex === queue.length - 1}
                className="flex items-center gap-1 px-3 py-1.5 rounded hover:bg-muted disabled:opacity-50 text-sm font-medium"
              >
                Próxima <ChevronRight size={16} />
              </button>
            </div>

            <div className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex-1 overflow-y-auto">
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-6">
                <span className="bg-muted px-2 py-1 rounded">{qDetail.institution_code} {qDetail.year}</span>
                <span className="bg-muted px-2 py-1 rounded">{qDetail.area}</span>
                <span className="bg-muted px-2 py-1 rounded">{qDetail.subtema}</span>
              </div>
              
              <div className="text-foreground text-body-l leading-relaxed whitespace-pre-wrap mb-8">
                {qDetail.stem}
              </div>

              {qDetail.images && qDetail.images.length > 0 && (
                <div className="flex flex-col gap-4 mb-8">
                  {qDetail.images.map((img, i) => (
                    <img key={i} src={`/api/images/${img}`} alt={`Imagem ${i+1}`} className="max-w-full rounded-md border border-border" />
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
            </div>
          </div>
        )}
      </div>

      {showFinishConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="bg-card border border-border shadow-lg rounded-xl p-6 max-w-sm w-full flex flex-col gap-4 animate-in zoom-in-95 duration-200">
            <h3 className="font-bold text-lg text-foreground">Atenção!</h3>
            <p className="text-muted-foreground text-sm">
              Você ainda tem {unansweredCount} questões em branco. Deseja finalizar mesmo assim?
            </p>
            <div className="flex justify-end gap-3 mt-2">
              <button
                onClick={() => setShowFinishConfirm(false)}
                className="px-4 py-2 bg-muted text-muted-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  setShowFinishConfirm(false);
                  submitSimulado();
                }}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
              >
                Finalizar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
