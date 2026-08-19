import { serverApi } from "@/lib/server-api";
import { OverviewStats } from "@/types/api";
import Link from "next/link";
import { currentUser } from '@clerk/nextjs/server';

export default async function Dashboard() {
  const stats: OverviewStats = await serverApi.stats.getOverview();
  const user = await currentUser();

  const accuracyFormatted = stats.accuracy_all_attempts != null 
    ? (stats.accuracy_all_attempts * 100).toFixed(1) + "%" 
    : "--";

  const coverageFormatted = stats.coverage_pct != null
    ? (stats.coverage_pct * 100).toFixed(1) + "%"
    : "--";

  const firstName = user?.firstName || "Doutor(a)";

  return (
    <>
      {/* Welcome Header */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-stack-md mb-stack-lg">
        <div>
          <h2 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface mb-2">
            Bom dia, {firstName}
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Aqui está o seu progresso semanal na preparação para a USP.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {stats.srs_due_count === 0 ? (
            <button disabled className="flex items-center gap-2 px-6 py-3 bg-surface-variant text-on-surface-variant rounded-xl opacity-70 cursor-not-allowed font-body-sm text-body-sm font-semibold">
              <span className="material-symbols-outlined" data-icon="psychology">psychology</span>
              Nenhuma revisão pendente
            </button>
          ) : (
            <Link href="/estudar?status=srs_due&limit=100">
              <button className="flex items-center gap-2 px-6 py-3 bg-primary text-on-primary rounded-xl shadow-[0_4px_14px_0_rgba(26,75,132,0.39)] hover:shadow-[0_6px_20px_rgba(26,75,132,0.23)] hover:-translate-y-1 transform transition-all duration-200 font-body-sm text-body-sm font-semibold cursor-pointer">
                <span className="material-symbols-outlined" data-icon="psychology">psychology</span>
                Iniciar Revisão ({stats.srs_due_count})
              </button>
            </Link>
          )}
          {stats.flashcards_due_count != null && stats.flashcards_due_count > 0 && (
            <Link href="/revisao-ativa">
              <button className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white rounded-xl shadow-[0_4px_14px_rgba(139,92,246,0.3)] hover:-translate-y-1 transform transition-all duration-200 font-body-sm text-body-sm font-semibold cursor-pointer">
                <span className="material-symbols-outlined" data-icon="auto_awesome">auto_awesome</span>
                Revisar Flashcards ({stats.flashcards_due_count})
              </button>
            </Link>
          )}
        </div>
      </section>

      {/* Daily Challenge Banner */}
      <div className="mb-stack-lg animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl p-6 text-white shadow-lg flex flex-col sm:flex-row items-center justify-between gap-4 transition-transform hover:-translate-y-1 hover:shadow-xl duration-300">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/20 rounded-full flex items-center justify-center">
              <span className="material-symbols-outlined text-3xl" data-icon="local_fire_department">local_fire_department</span>
            </div>
            <div>
              <h3 className="font-headline-md font-bold text-white mb-1">Desafio do Dia</h3>
              <p className="text-white/90 text-sm">Mantenha sua ofensiva de {stats.streak_days} dia(s) acesa! Resolva a questão selecionada para você hoje.</p>
            </div>
          </div>
          <Link href="/estudar?status=unanswered&limit=1">
            <button className="px-6 py-3 bg-white text-orange-600 rounded-xl font-bold shadow-md hover:bg-gray-50 transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined" data-icon="play_arrow">play_arrow</span>
              Resolver Agora
            </button>
          </Link>
        </div>
      </div>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
        {/* Weekly Progress Summary (4 Stats) */}
        <div className="md:col-span-8">
          {stats.distinct_answered === 0 ? (
            <div className="bg-surface border border-outline-variant rounded-xl p-8 flex flex-col items-center justify-center text-center h-full shadow-[0px_1px_3px_rgba(0,0,0,0.05)]">
              <div className="w-16 h-16 bg-primary-container text-on-primary-container rounded-full flex items-center justify-center mb-4">
                <span className="material-symbols-outlined text-3xl" data-icon="school">school</span>
              </div>
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-2">Bem-vindo(a) ao MedQuest!</h3>
              <p className="font-body-md text-body-md text-on-surface-variant max-w-md mb-6">
                Você ainda não respondeu nenhuma questão. Que tal começar agora mesmo e testar seus conhecimentos?
              </p>
              <Link href="/estudar">
                <button className="px-6 py-3 bg-primary text-on-primary rounded-xl font-body-sm font-semibold hover:opacity-90 transition-opacity">
                  Explorar Banco de Questões
                </button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-gutter h-full">
              {/* Stat Card 1 */}
              <div className="bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/30 group">
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
              <div className="bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/30 group">
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
                  <span className="material-symbols-outlined text-6xl text-orange-600">local_fire_department</span>
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
              <div className="bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-purple-500/30 group">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3 text-purple-600 transition-transform group-hover:scale-105 origin-left">
                    <span className="material-symbols-outlined" data-icon="social_leaderboard">social_leaderboard</span>
                    <span className="font-label-md text-label-md uppercase font-bold">Nível XP</span>
                  </div>
                  <span className="text-xs font-bold text-purple-600 bg-purple-100 dark:bg-purple-900/30 px-2 py-1 rounded-full">
                    Lvl {Math.floor((stats.distinct_answered * 10) / 100) + 1}
                  </span>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1.5 text-on-surface-variant font-medium">
                    <span>{stats.distinct_answered * 10} XP</span>
                    <span>{(Math.floor((stats.distinct_answered * 10) / 100) + 1) * 100} XP</span>
                  </div>
                  <div className="w-full bg-surface-variant rounded-full h-2.5 overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-purple-500 to-indigo-500 h-2.5 rounded-full transition-all duration-1000 ease-out" 
                      style={{ width: `${((stats.distinct_answered * 10) % 100)}%` }}
                    />
                  </div>
                  <span className="block mt-3 font-body-sm text-body-sm text-on-surface-variant text-xs">
                    Resolva questões e revise para subir de nível!
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Access List */}
        <div className="md:col-span-4 bg-surface border border-outline-variant rounded-xl p-6 shadow-[0px_1px_3px_rgba(0,0,0,0.05)] flex flex-col">
          <div className="flex items-center justify-between mb-6 pb-2 border-b border-outline-variant">
            <h3 className="font-headline-md text-headline-md text-on-surface">Acesso Rápido</h3>
          </div>
          <ul className="flex flex-col gap-4">
            <li>
              <Link href="/estudar" className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer group">
                <div className="p-2 bg-primary-fixed rounded-lg text-on-primary-fixed group-hover:bg-primary group-hover:text-on-primary transition-colors">
                  <span className="material-symbols-outlined" data-icon="menu_book">menu_book</span>
                </div>
                <div>
                  <h4 className="font-body-md text-body-md font-semibold text-on-surface">Estudar Banco de Questões</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Filtre por especialidade ou tema.</p>
                </div>
              </Link>
            </li>
            <li>
              <Link href="/simulado" className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer group">
                <div className="p-2 bg-secondary-fixed rounded-lg text-on-secondary-fixed group-hover:bg-secondary group-hover:text-on-secondary transition-colors">
                  <span className="material-symbols-outlined" data-icon="description">description</span>
                </div>
                <div>
                  <h4 className="font-body-md text-body-md font-semibold text-on-surface">Simulado USP</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Realize provas na íntegra.</p>
                </div>
              </Link>
            </li>
            <li>
              <Link href="/planner" className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer group">
                <div className="p-2 bg-tertiary-fixed rounded-lg text-on-tertiary-fixed group-hover:bg-tertiary group-hover:text-on-tertiary transition-colors">
                  <span className="material-symbols-outlined" data-icon="calendar_month">calendar_month</span>
                </div>
                <div>
                  <h4 className="font-body-md text-body-md font-semibold text-on-surface">Planner Anual</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Acompanhe seu cronograma de estudos.</p>
                </div>
              </Link>
            </li>
            <li>
              <Link href="/revisao-ativa" className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer group">
                <div className="p-2 bg-purple-500/10 rounded-lg text-purple-500 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                  <span className="material-symbols-outlined" data-icon="auto_awesome">auto_awesome</span>
                </div>
                <div>
                  <h4 className="font-body-md text-body-md font-semibold text-on-surface">Revisão Ativa</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Estude com flashcards gerados por IA.</p>
                </div>
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </>
  );
}
