"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { CoverageArea, CoverageSubtema } from "@/types/api";
import { AlertCircle, CheckCircle2, ChevronDown, ChevronRight, CircleDashed, Clock, Flame, PlayCircle, Search, Sparkles } from "lucide-react";
import clsx from "clsx";

type StatusFilter = "all" | "high_yield" | "evidence" | "in_progress" | "not_started";

const statusRank: Record<CoverageSubtema["status"], number> = { not_started: 0, in_progress: 1, proficient: 2, mastered: 3 };

function formatCoverage(sub: CoverageSubtema) {
  return `${sub.answered}/${sub.n_questions} (${(sub.coverage_pct * 100).toFixed(0)}%)`;
}

function priorityReason(sub: CoverageSubtema) {
  if (sub.status === "not_started") return `Ainda não iniciado · ${sub.n_questions} questões disponíveis`;
  if (sub.status === "in_progress") return `Em aprendizado · ${formatCoverage(sub)} coberto`;
  return `Boa evidência inicial · ${formatCoverage(sub)} coberto`;
}

export function CoverageClient({ areas }: { areas: CoverageArea[] }) {
  const [expandedArea, setExpandedArea] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const toggleArea = (area: string) => setExpandedArea(expandedArea === area ? null : area);

  const getStatusTag = (status: CoverageSubtema["status"]) => {
    if (status === "mastered") return <span title="Boa acurácia, cobertura relevante e amostra suficiente" className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-success/10 text-success border border-success/20"><CheckCircle2 size={14} /> Consolidado</span>;
    if (status === "proficient") return <span title="Boa acurácia inicial; continue praticando para consolidar" className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20"><Sparkles size={14} /> Boa evidência</span>;
    if (status === "in_progress") return <span title="Tema iniciado, mas ainda sem evidência suficiente de consolidação" className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-warning/10 text-warning border border-warning/20"><PlayCircle size={14} /> Em aprendizado</span>;
    return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border"><CircleDashed size={14} /> Não iniciado</span>;
  };

  const getAreaColorClass = (areaName: string) => {
    const name = areaName.toLowerCase();
    if (name.includes("preventiva")) return "bg-area-preventiva";
    if (name.includes("pediatria")) return "bg-area-pediatria";
    if (name.includes("go") || name.includes("ginecologia")) return "bg-area-go";
    if (name.includes("cirurgia")) return "bg-area-cirurgia";
    return "bg-area-clinica";
  };

  const filteredAreas = useMemo(() => areas.map(area => {
    const filteredSubtemas = area.subtemas.filter(sub => {
      const q = searchQuery.trim().toLowerCase();
      if (q && !sub.subtema.toLowerCase().includes(q) && !(sub.area || area.area).toLowerCase().includes(q)) return false;
      if (statusFilter === "high_yield") return Boolean(sub.highYield);
      if (statusFilter === "evidence") return sub.status === "mastered" || sub.status === "proficient";
      if (statusFilter === "in_progress") return sub.status === "in_progress";
      if (statusFilter === "not_started") return sub.status === "not_started";
      return true;
    });
    return { ...area, filteredSubtemas };
  }), [areas, searchQuery, statusFilter]);

  const priorities = useMemo(() => areas.flatMap(area => area.subtemas.map(sub => ({ ...sub, displayArea: sub.area || area.area })))
    .filter(sub => sub.highYield && sub.status !== "mastered")
    .sort((a, b) => statusRank[a.status] - statusRank[b.status] || a.coverage_pct - b.coverage_pct || b.n_questions - a.n_questions)
    .slice(0, 3), [areas]);

  const totalSubtemas = areas.reduce((acc, a) => acc + a.n_subtemas, 0);
  const totalHighYield = areas.reduce((acc, a) => acc + (a.high_yield_count || 0), 0);
  const totalWithEvidence = areas.reduce((acc, a) => acc + a.mastered + a.proficient, 0);
  const totalInProgress = areas.reduce((acc, a) => acc + a.in_progress, 0);

  return <div className="flex flex-col gap-6 pb-12">
    {priorities.length > 0 && <section className="bg-card border border-orange-500/20 rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 mb-4"><div><div className="flex items-center gap-2 text-orange-600 dark:text-orange-400"><AlertCircle size={19} /><h2 className="text-lg font-bold text-foreground">Prioridades de cobertura</h2></div><p className="text-sm text-muted-foreground mt-1">Temas de alta incidência ainda sem evidência suficiente de consolidação.</p></div><span className="text-xs text-muted-foreground">Base: prevalência histórica USP-SP / USP-RP</span></div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">{priorities.map(sub => <div key={`${sub.displayArea}-${sub.subtema}`} className="border border-border rounded-xl p-4 bg-muted/20 flex flex-col gap-3"><div><div className="flex items-start justify-between gap-2"><h3 className="font-semibold text-sm text-foreground leading-snug">{sub.subtema}</h3><Flame size={16} className="shrink-0 text-orange-500 fill-current" aria-label="Alta incidência" /></div><p className="text-xs text-muted-foreground mt-1">{sub.displayArea} · {priorityReason(sub)}</p></div><Link href={`/estudar?area=${encodeURIComponent(sub.displayArea)}&subtema=${encodeURIComponent(sub.subtema)}&limit=20`} className="inline-flex items-center justify-center gap-1.5 w-full px-3 py-2 text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors ring-1 ring-primary/20"><PlayCircle size={14} /> Praticar agora</Link></div>)}</div>
    </section>}

    <div className="bg-card border border-border rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4"><div className="relative w-full md:w-80"><Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" /><input type="text" placeholder="Buscar tema ou módulo..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full pl-9 pr-4 py-2 bg-muted/40 border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30" /></div><div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">{[["all", `Todos (${totalSubtemas})`], ["high_yield", `Alta incidência (${totalHighYield})`], ["evidence", `Boa evidência (${totalWithEvidence})`], ["in_progress", `Em aprendizado (${totalInProgress})`], ["not_started", "Não iniciados"]].map(([value, label]) => <button key={value} onClick={() => setStatusFilter(value as StatusFilter)} className={clsx("px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0", statusFilter === value ? "bg-primary text-primary-foreground shadow-sm" : "bg-muted hover:bg-muted/80 text-muted-foreground")}>{value === "high_yield" && <Flame size={14} className="inline mr-1 -mt-0.5 text-orange-500 fill-current" />}{label}</button>)}</div></div>

    {filteredAreas.some(a => a.filteredSubtemas.length > 0) ? <div className="flex flex-col gap-4">{filteredAreas.map(area => {
      const isExpanded = expandedArea === area.area || searchQuery.length > 0;
      const coveragePct = area.n_questions > 0 ? (area.answered_questions / area.n_questions) * 100 : 0;
      if (area.filteredSubtemas.length === 0 && (searchQuery || statusFilter !== "all")) return null;
      return <div key={area.area} className="bg-card border border-border rounded-xl flex flex-col shadow-sm hover:border-border/80 transition-all overflow-hidden"><button onClick={() => toggleArea(area.area)} className="flex flex-col sm:flex-row sm:items-center justify-between p-5 hover:bg-muted/30 transition-colors gap-4 text-left outline-none focus-visible:ring-2 focus-visible:ring-primary/20"><div className="flex items-center gap-4"><div className={clsx("w-2.5 h-12 rounded-full shrink-0 shadow-sm", getAreaColorClass(area.area))} /><div><h2 className="text-lg font-bold text-foreground">{area.area}</h2><div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground mt-1"><span>{area.n_subtemas} módulos</span><span>•</span><span>{area.n_questions} questões</span>{area.high_yield_count ? <><span>•</span><span className="text-orange-500 font-semibold"><Flame size={12} className="inline fill-current -mt-0.5" /> {area.high_yield_count} alta incidência</span></> : null}</div></div></div><div className="flex items-center gap-5 sm:min-w-[360px]"><div className="flex-1"><div className="flex justify-between text-[11px] uppercase tracking-wider mb-2 font-semibold"><span className="text-muted-foreground">Cobertura do banco</span><span className="text-foreground">{coveragePct.toFixed(1)}%</span></div><div className="h-2.5 w-full bg-muted rounded-full overflow-hidden ring-1 ring-inset ring-black/5 dark:ring-white/5"><div className="h-full bg-success shadow-inner" style={{ width: `${coveragePct}%` }} /></div></div><div className="flex flex-col items-end border-l border-border/50 pl-5"><span className="text-[11px] text-muted-foreground uppercase tracking-wider font-semibold mb-1">Consolidados</span><span className="text-xl font-bold text-foreground leading-none">{area.mastered}/{area.n_subtemas}</span></div><div className="text-muted-foreground">{isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}</div></div></button>
        {isExpanded && <div className="border-t border-border bg-muted/10 p-0 sm:p-5 rounded-b-xl overflow-hidden animate-in slide-in-from-top-2 fade-in duration-200"><div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm"><table className="w-full text-sm text-left"><thead className="text-xs text-muted-foreground uppercase tracking-wider bg-muted/50 border-b border-border"><tr><th className="px-5 py-3.5 font-semibold">Módulo / Tema</th><th className="px-4 py-3.5 font-semibold text-center">Teoria</th><th className="px-4 py-3.5 font-semibold text-right">Cobertura</th><th className="px-4 py-3.5 font-semibold text-right">Acurácia</th><th className="px-4 py-3.5 font-semibold text-center">Evidência</th><th className="px-4 py-3.5 font-semibold text-center">Status</th><th className="px-5 py-3.5 font-semibold text-center">Ação</th></tr></thead><tbody className="divide-y divide-border/50">{area.filteredSubtemas.map(sub => <tr key={sub.subtema} className="hover:bg-muted/30 transition-colors"><td className="px-5 py-3.5 font-semibold text-foreground"><div className="flex items-center gap-2 flex-wrap"><span>{sub.subtema}</span>{sub.highYield && <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20"><Flame size={12} className="fill-current" /> Alta incidência</span>}</div></td><td className="px-4 py-3.5 text-center text-xs text-muted-foreground font-medium whitespace-nowrap">{sub.theory_hours ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted"><Clock size={12} /> {sub.theory_hours}h</span> : "--"}</td><td className="px-4 py-3.5 text-right font-semibold text-foreground whitespace-nowrap">{formatCoverage(sub)}</td><td className="px-4 py-3.5 text-right font-bold text-foreground">{sub.accuracy != null ? (sub.accuracy * 100).toFixed(0) + "%" : "--"}</td><td className="px-4 py-3.5 text-center text-xs text-muted-foreground whitespace-nowrap">{sub.attempts} tentativa{sub.attempts === 1 ? "" : "s"}</td><td className="px-4 py-3.5 text-center whitespace-nowrap"><div className="flex items-center justify-center">{getStatusTag(sub.status)}</div></td><td className="px-5 py-3.5 text-center"><Link href={`/estudar?area=${encodeURIComponent(sub.area || area.area)}&subtema=${encodeURIComponent(sub.subtema)}&limit=50`} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors ring-1 ring-primary/20 whitespace-nowrap"><PlayCircle size={14} /> Praticar</Link></td></tr>)}</tbody></table></div></div>}
      </div>;
    })}</div> : <div className="bg-card border border-border border-dashed rounded-xl p-12 text-center flex flex-col items-center justify-center gap-3 animate-in fade-in zoom-in-95 duration-200"><div className="w-12 h-12 rounded-full bg-muted/60 flex items-center justify-center text-muted-foreground"><Search size={22} /></div><h3 className="font-bold text-base text-foreground">Nenhum módulo encontrado</h3><p className="text-xs text-muted-foreground max-w-sm">Não encontramos módulos com os filtros ativos. Tente buscar por outros termos ou redefinir os filtros.</p><button onClick={() => { setSearchQuery(""); setStatusFilter("all"); }} className="mt-2 text-xs font-semibold text-primary bg-primary/10 hover:bg-primary/20 px-3 py-1.5 rounded-lg transition-colors cursor-pointer">Limpar filtros</button></div>}
  </div>;
}
