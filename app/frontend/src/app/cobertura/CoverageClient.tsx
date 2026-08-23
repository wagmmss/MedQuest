"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { CoverageArea, CoverageSubtema } from "@/types/api";
import { 
  ChevronDown, ChevronRight, CheckCircle2, CircleDashed, PlayCircle, 
  Flame, Search, BookOpen, Layers, CheckSquare, Award, Clock
} from "lucide-react";
import clsx from "clsx";

export function CoverageClient({ areas }: { areas: CoverageArea[] }) {
  const [expandedArea, setExpandedArea] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "high_yield" | "mastered" | "in_progress" | "not_started">("all");

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
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-warning/10 text-warning border border-warning/20" title="Em resolução de questões">
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
    if (name.includes("preventiva")) return "bg-area-preventiva text-area-preventiva";
    if (name.includes("pediatria")) return "bg-area-pediatria text-area-pediatria";
    if (name.includes("go") || name.includes("ginecologia")) return "bg-area-go text-area-go";
    if (name.includes("cirurgia")) return "bg-area-cirurgia text-area-cirurgia";
    return "bg-area-clinica text-area-clinica";
  };

  // Filtered subtemas per area
  const filteredAreas = useMemo(() => {
    return areas.map(area => {
      const filteredSubs = area.subtemas.filter(sub => {
        // Search filter
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchTitle = sub.subtema.toLowerCase().includes(q);
          const matchArea = (sub.area || area.area).toLowerCase().includes(q);
          if (!matchTitle && !matchArea) return false;
        }

        // Status / High Yield filter
        if (statusFilter === "high_yield") {
          return !!sub.highYield;
        }
        if (statusFilter === "mastered") {
          return sub.status === "mastered" || sub.status === "proficient";
        }
        if (statusFilter === "in_progress") {
          return sub.status === "in_progress";
        }
        if (statusFilter === "not_started") {
          return sub.status === "not_started";
        }
        return true;
      });

      return {
        ...area,
        filteredSubtemas: filteredSubs
      };
    });
  }, [areas, searchQuery, statusFilter]);

  // Overall statistics
  const totalSubtemas = areas.reduce((acc, a) => acc + a.n_subtemas, 0);
  const totalHighYield = areas.reduce((acc, a) => acc + (a.high_yield_count || 0), 0);
  const totalMastered = areas.reduce((acc, a) => acc + a.mastered + a.proficient, 0);
  const totalInProgress = areas.reduce((acc, a) => acc + a.in_progress, 0);

  return (
    <div className="flex flex-col gap-6 pb-12">
      {/* Quick Filters and Search Bar */}
      <div className="bg-card border border-border rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar tema ou módulo..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-muted/40 border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          <button
            onClick={() => setStatusFilter("all")}
            className={clsx(
              "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0",
              statusFilter === "all"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "bg-muted hover:bg-muted/80 text-muted-foreground"
            )}
          >
            Todos ({totalSubtemas})
          </button>
          <button
            onClick={() => setStatusFilter("high_yield")}
            className={clsx(
              "inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0",
              statusFilter === "high_yield"
                ? "bg-orange-500 text-white shadow-sm"
                : "bg-orange-500/10 text-orange-600 dark:text-orange-400 hover:bg-orange-500/20"
            )}
          >
            <Flame size={14} className="fill-current" /> Foco USP ({totalHighYield})
          </button>
          <button
            onClick={() => setStatusFilter("mastered")}
            className={clsx(
              "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0",
              statusFilter === "mastered"
                ? "bg-success text-success-foreground shadow-sm"
                : "bg-success/10 text-success hover:bg-success/20"
            )}
          >
            Dominados ({totalMastered})
          </button>
          <button
            onClick={() => setStatusFilter("in_progress")}
            className={clsx(
              "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0",
              statusFilter === "in_progress"
                ? "bg-warning text-warning-foreground shadow-sm"
                : "bg-warning/10 text-warning hover:bg-warning/20"
            )}
          >
            Em Revisão ({totalInProgress})
          </button>
        </div>
      </div>

      {/* Areas Accordion List */}
      <div className="flex flex-col gap-4">
        {filteredAreas.map((area) => {
          const isExpanded = expandedArea === area.area || searchQuery.length > 0;
          const progressPct = area.n_questions > 0 ? (area.answered_questions / area.n_questions) * 100 : 0;
          const accuracyFormatted = area.accuracy != null ? (area.accuracy * 100).toFixed(0) + "%" : "--";
          const colorClass = getAreaColorClass(area.area).split(" ")[0];

          // If filtering active and area has 0 matching subtemas, skip displaying
          if (area.filteredSubtemas.length === 0 && (searchQuery || statusFilter !== "all")) {
            return null;
          }

          return (
            <div key={area.area} className="bg-card border border-border rounded-xl flex flex-col shadow-sm hover:border-border/80 transition-all overflow-hidden">
              {/* Area Header */}
              <button 
                onClick={() => toggleArea(area.area)}
                className="flex flex-col sm:flex-row sm:items-center justify-between p-5 hover:bg-muted/30 transition-colors gap-4 text-left outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
              >
                <div className="flex items-center gap-4">
                  <div className={clsx("w-2.5 h-12 rounded-full shrink-0 shadow-sm", colorClass)} />
                  <div>
                    <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                      {area.area}
                    </h2>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                      <span>{area.n_subtemas} módulos oficiais</span>
                      <span>•</span>
                      <span>{area.n_questions} questões</span>
                      {area.high_yield_count ? (
                        <>
                          <span>•</span>
                          <span className="text-orange-500 font-semibold flex items-center gap-0.5">
                            <Flame size={12} className="fill-current" /> {area.high_yield_count} Focos USP
                          </span>
                        </>
                      ) : null}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6 sm:min-w-[320px]">
                  <div className="flex-1">
                    <div className="flex justify-between text-[11px] uppercase tracking-wider mb-2 font-semibold">
                      <span className="text-muted-foreground">Progresso</span>
                      <span className="text-foreground">{progressPct.toFixed(1)}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-muted rounded-full overflow-hidden flex ring-1 ring-inset ring-black/5 dark:ring-white/5">
                      <div className="h-full bg-success shadow-inner" style={{ width: `${(area.mastered / area.n_subtemas) * 100}%` }} title="Dominado" />
                      <div className="h-full bg-primary shadow-inner" style={{ width: `${(area.proficient / area.n_subtemas) * 100}%` }} title="Proficiente" />
                      <div className="h-full bg-warning shadow-inner" style={{ width: `${(area.in_progress / area.n_subtemas) * 100}%` }} title="Em Revisão" />
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

              {/* Subtemas Table */}
              {isExpanded && (
                <div className="border-t border-border bg-muted/10 p-0 sm:p-5 rounded-b-xl overflow-hidden animate-in slide-in-from-top-2 fade-in duration-200">
                  <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-muted-foreground uppercase tracking-wider bg-muted/50 border-b border-border">
                        <tr>
                          <th className="px-5 py-3.5 font-semibold">Módulo / Tema de Estudo</th>
                          <th className="px-4 py-3.5 font-semibold text-center">Teoria</th>
                          <th className="px-4 py-3.5 font-semibold text-right">Questões</th>
                          <th className="px-4 py-3.5 font-semibold text-right">Feitas</th>
                          <th className="px-4 py-3.5 font-semibold text-right">Acurácia</th>
                          <th className="px-4 py-3.5 font-semibold text-center">Status</th>
                          <th className="px-5 py-3.5 font-semibold text-center"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        {area.filteredSubtemas.map((sub) => (
                          <tr key={sub.subtema} className="hover:bg-muted/30 transition-colors group">
                            <td className="px-5 py-3.5 font-semibold text-foreground">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span>{sub.subtema}</span>
                                {sub.highYield && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
                                    <Flame size={12} className="fill-current text-orange-500" /> Foco USP
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3.5 text-center text-xs text-muted-foreground font-medium whitespace-nowrap">
                              {sub.theory_hours ? (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-muted-foreground">
                                  <Clock size={12} /> {sub.theory_hours}h
                                </span>
                              ) : "--"}
                            </td>
                            <td className="px-4 py-3.5 text-right text-muted-foreground font-medium">
                              {sub.n_questions}
                            </td>
                            <td className="px-4 py-3.5 text-right text-muted-foreground font-medium">
                              {sub.answered}
                            </td>
                            <td className="px-4 py-3.5 text-right font-bold text-foreground">
                              {sub.accuracy != null ? (sub.accuracy * 100).toFixed(0) + "%" : "--"}
                            </td>
                            <td className="px-4 py-3.5 text-center whitespace-nowrap">
                              <div className="flex items-center justify-center">
                                {getStatusTag(sub.status)}
                              </div>
                            </td>
                            <td className="px-5 py-3.5 text-center">
                              <Link
                                href={`/estudar?area=${encodeURIComponent(sub.area || area.area)}&subtema=${encodeURIComponent(sub.subtema)}&limit=50`}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100 ring-1 ring-primary/20 whitespace-nowrap"
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
    </div>
  );
}
