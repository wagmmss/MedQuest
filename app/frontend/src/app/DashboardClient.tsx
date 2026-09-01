"use client";

import Link from "next/link";
import { 
  OverviewStats, PlannerWeek, PlannerTopic,
  BenchmarkStat, BottleneckTopic, DomainSummaryResponse, ErrorNotebookSummary 
} from "@/types/api";
import { OfflineModal } from "@/components/OfflineModal";
import { motion, Variants } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { 
  BarChart3, Brain, Play, Clock, ArrowRight, Target, Sparkles, TrendingUp, AlertTriangle, Lightbulb, RefreshCw, Layers
} from "lucide-react";
import { readLearningSession, syncSessionFromCloud } from "@/lib/sessionState";
import { triggerConfetti } from "@/lib/confetti";
import clsx from "clsx";

interface DashboardClientProps {
  stats: OverviewStats;
  currentPlannerWeek: PlannerWeek | null;
  suggestedPlannerTopic?: PlannerTopic | null;
  remainingPlannerMetas?: number;
  totalPlannerMetas?: number;
  isPlanCompleted?: boolean;
  firstName: string;
  benchmarkStats?: BenchmarkStat | null;
  bottlenecks?: BottleneckTopic[];
  domainSummary?: DomainSummaryResponse | null;
  errorNotebook?: ErrorNotebookSummary | null;
}

