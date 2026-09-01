"use client";

import React from "react";
import { RadarInstitutionData, RadarAreaStat } from "@/types/api";
import Link from "next/link";
import { BookOpen, Play, AlertTriangle } from "lucide-react";

interface InstitutionRadarTableProps {
  institution: RadarInstitutionData;
  comparison?: (RadarInstitutionData & { type: "global" | "institution" }) | null;
  onActionClick?: (action: "study" | "simulado" | "review") => void;
}


export function InstitutionRadarTable({
  institution,
  comparison,
  onActionClick,
}: InstitutionRadarTableProps) {
  const comparisonMap = React.useMemo(() => {
    if (!comparison || !Array.isArray(comparison.areas)) return {};
    const map: Record<string, RadarAreaStat> = {};
    comparison.areas.forEach(a => {
      map[a.area] = a;
    });
    return map;
  }, [comparison]);


  const getStatusBadge = (status: string, attempts: number) => {
    if (status === "insufficient") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          <AlertTriangle size={12} /> Amostra Insuficiente ({attempts} tent.)
        </span>
      );
    }
    if (status === "forming") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Em Formação ({attempts} tent.)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        Confiável ({attempts} tent.)
      </span>
    );
  };

  return (
    <div className="w-full space-y-6">
      {/* Tabela Acessível */}
      <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
        <table className="w-full text-left text-sm" role="table" aria-label={`Desempenho comparativo por área na banca ${institution.label}`}>
          <caption className="sr-only">
            Tabela de acurácia, intervalo de confiança (95% CI) e cobertura por grande área na banca {institution.label}
          </caption>
          <thead className="bg-muted/50 text-xs uppercase font-semibold text-muted-foreground border-b border-border">
            <tr>
              <th scope="col" className="px-4 py-3.5">Grande Área</th>
              <th scope="col" className="px-4 py-3.5">Cobertura</th>
              <th scope="col" className="px-4 py-3.5">Acurácia (Banca)</th>
              <th scope="col" className="px-4 py-3.5">Intervalo de Incerteza (95% CI)</th>
              {comparison && (
                <th scope="col" className="px-4 py-3.5">
                  {comparison.type === "global" ? "Desempenho Geral" : (comparison.label || "Comparativo")}
                </th>
              )}
              <th scope="col" className="px-4 py-3.5">Status da Amostra</th>
              <th scope="col" className="px-4 py-3.5 text-right">Ação Direta</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {institution.areas.map((area) => {
              const compArea = comparisonMap[area.area];
              const accPct = area.accuracy !== null ? Math.round(area.accuracy * 100) : null;
              const ciLowPct = area.ci_lower !== null ? Math.round(area.ci_lower * 100) : null;
              const ciHighPct = area.ci_upper !== null ? Math.round(area.ci_upper * 100) : null;
              const compAccPct = compArea && compArea.accuracy !== null ? Math.round(compArea.accuracy * 100) : null;

              return (
                <tr key={area.area} className="hover:bg-muted/30 transition-colors">
                  <th scope="row" className="px-4 py-3.5 font-semibold text-foreground">
                    {area.area}
                  </th>
                  <td className="px-4 py-3.5 text-muted-foreground">
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">{Math.round(area.coverage * 100)}%</span>
                      <span className="text-xs">{area.answered}/{area.available} questões</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    {accPct !== null ? (
                      <span className="font-bold text-foreground text-base">{accPct}%</span>
                    ) : (
                      <span className="text-muted-foreground italic">Sem tentativas</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-muted-foreground">
                    {ciLowPct !== null && ciHighPct !== null ? (
                      <div className="flex flex-col">
                        <span className="font-mono text-xs text-foreground font-medium">[{ciLowPct}% – {ciHighPct}%]</span>
                        <span className="text-[10px] text-muted-foreground">Margem Wilson 95%</span>
                      </div>
                    ) : (
                      <span className="text-xs italic">—</span>
                    )}
                  </td>
                  {comparison && (
                    <td className="px-4 py-3.5 text-muted-foreground">
                      {compAccPct !== null ? (
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">{compAccPct}%</span>
                          <span className="text-xs">{compArea?.attempts || 0} tentativas</span>
                        </div>
                      ) : (
                        <span className="text-xs italic">—</span>
                      )}
                    </td>
                  )}
                  <td className="px-4 py-3.5">
                    {getStatusBadge(area.sample_status, area.attempts)}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/estudar?institution=${encodeURIComponent(institution.code || "")}&area=${encodeURIComponent(area.area)}&status=all&limit=20`}
                        onClick={() => onActionClick?.("study")}
                        className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                        title={`Estudar questões de ${area.area}`}
                      >
                        <BookOpen size={14} /> Estudar
                      </Link>
                      <Link
                        href={`/simulado?institutions=${encodeURIComponent(institution.code || "")}&area=${encodeURIComponent(area.area)}`}
                        onClick={() => onActionClick?.("simulado")}
                        className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-secondary/10 text-secondary hover:bg-secondary/20 transition-colors"
                        title={`Criar simulado de ${area.area}`}
                      >
                        <Play size={14} /> Simulado
                      </Link>
                    </div>

                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
