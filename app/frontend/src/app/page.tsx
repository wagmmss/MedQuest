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
        <div className="flex gap-3">
          <Link href="/estudar?status=srs_due&limit=100">
            <button className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded-lg font-body-sm text-body-sm font-semibold hover:opacity-90 transition-opacity">
              <span className="material-symbols-outlined" data-icon="play_arrow">play_arrow</span>
              Revisar ({stats.srs_due_count})
            </button>
          </Link>
        </div>
      </section>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
        {/* Weekly Progress Summary */}
        <div className="md:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-gutter">
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
        </div>

        {/* Library Quick Access */}
        <div className="md:col-span-4 bg-surface border border-outline-variant rounded-xl p-6 shadow-[0px_1px_3px_rgba(0,0,0,0.05)] flex flex-col">
          <div className="flex items-center justify-between mb-6 pb-2 border-b border-outline-variant">
            <h3 className="font-headline-md text-headline-md text-on-surface">Biblioteca Médica</h3>
            <Link className="text-primary font-label-md text-label-md hover:underline" href="/estudar">Ver Tudo</Link>
          </div>
          <ul className="flex flex-col gap-4">
            <li className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer">
              <div className="p-2 bg-primary-fixed rounded-lg text-on-primary-fixed">
                <span className="material-symbols-outlined" data-icon="description">description</span>
              </div>
              <div>
                <h4 className="font-body-md text-body-md font-semibold text-on-surface">Diretrizes de Cardiologia</h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">Protocolo atualizado para IAM.</p>
              </div>
            </li>
            <li className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer">
              <div className="p-2 bg-secondary-fixed rounded-lg text-on-secondary-fixed">
                <span className="material-symbols-outlined" data-icon="science">science</span>
              </div>
              <div>
                <h4 className="font-body-md text-body-md font-semibold text-on-surface">Casos de Neurologia</h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">Doenças desmielinizantes.</p>
              </div>
            </li>
          </ul>
        </div>

        {/* Current Quests Section */}
        <div className="md:col-span-12 mt-stack-lg">
          <div className="flex items-center justify-between mb-6 border-b border-outline-variant pb-2">
            <h3 className="font-headline-md text-headline-md text-on-surface">Quests Atuais</h3>
            <div className="flex gap-2">
              <button className="p-1 rounded text-on-surface-variant hover:bg-surface-container-low"><span className="material-symbols-outlined" data-icon="chevron_left">chevron_left</span></button>
              <button className="p-1 rounded text-on-surface-variant hover:bg-surface-container-low"><span className="material-symbols-outlined" data-icon="chevron_right">chevron_right</span></button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
            {/* Quest Card 1 */}
            <div className="bg-surface border border-outline-variant rounded-xl overflow-hidden shadow-[0px_1px_3px_rgba(0,0,0,0.05)] hover:shadow-[0px_4px_12px_rgba(0,0,0,0.08)] transition-shadow">
              <div className="h-32 bg-surface-variant relative">
                <div className="absolute inset-0 bg-cover bg-center opacity-80 mix-blend-multiply" style={{backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCRYhsrNM1ei06N0OAx-9xLNS00RkTYrRX2vMkb-JJNOl9qY367zzpgNWKCE8-QdPLAQYbVGIgDxG5Nq37S7lF2-hKvA3cEIpIqNJMqw_-LLHk3QFE_a7REurHE9B4GPtrx_em4ql8PLXaeTGQbPYV4BRg3vDHc1ItBQDH_MmctV5geyKPvlvDRWfFz8Nr6VQOIWl4QVibKS3vCwINAWBOwp05uOQzxnhUte76VyyKaXoM08ARV6NYrxw')"}}></div>
                <div className="absolute top-3 left-3 bg-error-container text-on-error-container font-label-md text-label-md px-2 py-1 rounded">Cardiologia</div>
              </div>
              <div className="p-5 flex flex-col h-[180px]">
                <h4 className="font-headline-md text-headline-md font-semibold text-on-surface mb-2 truncate">Simulação IAM</h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant mb-4 line-clamp-2">Paciente com dor torácica irradiada. O tempo é crítico para o diagnóstico.</p>
                <div className="flex items-center justify-between mt-auto">
                  <div className="flex items-center gap-1 text-on-surface-variant font-label-md text-label-md">
                    <span className="material-symbols-outlined text-sm" data-icon="schedule">schedule</span>
                    15 mins
                  </div>
                  <button className="px-4 py-2 bg-surface-container-low hover:bg-surface-container-high text-primary font-body-sm text-body-sm font-semibold rounded-lg transition-colors border border-outline-variant">Retomar</button>
                </div>
              </div>
            </div>

            {/* Quest Card 2 */}
            <div className="bg-surface border border-outline-variant rounded-xl overflow-hidden shadow-[0px_1px_3px_rgba(0,0,0,0.05)] hover:shadow-[0px_4px_12px_rgba(0,0,0,0.08)] transition-shadow">
              <div className="h-32 bg-surface-variant relative">
                <div className="absolute inset-0 bg-cover bg-center opacity-80 mix-blend-multiply" style={{backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuB_yjKy71mfFnMPqKyvFKPqz5sqHbfAzpfR_siEP2WzMB5nO8SGJGdpmIt0cXjSqCl_WhFHRGv4_rEnMv7uWjcYm42_HzNtl7ikRSvBsYurEAwdJ3VTo6IH7owH3H0K59vjBuLYRSkcSMTgTBdyUAMai0IinzZGOejKX1SBPpqIPxPwkmBavxuwF9_SHQzq1nAnoZXgRDK1CWLwjyOdVZidR19dCJL-5_8zbFGm4d3Gt2tlhyRp3c6L5Q')"}}></div>
                <div className="absolute top-3 left-3 bg-secondary-container text-on-secondary-container font-label-md text-label-md px-2 py-1 rounded">Endocrinologia</div>
              </div>
              <div className="p-5 flex flex-col h-[180px]">
                <h4 className="font-headline-md text-headline-md font-semibold text-on-surface mb-2 truncate">Manejo Complexo DM</h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant mb-4 line-clamp-2">Ajuste de insulina em paciente com glicemia flutuante e disfunção renal.</p>
                <div className="flex items-center justify-between mt-auto">
                  <div className="flex items-center gap-1 text-on-surface-variant font-label-md text-label-md">
                    <span className="material-symbols-outlined text-sm" data-icon="schedule">schedule</span>
                    45 mins
                  </div>
                  <button className="px-4 py-2 bg-primary text-on-primary font-body-sm text-body-sm font-semibold rounded-lg transition-opacity hover:opacity-90">Iniciar</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
