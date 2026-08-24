"use client";

import React, { useMemo, useState } from "react";
import { 
  Sparkles, 
  Stethoscope, 
  CheckCircle2, 
  XCircle, 
  BookOpen, 
  Award,
  AlertCircle,
  Bot,
  Send,
  Loader2,
  HelpCircle,
  Lightbulb
} from "lucide-react";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

interface ExplanationViewerProps {
  explanation: string | null | undefined;
  medicalReferences?: string | null;
  correctLetter?: string | null;
  questionId?: number;
  userLetter?: string;
}

interface ParsedSection {
  gabarito?: string;
  puloDoGato?: string;
  raciocinioClinico?: string;
  alternativaCorreta?: {
    letter?: string;
    text: string;
  };
  distratores?: Array<{
    letter: string;
    text: string;
  }>;
  fallbackText?: string;
}

/**
 * Helper to render inline markdown text (bold **text**, italic *text*, math $...$)
 */
function renderInlineFormattedText(text: string) {
  if (!text) return null;

  // Split by bold tokens **...**
  const parts = text.split(/(\*\*[^*]+\*\*|\$[^\$]+\$)/g);

  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className="font-bold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("$") && part.endsWith("$")) {
      return (
        <span key={idx} className="font-mono italic px-1 bg-muted/60 rounded text-sm text-primary">
          {part.slice(1, -1)}
        </span>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

/**
 * Parses structured markdown explanations into distinct semantic sections
 */
function parseExplanation(raw: string): ParsedSection {
  const clean = raw.replace(/\\n/g, "\n").trim();
  if (!clean) return { fallbackText: "Nenhum comentário disponível para esta questão." };

  const parsed: ParsedSection = {};

  // 1. Extract Gabarito
  const gabaritoMatch = clean.match(/(?:\*\*Gabarito\*\*|Gabarito):\s*([^\n]+)/i);
  if (gabaritoMatch) {
    parsed.gabarito = gabaritoMatch[1].trim();
  }

  // 2. Extract Pulo do Gato
  const puloMatch = clean.match(/(?:\*\*Pulo do Gato\*\*|\*\*Pulo_do_Gato\*\*|Pulo do Gato):\s*([\s\S]*?)(?=(?:\n\s*\*\*(?:Raciocínio Clínico|Alternativa Correta|Alternativa Incorreta|Por que a|Alternativas Incorretas|Distratores)\*\*|\n\s*Raciocínio Clínico|\n\s*Alternativa Correta|\n\s*Alternativas Incorretas|$))/i);
  if (puloMatch) {
    parsed.puloDoGato = puloMatch[1].trim();
  }

  // 3. Extract Raciocínio Clínico (if present)
  const raciocinioMatch = clean.match(/(?:\*\*Raciocínio Clínico\*\*|Raciocínio Clínico):\s*([\s\S]*?)(?=(?:\n\s*\*\*(?:Alternativa Correta|Alternativa Incorreta|Por que a|Alternativas Incorretas|Distratores)\*\*|\n\s*Alternativa Correta|\n\s*Alternativas Incorretas|$))/i);
  if (raciocinioMatch) {
    parsed.raciocinioClinico = raciocinioMatch[1].trim();
  }

  // 4. Extract Alternativa Correta / Por que é correta
  const corretaMatch = clean.match(/(?:\*\*(?:Alternativa Correta|Por que a Letra [A-E] é a Correta\??)\*\*(?:\s*\(([A-E])\))?|Alternativa Correta(?:\s*\(([A-E])\))?):\s*([\s\S]*?)(?=(?:\n\s*\*\*(?:Alternativas Incorretas|Distratores|Análise dos Distratores)\*\*|\n\s*Alternativas Incorretas|\n\s*Distratores|$))/i);
  if (corretaMatch) {
    const letter = corretaMatch[1] || corretaMatch[2];
    parsed.alternativaCorreta = {
      letter: letter ? letter.trim() : undefined,
      text: corretaMatch[3].trim()
    };
  }

  // 5. Extract Distratores / Alternativas Incorretas
  const incorretasMatch = clean.match(/(?:\*\*(?:Alternativas Incorretas|Distratores|Análise dos Distratores)\*\*|Alternativas Incorretas|Distratores):\s*([\s\S]*)$/i);
  if (incorretasMatch) {
    const rawDistratores = incorretasMatch[1].trim();
    const distratorLines = rawDistratores.split(/\n(?=(?:[-•*]\s*(?:\*\*)?Letra\s+[A-E]|(?:\*\*)?Letra\s+[A-E]))/i);

    const distratoresList: Array<{ letter: string; text: string }> = [];

    for (const item of distratorLines) {
      const matchItem = item.match(/^(?:[-•*]\s*)?(?:\*\*)?Letra\s+([A-E](?:\s+e\s+[A-E])?)(?:\*\*)?(?:\s*\([^)]+\))?:\s*([\s\S]*)$/i);
      if (matchItem) {
        distratoresList.push({
          letter: matchItem[1].trim(),
          text: matchItem[2].trim()
        });
      } else if (item.trim()) {
        distratoresList.push({
          letter: "•",
          text: item.replace(/^[-•*]\s*/, "").trim()
        });
      }
    }

    if (distratoresList.length > 0) {
      parsed.distratores = distratoresList;
    }
  }

  // Fallback if structure parsing didn't find standard sections
  if (!parsed.puloDoGato && !parsed.alternativaCorreta && !parsed.distratores) {
    parsed.fallbackText = clean;
  }

  return parsed;
}

export function ExplanationViewer({ 
  explanation, 
  medicalReferences,
  correctLetter,
  questionId,
  userLetter
}: ExplanationViewerProps) {
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const handleAskPreceptor = async (customPrompt?: string) => {
    const questionText = customPrompt || aiQuestion;
    if (!questionId) return;
    setLoadingAi(true);
    try {
      const res = await api.questions.askAI(questionId, questionText, userLetter);
      setAiAnswer(res.answer);
      if (!customPrompt) setAiQuestion("");
    } catch {
      toast.error("Não foi possível consultar o Preceptor IA no momento.");
    } finally {
      setLoadingAi(false);
    }
  };

  const parsed = useMemo(() => {
    if (!explanation) return null;
    return parseExplanation(explanation);
  }, [explanation]);

  const renderPreceptorWidget = () => {
    if (!questionId) return null;
    return (
      <div className="mt-6 rounded-2xl bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-primary/10 border border-purple-500/20 p-5 md:p-6 shadow-sm">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300 font-bold text-sm md:text-base">
            <Bot size={20} className="text-purple-600 dark:text-purple-400" />
            <span>Preceptor Clínico IA (Gemini 3.7 Flash)</span>
          </div>
          <span className="text-[11px] font-semibold text-purple-600 bg-purple-500/10 px-2.5 py-0.5 rounded-full border border-purple-500/20">
            Google AI
          </span>
        </div>

        <p className="text-xs md:text-sm text-muted-foreground mb-4">
          Ficou com dúvida sobre a fisiopatologia ou a pegadinha da banca? Peça uma explicação aprofundada ao Preceptor IA.
        </p>

        {/* Sugestões rápidas */}
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            type="button"
            disabled={loadingAi}
            onClick={() => handleAskPreceptor("Explique o raciocínio fisiopatológico e a conduta padrão-ouro.")}
            className="text-xs font-medium bg-background/80 hover:bg-muted text-foreground border border-border px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <Lightbulb size={12} className="text-amber-500" /> Raciocínio Fisiopatológico
          </button>
          <button
            type="button"
            disabled={loadingAi}
            onClick={() => handleAskPreceptor("Por que as alternativas incorretas são as maiores pegadinhas nesta questão?")}
            className="text-xs font-medium bg-background/80 hover:bg-muted text-foreground border border-border px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <HelpCircle size={12} className="text-purple-500" /> Armadilhas dos Distratores
          </button>
        </div>

        {/* Input customizado */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Faça uma pergunta específica para o Preceptor..."
            value={aiQuestion}
            onChange={(e) => setAiQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !loadingAi && aiQuestion.trim()) {
                e.preventDefault();
                handleAskPreceptor();
              }
            }}
            className="flex-1 bg-background/90 border border-border rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500/40"
          />
          <button
            type="button"
            disabled={loadingAi || !aiQuestion.trim()}
            onClick={() => handleAskPreceptor()}
            className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white p-2.5 rounded-xl transition-colors flex items-center justify-center shrink-0 shadow-sm cursor-pointer"
            aria-label="Enviar pergunta ao Preceptor IA"
          >
            {loadingAi ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>

        {/* Resposta da IA */}
        {aiAnswer && (
          <div className="mt-4 pt-4 border-t border-purple-500/20 bg-background/80 p-4 rounded-xl border border-border text-sm md:text-base text-foreground leading-relaxed whitespace-pre-wrap animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex items-center gap-1.5 text-xs font-bold text-purple-600 dark:text-purple-400 uppercase tracking-wider mb-2">
              <Sparkles size={14} /> Resposta do Preceptor Virtual
            </div>
            {renderInlineFormattedText(aiAnswer)}
          </div>
        )}
      </div>
    );
  };

  if (!explanation || !parsed) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-5 rounded-xl bg-muted/40 border border-border text-muted-foreground">
          <AlertCircle size={18} />
          <span>Nenhum comentário oficial disponível para esta questão.</span>
        </div>
        {renderPreceptorWidget()}
      </div>
    );
  }

  // If structured parsing succeeded
  if (!parsed.fallbackText) {
    return (
      <div className="space-y-5">
        {/* Top Banner: Gabarito */}
        {parsed.gabarito && (
          <div className="flex items-center gap-3 bg-primary/10 border border-primary/20 text-primary px-4 py-2.5 rounded-xl w-fit">
            <Award size={18} className="text-primary shrink-0" />
            <span className="font-bold text-sm md:text-base">
              Gabarito Oficial: <span className="underline decoration-2 underline-offset-2">{parsed.gabarito}</span>
            </span>
          </div>
        )}

        {/* 1. PULO DO GATO (Âncora de Alto Rendimento) */}
        {parsed.puloDoGato && (
          <div className="relative overflow-hidden rounded-2xl bg-amber-500/10 border border-amber-500/25 p-5 md:p-6 text-foreground shadow-sm">
            <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 font-bold text-sm md:text-base uppercase tracking-wider mb-2">
              <Sparkles size={18} className="shrink-0 animate-pulse" />
              <span>Pulo do Gato</span>
            </div>
            <div className="text-foreground text-sm md:text-base leading-relaxed font-medium">
              {renderInlineFormattedText(parsed.puloDoGato)}
            </div>
          </div>
        )}

        {/* 2. RACIOCÍNIO CLÍNICO (Se presente) */}
        {parsed.raciocinioClinico && (
          <div className="rounded-2xl bg-blue-500/10 border border-blue-500/20 p-5 md:p-6 text-foreground">
            <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400 font-bold text-sm md:text-base uppercase tracking-wider mb-2">
              <Stethoscope size={18} className="shrink-0" />
              <span>Raciocínio Clínico</span>
            </div>
            <div className="text-foreground text-sm md:text-base leading-relaxed whitespace-pre-wrap">
              {renderInlineFormattedText(parsed.raciocinioClinico)}
            </div>
          </div>
        )}

        {/* 3. ALTERNATIVA CORRETA (Fundamentação Teórica) */}
        {parsed.alternativaCorreta && (
          <div className="rounded-2xl bg-emerald-500/10 border border-emerald-500/25 p-5 md:p-6 text-foreground">
            <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 font-bold text-sm md:text-base uppercase tracking-wider mb-2">
              <CheckCircle2 size={18} className="shrink-0" />
              <span>
                Alternativa Correta {parsed.alternativaCorreta.letter ? `(${parsed.alternativaCorreta.letter})` : (correctLetter ? `(${correctLetter})` : "")}
              </span>
            </div>
            <div className="text-foreground text-sm md:text-base leading-relaxed whitespace-pre-wrap">
              {renderInlineFormattedText(parsed.alternativaCorreta.text)}
            </div>
          </div>
        )}

        {/* 4. ANÁLISE DOS DISTRATORES (Alternativas Incorretas) */}
        {parsed.distratores && parsed.distratores.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground font-bold text-xs uppercase tracking-wider px-1">
              <XCircle size={14} className="text-rose-500" />
              <span>Análise das Alternativas Incorretas</span>
            </div>
            <div className="grid gap-2.5">
              {parsed.distratores.map((dist, idx) => (
                <div 
                  key={idx} 
                  className="rounded-xl border border-border bg-card/60 p-4 transition-all hover:bg-muted/30"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex h-6 min-w-6 items-center justify-center rounded-md bg-rose-500/15 text-rose-700 dark:text-rose-400 font-bold text-xs shrink-0 mt-0.5">
                      {dist.letter}
                    </span>
                    <div className="text-sm md:text-base text-foreground leading-relaxed">
                      {renderInlineFormattedText(dist.text)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Referências Médicas (se houver) */}
        {medicalReferences && (
          <div className="mt-6 pt-5 border-t border-border">
            <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
              <BookOpen size={14} />
              <span>Referências e Diretrizes</span>
            </div>
            <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap bg-muted/30 p-4 rounded-xl border border-border">
              {medicalReferences}
            </div>
          </div>
        )}

        {/* Preceptor Clínico IA */}
        {renderPreceptorWidget()}
      </div>
    );
  }

  // Fallback: render formatted raw markdown
  return (
    <div className="space-y-4">
      <div className="text-foreground text-sm md:text-base leading-relaxed whitespace-pre-wrap">
        {renderInlineFormattedText(parsed.fallbackText || "")}
      </div>

      {medicalReferences && (
        <div className="mt-6 pt-5 border-t border-border">
          <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
            <BookOpen size={14} />
            <span>Referências e Diretrizes</span>
          </div>
          <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap bg-muted/30 p-4 rounded-xl border border-border">
            {medicalReferences}
          </div>
        </div>
      )}

      {/* Preceptor Clínico IA */}
      {renderPreceptorWidget()}
    </div>
  );
}
