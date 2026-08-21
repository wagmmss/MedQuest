"use client";

import Link from "next/link";
import { OverviewStats, PlannerWeek } from "@/types/api";
import { OfflinePanel } from "@/components/OfflinePanel";
import { motion, Variants } from "framer-motion";
import { useEffect, useRef } from "react";
import { triggerConfetti } from "@/lib/confetti";

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
    hidden: { opacity: 0, y: 20 },
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
      className="flex flex-col gap-stack-lg"
    >
      {/* Welcome Header */}
      <motion.section variants={itemVariants} className="flex flex-col md:flex-row md:items-end justify-between gap-stack-md">
        <div>
          <h2 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface mb-2">
            Olá, {firstName}
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant">
            {motivationalMessage}
          </p>
        </div>
      </motion.section>

      {/* Plano Diário (3 Cards) */}
      <motion.div variants={itemVariants}>
        <h3 className="font-headline-sm font-bold text-on-surface mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-primary" data-icon="today">today</span>
          Seu Plano Diário
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
          {/* Card 1: Revisões */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="bg-surface/80 backdrop-blur-md border border-outline-variant/50 rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-lg transition-all relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-bl-full -mr-4 -mt-4 transition-transform duration-500 group-hover:scale-125" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-2 text-purple-600">
                <span className="material-symbols-outlined" data-icon="psychology">psychology</span>
                <span className="font-label-md font-bold uppercase tracking-wider">Revisão Ativa</span>
              </div>
              <p className="font-display-sm text-on-surface mb-1">
                {pendentes > 0 ? `${pendentes} pendentes` : "Tudo em dia!"}
              </p>
              <p className="text-sm text-on-surface-variant">
                Flashcards e questões no tempo ideal do FSRS.
              </p>
            </div>
            
            <div className="mt-6 relative z-10">
              {pendentes > 0 ? (
                <div className="flex gap-2 flex-col sm:flex-row">
                  {stats.flashcards_due_count! > 0 && (
                    <Link href="/revisao-ativa" className="flex-1 w-full py-2.5 bg-purple-100 hover:bg-purple-200 text-purple-700 dark:bg-purple-900/30 dark:hover:bg-purple-900/50 dark:text-purple-300 font-semibold rounded-lg transition-colors text-sm flex items-center justify-center gap-2">
                      <span className="material-symbols-outlined text-sm" data-icon="auto_awesome">auto_awesome</span> Flashcards ({stats.flashcards_due_count})
                    </Link>
                  )}
                  {stats.srs_due_count! > 0 && (
                    <Link href="/estudar?status=srs_due&limit=100" className="flex-1 w-full py-2.5 bg-primary/10 hover:bg-primary/20 text-primary font-semibold rounded-lg transition-colors text-sm flex items-center justify-center gap-2">
                      <span className="material-symbols-outlined text-sm" data-icon="psychology">psychology</span> Questões ({stats.srs_due_count})
                    </Link>
                  )}
                </div>
              ) : (
                <button disabled className="w-full py-2.5 bg-success/10 text-success font-semibold rounded-lg cursor-not-allowed text-sm flex items-center justify-center gap-2">
                  <span className="material-symbols-outlined text-sm" data-icon="done_all">done_all</span> Meta batida hoje
                </button>
              )}
            </div>
          </motion.div>

          {/* Card 2: Questões Novas */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="bg-surface/80 backdrop-blur-md border border-outline-variant/50 rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-lg transition-all relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-bl-full -mr-4 -mt-4 transition-transform duration-500 group-hover:scale-125" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-2 text-blue-600">
                <span className="material-symbols-outlined" data-icon="post_add">post_add</span>
                <span className="font-label-md font-bold uppercase tracking-wider">Questões Novas</span>
              </div>
              <p className="font-display-sm text-on-surface mb-1">Meta: 20 inéditas</p>
              <p className="text-sm text-on-surface-variant">
                Avance na sua cobertura resolvendo questões que você nunca viu.
              </p>
            </div>
            
            <div className="mt-6 relative z-10">
              <Link href={currentPlannerWeek && currentPlannerWeek.topics.length > 0 ? `/estudar?subtema=${encodeURIComponent(currentPlannerWeek.topics[0].subtema)}&status=new&limit=20` : "/estudar?status=new&limit=20"} className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all text-sm flex items-center justify-center gap-2 shadow-md hover:shadow-blue-500/25">
                <span className="material-symbols-outlined text-sm" data-icon="play_arrow">play_arrow</span> Iniciar Bateria
              </Link>
            </div>
          </motion.div>

          {/* Card 3: Planner */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-2xl p-6 flex flex-col justify-between shadow-md hover:shadow-lg hover:shadow-indigo-500/25 transition-all text-white relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-bl-full -mr-8 -mt-8 transition-transform duration-500 group-hover:scale-125" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-2 text-blue-100">
                <span className="material-symbols-outlined" data-icon="calendar_month">calendar_month</span>
                <span className="font-label-md font-bold uppercase tracking-wider">Tópico da Semana</span>
              </div>
              <p className="font-display-sm mb-1 leading-tight">
                {currentPlannerWeek && currentPlannerWeek.topics.length > 0 
                  ? currentPlannerWeek.topics[0].subtema 
                  : "Nenhum plano ativo"}
              </p>
              <p className="text-sm text-blue-100/80">
                {currentPlannerWeek 
                  ? `Semana ${currentPlannerWeek.week} • ${currentPlannerWeek.topics.length} metas` 
                  : "Defina sua data de prova no planner."}
              </p>
            </div>
            
            <div className="mt-6 relative z-10">
              <Link href="/planner" className="w-full py-2.5 bg-white/20 hover:bg-white/30 text-white border border-white/30 font-semibold rounded-lg transition-colors text-sm flex items-center justify-center gap-2 backdrop-blur-sm">
                <span className="material-symbols-outlined text-sm" data-icon="arrow_forward">arrow_forward</span> Ver Planner
              </Link>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Bento Grid Layout */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
        {/* Weekly Progress Summary (4 Stats) */}
        <div className="md:col-span-8">
          {stats.distinct_answered === 0 ? (
            <div className="bg-surface/80 backdrop-blur-md border border-outline-variant/50 rounded-xl p-8 flex flex-col items-center justify-center text-center h-full shadow-sm">
              <motion.div 
                animate={{ y: [0, -10, 0] }} 
                transition={{ repeat: Infinity, duration: 2 }}
                className="w-16 h-16 bg-primary-container text-on-primary-container rounded-full flex items-center justify-center mb-4"
              >
                <span className="material-symbols-outlined text-3xl" data-icon="school">school</span>
              </motion.div>
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-2">Bem-vindo(a) ao MedQuest!</h3>
              <p className="font-body-md text-body-md text-on-surface-variant max-w-md mb-6">
                Você ainda não respondeu nenhuma questão. Que tal começar agora mesmo e testar seus conhecimentos?
              </p>
              <Link href="/estudar" className="px-6 py-3 bg-primary text-on-primary rounded-xl font-body-sm font-semibold hover:opacity-90 transition-opacity">
                Explorar Banco de Questões
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-gutter h-full">
              {/* Stat Card 1 */}
              <div className="bg-surface/80 backdrop-blur-md border border-outline-variant/50 rounded-xl p-6 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/30 group">
                <div className="flex items-center gap-3 mb-4 text-primary transition-transform group-hover:scale-105 origin-left">
                  <span className="material-symbols-outlined" data-icon="task_alt">task_alt</span>
                  <span className="font-label-md text-label-md uppercase">Questões Feitas</span>
                </div>
                <div>
                  <span className="font-display-lg text-display-lg text-on-surface">{stats.distinct_answered}</span>
                  <span className="font-body-sm text-body-sm text-secondary ml-2 font-semibold">únicas</span>
                </div>
              </div>

              {/* Stat Card 2 */}
              <div className="bg-surface/80 backdrop-blur-md border border-outline-variant/50 rounded-xl p-6 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/30 group">
                <div className="flex items-center gap-3 mb-4 text-primary transition-transform group-hover:scale-105 origin-left">
                  <span className="material-symbols-outlined" data-icon="my_location">my_location</span>
                  <span className="font-label-md text-label-md uppercase">Acurácia Geral</span>
                </div>
                <div>
                  <span className="font-display-lg text-display-lg text-on-surface">{accuracyFormatted}</span>
                </div>
              </div>

              {/* Stat Card 3 */}
              <div className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-xl p-6 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_8px_20px_rgba(234,88,12,0.15)] group relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <span className="material-symbols-outlined text-6xl text-orange-600">self_improvement</span>
                </div>
                <div className="flex items-center gap-3 mb-4 text-orange-600 transition-transform group-hover:scale-105 origin-left relative z-10">
                  <span className="material-symbols-outlined animate-pulse" data-icon="local_fire_department">local_fire_department</span>
                  <span className="font-label-md text-label-md uppercase font-bold">Ofensiva Atual</span>
                </div>
                <div className="relative z-10">
                  <span className="font-display-lg text-display-lg text-on-surface">{stats.streak_days}</span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant ml-2 font-semibold">Dias seguidos</span>
                </div>
              </div>

              {/* Stat Card 4 (Nível XP) */}
              <div className="bg-surface/80 backdrop-blur-md border border-outline-variant/50 rounded-xl p-6 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-purple-500/30 group">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3 text-purple-600 transition-transform group-hover:scale-105 origin-left">
                    <span className="material-symbols-outlined" data-icon="social_leaderboard">social_leaderboard</span>
                    <span className="font-label-md text-label-md uppercase font-bold">Nível XP</span>
                  </div>
                  <span className="text-xs font-bold text-purple-600 bg-purple-100 dark:bg-purple-900/30 px-2 py-1 rounded-full">
                    Lvl {nivelAtual}
                  </span>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1.5 text-on-surface-variant font-medium">
                    <span>{xpAtual} XP</span>
                    <span>{xpProximoNivel} XP</span>
                  </div>
                  <div className="w-full bg-surface-variant rounded-full h-2.5 overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${progressoNivel}%` }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      className="bg-gradient-to-r from-purple-500 to-indigo-500 h-2.5 rounded-full" 
                    />
                  </div>
                  <span className="block mt-3 font-body-sm text-body-sm text-on-surface-variant text-xs">
                    Faltam {xpProximoNivel - xpAtual} XP para o próximo nível
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Access List */}
        <div className="md:col-span-4 bg-surface/80 backdrop-blur-md border border-outline-variant/50 rounded-xl p-6 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-6 pb-2 border-b border-outline-variant/50">
            <h3 className="font-headline-md text-headline-md text-on-surface">Acesso Rápido</h3>
          </div>
          <ul className="flex flex-col gap-4">
            {[
              { href: "/estudar", icon: "menu_book", title: "Estudar Banco de Questões", desc: "Filtre por especialidade ou tema.", colorClass: "text-primary", bgClass: "bg-primary/10", groupHoverBg: "group-hover:bg-primary", groupHoverText: "group-hover:text-white" },
              { href: "/simulado", icon: "description", title: "Simulado USP", desc: "Realize provas na íntegra.", colorClass: "text-secondary", bgClass: "bg-secondary/10", groupHoverBg: "group-hover:bg-secondary", groupHoverText: "group-hover:text-white" },
              { href: "/planner", icon: "calendar_month", title: "Planner Anual", desc: "Acompanhe seu cronograma de estudos.", colorClass: "text-blue-500", bgClass: "bg-blue-500/10", groupHoverBg: "group-hover:bg-blue-500", groupHoverText: "group-hover:text-white" },
              { href: "/revisao-ativa", icon: "auto_awesome", title: "Revisão Ativa", desc: "Estude com flashcards gerados por IA.", colorClass: "text-purple-500", bgClass: "bg-purple-500/10", groupHoverBg: "group-hover:bg-purple-500", groupHoverText: "group-hover:text-white" }
            ].map((item) => (
              <motion.li key={item.href} whileHover={{ x: 5 }}>
                <Link href={item.href} className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer group">
                  <div className={`p-2 rounded-lg transition-colors ${item.colorClass} ${item.bgClass} ${item.groupHoverBg} ${item.groupHoverText}`}>
                    <span className="material-symbols-outlined" data-icon={item.icon}>{item.icon}</span>
                  </div>
                  <div>
                    <h4 className="font-body-md text-body-md font-semibold text-on-surface">{item.title}</h4>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">{item.desc}</p>
                  </div>
                </Link>
              </motion.li>
            ))}
          </ul>
        </div>
        
        {/* Offline Panel */}
        <div className="md:col-span-8 flex flex-col">
          <OfflinePanel />
        </div>
      </motion.div>
    </motion.div>
  );
}
