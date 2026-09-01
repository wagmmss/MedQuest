"use client";

import React, { useState, useEffect, useRef } from "react";
import { InstitutionRadarResponse, RadarTopicGap } from "@/types/api";
import { api } from "@/lib/api";
import Link from "next/link";

import { AlertTriangle } from "lucide-react";
import clsx from "clsx";
import { InstitutionRadarTable } from "./InstitutionRadarTable";
import { InstitutionRadarChart } from "./InstitutionRadarChart";



interface InstitutionRadarSectionProps {

  initialData?: InstitutionRadarResponse | null;
  institutionOptions: { key: string; label: string }[];
  defaultInstitution?: string;
}

export function InstitutionRadarSection({
  initialData,
  institutionOptions,
  defaultInstitution = "USP-SP",
}: InstitutionRadarSectionProps) {
  const [selectedInst, setSelectedInst] = useState<string>(
    initialData?.institution.code || defaultInstitution
  );
  const [compareInst, setCompareInst] = useState<string>("");
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const [radarData, setRadarData] = useState<InstitutionRadarResponse | null>(initialData || null);
  const [loading, setLoading] = useState(false);
  const isFirstMount = useRef(true);

  useEffect(() => {
    if (isFirstMount.current) {
      isFirstMount.current = false;
      if (initialData) return;
    }

    const controller = new AbortController();
    setLoading(true);

    api.stats
      .getInstitutionRadar(selectedInst || undefined, compareInst || undefined, controller.signal)
      .then(data => {
        if (!controller.signal.aborted) {
          setRadarData(data);
        }
      })
      .catch(err => {
        if (!controller.signal.aborted) {
          console.error("Falha ao carregar radar comparativo:", err);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [selectedInst, compareInst, initialData]);

  const handleActionClick = (action: "study" | "simulado" | "review") => {
    // Chamada autenticada não-bloqueante de observabilidade privada
    api.stats.logRadarAction(action).catch(() => {});
  };


  // Coleta todas as lacunas prioritárias de todas as áreas
  const allGaps = React.useMemo(() => {
    if (!radarData || !radarData.institution.areas) return [];
    const list: Array<RadarTopicGap & { area: string }> = [];
    radarData.institution.areas.forEach(area => {
      (area.priority_topics || []).forEach(top => {
        list.push({ ...top, area: area.area });
      });
    });
    // Ordena: não respondidas primeiro, depois menor acurácia
    list.sort((a, b) => {
      if (a.attempts === 0 && b.attempts > 0) return -1;
      if (b.attempts === 0 && a.attempts > 0) return 1;
      const accA = a.accuracy !== null ? a.accuracy : 1;
      const accB = b.accuracy !== null ? b.accuracy : 1;
      return accA - accB;
    });
    return list.slice(0, 4);
  }, [radarData]);

  const isSampleInsufficient = radarData?.institution.sample_status === "insufficient";

  return (
    <section className="animate-in fade-in slide-in-from-bottom-4 duration-500 bg-card border border-border shadow-sm rounded-2xl p-6 md:p-8 flex flex-col gap-6">

      {/* Header e Controles */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 border-b border-border pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor"/>
              </svg>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-foreground">
              Radar Comparativo de Bancas
            </h2>
          </div>
          <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
            Diagnóstico transparente de cobertura e acurácia por grande área, com intervalo de incerteza estatística (Wilson 95% CI) e ações diretas de estudo.
          </p>
        </div>

        {/* Seletores e Alternância de Visualização */}
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex flex-col text-xs font-semibold text-muted-foreground">
            Banca Alvo
            <select
              value={selectedInst}
              onChange={(e) => setSelectedInst(e.target.value)}
              aria-label="Selecionar banca alvo"
              className="mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:ring-2 focus:ring-primary/20"
            >
              {institutionOptions.map(opt => (
                <option key={opt.key} value={opt.key}>{opt.label}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col text-xs font-semibold text-muted-foreground">
            Comparar com
            <select
              value={compareInst}
              onChange={(e) => setCompareInst(e.target.value)}
              aria-label="Selecionar banca para comparação"
              className="mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:ring-2 focus:ring-primary/20"
            >
              <option value="">Desempenho Geral</option>
              {institutionOptions
                .filter(opt => opt.key !== selectedInst)
                .map(opt => (
                  <option key={opt.key} value={opt.key}>{opt.label}</option>
                ))}
            </select>
          </label>

          {/* Toggle Gráfico / Tabela */}
          <div className="flex flex-col justify-end">
            <span className="text-xs font-semibold text-muted-foreground mb-1">Visualização</span>
            <div className="inline-flex rounded-lg border border-border p-1 bg-muted/30">
              <button
                type="button"
                onClick={() => setViewMode("chart")}
                className={clsx(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer",
                  viewMode === "chart" ? "bg-background text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
                )}
                aria-label="Visualização em gráfico"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 20V10M12 20V4M6 20v-6" />
                </svg> Gráfico
              </button>
              <button
                type="button"
                onClick={() => setViewMode("table")}
                className={clsx(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer",
                  viewMode === "table" ? "bg-background text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
                )}
                aria-label="Visualização em tabela acessível"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18M9 4v16M15 4v16M4 4h16a1 1 0 011 1v14a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z" />
                </svg> Tabela
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Alerta de Amostra Insuficiente */}
      {isSampleInsufficient && radarData && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-start gap-3">
          <AlertTriangle className="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" size={18} />
          <div className="text-xs space-y-1">
            <p className="font-semibold text-amber-900 dark:text-amber-200">
              Amostra em estágio inicial ({radarData.institution.total_attempts} tentativas)
            </p>
            <p className="text-amber-800 dark:text-amber-300/90 leading-relaxed">
              Com menos de 20 tentativas nesta instituição, o intervalo de incerteza é elevado e não são geradas conclusões definitivas de competitividade. Resolva mais questões para calibrar a precisão estatística.
            </p>
          </div>
        </div>
      )}

      {/* Visualização Principal: Gráfico ou Tabela */}
      {loading ? (
        <div className="w-full h-[360px] bg-muted/20 rounded-2xl border border-border p-4 flex items-center justify-center animate-pulse">
          <p className="text-sm text-muted-foreground">Atualizando dados da banca...</p>
        </div>
      ) : radarData ? (
        <div>
          {viewMode === "chart" ? (
            <InstitutionRadarChart
              institution={radarData.institution}
              comparison={radarData.comparison}
            />
          ) : (

            <InstitutionRadarTable
              institution={radarData.institution}
              comparison={radarData.comparison}
              onActionClick={handleActionClick}
            />
          )}
        </div>
      ) : null}

      {/* Lacunas Prioritárias da Banca com Ações em até 2 Cliques */}
      {allGaps.length > 0 && radarData && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
              <h3 className="text-base font-bold text-foreground">
                Ações Imediatas para Fechar Lacunas em {radarData.institution.label}
              </h3>
            </div>
            <span className="text-xs text-muted-foreground">
              Acesso direto em 1 clique
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {allGaps.map((gap, idx) => {
              const accPct = gap.accuracy !== null ? Math.round(gap.accuracy * 100) : null;

              return (
                <div
                  key={`${gap.area}-${gap.subtema}-${idx}`}
                  className="rounded-xl border border-border p-4 bg-background/60 flex flex-col justify-between gap-3 hover:border-primary/40 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        {gap.area}
                      </span>
                      <h4 className="font-semibold text-sm text-foreground line-clamp-1" title={gap.subtema}>
                        {gap.subtema}
                      </h4>
                    </div>
                    {gap.gap_type === "unanswered" ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-muted text-muted-foreground">
                        Não Praticado
                      </span>
                    ) : gap.gap_type === "low_accuracy" ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-destructive/10 text-destructive">
                        {accPct}% Acerto ({gap.attempts} tent.)
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-warning/10 text-warning">
                        Baixa Cobertura
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <Link
                      href={gap.study_url}
                      onClick={() => handleActionClick("study")}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors cursor-pointer"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg> Estudar Tema
                    </Link>
                    <Link
                      href={gap.simulado_url}
                      onClick={() => handleActionClick("simulado")}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-secondary text-secondary-foreground text-xs font-semibold hover:bg-secondary/90 transition-colors cursor-pointer"
                      title="Iniciar simulado filtrado"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg> Simulado
                    </Link>
                    <Link
                      href={gap.review_url}
                      onClick={() => handleActionClick("review")}
                      className="p-2 rounded-lg border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                      title="Revisão Ativa"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </Link>
                  </div>

                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Disclaimer explicativo de transparência */}
      <p className="text-xs text-muted-foreground pt-2 border-t border-border/50">
        <svg className="w-3.5 h-3.5 inline mr-1 -mt-0.5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {radarData?.disclaimer || "Métricas isoladas exclusivamente para sua conta. Intervalos de incerteza calculados via Wilson Score a 95% de confiança estatística."}
      </p>
    </section>

  );
}
