"use client";

import Link from "next/link";
import { OverviewStats, PlannerWeek } from "@/types/api";
import { OfflinePanel } from "@/components/OfflinePanel";
import { motion, Variants } from "framer-motion";
import { useEffect, useRef } from "react";
import { triggerConfetti } from "@/lib/confetti";
import clsx from "clsx";

interface DashboardClientProps {
  stats: OverviewStats;
  currentPlannerWeek: PlannerWeek | null;
  firstName: string;
}

export function DashboardClient({ stats, currentPlannerWeek, firstName }: DashboardClientProps) {
  const hasAnimated = useRef(false);

  useEffect(() => {
    // Dispara confete se as revisões diárias estiverem zeradas e houver pelo menos 1 questão feita
    if (stats.srs_due_count === 0 && stats.flashcards_due_count === 0 && stats.distinct_answered > 0 && !hasAnimated.current) {
      hasAnimated.current = true;
      triggerConfetti();
    }
  }, [stats]);

  const accuracyFormatted = stats.accuracy_all_attempts != null 
    ? (stats.accuracy_all_attempts * 100).toFixed(1) + "%" 
    : "--";

  const pendentes = (stats.srs_due_count || 0) + (stats.flashcards_due_count || 0);
  const xpAtual = stats.distinct_answered * 10;
  const nivelAtual = Math.floor(xpAtual / 100) + 1;
  const xpProximoNivel = nivelAtual * 100;
  const progressoNivel = (xpAtual % 100);

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  const motivationalMessages = [
    stats.streak_days >= 5 ? `Você estudou em ${stats.streak_days} dias da sua sequência. Descansos planejados não apagam seu progresso.` : null,
    currentPlannerWeek && currentPlannerWeek.week > 20 ? `Reta final! Você está na Semana ${currentPlannerWeek.week}.` : null,
    pendentes === 0 && stats.distinct_answered > 0 ? "Você já bateu sua meta diária de revisões! 🎉" : null,
    "Aqui está o seu progresso na preparação para a USP."
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
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
          Olá, {firstName}
        </h2>
        <p className="text-muted-foreground text-base md:text-lg">
          {motivationalMessage}
        </p>
      </motion.section>

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
            className="bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-all relative overflow-hidden group"
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
                  {stats.flashcards_due_count! > 0 && (
                    <Link href="/revisao-ativa" className="flex-1 w-full py-2.5 bg-purple-100 hover:bg-purple-200 text-purple-700 dark:bg-purple-500/10 dark:hover:bg-purple-500/20 dark:text-purple-300 font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2 ring-1 ring-purple-500/20">
                      <span className="material-symbols-outlined text-[18px]" data-icon="auto_awesome">auto_awesome</span> ({stats.flashcards_due_count})
                    </Link>
                  )}
                  {stats.srs_due_count! > 0 && (
                    <Link href="/estudar?status=srs_due&limit=100" className="flex-1 w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2 shadow-sm">
                      <span className="material-symbols-outlined text-[18px]" data-icon="psychology">psychology</span> ({stats.srs_due_count})
                    </Link>
                  )}
                </>
              ) : (
                <button disabled className="w-full py-2.5 bg-success/10 text-success font-semibold rounded-xl cursor-not-allowed text-sm flex items-center justify-center gap-2 ring-1 ring-success/20">
                  <span className="material-symbols-outlined text-[18px]" data-icon="done_all">done_all</span> Meta diária completa
                </button>
              )}
            </div>
          </motion.div>

          {/* Card 2: Questões Novas */}
          <motion.div 
            whileHover={{ y: -2 }}
            className="bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-all relative overflow-hidden group"
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
              <Link href={currentPlannerWeek && currentPlannerWeek.topics.length > 0 ? `/estudar?subtema=${encodeURIComponent(currentPlannerWeek.topics[0].subtema)}&status=new&limit=20` : "/estudar?status=new&limit=20"} className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all text-sm flex items-center justify-center gap-2 shadow-sm">
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
              <Link href="/planner" className="w-full py-2.5 bg-white/10 hover:bg-white/20 text-white border border-white/20 font-semibold rounded-xl transition-colors text-sm flex items-center justify-center gap-2 backdrop-blur-sm">
                <span className="material-symbols-outlined text-[18px]" data-icon="arrow_forward">arrow_forward</span> Acessar Planner
              </Link>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Bento Grid Layout */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-4">
        {/* Weekly Progress Summary (4 Stats) */}
        <div className="lg:col-span-8">
          {stats.distinct_answered === 0 ? (
            <div className="bg-card border border-border/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center h-full shadow-sm">
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
              <Link href="/estudar" className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-semibold hover:opacity-90 transition-opacity shadow-sm">
                Explorar Banco de Questões
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 h-full">
              {/* Stat Card 1 */}
              <div className="bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group">
                <div className="flex items-center gap-2 mb-4 text-primary transition-transform group-hover:translate-x-1">
                  <span className="material-symbols-outlined text-[20px]" data-icon="task_alt">task_alt</span>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Questões Feitas</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-black text-foreground tracking-tight">{stats.distinct_answered}</span>
                  <span className="text-sm text-muted-foreground font-semibold">únicas</span>
                </div>
              </div>

              {/* Stat Card 2 */}
              <div className="bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group">
                <div className="flex items-center gap-2 mb-4 text-primary transition-transform group-hover:translate-x-1">
                  <span className="material-symbols-outlined text-[20px]" data-icon="my_location">my_location</span>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Acurácia Geral</span>
                </div>
                <div>
                  <span className="text-4xl font-black text-foreground tracking-tight">{accuracyFormatted}</span>
                </div>
              </div>

              {/* Stat Card 3 (Streak) */}
              <div className="bg-orange-500/5 dark:bg-orange-500/10 border border-orange-500/20 rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-orange-500/30 group relative overflow-hidden">
                <div className="absolute -top-4 -right-4 p-4 opacity-[0.03] dark:opacity-10 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <span className="material-symbols-outlined text-8xl text-orange-600">self_improvement</span>
                </div>
                <div className="flex items-center gap-2 mb-4 text-orange-600 dark:text-orange-400 transition-transform group-hover:translate-x-1 relative z-10">
                  <span className="material-symbols-outlined text-[20px] animate-pulse" data-icon="local_fire_department">local_fire_department</span>
                  <span className="text-xs font-bold uppercase tracking-wider">Ofensiva Atual</span>
                </div>
                <div className="relative z-10 flex items-baseline gap-2">
                  <span className="text-4xl font-black text-orange-700 dark:text-orange-400 tracking-tight">{stats.streak_days}</span>
                  <span className="text-sm text-orange-600/70 dark:text-orange-400/70 font-semibold">dias</span>
                </div>
              </div>

              {/* Stat Card 4 (Nível XP) */}
              <div className="bg-card border border-border/50 rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-md hover:border-border group">
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-2 text-indigo-500 transition-transform group-hover:translate-x-1">
                    <span className="material-symbols-outlined text-[20px]" data-icon="social_leaderboard">social_leaderboard</span>
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Nível XP</span>
                  </div>
                  <span className="text-xs font-bold text-indigo-700 bg-indigo-100 dark:bg-indigo-500/10 dark:text-indigo-300 px-2.5 py-1 rounded-full ring-1 ring-indigo-500/20">
                    Lvl {nivelAtual}
                  </span>
                </div>
                <div>
                  <div className="flex justify-between text-[11px] mb-2 text-muted-foreground font-semibold uppercase tracking-wider">
                    <span>{xpAtual} XP</span>
                    <span>{xpProximoNivel} XP</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2.5 overflow-hidden ring-1 ring-inset ring-black/5 dark:ring-white/5">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${progressoNivel}%` }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      className="bg-indigo-500 h-2.5 rounded-full shadow-inner" 
                    />
                  </div>
                  <span className="block mt-3 text-xs text-muted-foreground font-medium">
                    Faltam <strong className="text-foreground">{xpProximoNivel - xpAtual} XP</strong> para o próximo nível
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Access List */}
        <div className="lg:col-span-4 bg-card border border-border/50 rounded-2xl p-6 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-bold text-foreground tracking-tight">Acesso Rápido</h3>
          </div>
          <ul className="flex flex-col gap-2">
            {[
              { href: "/estudar", icon: "menu_book", title: "Estudar Questões", desc: "Filtre por especialidade ou tema", colorClass: "text-primary", bgClass: "bg-primary/10 ring-primary/20", groupHoverBg: "group-hover:bg-primary", groupHoverText: "group-hover:text-primary-foreground" },
              { href: "/simulado", icon: "description", title: "Simulado USP", desc: "Realize provas na íntegra", colorClass: "text-secondary", bgClass: "bg-secondary/10 ring-secondary/20", groupHoverBg: "group-hover:bg-secondary", groupHoverText: "group-hover:text-secondary-foreground" },
              { href: "/planner", icon: "calendar_month", title: "Planner Anual", desc: "Acompanhe seu cronograma", colorClass: "text-blue-500 dark:text-blue-400", bgClass: "bg-blue-500/10 ring-blue-500/20", groupHoverBg: "group-hover:bg-blue-600", groupHoverText: "group-hover:text-white" },
              { href: "/revisao-ativa", icon: "auto_awesome", title: "Revisão Ativa", desc: "Estude com flashcards de IA", colorClass: "text-purple-500 dark:text-purple-400", bgClass: "bg-purple-500/10 ring-purple-500/20", groupHoverBg: "group-hover:bg-purple-600", groupHoverText: "group-hover:text-white" }
            ].map((item) => (
              <motion.li key={item.href} whileHover={{ x: 4 }} transition={{ type: "spring", stiffness: 400, damping: 30 }}>
                <Link href={item.href} className="flex items-center gap-4 p-3 rounded-xl hover:bg-muted/50 transition-colors cursor-pointer group">
                  <div className={clsx("p-2.5 rounded-xl transition-colors ring-1", item.colorClass, item.bgClass, item.groupHoverBg, item.groupHoverText)}>
                    <span className="material-symbols-outlined text-[20px]" data-icon={item.icon}>{item.icon}</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-foreground">{item.title}</h4>
                    <p className="text-xs text-muted-foreground font-medium mt-0.5">{item.desc}</p>
                  </div>
                </Link>
              </motion.li>
            ))}
          </ul>
        </div>
        
        {/* Offline Panel */}
        <div className="lg:col-span-12 flex flex-col">
          <OfflinePanel />
        </div>
      </motion.div>
    </motion.div>
  );
}
