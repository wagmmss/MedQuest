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
          <div key={area.area} className="bg-card border border-border rounded-lg overflow-hidden flex flex-col shadow-1 transition-all">
            {/* Area Header (Clickable) */}
            <button 
              onClick={() => toggleArea(area.area)}
              className="flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-5 hover:bg-muted/50 transition-colors gap-4 text-left"
            >
              <div className="flex items-center gap-3">
                <div className={clsx("w-2 h-10 rounded-full shrink-0", colorClass)} />
                <div>
                  <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                    {area.area}
                    {isExpanded ? <ChevronDown size={18} className="text-muted-foreground" /> : <ChevronRight size={18} className="text-muted-foreground" />}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {area.n_subtemas} subtemas • {area.n_questions} questões
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-6 sm:min-w-[300px]">
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1 font-medium">
                    <span className="text-muted-foreground">Progresso</span>
                    <span className="text-foreground">{progressPct.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 w-full bg-muted rounded-full overflow-hidden flex">
                    <div className="h-full bg-success" style={{ width: `${(area.mastered / area.n_subtemas) * 100}%` }} title="Dominado" />
                    <div className="h-full bg-warning" style={{ width: `${(area.in_progress / area.n_subtemas) * 100}%` }} title="Em Progresso" />
                  </div>
                </div>
                
                <div className="flex flex-col items-end">
                  <span className="text-xs text-muted-foreground font-medium mb-0.5">Acurácia</span>
                  <span className="text-lg font-bold text-foreground leading-none">{accuracyFormatted}</span>
                </div>
              </div>
            </button>

            {/* Subtemas Expanded View */}
            {isExpanded && (
              <div className="border-t border-border bg-card-2 p-0 sm:p-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b border-border">
                      <tr>
                        <th className="px-4 py-3 font-semibold rounded-tl-md">Subtema</th>
                        <th className="px-4 py-3 font-semibold text-right">Questões</th>
                        <th className="px-4 py-3 font-semibold text-right">Feitas</th>
                        <th className="px-4 py-3 font-semibold text-right">Acurácia</th>
                        <th className="px-4 py-3 font-semibold text-center">Status</th>
                        <th className="px-4 py-3 font-semibold text-center rounded-tr-md"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {area.subtemas.map((sub) => (
                        <tr key={sub.subtema} className="hover:bg-muted/30 transition-colors">
                          <td className="px-4 py-3 font-medium text-foreground">{sub.subtema}</td>
                          <td className="px-4 py-3 text-right text-muted-foreground">{sub.n_questions}</td>
                          <td className="px-4 py-3 text-right text-muted-foreground">{sub.answered}</td>
                          <td className="px-4 py-3 text-right font-medium">
                            {sub.accuracy != null ? (sub.accuracy * 100).toFixed(0) + "%" : "--"}
                          </td>
                          <td className="px-4 py-3 flex justify-center">
                            <div className="flex items-center justify-center p-1">
                              {getStatusTag(sub.status)}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <Link
                              href={`/estudar?subtema=${encodeURIComponent(sub.subtema)}&limit=50`}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors"
                            >
                              <PlayCircle size={14} />
                              Estudar
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
