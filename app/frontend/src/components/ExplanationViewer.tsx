"use client";

import React, { useMemo, useState } from "react";
import { 
  Sparkles, 
  Stethoscope, 
  CheckCircle2, 
  XCircle, 
  Award,
  AlertCircle,
  X
} from "lucide-react";
import { FormattedContent } from "@/components/FormattedContent";

interface ExplanationViewerProps {
  explanation: string | null | undefined;
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

function withoutReferenceSection(text: string): string {
  return text
    .replace(
      /(?:^|\n)\s*(?:[-*+]\s+)?(?:#{1,6}\s+)?(?:<br\s*\/?\>\s*)?(?:\*\*)?\s*(?:refer[eê]ncias?(?:\s+bibliogr[aá]ficas?)?|bibliografia|fontes?)\s*:?\s*(?:\*\*)?[\s\S]*?(?=\n\s*(?:#{1,6}\s+)?(?:\*\*)?\s*(?:pulo do gato|racioc[ií]nio cl[ií]nico|fundamentação teórica|discussão do caso|comentário do caso|padrão de resposta|resolução detalhada|alternativa correta|por que a letra|análise dos distratores|distratores|alternativas incorretas|gabarito)\b|$)/i,
      ""
    )
    .replace(/(?:\s|<br\s*\/?\>\s*)+$/i, "");
}

/**
 * Parses structured markdown explanations into distinct semantic sections
 */
function parseExplanation(raw: string): ParsedSection {
  const clean = withoutReferenceSection(raw.replace(/\\n/g, "\n")).trim();
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
    const letterMatch = corrMatch[0].match(/(?:Letra|\()\s*([A-E])\b/i) || corrMatch[0].match(/Alternativa\s+Correta\s*([A-E])\b/i);
    const gabLetter = parsed.gabarito?.match(/(?:Letra|\b)\s*([A-E])\b/i)?.[1]?.toUpperCase();
    const parsedLetter = letterMatch ? letterMatch[1].toUpperCase() : gabLetter;
    parsed.alternativaCorreta = {
      letter: parsedLetter,
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
  correctLetter,
}: ExplanationViewerProps) {
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);

  const parsed = useMemo(() => {
    if (!explanation) return null;
    return parseExplanation(explanation);
  }, [explanation]);

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

      {renderZoomModal()}
    </div>
  );
}
