"use client";

import React, { useMemo } from "react";
import { 
  Sparkles, 
  Stethoscope, 
  CheckCircle2, 
  XCircle, 
  BookOpen, 
  Award,
  AlertCircle
} from "lucide-react";

interface ExplanationViewerProps {
  explanation: string | null | undefined;
  medicalReferences?: string | null;
  correctLetter?: string | null;
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
  correctLetter 
}: ExplanationViewerProps) {
  const parsed = useMemo(() => {
    if (!explanation) return null;
    return parseExplanation(explanation);
  }, [explanation]);

  if (!explanation || !parsed) {
    return (
      <div className="flex items-center gap-3 p-5 rounded-xl bg-muted/40 border border-border text-muted-foreground">
        <AlertCircle size={18} />
        <span>Nenhum comentário disponível para esta questão.</span>
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
    </div>
  );
}
