"use client";

import { useState, useEffect, useCallback } from "react";
import { Flashcard } from "@/types/api";
import { api } from "@/lib/api";
import { Sparkles, CheckCircle2, RotateCcw, BrainCircuit, XCircle, ArrowRight } from "lucide-react";

export function FlashcardClient() {
  const [queue, setQueue] = useState<Flashcard[]>([]);
  const [loading, setLoading] = useState(true);
  const [flipped, setFlipped] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchDue = useCallback(async () => {
    setLoading(true);
    try {
      const cards = await api.flashcards.getDue();
      setQueue(cards);
    } catch (e) {
      console.error("Erro ao buscar flashcards", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDue();
  }, [fetchDue]);

  const handleReview = async (confidence: string) => {
    if (queue.length === 0 || submitting) return;
    setSubmitting(true);
    
    try {
      await api.flashcards.review(queue[0].id, confidence);
      
      // Remove da fila e vira
      setQueue(prev => prev.slice(1));
      setFlipped(false);
    } catch (e) {
      alert("Erro ao enviar avaliação.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="w-10 h-10 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
        <p className="text-muted-foreground font-medium">Buscando seus flashcards...</p>
      </div>
    );
  }

  if (queue.length === 0) {
    return (
      <div className="bg-card border border-border shadow-1 rounded-xl p-10 max-w-2xl mx-auto w-full text-center">
        <div className="w-20 h-20 bg-success/20 text-success rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 size={40} />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-3">Tudo Revisado!</h2>
        <p className="text-muted-foreground mb-8">
          Você não tem nenhum flashcard vencido no momento. Volte a estudar para gerar novos cartões com seus erros!
        </p>
      </div>
    );
  }

  const current = queue[0];

  return (
    <div className="max-w-3xl mx-auto w-full flex flex-col items-center gap-6 pb-12">
      <div className="w-full flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-purple-500 font-bold">
          <Sparkles size={20} /> Revisão Ativa (IA)
        </div>
        <div className="text-sm font-medium text-muted-foreground">
          {queue.length} card{queue.length > 1 ? "s" : ""} restante{queue.length > 1 ? "s" : ""}
        </div>
      </div>

      {/* Cartão */}
      <div 
        className="w-full min-h-[300px] bg-card border border-border shadow-1 rounded-2xl p-8 flex flex-col items-center justify-center relative cursor-pointer hover:border-purple-500/50 transition-colors"
        onClick={() => !flipped && setFlipped(true)}
      >
        {current.stem && (
          <div className="w-full mb-8 pb-6 border-b border-border/50 text-muted-foreground text-sm md:text-base leading-relaxed text-left opacity-80">
            <span className="font-bold text-foreground/50 uppercase text-xs tracking-wider mb-3 block">Questão Original (Contexto)</span>
            <div dangerouslySetInnerHTML={{ __html: current.stem }} />
          </div>
        )}

        <p className="text-2xl md:text-3xl font-medium text-foreground text-center leading-relaxed">
          {current.front.split(/({{c1::.*?}})/).map((part, i) => {
            if (part.startsWith("{{c1::") && part.endsWith("}}")) {
              const content = part.substring(6, part.length - 2);
              if (!flipped) {
                return <span key={i} className="inline-block px-3 py-1 bg-muted text-transparent border-b-2 border-foreground mx-1 rounded select-none">[{content}]</span>;
              }
              return <span key={i} className="inline-block px-2 py-1 bg-purple-500/20 text-purple-600 border border-purple-500/30 rounded mx-1 font-bold animate-in fade-in zoom-in-95 duration-200">{content}</span>;
            }
            return <span key={i}>{part}</span>;
          })}
        </p>

        {flipped && current.back && (
          <div className="mt-8 pt-8 border-t border-border w-full text-center animate-in slide-in-from-bottom-4 fade-in duration-300">
            <p className="text-muted-foreground text-body-m">{current.back}</p>
          </div>
        )}

        {!flipped && (
          <div className="absolute bottom-6 text-sm font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
            <RotateCcw size={16} /> Clique para Revelar
          </div>
        )}
      </div>

      {/* Controles FSRS */}
      {flipped && (
        <div className="flex w-full gap-4 mt-4 animate-in slide-in-from-bottom-4 fade-in duration-300">
          <button 
            onClick={() => handleReview("errei")}
            disabled={submitting}
            className="flex-1 bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/20 font-bold py-4 rounded-xl transition-colors flex flex-col items-center justify-center gap-1 disabled:opacity-50"
          >
            <XCircle size={24} />
            Errei (Redefinir)
          </button>
          <button 
            onClick={() => handleReview("duvida")}
            disabled={submitting}
            className="flex-1 bg-warning/10 hover:bg-warning/20 text-warning border border-warning/20 font-bold py-4 rounded-xl transition-colors flex flex-col items-center justify-center gap-1 disabled:opacity-50"
          >
            <BrainCircuit size={24} />
            Difícil
          </button>
          <button 
            onClick={() => handleReview("certeza")}
            disabled={submitting}
            className="flex-1 bg-success/10 hover:bg-success/20 text-success border border-success/20 font-bold py-4 rounded-xl transition-colors flex flex-col items-center justify-center gap-1 disabled:opacity-50"
          >
            <CheckCircle2 size={24} />
            Fácil
          </button>
        </div>
      )}
    </div>
  );
}