export function DashboardClient({ 
  stats, 
  currentPlannerWeek, 
  suggestedPlannerTopic,
  remainingPlannerMetas,
  totalPlannerMetas,
  isPlanCompleted,
  firstName, 
  benchmarkStats,
  bottlenecks = [],
  domainSummary,
  errorNotebook,
}: DashboardClientProps) {
  const hasAnimated = useRef(false);
  const [activeSession, setActiveSession] = useState<{ kind: "quiz" | "simulado"; url: string } | null>(null);
  const [isOfflineModalOpen, setIsOfflineModalOpen] = useState(false);

  useEffect(() => {
    // Dispara confete se as revisões diárias estiverem zeradas e houver pelo menos 1 questão feita
    if (stats.srs_due_count === 0 && (stats.flashcards_due_count || 0) === 0 && stats.distinct_answered > 0 && !hasAnimated.current) {
      hasAnimated.current = true;
      triggerConfetti();
    }
  }, [stats]);

  useEffect(() => {
    // Check for active sessions
    const checkSessions = async () => {
      // Sincroniza da nuvem de forma assíncrona para não travar o carregamento
      await Promise.allSettled([
        syncSessionFromCloud<{ state?: string }>("simulado", (val): val is { state?: string } => typeof val === "object" && val !== null),
        syncSessionFromCloud<{ state?: string }>("quiz", (val): val is { state?: string } => typeof val === "object" && val !== null)
      ]);

      const hasSimulado = readLearningSession<{ state?: string }>(
        "simulado",
        (val): val is { state?: string } => typeof val === "object" && val !== null
      );
      if (hasSimulado?.state && hasSimulado.state !== "RESULTS" && hasSimulado.state !== "OFFLINE_SUBMITTED") {
        setActiveSession({ kind: "simulado", url: "/simulado" });
      } else {
        const hasQuiz = readLearningSession<{ state?: string }>(
          "quiz",
          (val): val is { state?: string } => typeof val === "object" && val !== null
        );
        if (hasQuiz?.state && hasQuiz.state !== "RESULTS") {
          setActiveSession({ kind: "quiz", url: "/estudar?resume=true" });
        }
      }
    };
    checkSessions();
  }, []);

  // Listen to open-offline-modal custom event
  useEffect(() => {
    const handleOpenOffline = () => setIsOfflineModalOpen(true);
    window.addEventListener("open-offline-modal", handleOpenOffline);
    return () => window.removeEventListener("open-offline-modal", handleOpenOffline);
  }, []);

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.06 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 8 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 320, damping: 26 } }
  };

  // Métricas de Decisão Diária
  const pendentesRevisao = (stats.srs_due_count || 0) + (stats.flashcards_due_count || 0);
  const dailyTarget = stats.daily_target || 20;
  const todayDone = stats.today_answered || 0;
  const dailyRemaining = Math.max(0, dailyTarget - todayDone);
  const dailyProgressPct = Math.min(100, Math.round((todayDone / dailyTarget) * 100));

  const sugestaoTema = suggestedPlannerTopic
    ? suggestedPlannerTopic.subtema 
    : (bottlenecks.length > 0 ? bottlenecks[0].subtema : "Clínica Médica");

  const sugestaoArea = suggestedPlannerTopic
    ? suggestedPlannerTopic.area
    : (bottlenecks.length > 0 ? bottlenecks[0].area : "");

  const topBottleneck = bottlenecks.length > 0 ? bottlenecks[0] : null;

  const totalAttempts = benchmarkStats?.total_attempts || stats.total_attempts || 0;
  const targetScorePct = stats.target_score || benchmarkStats?.target_score_pct || 76;
  const overallAccPct = stats.accuracy_all_attempts != null ? stats.accuracy_all_attempts * 100 : null;
  const diffPct = overallAccPct != null ? parseFloat((overallAccPct - targetScorePct).toFixed(1)) : null;

  // Semanas do planner
  const plannerWeekNum = suggestedPlannerTopic ? (currentPlannerWeek?.week || null) : null;
  const plannerMetasCount = remainingPlannerMetas !== undefined ? remainingPlannerMetas : (currentPlannerWeek?.topics?.length || 0);
  const totalMetasCount = totalPlannerMetas !== undefined ? totalPlannerMetas : (currentPlannerWeek?.topics?.length || 0);

  // Subtítulo Contextual Direto
  const subtitleMessage = (() => {
    if (stats.distinct_answered === 0) {
      return "Defina seu plano e resolva 20 questões para calibrar seu diagnóstico inicial.";
    }
    if (pendentesRevisao > 0) {
      return `Foco de hoje: ${pendentesRevisao} revisões pendentes para blindar sua curva de esquecimento.`;
    }
    if (dailyRemaining > 0) {
      return `Você está a ${dailyRemaining} questões de bater a meta diária de hoje.`;
    }
    return "Todas as metas de estudo de hoje concluídas! Excelente consistência.";
  })();

  // Determina a Ação Principal (Hero CTA)
  const renderPrimaryAction = () => {
    // 1. Retomar sessão ativa
    if (activeSession) {
      return (
        <div className="bg-primary text-primary-foreground rounded-2xl p-5 sm:p-6 shadow-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative overflow-hidden group">
          <div className="flex items-center gap-4 relative z-10">
            <div className="w-12 h-12 rounded-xl bg-primary-foreground/20 flex items-center justify-center text-primary-foreground shrink-0">
              <span className="material-symbols-outlined text-[28px]" data-icon={activeSession.kind === "simulado" ? "history_edu" : "play_lesson"}>
                {activeSession.kind === "simulado" ? "history_edu" : "play_lesson"}
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-primary-foreground/25">
                  Sessão em Andamento
                </span>
              </div>
              <h3 className="text-lg sm:text-xl font-bold">Retomar {activeSession.kind === "simulado" ? "Simulado" : "Sessão de Estudos"}</h3>
              <p className="text-xs sm:text-sm text-primary-foreground/80 font-medium">Continue de onde você parou para não perder o ritmo.</p>
            </div>
          </div>
          <Link 
            href={activeSession.url} 
            className="w-full sm:w-auto px-5 py-2.5 font-bold bg-primary-foreground text-primary rounded-xl hover:bg-white hover:scale-[1.02] transition-all flex items-center justify-center gap-2 shadow-xs shrink-0"
          >
            Continuar sessão <span className="material-symbols-outlined text-[18px]" data-icon="arrow_forward">arrow_forward</span>
          </Link>
        </div>
      );
    }

    // 2. Revisões vencidas no FSRS
    if (pendentesRevisao > 0) {
      const estimatedMinutes = Math.max(5, Math.ceil(pendentesRevisao * 1.5));
      const srsCount = stats.srs_due_count || 0;
      const flashcardsCount = stats.flashcards_due_count || 0;

      return (
        <div className="bg-card border-2 border-purple-500/30 dark:border-purple-500/20 bg-gradient-to-r from-purple-500/5 via-card to-card rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative overflow-hidden">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 ring-1 ring-purple-500/20 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-[26px]" data-icon="psychology">psychology</span>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-500/10 text-purple-600 dark:text-purple-400">
                  Próxima Ação Prioritária
                </span>
                <span className="text-xs text-muted-foreground">• ~{estimatedMinutes} min</span>
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-foreground">
                {pendentesRevisao} revisões vencidas hoje
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Reforce os conceitos no tempo ideal do FSRS antes de resolver questões inéditas.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            {flashcardsCount > 0 && (
              <Link 
                href="/revisao-ativa" 
                className="flex-1 sm:flex-initial px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl text-xs sm:text-sm transition-all flex items-center justify-center gap-1.5 shadow-xs"
              >
                <span className="material-symbols-outlined text-[16px]" data-icon="auto_awesome">auto_awesome</span> Flashcards ({flashcardsCount})
              </Link>
            )}
            {srsCount > 0 && (
              <Link 
                href="/estudar?status=srs_due&limit=100" 
                className="flex-1 sm:flex-initial px-4 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-bold rounded-xl text-xs sm:text-sm transition-all flex items-center justify-center gap-1.5 shadow-xs"
              >
                <span className="material-symbols-outlined text-[16px]" data-icon="replay">replay</span> Questões ({srsCount})
              </Link>
            )}
          </div>
        </div>
      );
    }

    // 3. Meta diária de questões novas pendente
    if (dailyRemaining > 0) {
      const practiceUrl = suggestedPlannerTopic
        ? `/estudar?subtema=${encodeURIComponent(sugestaoTema)}&status=new&limit=${Math.min(20, dailyRemaining)}`
        : bottlenecks.length > 0
        ? `/estudar?subtema=${encodeURIComponent(bottlenecks[0].subtema)}&status=new&limit=${Math.min(20, dailyRemaining)}`
        : `/estudar?status=new&limit=${Math.min(20, dailyRemaining)}`;

      return (
        <div className="bg-card border-2 border-primary/30 bg-gradient-to-r from-primary/5 via-card to-card rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative overflow-hidden">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-[26px]" data-icon="play_arrow">play_arrow</span>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary">
                  Meta de Hoje
                </span>
                <span className="text-xs text-muted-foreground">• {todayDone}/{dailyTarget} concluídas</span>
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-foreground">
                {dailyRemaining} questões para bater sua meta de hoje
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Tópico sugerido: <strong className="text-foreground">{sugestaoTema}</strong> {sugestaoArea ? `(${sugestaoArea})` : ""}
              </p>
            </div>
          </div>

          <Link 
            href={practiceUrl}
            className="w-full sm:w-auto px-5 py-2.5 font-bold bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-all flex items-center justify-center gap-2 shadow-xs shrink-0"
          >
            Iniciar bateria ({Math.min(20, dailyRemaining)} Qs) <span className="material-symbols-outlined text-[18px]" data-icon="arrow_forward">arrow_forward</span>
          </Link>
        </div>
      );
    }

    // 4. Todas as metas do dia concluídas
    if (topBottleneck) {
      return (
        <div className="bg-card border border-emerald-500/30 bg-gradient-to-r from-emerald-500/5 via-card to-card rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative overflow-hidden">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-[26px]" data-icon="check_circle">check_circle</span>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  Metas Diárias Concluídas 🎉
                </span>
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-foreground">
                Aproveite para reforçar seu maior gargalo
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground">
                {topBottleneck.subtema}: <strong className="text-amber-600 dark:text-amber-400">{topBottleneck.accuracy_pct}%</strong> em {topBottleneck.attempts} questões ({topBottleneck.wrong_count} erros)
              </p>
            </div>
          </div>

          <Link 
            href={topBottleneck.practice_url}
            className="w-full sm:w-auto px-5 py-2.5 font-bold bg-amber-500 hover:bg-amber-600 text-white rounded-xl transition-all flex items-center justify-center gap-2 shadow-xs shrink-0"
          >
            Treinar gargalo (10 Qs) <span className="material-symbols-outlined text-[18px]" data-icon="play_arrow">play_arrow</span>
          </Link>
        </div>
      );
    }

    return (
      <div className="bg-card border border-emerald-500/30 bg-gradient-to-r from-emerald-500/5 via-card to-card rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20 flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-[26px]" data-icon="done_all">done_all</span>
          </div>
          <div>
            <h3 className="text-lg sm:text-xl font-bold text-foreground">Metas de hoje cumpridas com sucesso!</h3>
            <p className="text-xs sm:text-sm text-muted-foreground">Você está mantendo sua consistência em dia. Descanse ou avance no cronograma semanal.</p>
          </div>
        </div>
        <Link 
          href="/planner" 
          className="w-full sm:w-auto px-4 py-2 bg-muted hover:bg-muted/80 text-foreground font-semibold rounded-xl text-xs sm:text-sm transition-colors flex items-center justify-center gap-1.5"
        >
          Acessar Planner
        </Link>
      </div>
    );
  };

  return (
    <motion.div 
      variants={containerVariants} 
      initial="hidden" 
      animate="show"
      className="flex flex-col gap-6 md:gap-8 pt-2 pb-10 max-w-6xl mx-auto"
    >
      {/* Header: Saudação & Contagem Regressiva */}
      <motion.section variants={itemVariants} className="flex flex-col gap-1">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Olá, {firstName}
            </h2>
            <p className="text-muted-foreground text-sm md:text-base mt-0.5">
              {subtitleMessage}
            </p>
          </div>

          {/* Badge Contagem Regressiva da Prova */}
          <div className="self-start sm:self-auto">
            {stats.days_until_exam != null ? (
              <div className="flex items-center gap-2 bg-card border border-border/80 rounded-2xl px-4 py-2 shadow-2xs">
                <span className="material-symbols-outlined text-primary text-[18px]" data-icon="event">event</span>
                <span className="text-xs text-muted-foreground font-medium">Prova em:</span>
                <span className="text-xs font-bold text-foreground">{stats.days_until_exam} dias</span>
              </div>
            ) : stats.exam_date ? (
              <div className="flex items-center gap-2 bg-card border border-border/80 rounded-2xl px-4 py-2 shadow-2xs">
                <span className="material-symbols-outlined text-primary text-[18px]" data-icon="flag">flag</span>
                <span className="text-xs text-muted-foreground font-medium">Data-alvo:</span>
                <span className="text-xs font-bold text-foreground">
                  {new Date(stats.exam_date).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                </span>
              </div>
            ) : (
              <Link 
                href="/planner" 
                className="flex items-center gap-1.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-2xl px-3.5 py-1.5 text-xs font-bold transition-colors"
              >
                <span className="material-symbols-outlined text-[16px]" data-icon="calendar_month">calendar_month</span>
                Definir data da prova &rarr;
              </Link>
            )}
          </div>
        </div>
      </motion.section>

      {/* ESTADO ZERO (ONBOARDING DIRETO) */}
      {stats.distinct_answered === 0 ? (
        <motion.div variants={itemVariants} className="bg-card border border-border/80 rounded-3xl p-6 sm:p-8 shadow-xs">
          <div className="flex flex-col sm:flex-row items-center gap-6 mb-6">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center ring-1 ring-primary/20 shadow-inner shrink-0">
              <span className="material-symbols-outlined text-3xl" data-icon="school">school</span>
            </div>
            <div className="text-center sm:text-left">
              <h3 className="text-xl sm:text-2xl font-bold text-foreground mb-1">
                Boas-vindas ao MedQuest!
              </h3>
              <p className="text-sm text-muted-foreground max-w-xl">
                Seu painel inteligente é calibrado a cada questão respondida. Siga os 2 passos abaixo para configurar seu direcionamento:
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Passo 1 */}
            <div className="p-5 rounded-2xl bg-muted/20 border border-border/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2 text-primary font-bold text-xs uppercase tracking-wider">
                  <span className="w-5 h-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">1</span>
                  Planejamento
                </div>
                <h4 className="font-bold text-foreground text-base mb-1">Defina sua Prova e Meta</h4>
                <p className="text-xs text-muted-foreground mb-4">
                  Informe a data do seu exame e horas semanais para receber sugestões de cronograma.
                </p>
              </div>
              <Link 
                href="/planner" 
                className="w-full py-2.5 px-4 bg-muted hover:bg-muted/80 text-foreground border border-border font-semibold rounded-xl text-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <span className="material-symbols-outlined text-[16px]" data-icon="tune">tune</span> Configurar no Planner
              </Link>
            </div>

            {/* Passo 2 */}
            <div className="p-5 rounded-2xl bg-primary/5 border border-primary/20 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2 text-primary font-bold text-xs uppercase tracking-wider">
                  <span className="w-5 h-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">2</span>
                  Diagnóstico Inicial
                </div>
                <h4 className="font-bold text-foreground text-base mb-1">Faça 20 Questões de Teste</h4>
                <p className="text-xs text-muted-foreground mb-4">
                  Calibre seu diagnóstico inicial de pontos fracos, retenção e faixa estimada de prontidão.
                </p>
              </div>
              <Link 
                href="/estudar?limit=20" 
                className="w-full py-2.5 px-4 bg-primary hover:bg-primary/90 text-primary-foreground font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs"
              >
                <span className="material-symbols-outlined text-[16px]" data-icon="play_arrow">play_arrow</span> Iniciar 20 Questões
              </Link>
            </div>
          </div>
        </motion.div>
      ) : (
        <>
          {/* AÇÃO PRINCIPAL / HERO PRIORITÁRIO */}
          <motion.section variants={itemVariants}>
            {renderPrimaryAction()}
          </motion.section>

          {/* PLANO DE HOJE (Card Integrado em 3 Pilares) */}
          <motion.section variants={itemVariants} className="bg-card border border-border/70 rounded-3xl p-5 sm:p-6 shadow-2xs">
            <div className="flex items-center justify-between gap-2 mb-4 pb-3 border-b border-border/50">
              <div className="flex items-center gap-2 text-foreground">
                <span className="material-symbols-outlined text-primary text-[20px]" data-icon="today">today</span>
                <h3 className="text-base font-bold tracking-tight">Plano de Hoje</h3>
              </div>
              <span className="text-xs text-muted-foreground">Metas personalizadas diárias</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Pilar 1: Revisões */}
              <div className="p-4 rounded-2xl bg-muted/20 border border-border/40 flex flex-col justify-between gap-3">
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold text-purple-600 dark:text-purple-400 mb-1">
                    <span className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-[16px]" data-icon="psychology">psychology</span> Revisão Ativa
                    </span>
                    {pendentesRevisao === 0 && (
                      <span className="inline-flex items-center gap-0.5 text-emerald-600 dark:text-emerald-400 text-[11px] font-bold">
                        <span className="material-symbols-outlined text-[14px]" data-icon="done">done</span> Em dia
                      </span>
                    )}
                  </div>
                  <p className="text-2xl font-bold text-foreground tracking-tight">
                    {pendentesRevisao > 0 ? `${pendentesRevisao} pendentes` : "Tudo em dia!"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {stats.flashcards_due_count || 0} flashcards · {stats.srs_due_count || 0} questões
                  </p>
                </div>
                {pendentesRevisao > 0 ? (
                  <Link 
                    href={(stats.flashcards_due_count || 0) > 0 ? "/revisao-ativa" : "/estudar?status=srs_due&limit=100"}
                    className="w-full py-2 bg-purple-500/10 hover:bg-purple-500/20 text-purple-700 dark:text-purple-300 font-bold rounded-xl text-xs flex items-center justify-center gap-1 transition-colors"
                  >
                    Revisar agora &rarr;
                  </Link>
                ) : (
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="verified">verified</span> Sem revisões atrasadas
                  </span>
                )}
              </div>

              {/* Pilar 2: Questões Novas */}
              <div className="p-4 rounded-2xl bg-muted/20 border border-border/40 flex flex-col justify-between gap-3">
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">
                    <span className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-[16px]" data-icon="post_add">post_add</span> Questões do Dia
                    </span>
                    <span className="text-xs font-bold text-foreground">{todayDone}/{dailyTarget}</span>
                  </div>
                  <p className="text-2xl font-bold text-foreground tracking-tight">
                    {dailyRemaining > 0 ? `${dailyRemaining} restantes` : "Meta batida! 🎉"}
                  </p>
                  <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden mt-2">
                    <div 
                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${dailyProgressPct}%` }}
                    />
                  </div>
                </div>
                <Link 
                  href={`/estudar?status=new&limit=${Math.min(20, Math.max(5, dailyRemaining))}`}
                  className="w-full py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-700 dark:text-blue-300 font-bold rounded-xl text-xs flex items-center justify-center gap-1 transition-colors"
                >
                  {dailyRemaining > 0 ? "Praticar questões &rarr;" : "Fazer questões extras &rarr;"}
                </Link>
              </div>

              {/* Pilar 3: Tema Sugerido */}
              <div className="p-4 rounded-2xl bg-muted/20 border border-border/40 flex flex-col justify-between gap-3">
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold text-primary mb-1">
                    <span className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-[16px]" data-icon="calendar_month">calendar_month</span> Tema Sugerido
                    </span>
                    {plannerWeekNum && <span className="text-[11px] text-muted-foreground">Semana {plannerWeekNum}</span>}
                    {isPlanCompleted && <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-bold">100% Concluído</span>}
                  </div>
                  <p className="text-base font-bold text-foreground line-clamp-1" title={sugestaoTema}>
                    {isPlanCompleted ? "Plano 100% Concluído! 🎉" : sugestaoTema}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {isPlanCompleted
                      ? "Parabéns! Todas as metas do cronograma foram finalizadas."
                      : suggestedPlannerTopic
                      ? `${plannerMetasCount} ${plannerMetasCount === 1 ? "meta restante" : "metas restantes"} no cronograma semanal`
                      : "Baseado nas prioridades do edital"}
                  </p>
                </div>
                <Link 
                  href={
                    isPlanCompleted
                      ? "/planner"
                      : suggestedPlannerTopic
                      ? `/estudar?subtema=${encodeURIComponent(sugestaoTema)}&limit=20`
                      : bottlenecks.length > 0
                      ? `/estudar?subtema=${encodeURIComponent(bottlenecks[0].subtema)}&limit=20`
                      : "/planner"
                  }
                  className="w-full py-2 bg-primary/10 hover:bg-primary/20 text-primary font-bold rounded-xl text-xs flex items-center justify-center gap-1 transition-colors"
                >
                  {isPlanCompleted ? "Ver cronograma &rarr;" : "Continuar plano &rarr;"}
                </Link>
              </div>
            </div>
          </motion.section>

          {/* ERROS PRIORITÁRIOS & GARGALOS CRÍTICOS (UNIFICADO) */}
          <motion.section variants={itemVariants} className="bg-card border border-border/70 rounded-3xl p-5 sm:p-6 shadow-2xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-border/50">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center ring-1 ring-amber-500/20">
                  <span className="material-symbols-outlined text-[18px]" data-icon="report_problem">report_problem</span>
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">Erros Prioritários & Gargalos de Maior Impacto</h3>
                  <p className="text-xs text-muted-foreground">Foco estratégico nos temas com maior taxa de erro e questões a reverter</p>
                </div>
              </div>

              {/* Badge / Acesso ao Caderno de Erros */}
              {errorNotebook && errorNotebook.currently_unresolved_count > 0 && (
                <Link 
                  href={errorNotebook.practice_url}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/20 text-xs font-bold transition-colors self-start sm:self-auto"
                >
                  <span className="material-symbols-outlined text-[16px]" data-icon="edit_note">edit_note</span>
                  <span>{errorNotebook.currently_unresolved_count} erros em aberto</span>
                  <span className="material-symbols-outlined text-[14px]" data-icon="arrow_forward">arrow_forward</span>
                </Link>
              )}
            </div>

            {bottlenecks.length > 0 ? (
              <div className="flex flex-col gap-2.5">
                {bottlenecks.slice(0, 3).map((b) => (
                  <div 
                    key={b.subtema}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-2xl bg-muted/20 hover:bg-muted/35 border border-border/40 transition-all gap-3"
                  >
                    <div className="flex flex-col min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-foreground truncate">{b.subtema}</span>
                        <span className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-bold shrink-0">{b.area}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                        <span>Amostra: <strong className="text-foreground">{b.attempts} tentativas</strong> ({b.wrong_count} erros)</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-end sm:self-center shrink-0">
                      <span className={clsx(
                        "text-xs font-bold px-2.5 py-1 rounded-lg",
                        b.accuracy_pct < 50 ? "bg-destructive/10 text-destructive" : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                      )}>
                        {b.accuracy_pct}% acertos
                      </span>
                      <Link 
                        href={b.practice_url}
                        className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-xl transition-colors flex items-center gap-1 shadow-2xs"
                      >
                        <span className="material-symbols-outlined text-[14px]" data-icon="play_arrow">play_arrow</span> Treinar
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-muted-foreground flex flex-col items-center justify-center gap-2">
                <span className="material-symbols-outlined text-3xl text-emerald-500" data-icon="check_circle">check_circle</span>
                <p className="text-sm font-semibold text-foreground">Nenhum gargalo crítico no momento!</p>
                <p className="text-xs max-w-sm">Continue respondendo questões para calibrar o diagnóstico contínuo.</p>
              </div>
            )}
          </motion.section>

          {/* RITMO DA SEMANA (COMPACTO) */}
          {benchmarkStats && (
            <motion.section variants={itemVariants} className="bg-card border border-border/70 rounded-3xl p-5 sm:p-6 shadow-2xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2.5">
                  <span className="material-symbols-outlined text-blue-500 text-[20px]" data-icon="speed">speed</span>
                  <div>
                    <h3 className="text-sm font-bold text-foreground">Ritmo da Semana</h3>
                    <p className="text-xs text-muted-foreground">
                      {benchmarkStats.last7_attempts} de {benchmarkStats.weekly_target_questions} questões nos últimos 7 dias
                      {benchmarkStats.accuracy_last7 != null && (
                        <span> · <strong className="text-foreground">{Math.round(benchmarkStats.accuracy_last7 * 100)}%</strong> de acerto recente</span>
                      )}
                    </p>
                  </div>
                </div>

                <Link 
                  href="/analise" 
                  className="text-xs font-bold text-primary hover:underline flex items-center gap-1 self-start sm:self-auto"
                >
                  Ver análise detalhada <span className="material-symbols-outlined text-[14px]" data-icon="arrow_forward">arrow_forward</span>
                </Link>
              </div>

              <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${benchmarkStats.weekly_progress_pct}%` }}
                />
              </div>
            </motion.section>
          )}

          {/* FAIXA ESTIMADA DE PRONTIDÃO (BENCHMARK PROBABILÍSTICO CONDICIONAL: APENAS SE >= 20 QUESTÕES) */}
          {stats.distinct_answered >= 20 && benchmarkStats && overallAccPct != null && (
            <motion.section variants={itemVariants} className="bg-card border border-border/70 rounded-3xl p-5 sm:p-6 shadow-2xs relative overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center ring-1 ring-primary/20">
                    <span className="material-symbols-outlined text-[18px]" data-icon="analytics">analytics</span>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-foreground">Faixa Estimada de Prontidão</h3>
                    <p className="text-xs text-muted-foreground">
                      Estimativa preliminar baseada em {totalAttempts} tentativas vs. Meta de corte ({targetScorePct}%)
                    </p>
                  </div>
                </div>

                {/* Badge Probabilístico */}
                <div>
                  {diffPct != null && diffPct >= 0 ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-bold ring-1 ring-emerald-500/20">
                      <span className="material-symbols-outlined text-[14px]" data-icon="verified">verified</span>
                      Faixa Competitiva Estimada (+{diffPct}%)
                    </span>
                  ) : diffPct != null && diffPct >= -10 ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-bold ring-1 ring-blue-500/20">
                      <span className="material-symbols-outlined text-[14px]" data-icon="trending_up">trending_up</span>
                      Faixa de Aproximação ({diffPct}%)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 text-xs font-bold ring-1 ring-amber-500/20">
                      <span className="material-symbols-outlined text-[14px]" data-icon="fitness_center">fitness_center</span>
                      Fase de Consolidação ({diffPct}%)
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-2 p-3.5 bg-muted/20 border border-border/40 rounded-2xl">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground font-medium">Seu Acerto Geral vs. Meta</span>
                  <span className="font-bold text-foreground">
                    {overallAccPct.toFixed(1)}% <span className="text-muted-foreground font-normal text-[11px]">/ Meta: {targetScorePct}%</span>
                  </span>
                </div>

                <div className="relative w-full bg-muted rounded-full h-2.5 overflow-hidden ring-1 ring-inset ring-black/5 dark:ring-white/5">
                  <div 
                    className="bg-primary h-2.5 rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(100, Math.max(0, overallAccPct))}%` }}
                  />
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-foreground/80 z-20"
                    style={{ left: `${targetScorePct}%` }}
                    title={`Meta: ${targetScorePct}%`}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-muted-foreground mt-0.5">
                  <span>0%</span>
                  <span className="font-semibold text-foreground/80">Meta de Corte: {targetScorePct}%</span>
                  <span>100%</span>
                </div>
              </div>

              <p className="text-[11px] text-muted-foreground mt-2">
                * A acurácia por Grande Área e o desempenho em simulados refinam a projeção na aba <Link href="/analise" className="text-primary font-semibold hover:underline">Análise</Link>.
              </p>
            </motion.section>
          )}

          {/* RESUMO DISCRETO DE CONTEXTO (BOTTOM STRIP) */}
          <motion.section variants={itemVariants} className="bg-card border border-border/60 rounded-2xl px-5 py-3.5 shadow-2xs">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex flex-wrap items-center gap-4 sm:gap-6 text-muted-foreground">
                <Link href="/cobertura" className="flex items-center gap-1.5 hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[16px] text-emerald-500" data-icon="domain_verification">domain_verification</span>
                  <span>
                    Cobertura: <strong className="text-foreground">
                      {domainSummary ? `${domainSummary.overall_domain_pct}% (${domainSummary.total_mastered}/${domainSummary.total_subtemas} focos)` : (stats.coverage_pct != null ? `${(stats.coverage_pct * 100).toFixed(0)}%` : "--")}
                    </strong>
                  </span>
                </Link>

                {errorNotebook && (
                  <Link href={errorNotebook.practice_url} className="flex items-center gap-1.5 hover:text-rose-500 transition-colors">
                    <span className="material-symbols-outlined text-[16px] text-rose-500" data-icon="edit_note">edit_note</span>
                    <span>
                      Caderno de Erros: <strong className="text-foreground">{errorNotebook.currently_unresolved_count} a revisar</strong>
                    </span>
                  </Link>
                )}

                <div className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[16px] text-orange-500" data-icon="local_fire_department">local_fire_department</span>
                  <span>
                    Sequência: <strong className="text-foreground">{stats.streak_days} dias</strong>
                  </span>
                </div>
              </div>

              <button
                onClick={() => setIsOfflineModalOpen(true)}
                className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-semibold px-2.5 py-1 rounded-lg bg-muted/40 hover:bg-muted transition-colors cursor-pointer border border-border/50"
                title="Abrir gerenciador do Modo Plantão (Offline)"
              >
                <span className="material-symbols-outlined text-[16px] text-primary" data-icon="cloud_download">cloud_download</span>
                Modo Plantão (Offline)
              </button>
            </div>
          </motion.section>
        </>
      )}

      {/* Modal do Modo Plantão (Offline) */}
      <OfflineModal 
        isOpen={isOfflineModalOpen} 
        onClose={() => setIsOfflineModalOpen(false)} 
      />
    </motion.div>
  );
}


