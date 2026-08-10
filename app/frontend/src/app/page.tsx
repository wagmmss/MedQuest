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

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
        {/* Weekly Progress Summary (4 Stats) */}
        <div className="md:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-gutter">
          {/* Stat Card 1 */}
          <div className="bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between hover:bg-surface-container-lowest transition-colors shadow-[0px_1px_3px_rgba(0,0,0,0.05)]">
            <div className="flex items-center gap-3 mb-4 text-primary">
              <span className="material-symbols-outlined" data-icon="task_alt">task_alt</span>
              <span className="font-label-md text-label-md uppercase">Questões Feitas</span>
            </div>
            <div>
              <span className="font-display-lg text-display-lg text-on-surface">{stats.distinct_answered}</span>
              <span className="font-body-sm text-body-sm text-secondary ml-2 font-semibold">únicas</span>
            </div>
          </div>

          {/* Stat Card 2 */}
          <div className="bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between hover:bg-surface-container-lowest transition-colors shadow-[0px_1px_3px_rgba(0,0,0,0.05)]">
            <div className="flex items-center gap-3 mb-4 text-primary">
              <span className="material-symbols-outlined" data-icon="my_location">my_location</span>
              <span className="font-label-md text-label-md uppercase">Acurácia Geral</span>
            </div>
            <div>
              <span className="font-display-lg text-display-lg text-on-surface">{accuracyFormatted}</span>
            </div>
          </div>

          {/* Stat Card 3 */}
          <div className="bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between hover:bg-surface-container-lowest transition-colors shadow-[0px_1px_3px_rgba(0,0,0,0.05)]">
            <div className="flex items-center gap-3 mb-4 text-primary">
              <span className="material-symbols-outlined" data-icon="local_fire_department">local_fire_department</span>
              <span className="font-label-md text-label-md uppercase">Ofensiva</span>
            </div>
            <div>
              <span className="font-display-lg text-display-lg text-on-surface">{stats.streak_days}</span>
              <span className="font-body-sm text-body-sm text-on-surface-variant ml-2">Dias</span>
            </div>
          </div>

          {/* Stat Card 4 */}
          <div className="bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between hover:bg-surface-container-lowest transition-colors shadow-[0px_1px_3px_rgba(0,0,0,0.05)]">
            <div className="flex items-center gap-3 mb-4 text-primary">
              <span className="material-symbols-outlined" data-icon="pie_chart">pie_chart</span>
              <span className="font-label-md text-label-md uppercase">Cobertura</span>
            </div>
            <div>
              <span className="font-display-lg text-display-lg text-on-surface">{coverageFormatted}</span>
              <span className="font-body-sm text-body-sm text-on-surface-variant ml-2">de {stats.total_questions} Qs</span>
            </div>
          </div>
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
