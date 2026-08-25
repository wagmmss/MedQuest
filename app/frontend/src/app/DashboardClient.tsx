"use client";

import Link from "next/link";
import { 
  OverviewStats, PlannerWeek, TimelineStat, BreakdownStat,
  BenchmarkStat, BottleneckTopic, DomainSummaryResponse, ErrorNotebookSummary 
} from "@/types/api";
import { OfflinePanel } from "@/components/OfflinePanel";
import { motion, Variants } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { triggerConfetti } from "@/lib/confetti";
import clsx from "clsx";
import { readLearningSession } from "@/lib/sessionState";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";

interface DashboardClientProps {
  stats: OverviewStats;
  currentPlannerWeek: PlannerWeek | null;
  firstName: string;
  timelineStats?: TimelineStat[];
  breakdownStats?: BreakdownStat[];
  benchmarkStats?: BenchmarkStat | null;
  bottlenecks?: BottleneckTopic[];
  domainSummary?: DomainSummaryResponse | null;
  errorNotebook?: ErrorNotebookSummary | null;
}

export function DashboardClient({ 
  stats, 
  currentPlannerWeek, 
  firstName, 
  timelineStats, 
  breakdownStats,
  benchmarkStats,
  bottlenecks = [],
  domainSummary,
  errorNotebook,
}: DashboardClientProps) {
  const hasAnimated = useRef(false);
  const [activeSession, setActiveSession] = useState<{ kind: "quiz" | "simulado"; url: string } | null>(null);

  useEffect(() => {
    // Dispara confete se as revisões diárias estiverem zeradas e houver pelo menos 1 questão feita
    if (stats.srs_due_count === 0 && stats.flashcards_due_count === 0 && stats.distinct_answered > 0 && !hasAnimated.current) {
      hasAnimated.current = true;
      triggerConfetti();
    }
  }, [stats]);

  useEffect(() => {
    // Check for active sessions
    const hasSimulado = readLearningSession<{ state?: string }>(
      "simulado",
      (val): val is { state?: string } => typeof val === "object" && val !== null
    );
    if (hasSimulado?.state && hasSimulado.state !== "RESULTS" && hasSimulado.state !== "OFFLINE_SUBMITTED") {
      window.queueMicrotask(() => setActiveSession({ kind: "simulado", url: "/simulado" }));
    } else {
      const hasQuiz = readLearningSession<{ state?: string }>(
        "quiz",
        (val): val is { state?: string } => typeof val === "object" && val !== null
      );
      if (hasQuiz?.state && hasQuiz.state !== "RESULTS") {
        window.queueMicrotask(() => setActiveSession({ kind: "quiz", url: "/estudar?resume=true" }));
      }
    }
  }, []);

  const accuracyFormatted = stats.accuracy_all_attempts != null 
    ? (stats.accuracy_all_attempts * 100).toFixed(1) + "%" 
    : "--";

  const pendentes = (stats.srs_due_count || 0) + (stats.flashcards_due_count || 0);
  const xpAtual = stats.distinct_answered * 10;
  const nivelAtual = Math.floor(xpAtual / 100) + 1;
  const progressoNivel = (xpAtual % 100);

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  const renderHeatmap = () => {
    if (!timelineStats || timelineStats.length === 0) return null;
    
    const today = new Date();
    const days = 180;
    const startDate = new Date(today.getTime() - (days - 1) * 24 * 60 * 60 * 1000);
    startDate.setDate(startDate.getDate() - startDate.getDay());
    const totalDays = Math.floor((today.getTime() - startDate.getTime()) / (24*60*60*1000)) + 1;
    
    const activityMap = new Map<string, number>();
    timelineStats.forEach(t => {
      activityMap.set(t.day, t.attempts);
    });

    const grid = [];
    for (let i = 0; i < totalDays; i++) {
      const d = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000);
      const dateStr = d.toISOString().split('T')[0];
      const count = activityMap.get(dateStr) || 0;
      
      let colorClass = "bg-muted/50 dark:bg-muted/20";
      if (count > 0 && count <= 10) colorClass = "bg-primary/30";
      else if (count > 10 && count <= 30) colorClass = "bg-primary/50";
      else if (count > 30 && count <= 60) colorClass = "bg-primary/70";
      else if (count > 60) colorClass = "bg-primary";
      
      grid.push(
        <div 
          key={dateStr}
          title={`${dateStr}: ${count} questões`}
          className={clsx("w-[14px] h-[14px] rounded-[3px] transition-colors hover:ring-2 ring-primary/50", colorClass)}
        />
      );
    }

    return (
      <div className="flex flex-col h-full justify-between">
        <div className="flex items-center gap-2 mb-4 text-foreground transition-transform group-hover:translate-x-1">
          <span className="material-symbols-outlined text-[20px]" data-icon="calendar_month">calendar_month</span>
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Atividade (Últimos 6 meses)</span>
        </div>
        <div className="flex-1 w-full overflow-x-auto pb-2 scrollbar-thin">
          <div className="flex flex-col flex-wrap gap-1 h-[105px] min-w-max content-start">
            {grid}
          </div>
        </div>
      </div>
    );
  };

  const renderRadar = () => {
    if (!breakdownStats || breakdownStats.length === 0) return null;
    
    const data = breakdownStats.slice(0, 5).map(stat => ({
      subject: stat.label.substring(0, 15) + (stat.label.length > 15 ? '...' : ''),
      A: Math.round((stat.accuracy || 0) * 100),
      fullMark: 100,
    }));

    return (
      <div className="flex flex-col h-full justify-between w-full relative">
        <div className="flex items-center gap-2 text-foreground transition-transform group-hover:translate-x-1 absolute top-0 left-0 z-10">
          <span className="material-symbols-outlined text-[20px]" data-icon="radar">radar</span>
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Performance por Área</span>
        </div>
        <div className="flex-1 w-full h-[220px] mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="65%" data={data}>
              <PolarGrid stroke="currentColor" className="text-border" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'currentColor', fontSize: 11, fontWeight: 500, className: 'text-muted-foreground' }} />
              <Radar name="Acurácia" dataKey="A" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.4} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  const motivationalMessages = [
    stats.streak_days >= 5 ? `Você estudou em ${stats.streak_days} dias da sua sequência. Descansos planejados não apagam seu progresso.` : null,
    currentPlannerWeek && currentPlannerWeek.week > 20 ? `Reta final! Você está na Semana ${currentPlannerWeek.week}.` : null,
    pendentes === 0 && stats.distinct_answered > 0 ? "Você já bateu sua meta diária de revisões! 🎉" : null,
    "Aqui está o seu painel de comando estratégico para a aprovação na Residência Médica."
  ].filter(Boolean);

  const motivationalMessage = motivationalMessages[0];

  return (
    <motion.div 
      variants={containerVariants} 
      initial="hidden" 
      animate="show"
      className="flex flex-col gap-8 md:gap-10 pt-4"
    >
      {/* Welcome Header */}
      <motion.section variants={itemVariants} className="flex flex-col gap-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
              Olá, {firstName}
            </h2>
            <p className="text-muted-foreground text-base md:text-lg">
              {motivationalMessage}
            </p>
          </div>
          {benchmarkStats && (
            <div className="flex items-center gap-2 self-start sm:self-auto bg-card border border-border/60 rounded-2xl px-4 py-2 shadow-xs">
              <span className="material-symbols-outlined text-primary text-[20px]" data-icon="flag">flag</span>
              <span className="text-xs font-medium text-muted-foreground">Meta de Corte:</span>
              <span className="text-xs font-bold text-foreground">{benchmarkStats.target_score_pct}%</span>
            </div>
          )}
        </div>
      </motion.section>

      {/* Resume Session Banner */}
      {activeSession && (
        <motion.div variants={itemVariants} className="w-full">
          <Link href={activeSession.url} className="bg-primary text-primary-foreground border-none rounded-2xl p-4 sm:p-6 shadow-md flex items-center justify-between hover:bg-primary/90 transition-all group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary-foreground/20 flex items-center justify-center text-primary-foreground">
                <span className="material-symbols-outlined text-[28px]" data-icon={activeSession.kind === "simulado" ? "history_edu" : "play_lesson"}>
                  {activeSession.kind === "simulado" ? "history_edu" : "play_lesson"}
                </span>
              </div>
              <div>
                <h3 className="text-lg font-bold">Retomar {activeSession.kind === "simulado" ? "Simulado" : "Sessão de Estudos"}</h3>
                <p className="text-sm text-primary-foreground/80 font-medium">Você tem uma sessão em andamento. Clique para continuar.</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 font-bold bg-primary-foreground text-primary px-4 py-2 rounded-lg group-hover:scale-105 transition-transform">
              Continuar <span className="material-symbols-outlined text-[18px]" data-icon="arrow_forward">arrow_forward</span>
            </div>
          </Link>
        </motion.div>
      )}

      {/* Benchmark de Aprovação & Ritmo Semanal (Inspirado no MedBrain da Medway) */}
      {benchmarkStats && (
        <motion.div variants={itemVariants} className="bg-card border border-border/60 rounded-3xl p-6 sm:p-7 shadow-xs relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-primary/5 rounded-bl-[160px] -mr-16 -mt-16 pointer-events-none transition-transform duration-700 hover:scale-110" />
          
          <div className="relative z-10 flex flex-col gap-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary ring-1 ring-primary/20">
                  <span className="material-symbols-outlined text-[22px]" data-icon="analytics">analytics</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground tracking-tight">
                    Benchmark de Aprovação & Ritmo Semanal
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Comparativo direto com a média de corte histórico dos aprovados na Residência Médica
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center gap-2 self-start sm:self-auto">
                {benchmarkStats.diff_pct != null && benchmarkStats.diff_pct >= 0 ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-bold ring-1 ring-emerald-500/20">
                    <span className="material-symbols-outlined text-[16px]" data-icon="verified">verified</span>
                    Zona de Aprovação (+{benchmarkStats.diff_pct}%)
                  </span>
                ) : benchmarkStats.diff_pct != null && benchmarkStats.diff_pct >= -10 ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-bold ring-1 ring-blue-500/20">
                    <span className="material-symbols-outlined text-[16px]" data-icon="trending_up">trending_up</span>
                    Zona Competitiva ({benchmarkStats.diff_pct}%)
                  </span>
                ) : benchmarkStats.diff_pct != null ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 text-xs font-bold ring-1 ring-amber-500/20">
                    <span className="material-symbols-outlined text-[16px]" data-icon="fitness_center">fitness_center</span>
                    Em Evolução ({benchmarkStats.diff_pct}%)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-muted text-muted-foreground text-xs font-semibold">
                    Inicie seus estudos
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              {/* Barra de Acurácia vs Meta */}
              <div className="flex flex-col gap-2 p-4 bg-muted/20 border border-border/40 rounded-2xl">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground font-medium flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-primary" data-icon="target">target</span>
                    Seu Acerto Geral vs. Meta
                  </span>
                  <span className="font-bold text-foreground">
                    {stats.accuracy_all_attempts != null ? (stats.accuracy_all_attempts * 100).toFixed(1) + "%" : "--"} 
                    <span className="text-muted-foreground font-normal text-xs ml-1">/ Meta: {benchmarkStats.target_score_pct}%</span>
                  </span>
                </div>
                
                <div className="relative w-full bg-muted rounded-full h-3 overflow-hidden ring-1 ring-inset ring-black/5 dark:ring-white/5 mt-1">
                  <div 
                    className="bg-primary h-3 rounded-full transition-all duration-700" 
                    style={{ width: `${Math.min(100, Math.max(0, (stats.accuracy_all_attempts || 0) * 100))}%` }}
                  />
                  {/* Marcador de Linha de Corte */}
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-foreground/80 z-20"
                    style={{ left: `${benchmarkStats.target_score_pct}%` }}
                    title={`Linha de Corte: ${benchmarkStats.target_score_pct}%`}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-muted-foreground">
                  <span>0%</span>
                  <span className="font-semibold text-foreground/80">Corte: {benchmarkStats.target_score_pct}%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* Ritmo Semanal */}
              <div className="flex flex-col gap-2 p-4 bg-muted/20 border border-border/40 rounded-2xl">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground font-medium flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-blue-500" data-icon="speed">speed</span>
                    Ritmo Semanal (Últimos 7 dias)
                  </span>
                  <span className="font-bold text-foreground">
                    {benchmarkStats.last7_attempts} <span className="text-muted-foreground font-normal text-xs">/ {benchmarkStats.weekly_target_questions} q</span>
                  </span>
                </div>

                <div className="w-full bg-muted rounded-full h-3 overflow-hidden ring-1 ring-inset ring-black/5 dark:ring-white/5 mt-1">
                  <div 
                    className="bg-blue-500 h-3 rounded-full transition-all duration-700" 
                    style={{ width: `${benchmarkStats.weekly_progress_pct}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-muted-foreground">
                  <span>{benchmarkStats.weekly_progress_pct}% da meta semanal</span>
                  <span>{Math.max(0, benchmarkStats.weekly_target_questions - benchmarkStats.last7_attempts)} questões restantes</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Plano Diário (3 Cards) */}
      <motion.div variants={itemVariants} className="flex flex-col gap-4">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary ring-1 ring-primary/20">
            <span className="material-symbols-outlined text-[18px]" data-icon="today">today</span>
          </div>
          <h3 className="text-xl font-semibold text-foreground tracking-tight">
            Plano Diário
          </h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Card 1: Revisões */}
          <motion.div 
            whileHover={{ y: -2 }}
            className="bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between shadow-xs hover:shadow-md transition-all relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-bl-[100px] -mr-4 -mt-4 transition-transform duration-500 group-hover:scale-125 pointer-events-none" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-3 text-purple-500">
                <span className="material-symbols-outlined text-[20px]" data-icon="psychology">psychology</span>
                <span className="text-xs font-bold uppercase tracking-wider">Revisão Ativa</span>
              </div>
              <p className="text-3xl font-bold text-foreground mb-1 tracking-tight">
                {pendentes > 0 ? `${pendentes} pendentes` : "Tudo em dia!"}
              </p>
              <p className="text-sm text-muted-foreground">
                Flashcards e questões no tempo ideal do FSRS.
              </p>
            </div>
            
            <div className="mt-8 relative z-10 flex gap-3 flex-col sm:flex-row">
              {pendentes > 0 ? (
                <>
                  {(stats.flashcards_due_count || 0) > 0 && (
                    <Link href="/revisao-ativa" className="flex-1 w-full py-2.5 bg-purple-100 hover:bg-purple-200 text-purple-700 dark:bg-purple-500/10 dark:hover:bg-purple-500/20 dark:text-purple-300 font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2 ring-1 ring-purple-500/20">
                      <span className="material-symbols-outlined text-[18px]" data-icon="auto_awesome">auto_awesome</span> ({stats.flashcards_due_count})
                    </Link>
                  )}
                  {(stats.srs_due_count || 0) > 0 && (
                    <Link href="/estudar?status=srs_due&limit=100" className="flex-1 w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2 shadow-xs">
                      <span className="material-symbols-outlined text-[18px]" data-icon="psychology">psychology</span> ({stats.srs_due_count})
                    </Link>
                  )}
                </>
              ) : (
                <button disabled className="w-full py-2.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold rounded-xl cursor-not-allowed text-sm flex items-center justify-center gap-2 ring-1 ring-emerald-500/20">
                  <span className="material-symbols-outlined text-[18px]" data-icon="done_all">done_all</span> Meta diária completa
                </button>
              )}
            </div>
          </motion.div>

          {/* Card 2: Questões Novas */}
          <motion.div 
            whileHover={{ y: -2 }}
            className="bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between shadow-xs hover:shadow-md transition-all relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-bl-[100px] -mr-4 -mt-4 transition-transform duration-500 group-hover:scale-125 pointer-events-none" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-3 text-blue-500">
                <span className="material-symbols-outlined text-[20px]" data-icon="post_add">post_add</span>
                <span className="text-xs font-bold uppercase tracking-wider">Questões Novas</span>
              </div>
              <p className="text-3xl font-bold text-foreground mb-1 tracking-tight">Meta: 20 un</p>
              <p className="text-sm text-muted-foreground">
                Avance na sua cobertura resolvendo tópicos inéditos.
              </p>
            </div>
            
            <div className="mt-8 relative z-10">
              <Link href={currentPlannerWeek && currentPlannerWeek.topics.length > 0 ? `/estudar?subtema=${encodeURIComponent(currentPlannerWeek.topics[0].subtema)}&status=new&limit=20` : "/estudar?status=new&limit=20"} className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all text-sm flex items-center justify-center gap-2 shadow-xs">
                <span className="material-symbols-outlined text-[18px]" data-icon="play_arrow">play_arrow</span> Iniciar Bateria
              </Link>
            </div>
          </motion.div>

          {/* Card 3: Planner */}
          <motion.div 
            whileHover={{ y: -2 }}
            className="bg-gradient-to-br from-primary to-primary-fixed-variant rounded-2xl p-6 flex flex-col justify-between shadow-md transition-all text-primary-foreground relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-bl-[120px] -mr-8 -mt-8 transition-transform duration-700 group-hover:scale-150 pointer-events-none" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-3 text-primary-foreground/80">
                <span className="material-symbols-outlined text-[20px]" data-icon="calendar_month">calendar_month</span>
                <span className="text-xs font-bold uppercase tracking-wider">Tópico da Semana</span>
              </div>
              <p className="text-2xl font-bold mb-2 leading-tight tracking-tight">
                {currentPlannerWeek && currentPlannerWeek.topics.length > 0 
                  ? currentPlannerWeek.topics[0].subtema 
                  : "Nenhum plano ativo"}
              </p>
              <p className="text-sm text-primary-foreground/70">
                {currentPlannerWeek 
                  ? `Semana ${currentPlannerWeek.week} • ${currentPlannerWeek.topics.length} metas pendentes` 
                  : "Defina sua data de prova no planner para receber sugestões."}
              </p>
            </div>
            
            <div className="mt-8 relative z-10">
              <Link href="/planner" className="w-full py-2.5 bg-white/10 hover:bg-white/20 text-white border border-white/20 font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2 backdrop-blur-xs">
                <span className="material-symbols-outlined text-[18px]" data-icon="arrow_forward">arrow_forward</span> Acessar Planner
              </Link>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Domínio de Focos por Grande Área (Inspirado no Domínio de Focos da Medway) */}
      {domainSummary && domainSummary.areas.length > 0 && (
        <motion.div variants={itemVariants} className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20">
                <span className="material-symbols-outlined text-[18px]" data-icon="domain_verification">domain_verification</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground tracking-tight">
                Domínio de Focos por Grande Área
              </h3>
            </div>
            <span className="text-xs text-muted-foreground">
              Total consolidado: <strong className="text-foreground">{domainSummary.total_mastered} de {domainSummary.total_subtemas} focos</strong> ({domainSummary.overall_domain_pct}%)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {domainSummary.areas.map(area => {
              const accFormatted = area.accuracy != null ? `${Math.round(area.accuracy * 100)}%` : "--";
              return (
                <div 
                  key={area.area}
                  className="bg-card border border-border/50 rounded-2xl p-4 flex flex-col justify-between shadow-2xs hover:shadow-xs hover:border-border transition-all group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-foreground truncate max-w-[130px]">{area.area}</span>
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                        {accFormatted}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-1 my-1">
                      <span className="text-lg font-black text-foreground">{area.mastered_subtemas}</span>
                      <span className="text-xs text-muted-foreground">/ {area.total_subtemas} dominados</span>
                    </div>
                  </div>

                  <div className="mt-3">
                    <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${area.domain_pct}%` }}
                      />
                    </div>
                    <div className="flex justify-between items-center mt-2 text-[11px] text-muted-foreground">
                      <span>{area.domain_pct}%</span>
                      <Link href={`/estudar?area=${encodeURIComponent(area.area)}&status=all`} className="hover:text-primary transition-colors font-medium">
                        Treinar &rarr;
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Seção Dupla: Recuperação de Gargalos (Medcof) + Caderno de Erros */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Coluna Esquerda: Recuperação de Gargalos (Worst Tags - Medcof) */}
        <div className={clsx(errorNotebook && errorNotebook.ever_wrong_count > 0 ? "lg:col-span-7" : "lg:col-span-12")}>
          <div className="bg-card border border-border/50 rounded-3xl p-6 flex flex-col justify-between h-full shadow-2xs hover:shadow-xs transition-all">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5 text-amber-600 dark:text-amber-400">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center ring-1 ring-amber-500/20">
                    <span className="material-symbols-outlined text-[18px]" data-icon="report_problem">report_problem</span>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-foreground">Recuperação de Gargalos Críticos</h3>
                    <p className="text-xs text-muted-foreground">Tópicos com maior concentração de erros recentes</p>
                  </div>
                </div>
              </div>

              {bottlenecks.length > 0 ? (
                <div className="flex flex-col gap-3">
                  {bottlenecks.map(b => (
                    <div 
                      key={b.subtema} 
                      className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-muted/20 hover:bg-muted/40 border border-border/30 transition-all gap-3"
                    >
                      <div className="flex flex-col min-w-0">
                        <span className="font-semibold text-sm text-foreground truncate">{b.subtema}</span>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                          <span className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-bold">{b.area}</span>
                          <span>{b.wrong_count} erro(s) em {b.attempts} tentativas</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 self-end sm:self-center">
                        <span className="text-xs font-bold px-2 py-1 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
                          {b.accuracy_pct}% acertos
                        </span>
                        <Link 
                          href={b.practice_url} 
                          className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-1 shadow-2xs"
                        >
                          <span className="material-symbols-outlined text-[14px]" data-icon="play_arrow">play_arrow</span> Treinar
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground">
                  <span className="material-symbols-outlined text-3xl text-emerald-500 mb-2" data-icon="check_circle">check_circle</span>
                  <p className="text-sm font-semibold text-foreground">Nenhum gargalo crítico detectado!</p>
                  <p className="text-xs mt-1 max-w-sm">Continue resolvendo questões para calibrar o diagnóstico inteligente de pontos fracos.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Coluna Direita: Caderno de Erros (Ever Answered Wrong - Medcof) */}
        {errorNotebook && errorNotebook.ever_wrong_count > 0 && (
          <div className="lg:col-span-5">
            <div className="bg-gradient-to-br from-rose-500/10 via-card to-card border border-rose-500/20 rounded-3xl p-6 flex flex-col justify-between h-full shadow-2xs">
              <div>
                <div className="flex items-center gap-2.5 mb-3 text-rose-600 dark:text-rose-400">
                  <div className="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center ring-1 ring-rose-500/20">
                    <span className="material-symbols-outlined text-[18px]" data-icon="edit_note">edit_note</span>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-foreground">Caderno de Erros</h3>
                    <p className="text-xs text-muted-foreground">Revisão focada nas questões erradas</p>
                  </div>
                </div>

                <div className="my-4 p-4 rounded-2xl bg-card border border-border/50">
                  <p className="text-3xl font-black text-rose-600 dark:text-rose-400 tracking-tight">
                    {errorNotebook.currently_unresolved_count}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Questões com erros ainda não revertidos em acerto (de um total de {errorNotebook.ever_wrong_count} questões já erradas).
                  </p>
                </div>
              </div>

              <Link 
                href={errorNotebook.practice_url} 
                className="w-full py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl transition-all text-sm flex items-center justify-center gap-2 shadow-xs"
              >
                <span className="material-symbols-outlined text-[18px]" data-icon="replay">replay</span> Zerar Caderno de Erros
              </Link>
            </div>
          </div>
        )}
      </motion.div>

      {/* Bento Grid Layout (Radar + Heatmap + Métricas) */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-2">
        <div className="lg:col-span-12">
          {stats.distinct_answered === 0 ? (
            <div className="bg-card border border-border/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center h-full shadow-xs">
              <motion.div 
                animate={{ y: [0, -10, 0] }} 
                transition={{ repeat: Infinity, duration: 2 }}
                className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mb-6 ring-1 ring-primary/20 shadow-inner"
              >
                <span className="material-symbols-outlined text-3xl" data-icon="school">school</span>
              </motion.div>
              <h3 className="text-2xl font-bold text-foreground mb-3 tracking-tight">Bem-vindo(a) ao MedQuest!</h3>
              <p className="text-base text-muted-foreground max-w-md mb-8">
                Você ainda não respondeu nenhuma questão. Que tal começar agora mesmo e testar seus conhecimentos?
              </p>
              <Link href="/estudar" className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-semibold hover:opacity-90 transition-opacity shadow-xs">
                Explorar Banco de Questões
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-5 h-full w-full">
              
              {/* Radar Chart (Col Span 4) */}
              {breakdownStats && breakdownStats.length > 0 && (
                <div className="lg:col-span-4 bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group min-h-[250px]">
                  {renderRadar()}
                </div>
              )}

              {/* Heatmap (Col Span 4 or 8) */}
              {timelineStats && timelineStats.length > 0 && (
                <div className={clsx("bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group overflow-hidden", breakdownStats && breakdownStats.length > 0 ? "lg:col-span-4" : "lg:col-span-8")}>
                  {renderHeatmap()}
                </div>
              )}

              {/* Small Stats Group (Col Span 4) */}
              <div className="lg:col-span-4 grid grid-cols-2 gap-4">
                {/* Stat Card 1 */}
                <div className="bg-card border border-border/50 rounded-2xl p-4 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group">
                  <div className="flex items-center gap-2 mb-2 text-primary transition-transform group-hover:translate-x-1">
                    <span className="material-symbols-outlined text-[18px]" data-icon="task_alt">task_alt</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Questões</span>
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-black text-foreground tracking-tight">{stats.distinct_answered}</span>
                  </div>
                </div>

                {/* Stat Card 2 */}
                <div className="bg-card border border-border/50 rounded-2xl p-4 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group">
                  <div className="flex items-center gap-2 mb-2 text-primary transition-transform group-hover:translate-x-1">
                    <span className="material-symbols-outlined text-[18px]" data-icon="my_location">my_location</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Acurácia</span>
                  </div>
                  <div>
                    <span className="text-2xl font-black text-foreground tracking-tight">{accuracyFormatted}</span>
                  </div>
                </div>

                {/* Stat Card 3 (Streak) */}
                <div className="bg-orange-500/5 dark:bg-orange-500/10 border border-orange-500/20 rounded-2xl p-4 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-orange-500/30 group relative overflow-hidden">
                  <div className="absolute -top-4 -right-4 p-2 opacity-[0.03] dark:opacity-10 group-hover:opacity-10 transition-opacity pointer-events-none">
                    <span className="material-symbols-outlined text-5xl text-orange-600">self_improvement</span>
                  </div>
                  <div className="flex items-center gap-2 mb-2 text-orange-600 dark:text-orange-400 transition-transform group-hover:translate-x-1 relative z-10">
                    <span className="material-symbols-outlined text-[18px] animate-pulse" data-icon="local_fire_department">local_fire_department</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider">Ofensiva</span>
                  </div>
                  <div className="relative z-10 flex items-baseline gap-1">
                    <span className="text-2xl font-black text-orange-700 dark:text-orange-400 tracking-tight">{stats.streak_days}</span>
                    <span className="text-xs text-orange-600/70 dark:text-orange-400/70 font-semibold">dias</span>
                  </div>
                </div>

                {/* Stat Card 4 (Nível XP) */}
                <div className="bg-card border border-border/50 rounded-2xl p-4 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5 text-indigo-500 transition-transform group-hover:translate-x-1">
                      <span className="material-symbols-outlined text-[18px]" data-icon="social_leaderboard">social_leaderboard</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Nível</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-baseline gap-1 mb-1">
                      <span className="text-2xl font-black text-indigo-700 dark:text-indigo-400 tracking-tight">Lvl {nivelAtual}</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden ring-1 ring-inset ring-black/5 dark:ring-white/5">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${progressoNivel}%` }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                        className="bg-indigo-500 h-1.5 rounded-full shadow-inner" 
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Offline Panel */}
        <div className="lg:col-span-12 flex flex-col">
          <OfflinePanel />
        </div>
      </motion.div>
    </motion.div>
  );
}

