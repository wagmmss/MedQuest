"use client";

import { useState } from "react";
import Link from "next/link";
import { CoverageArea } from "@/types/api";
import { ChevronDown, ChevronRight, CheckCircle2, CircleDashed, PlayCircle } from "lucide-react";
import clsx from "clsx";

export function CoverageClient({ areas }: { areas: CoverageArea[] }) {
  const [expandedArea, setExpandedArea] = useState<string | null>(null);

  const toggleArea = (area: string) => {
    setExpandedArea(expandedArea === area ? null : area);
  };

  const getStatusTag = (status: string) => {
    if (status === "mastered") return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-success/10 text-success border border-success/20">
        <CheckCircle2 size={14} /> Dominado
      </span>
    );
    if (status === "proficient") return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20" title="Boa acurácia, mas baixa cobertura">
        <CheckCircle2 size={14} /> Proficiente
      </span>
    );
    if (status === "in_progress") return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-warning/10 text-warning border border-warning/20 hover:bg-warning/20 transition-colors cursor-pointer" title="Clique para focar na revisão">
        <PlayCircle size={14} /> Revisar
      </span>
    );
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border">
        <CircleDashed size={14} /> Não iniciado
      </span>
    );
  };

  const getAreaColorClass = (areaName: string) => {
    const name = areaName.toLowerCase();
    if (name.includes("preventiva")) return "bg-area-preventiva";
    if (name.includes("pediatria")) return "bg-area-pediatria";
    if (name.includes("go") || name.includes("ginecologia")) return "bg-area-go";
    if (name.includes("cirurgia")) return "bg-area-cirurgia";
    return "bg-area-clinica";
  };

  return (
    <div className="flex flex-col gap-4 pb-10">
      {areas.map((area) => {
        const isExpanded = expandedArea === area.area;
        const progressPct = area.n_questions > 0 ? (area.answered_questions / area.n_questions) * 100 : 0;
        const accuracyFormatted = area.accuracy != null ? (area.accuracy * 100).toFixed(0) + "%" : "--";
        const colorClass = getAreaColorClass(area.area);

        return (
          <div key={area.area} className="bg-card border border-border/50 rounded-xl flex flex-col shadow-sm hover:shadow-md hover:border-border transition-all">
            {/* Area Header (Clickable) */}
            <button 
              onClick={() => toggleArea(area.area)}
              className="flex flex-col sm:flex-row sm:items-center justify-between p-5 hover:bg-muted/30 transition-colors gap-4 text-left rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
            >
              <div className="flex items-center gap-4">
                <div className={clsx("w-2.5 h-12 rounded-full shrink-0 shadow-sm", colorClass)} />
                <div>
                  <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                    {area.area}
                  </h2>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    {area.n_subtemas} subtemas • {area.n_questions} questões
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-6 sm:min-w-[300px]">
                <div className="flex-1">
                  <div className="flex justify-between text-[11px] uppercase tracking-wider mb-2 font-semibold">
                    <span className="text-muted-foreground">Progresso</span>
                    <span className="text-foreground">{progressPct.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 w-full bg-muted rounded-full overflow-hidden flex ring-1 ring-inset ring-black/5 dark:ring-white/5">
                    <div className="h-full bg-success shadow-inner" style={{ width: `${(area.mastered / area.n_subtemas) * 100}%` }} title="Dominado" />
                    <div className="h-full bg-primary shadow-inner" style={{ width: `${(area.proficient / area.n_subtemas) * 100}%` }} title="Proficiente (Baixa Cobertura)" />
                    <div className="h-full bg-warning shadow-inner" style={{ width: `${(area.in_progress / area.n_subtemas) * 100}%` }} title="Em Progresso" />
                  </div>
                </div>
                
                <div className="flex flex-col items-end border-l border-border/50 pl-6">
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wider font-semibold mb-1">Acurácia</span>
                  <span className="text-xl font-bold text-foreground leading-none">{accuracyFormatted}</span>
                </div>
                <div className="text-muted-foreground transition-transform duration-200">
                  {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </div>
              </div>
            </button>

            {/* Subtemas Expanded View */}
            {isExpanded && (
              <div className="border-t border-border/50 bg-muted/10 p-0 sm:p-5 rounded-b-xl overflow-hidden animate-in slide-in-from-top-2 fade-in duration-200">
                <div className="overflow-x-auto rounded-lg border border-border/50 bg-card shadow-sm">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-muted-foreground uppercase tracking-wider bg-muted/50 border-b border-border/50">
                      <tr>
                        <th className="px-5 py-4 font-semibold">Subtema</th>
                        <th className="px-5 py-4 font-semibold text-right">Questões</th>
                        <th className="px-5 py-4 font-semibold text-right">Feitas</th>
                        <th className="px-5 py-4 font-semibold text-right">Acurácia</th>
                        <th className="px-5 py-4 font-semibold text-center">Status</th>
                        <th className="px-5 py-4 font-semibold text-center"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50">
                      {area.subtemas.map((sub) => (
                        <tr key={sub.subtema} className="hover:bg-muted/30 transition-colors group">
                          <td className="px-5 py-3.5 font-semibold text-foreground">{sub.subtema}</td>
                          <td className="px-5 py-3.5 text-right text-muted-foreground font-medium">{sub.n_questions}</td>
                          <td className="px-5 py-3.5 text-right text-muted-foreground font-medium">{sub.answered}</td>
                          <td className="px-5 py-3.5 text-right font-bold text-foreground">
                            {sub.accuracy != null ? (sub.accuracy * 100).toFixed(0) + "%" : "--"}
                          </td>
                          <td className="px-5 py-3.5 flex justify-center">
                            <div className="flex items-center justify-center">
                              {getStatusTag(sub.status)}
                            </div>
                          </td>
                          <td className="px-5 py-3.5 text-center">
                            <Link
                              href={`/estudar?subtema=${encodeURIComponent(sub.subtema)}&limit=50`}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100 ring-1 ring-primary/20"
                            >
                              <PlayCircle size={14} />
                              Praticar
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
