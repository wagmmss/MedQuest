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
  Lightbulb,
  Maximize,
  X
} from "lucide-react";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import { FormattedContent } from "@/components/FormattedContent";

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
 * Helper to render inline markdown text (bold **text**, italic *text*, math $...$, and images ![alt](src))
 */
function renderInlineFormattedText(text: string, onImageClick?: (src: string) => void) {
  if (!text) return null;

  // Split by markdown image !\[alt\](src), bold **...**, and math $...$
  const parts = text.split(/(!\[[^\]]*\]\([^)]+\)|\*\*[^*]+\*\*|\$[^\$]+\$)/g);

  return parts.map((part, idx) => {
    const imgMatch = part.match(/^!\[(.*?)\]\((.*?)\)$/);
    if (imgMatch) {
      const alt = imgMatch[1] || "Figura Explicativa";
      const src = imgMatch[2];
      return (
        <div key={idx} className="my-3 flex flex-col items-center">
          <div 
            onClick={() => onImageClick?.(src)}
            className="relative group rounded-xl overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all max-w-md w-full"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img 
              src={src} 
              alt={alt}
              className="w-full h-auto object-contain max-h-[350px] mx-auto hover:scale-[1.02] transition-transform duration-300"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center pointer-events-none">
              <Maximize size={20} className="text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-md" />
            </div>
          </div>
          {alt && alt !== "image.png" && alt !== "Figura Explicativa" && (
            <span className="text-xs text-muted-foreground mt-1 text-center italic">{alt}</span>
          )}
        </div>
      );
    }
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

  // Helper to find header positions
  const distMatch = clean.match(/(?:\n|^)\s*\*\*(?:Análise dos Distratores|Distratores|Alternativas Incorretas|Análise das Alternativas Incorretas|Alternativas Verdadeiras)\*\*:/i);
  const corrMatch = clean.match(/(?:\n|^)\s*\*\*(?:Por que a Letra [A-E] [eé] a Correta\??|Por que a Letra [A-E] [eé] a Incorreta\??|Alternativa Correta(?:\s*\([A-E]\))?)\*\*:/i);
  const racMatch = clean.match(/(?:\n|^)\s*\*\*(?:Raciocínio Clínico(?:[^\*:]*)?|Fundamentação Teórica|Discussão do Caso|Comentário do Caso|Padrão de Resposta(?:[^\*:]*)?|Resolução Detalhada(?:[^\*:]*)?)\*\*:/i);
  const puloMatch = clean.match(/(?:\n|^)\s*(?:\*\*Pulo do Gato\*\*|\*\*Pulo_do_Gato\*\*|Pulo do Gato):\s*/i);

  // 2. Extract Distratores
  if (distMatch && distMatch.index !== undefined) {
    const rawDistratores = clean.slice(distMatch.index + distMatch[0].length).trim();
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

  // 3. Extract Alternativa Correta
  if (corrMatch && corrMatch.index !== undefined) {
    const endIdx = distMatch && distMatch.index !== undefined && distMatch.index > corrMatch.index ? distMatch.index : clean.length;
    const rawCorr = clean.slice(corrMatch.index + corrMatch[0].length, endIdx).trim();
    const letterMatch = corrMatch[0].match(/([A-E])/i);
    parsed.alternativaCorreta = {
      letter: letterMatch ? letterMatch[1] : undefined,
      text: rawCorr
    };
  }

  // 4. Extract Raciocínio Clínico
  if (racMatch && racMatch.index !== undefined) {
    let endIdx = clean.length;
    if (corrMatch && corrMatch.index !== undefined && corrMatch.index > racMatch.index) {
      endIdx = corrMatch.index;
    } else if (distMatch && distMatch.index !== undefined && distMatch.index > racMatch.index) {
      endIdx = distMatch.index;
    }
    parsed.raciocinioClinico = clean.slice(racMatch.index + racMatch[0].length, endIdx).trim();
  }

  // 5. Extract Pulo do Gato
  if (puloMatch && puloMatch.index !== undefined) {
    let endIdx = clean.length;
    if (racMatch && racMatch.index !== undefined && racMatch.index > puloMatch.index) {
      endIdx = racMatch.index;
    } else if (corrMatch && corrMatch.index !== undefined && corrMatch.index > puloMatch.index) {
      endIdx = corrMatch.index;
    } else if (distMatch && distMatch.index !== undefined && distMatch.index > puloMatch.index) {
      endIdx = distMatch.index;
    }
    const puloText = clean.slice(puloMatch.index + puloMatch[0].length, endIdx).trim();
    parsed.puloDoGato = puloText;
  }

  // Deduplicate: if raciocinioClinico starts with puloDoGato, remove the duplicate prefix
  if (parsed.puloDoGato && parsed.raciocinioClinico && parsed.raciocinioClinico.startsWith(parsed.puloDoGato)) {
    parsed.raciocinioClinico = parsed.raciocinioClinico.slice(parsed.puloDoGato.length).replace(/^[.:,\s-]+/, "").trim();
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
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);

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
            {renderInlineFormattedText(aiAnswer, setEnlargedImage)}
          </div>
        )}
      </div>
    );
  };

  const renderZoomModal = () => {
    if (!enlargedImage) return null;
    return (
      <div 
        className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200"
        onClick={() => setEnlargedImage(null)}
      >
        <div className="relative max-w-5xl max-h-[90vh] flex flex-col items-center">
          <button 
            type="button"
            onClick={() => setEnlargedImage(null)}
            className="absolute -top-12 right-0 text-white/80 hover:text-white bg-black/50 p-2 rounded-full transition-colors cursor-pointer"
            aria-label="Fechar visualização"
          >
            <X size={24} />
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img 
            src={enlargedImage} 
            alt="Figura Ampliada"
            className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl border border-white/10"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
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
        {renderZoomModal()}
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
              <FormattedContent content={parsed.puloDoGato} onImageClick={setEnlargedImage} />
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
            <div className="text-foreground text-sm md:text-base leading-relaxed">
              <FormattedContent content={parsed.raciocinioClinico} onImageClick={setEnlargedImage} />
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
            <div className="text-foreground text-sm md:text-base leading-relaxed">
              <FormattedContent content={parsed.alternativaCorreta.text} onImageClick={setEnlargedImage} />
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
                    <div className="text-sm md:text-base text-foreground leading-relaxed flex-1">
                      <FormattedContent content={dist.text} onImageClick={setEnlargedImage} />
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
        {renderZoomModal()}
      </div>
    );
  }

  // Fallback: render formatted raw markdown
  return (
    <div className="space-y-4">
      <div className="text-foreground text-sm md:text-base leading-relaxed">
        <FormattedContent content={parsed.fallbackText || ""} onImageClick={setEnlargedImage} />
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
      {renderZoomModal()}
    </div>
  );
}
