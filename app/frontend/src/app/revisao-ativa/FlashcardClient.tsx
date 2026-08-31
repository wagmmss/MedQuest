"use client";

import { useState, useEffect, useCallback } from "react";
import { Flashcard } from "@/types/api";
import { api, OfflineQueuedError } from "@/lib/api";
import { localDb, getLocalOwnerId } from "@/lib/db";
import { normalizeFlashcard } from "@/lib/normalizeFlashcard";
import { Sparkles, CheckCircle2, RotateCcw, BrainCircuit, XCircle, Download, Loader2, AlertTriangle, ExternalLink, CalendarClock } from "lucide-react";
import toast from "react-hot-toast";
import { motion } from "framer-motion";
import Link from "next/link";

export function FlashcardClient() {
  const [queue, setQueue] = useState<Flashcard[]>([]);
  const [loading, setLoading] = useState(true);
  const [flipped, setFlipped] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [exportingAnki, setExportingAnki] = useState(false);
  const [initialDueCount, setInitialDueCount] = useState(0);
  const [upcoming, setUpcoming] = useState<Flashcard[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [lastScheduled, setLastScheduled] = useState<string | null>(null);
  const [showUpcoming, setShowUpcoming] = useState(false);

  const handleExportAnki = async () => {
    setExportingAnki(true);
    try {
      await api.flashcards.exportAnki(false);
      toast.success("Arquivo Anki (.txt) gerado com sucesso! Basta importar no Anki.");
    } catch {
      toast.error("Erro ao exportar flashcards para o Anki.");
    } finally {
      setExportingAnki(false);
    }
  };

  const fetchDue = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setLoadError(null);
    try {
      const [cards, upcomingCards] = await Promise.all([
        api.flashcards.getDue(false, signal),
        api.flashcards.getUpcoming(signal),
      ]);
      if (signal?.aborted) return;
      const normalizedCards = cards.map(normalizeFlashcard);
      setQueue(normalizedCards);
      setInitialDueCount(normalizedCards.length);
      setUpcoming(upcomingCards.map(normalizeFlashcard));

      // Migração automática de cartões legados no IndexedDB local
      if (typeof window !== "undefined" && localDb) {
        const uid = getLocalOwnerId();
        for (const card of normalizedCards) {
          localDb.flashcards
            .where({ _owner_id: uid })
            .filter(f => f.id === card.id)
            .modify({
              front: card.front,
              back: card.back,
            })
            .catch(() => {});
        }
      }
    } catch (error) {
      if (!signal?.aborted) {
        console.error("Erro ao buscar flashcards", error);
        setLoadError("Não foi possível carregar sua fila de revisão.");
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  const handleReview = useCallback(async (confidence: string) => {
    if (queue.length === 0 || submitting) return;
    setSubmitting(true);
    const currentCard = queue[0];

    // Atualização Otimista da Interface
    setQueue(prev => prev.slice(1));
    setFlipped(false);
    
    // Libera o estado de submitting quase imediatamente para não travar a próxima carta
    setTimeout(() => setSubmitting(false), 50);

    try {
      const result = await api.flashcards.review(currentCard.id, confidence);
      setLastScheduled(result.next_review_date);
      if (localDb) {
        try {
          const uid = getLocalOwnerId();
          await localDb.flashcards.where({ _owner_id: uid }).filter(f => f.id === currentCard.id).delete();
        } catch {
          // ignore local cleanup error
        }
      }
    } catch (err) {
      if (err instanceof OfflineQueuedError) {
        toast("Avaliação salva neste dispositivo e será sincronizada quando a conexão voltar.", { icon: "💾" });
        if (localDb) {
          try {
            const uid = getLocalOwnerId();
            await localDb.flashcards.where({ _owner_id: uid }).filter(f => f.id === currentCard.id).delete();
          } catch {
            // ignore local cleanup error
          }
        }
      } else {
        toast.error("Erro ao enviar avaliação.");
      }
    }
  }, [queue, submitting]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      void fetchDue(controller.signal);
    }, 0);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [fetchDue]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (queue.length === 0 || loading || submitting) return;
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      if (!flipped) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setFlipped(true);
        }
      } else {
        if (e.key === "1") {
          e.preventDefault();
          handleReview("errei");
        } else if (e.key === "2") {
          e.preventDefault();
          handleReview("duvida");
        } else if (e.key === "3" || e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleReview("certeza");
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [queue, loading, submitting, flipped, handleReview]);

  const handleReport = async () => {
    if (queue.length === 0 || submitting) return;
    const reason = window.prompt("Qual o problema com este flashcard? (Ex: Erro médico, desatualizado, mal formatado)");
    if (!reason) return;

    setSubmitting(true);
    try {
      await api.flashcards.report(queue[0].id, reason);
      toast.success("Obrigado! O flashcard foi reportado e será auditado.");
      setQueue(prev => prev.slice(1));
      setFlipped(false);
    } catch {
      toast.error("Erro ao reportar flashcard.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto w-full flex flex-col items-center gap-6 pb-12 animate-in fade-in duration-500">
        <div className="w-full flex items-center justify-between mb-2 opacity-50">
          <div className="flex items-center gap-2 text-purple-500 font-bold">
            <Sparkles size={20} /> Revisão Ativa (IA)
          </div>
          <div className="text-sm font-medium text-muted-foreground">
            Buscando...
          </div>
        </div>
        <div className="w-full min-h-[300px] bg-card border border-border shadow-1 rounded-2xl p-8 flex flex-col items-center justify-center gap-6">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-purple-500/10 rounded-full" />
            <div className="w-16 h-16 border-4 border-transparent border-t-purple-500 border-r-purple-500 rounded-full animate-spin absolute inset-0" />
            <div className="absolute inset-0 flex items-center justify-center text-purple-500">
              <BrainCircuit size={20} className="animate-pulse" />
            </div>
          </div>
          <p className="text-muted-foreground font-medium animate-pulse">Sincronizando seus flashcards...</p>
        </div>
      </div>
    );
  }

  if (queue.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-card border border-border shadow-1 rounded-xl p-12 max-w-2xl mx-auto w-full text-center flex flex-col items-center"
      >
        <motion.div 
          animate={{ scale: [1, 1.1, 1] }} 
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="w-24 h-24 bg-success/20 text-success rounded-full flex items-center justify-center mx-auto mb-6"
        >
          <CheckCircle2 size={48} />
        </motion.div>
        <h2 className="text-2xl font-black text-foreground mb-3 tracking-tight">
          {initialDueCount > 0 ? "Revisões de hoje concluídas" : "Nenhuma revisão vencida"}
        </h2>
        <p className="text-muted-foreground mb-8 text-lg max-w-md">
          {initialDueCount > 0
            ? `Você revisou ${initialDueCount} ${initialDueCount === 1 ? "cartão" : "cartões"}.`
            : "Você não tem flashcards vencidos no momento."}
        </p>
        {loadError && (
          <div className="mb-6 w-full rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-left text-sm text-destructive flex items-center gap-2">
            <AlertTriangle size={18} /> {loadError}
            <button onClick={() => void fetchDue()} className="ml-auto font-bold underline">Tentar novamente</button>
          </div>
        )}
        {!loadError && upcoming[0] && (
          <p className="mb-6 text-sm text-muted-foreground flex items-center gap-2"><CalendarClock size={16} /> Próximo cartão: {new Date(upcoming[0].next_review_date).toLocaleDateString("pt-BR")}</p>
        )}
        <div className="flex items-center gap-3 flex-wrap justify-center">
          <Link
            href="/estudar"
            className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 px-6 rounded-xl transition-all shadow-lg hover:-translate-y-0.5 flex items-center gap-2 text-sm"
          >
            <span className="material-symbols-outlined text-lg" data-icon="menu_book">menu_book</span>
              Estudar questões
          </Link>
          <button
            onClick={handleExportAnki}
            disabled={exportingAnki}
            className="bg-muted hover:bg-muted/80 text-foreground font-semibold py-3 px-5 rounded-xl border border-border transition-all flex items-center gap-2 text-sm"
          >
            {exportingAnki ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Exportar Todos para Anki (.txt)
          </button>
        </div>
      </motion.div>
    );
  }

  const current = queue[0];

  return (
    <div className="max-w-3xl mx-auto w-full flex flex-col items-center gap-6 pb-12">
      <div className="w-full flex items-center justify-between mb-2 flex-wrap gap-2">
        <div className="flex items-center gap-2 text-purple-500 font-bold">
          <BrainCircuit size={20} /> Revisões de hoje
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm font-medium text-muted-foreground">
            {queue.length} de {initialDueCount} restante{queue.length > 1 ? "s" : ""}
          </div>
        </div>
      </div>

      {lastScheduled && (
        <div className="w-full rounded-lg border border-success/30 bg-success/10 px-4 py-2 text-sm font-medium text-success">
          Cartão agendado para {new Date(lastScheduled).toLocaleDateString("pt-BR")}.
        </div>
      )}

      {/* Cartão */}
      <div 
        className="w-full min-h-[300px] bg-card border border-border shadow-1 rounded-2xl p-8 flex flex-col items-center justify-center relative cursor-pointer hover:border-purple-500/50 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
        onClick={() => !flipped && setFlipped(true)}
        onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && !flipped) { e.preventDefault(); setFlipped(true); } }}
        role="button"
        tabIndex={0}
        aria-label={flipped ? "Flashcard revelado" : "Clique para revelar o flashcard"}
      >
          {current.is_ai_generated && (
          <div className="absolute top-4 left-4 text-xs font-semibold text-purple-500 bg-purple-500/10 border border-purple-500/20 px-2.5 py-1 rounded-full flex items-center gap-1.5" title="Este flashcard foi gerado e estruturado a partir do seu histórico de erros.">
            <Sparkles size={12} /> Criado com assistência de IA
          </div>
        )}

        <div className="w-full text-base md:text-lg font-medium text-foreground text-left leading-relaxed whitespace-pre-line my-4">
          {current.front.split(/({{c1::.*?}})/).map((part, i) => {
            if (part.startsWith("{{c1::") && part.endsWith("}}")) {
              const content = part.substring(6, part.length - 2);
              if (!flipped) {
                return (
                  <span key={i} className="inline-block px-3 py-1 bg-purple-500/15 text-purple-600 font-bold border-b-2 border-purple-500 rounded mx-1 select-none animate-pulse">
                    [...]
                  </span>
                );
              }
              return (
                <span key={i} className="inline-block px-2.5 py-1 bg-purple-500/20 text-purple-600 border border-purple-500/40 rounded-lg mx-1 font-bold animate-in fade-in zoom-in-95 duration-200">
                  {content}
                </span>
              );
            }
            return <span key={i}>{part}</span>;
          })}
        </div>

        {flipped && current.back && (
          <div className="mt-6 pt-6 border-t border-border w-full text-left animate-in slide-in-from-bottom-3 fade-in duration-300">
            <div className="bg-muted/40 p-4 rounded-xl border border-border/60 text-sm md:text-base text-foreground leading-relaxed whitespace-pre-line">
              {current.back}
            </div>
            {current.source_context && (
              <p className="mt-3 text-xs font-semibold text-purple-600/80 uppercase tracking-wider bg-purple-500/10 py-1 px-3 rounded-full inline-block">
                Referência: {current.source_context}
              </p>
            )}
            <div className="mt-4 flex flex-wrap items-center gap-3 text-xs font-semibold text-muted-foreground">
              {(current.area || current.subtema) && <span>{[current.area, current.subtema].filter(Boolean).join(" · ")}</span>}
              <Link href={`/estudar?id=${current.question_id}`} className="inline-flex items-center gap-1 text-primary hover:underline"><ExternalLink size={13} /> Ver questão de origem</Link>
            </div>
          </div>
        )}

        {!flipped && (
          <div className="absolute bottom-6 text-sm font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
            <RotateCcw size={16} /> Clique para Revelar
          </div>
        )}
        
        {flipped && (
          <button 
            className="absolute top-4 right-4 text-xs font-semibold text-muted-foreground hover:text-destructive flex items-center gap-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive focus-visible:ring-offset-2 rounded"
            onClick={(e) => {
              e.stopPropagation();
              handleReport();
            }}
            title="Reportar Erro no Flashcard"
            aria-label="Reportar Erro no Flashcard"
          >
            <XCircle size={14} /> Reportar
          </button>
        )}
      </div>

      {/* Controles FSRS */}
      {flipped && (
        <div className="flex w-full gap-4 mt-4 animate-in slide-in-from-bottom-4 fade-in duration-300">
          <button 
            title="O algoritmo agendará a revisão deste flashcard para amanhã, já que você não conseguiu se lembrar do conceito."
            onClick={() => handleReview("errei")}
            disabled={submitting}
            className="flex-1 bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/20 font-bold py-4 rounded-xl transition-colors flex flex-col items-center justify-center gap-1 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive focus-visible:ring-offset-2"
          >
            <div className="flex items-center gap-2"><XCircle size={20} /> Errei</div>
            <span className="text-[10px] font-normal opacity-80 uppercase tracking-widest mt-1">Volta amanhã (1)</span>
          </button>
          <button 
            title="O algoritmo aplicará um multiplicador de intervalo moderado, agendando uma revisão em breve para fixar este conceito difícil."
            onClick={() => handleReview("duvida")}
            disabled={submitting}
            className="flex-1 bg-warning/10 hover:bg-warning/20 text-warning border border-warning/20 font-bold py-4 rounded-xl transition-colors flex flex-col items-center justify-center gap-1 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-warning focus-visible:ring-offset-2"
          >
            <div className="flex items-center gap-2"><BrainCircuit size={20} /> Difícil</div>
            <span className="text-[10px] font-normal opacity-80 uppercase tracking-widest mt-1">Bom tempo (2)</span>
          </button>
          <button 
            title="O algoritmo entende que este flashcard está bem consolidado na sua memória e estenderá significativamente o intervalo para a próxima revisão."
            onClick={() => handleReview("certeza")}
            disabled={submitting}
            className="flex-1 bg-success/10 hover:bg-success/20 text-success border border-success/20 font-bold py-4 rounded-xl transition-colors flex flex-col items-center justify-center gap-1 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-success focus-visible:ring-offset-2"
          >
            <div className="flex items-center gap-2"><CheckCircle2 size={20} /> Fácil</div>
            <span className="text-[10px] font-normal opacity-80 uppercase tracking-widest mt-1">Revisa depois (3)</span>
          </button>
        </div>
      )}

      <div className="w-full border-t border-border pt-5 flex flex-wrap items-center justify-between gap-3 text-sm">
        <button type="button" onClick={() => setShowUpcoming(value => !value)} className="font-semibold text-primary hover:underline">
          {showUpcoming ? "Ocultar próximos cartões" : `Ver próximos cartões${upcoming.length ? ` (${upcoming.length})` : ""}`}
        </button>
        <button onClick={handleExportAnki} disabled={exportingAnki} className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground">
          {exportingAnki ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />} Exportar para Anki
        </button>
      </div>
      {showUpcoming && (
        <div className="w-full rounded-xl border border-border bg-muted/20 p-4 text-sm">
          <p className="font-bold text-foreground mb-3">Próximos cartões — consulta apenas</p>
          {upcoming.length ? <ul className="space-y-2 text-muted-foreground">{upcoming.slice(0, 5).map(card => <li key={card.id} className="flex justify-between gap-3"><span className="truncate">{card.source_context || card.subtema || "Flashcard"}</span><span className="shrink-0">{new Date(card.next_review_date).toLocaleDateString("pt-BR")}</span></li>)}</ul> : <p className="text-muted-foreground">Não há cartões futuros programados.</p>}
        </div>
      )}
    </div>
  );
}
