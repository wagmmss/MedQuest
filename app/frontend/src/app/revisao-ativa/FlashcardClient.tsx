"use client";

import { useState, useEffect, useCallback } from "react";
import { Flashcard } from "@/types/api";
import { api, OfflineQueuedError } from "@/lib/api";
import { localDb, getLocalOwnerId } from "@/lib/db";
import { normalizeFlashcard } from "@/lib/normalizeFlashcard";
import { Sparkles, CheckCircle2, RotateCcw, BrainCircuit, XCircle, Download, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { motion } from "framer-motion";
import Link from "next/link";

export function FlashcardClient() {
  const [queue, setQueue] = useState<Flashcard[]>([]);
  const [loading, setLoading] = useState(true);
  const [flipped, setFlipped] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [exportingAnki, setExportingAnki] = useState(false);

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
    try {
      const cards = await api.flashcards.getDue(true, signal);
      if (signal?.aborted) return;
      const normalizedCards = cards.map(normalizeFlashcard);
      setQueue(normalizedCards);

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
      if (!signal?.aborted) console.error("Erro ao buscar flashcards", error);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  const handleReview = useCallback(async (confidence: string) => {
    if (queue.length === 0 || submitting) return;
    setSubmitting(true);
    const currentCard = queue[0];

    try {
      await api.flashcards.review(currentCard.id, confidence);
      setQueue(prev => prev.slice(1));
      setFlipped(false);
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
        setQueue(prev => prev.slice(1));
        setFlipped(false);
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
    } finally {
      setSubmitting(false);
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
        <h2 className="text-2xl font-black text-foreground mb-3 tracking-tight">Tudo Revisado!</h2>
        <p className="text-muted-foreground mb-8 text-lg max-w-md">
          Você não tem nenhum flashcard vencido no momento. Volte a estudar para gerar novos cartões com seus erros e fortalecer a memória.
        </p>
        <div className="flex items-center gap-3 flex-wrap justify-center">
          <Link
            href="/estudar"
            className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 px-6 rounded-xl transition-all shadow-lg hover:-translate-y-0.5 flex items-center gap-2 text-sm"
          >
            <span className="material-symbols-outlined text-lg" data-icon="menu_book">menu_book</span>
            Ir para Banco de Questões
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
          <Sparkles size={20} /> Revisão Ativa (IA)
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportAnki}
            disabled={exportingAnki}
            className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground bg-muted hover:bg-muted/80 px-2.5 py-1.5 rounded-lg border border-border transition-all"
            title="Exportar flashcards para o Anki (.txt)"
          >
            {exportingAnki ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
            Exportar Anki (.txt)
          </button>
          <div className="text-sm font-medium text-muted-foreground">
            {queue.length} card{queue.length > 1 ? "s" : ""} restante{queue.length > 1 ? "s" : ""}
          </div>
        </div>
      </div>

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
            <Sparkles size={12} /> Revisão Ativa MedQuest
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
    </div>
  );
}
