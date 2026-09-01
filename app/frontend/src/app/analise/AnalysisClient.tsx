"use client";

import { useMemo, useState, useEffect, useRef } from "react";
import { TimelineStat, WeakTopic, BreakdownStat, DistractorStat, PredictiveScore, AtRiskTopic, LearningProfile, ExamReadiness, InstitutionRadarResponse } from "@/types/api";
import Link from "next/link";
import clsx from "clsx";
import { api } from "@/lib/api";


import { InstitutionRadarSection } from "@/components/analytics/InstitutionRadarSection";
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Cell, LabelList, Area
} from 'recharts';

export function AnalysisClient({

  timeline,
  weakTopics,
  breakdown,
  distractors,
  predictiveScore,
  atRiskTopics,
  learningProfile,
  examReadiness,
  institutionOptions,
  timeline180,
  institutionRadar,
}: {
  timeline: TimelineStat[];
  weakTopics: WeakTopic[];
  breakdown: BreakdownStat[];
  distractors: DistractorStat[];
  predictiveScore: PredictiveScore;
  atRiskTopics: AtRiskTopic[];
  learningProfile: LearningProfile;
  examReadiness: ExamReadiness;
  institutionOptions: { key: string; label: string }[];
  timeline180?: TimelineStat[];
  institutionRadar?: InstitutionRadarResponse | null;
}) {

  const [days, setDays] = useState<number>(14);
  const [localTimeline, setLocalTimeline] = useState<TimelineStat[]>(timeline);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [selectedInstitution, setSelectedInstitution] = useState(examReadiness.institution || "");
  const [localReadiness, setLocalReadiness] = useState(examReadiness);
  const [loadingReadiness, setLoadingReadiness] = useState(false);
  const isFirstMount = useRef(true);
  const isFirstReadinessMount = useRef(true);

  useEffect(() => {
    if (isFirstMount.current) {
      isFirstMount.current = false;
      return;
    }
    
    const controller = new AbortController();
    setLoadingTimeline(true);
    api.stats.getTimeline(days, controller.signal)
      .then(data => {
        if (!controller.signal.aborted) setLocalTimeline(data);
      })
      .catch(error => {
        if (!controller.signal.aborted) console.error("Failed to fetch timeline:", error);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingTimeline(false);
      });

    return () => {
      controller.abort();
    };
  }, [days]);

  useEffect(() => {
    if (isFirstReadinessMount.current) {
      isFirstReadinessMount.current = false;
      return;
    }
    const controller = new AbortController();
    setLoadingReadiness(true);
    api.stats.getExamReadiness(selectedInstitution || undefined)
      .then(data => { if (!controller.signal.aborted) setLocalReadiness(data); })
      .catch(error => { if (!controller.signal.aborted) console.error("Failed to fetch readiness:", error); })
      .finally(() => { if (!controller.signal.aborted) setLoadingReadiness(false); });
    return () => controller.abort();
  }, [selectedInstitution]);

  const chartBreakdown = useMemo(() => {
    if (!Array.isArray(breakdown)) return [];
    return breakdown.slice(0, 8).map(b => ({
      ...b,
      accPct: parseFloat(((b.accuracy || 0) * 100).toFixed(1)),
      shortLabel: `${b.label.length > 28 ? b.label.substring(0, 25) + "..." : b.label} (${b.attempts})`
    }));
  }, [breakdown]);

  const chartTimeline = useMemo(() => {
    if (!Array.isArray(localTimeline)) return [];
    return localTimeline.map(t => ({
      ...t,
      dateShort: t.day.split("-").slice(1).reverse().join("/"),
      accPct: parseFloat(((t.accuracy || 0) * 100).toFixed(1))
    }));
  }, [localTimeline]);

  const priorityTopic = learningProfile.topics[0];
  const adaptiveRemainder = Math.max(0, learningProfile.goal.questions_today - learningProfile.goal.reviews_due);
  const scoreReliable = predictiveScore.is_reliable === true;
  const hasSufficientReadinessEvidence = localReadiness.evidence_status !== "insufficient";

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 pb-10">
      {/* Left Column (2/3 on xl screens) */}
      <div className="xl:col-span-2 flex flex-col gap-8 min-w-0">

        {/* Adaptive Goal Banner */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500 bg-card border border-primary/30 shadow-sm rounded-2xl p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <h2 className="text-xl font-bold text-foreground">Meta adaptativa de hoje</h2>
              </div>

              <p className="text-muted-foreground">
                {learningProfile.goal.questions_today} questões: {learningProfile.goal.reviews_due} revisões vencidas e até {adaptiveRemainder} questões adaptativas.
              </p>
              {priorityTopic && (
                <p className="text-sm text-muted-foreground mt-2">
                  Prioridade atual: <span className="font-semibold text-foreground">{priorityTopic.topic}</span>
                  {priorityTopic.reasons.length > 0 && <span> · {priorityTopic.reasons.map(reason => ({ low_accuracy: "baixa acurácia", reviews_due: "revisões vencidas", memory_at_risk: "risco de esquecimento", low_coverage: "baixa cobertura", balanced_practice: "prática equilibrada" }[reason] || reason)).join(", ")}</span>}
                </p>
              )}
            </div>
            <Link
              href={`/estudar?mode=adaptive&limit=${learningProfile.goal.questions_today}`}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 font-semibold text-primary-foreground hover:bg-primary/90 transition-colors cursor-pointer"
            >
              Iniciar sessão personalizada
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>

          </div>
        </section>

        {/* Prontidão Estimada por Edital com Modelo Bayesiano */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500 bg-card border border-border shadow-sm rounded-2xl p-6 md:p-8 flex flex-col gap-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
            <div className="space-y-1">
              <h2 className="text-xl md:text-2xl font-bold text-foreground">
                Prontidão Estimada por Edital
              </h2>

              <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
                Modelo estatístico bayesiano (Beta-Binomial) ponderado pela distribuição curricular do edital.
              </p>
            </div>
            <label className="text-xs font-semibold text-muted-foreground flex flex-col gap-1">
              Banca / Edital
              <select
                value={selectedInstitution}
                onChange={(e) => setSelectedInstitution(e.target.value)}
                className="bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:ring-2 focus:ring-primary/20"
                aria-label="Selecionar edital da instituição"
              >
                <option value="">Banco Geral (Padrão)</option>
                {institutionOptions.map((opt) => (
                  <option key={opt.key} value={opt.key}>{opt.label}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
            <div className="lg:col-span-1 bg-muted/20 border border-border rounded-2xl p-5 flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Prontidão Estimada
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-foreground tracking-tight">
                      {hasSufficientReadinessEvidence && localReadiness.readiness_score !== undefined
                        ? `${Math.round(localReadiness.readiness_score * 100)}%`
                        : "—"}
                    </span>
                    {hasSufficientReadinessEvidence && localReadiness.ci_lower !== undefined && localReadiness.ci_upper !== undefined && (
                      <span className="text-xs font-mono text-muted-foreground font-medium">
                        [{Math.round(localReadiness.ci_lower * 100)}% – {Math.round(localReadiness.ci_upper * 100)}%]
                      </span>
                    )}
                  </div>
                </div>
                {localReadiness.evidence_status === "insufficient" && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    Evidência Inicial
                  </span>
                )}
                {localReadiness.evidence_status === "forming" && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                    Evidência em Formação
                  </span>
                )}
                {localReadiness.evidence_status === "reliable" && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    Evidência Confiável
                  </span>
                )}
              </div>

              <div className="space-y-2 text-xs border-t border-border/50 pt-3">
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>Edital:</span>
                  <span className="font-semibold text-foreground">
                    {localReadiness.edital_profile ? `${localReadiness.edital_profile.institution_label} (v${localReadiness.edital_profile.version})` : "Padrão"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>Status do Perfil:</span>
                  <span className={clsx(
                    "font-semibold text-xs px-2 py-0.5 rounded",
                    localReadiness.edital_profile?.status === "validated"
                      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                      : "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                  )}>
                    {localReadiness.edital_profile?.status === "validated" ? "Validado" : "Experimental"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>Cobertura no Escopo:</span>
                  <span className="font-medium text-foreground">
                    {Math.round(localReadiness.coverage * 100)}% ({localReadiness.answered}/{localReadiness.available} q.)
                  </span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2 bg-muted/10 border border-border rounded-2xl p-5 flex flex-col justify-between gap-3">
              <h3 className="text-sm font-bold text-foreground">
                Fatores Determinantes para Calibrar a Evidência
              </h3>
              {localReadiness.evidence_status === "insufficient" && (
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-300 space-y-1">
                  <p className="font-semibold">Amostra Preliminar:</p>
                  <p className="leading-relaxed">
                    Ainda não exibimos uma pontuação de prontidão: faltam tentativas nas áreas ponderadas. Resolva as questões recomendadas para produzir uma estimativa responsável.
                  </p>
                </div>
              )}
              <div className="space-y-2">
                {(localReadiness.key_factors || []).slice(0, 3).map((factor, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-border/70 p-3 bg-card text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                  >
                    <div>
                      <span className="font-bold text-foreground">{factor.area}: </span>
                      <span className="text-muted-foreground">{factor.impact}</span>
                    </div>
                    <span className="text-primary font-medium shrink-0">
                      {factor.recommendation}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-bold text-foreground">
              Distribuição por Grande Área no Edital
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {localReadiness.areas.map((area) => {
                const meanPct = area.posterior_mean !== undefined
                  ? Math.round(area.posterior_mean * 100)
                  : (area.accuracy !== null ? Math.round(area.accuracy * 100) : null);
                const wPct = area.weight !== undefined ? Math.round(area.weight * 100) : 20;

                return (
                  <div
                    key={area.area}
                    className="rounded-xl border border-border p-4 bg-card flex flex-col justify-between gap-3 hover:border-primary/40 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[11px] font-semibold text-muted-foreground uppercase">
                          Peso {wPct}%
                        </span>
                        <h4 className="font-bold text-sm text-foreground line-clamp-1">{area.area}</h4>
                      </div>
                      <div className="text-right">
                        <span className="text-base font-bold text-foreground">
                          {meanPct !== null ? `${meanPct}%` : "—"}
                        </span>
                        <span className="block text-[10px] text-muted-foreground">Posterior</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground border-t border-border/40 pt-2">
                      <span>{area.attempts} tentativas</span>
                      {area.ci_lower !== undefined && area.ci_upper !== undefined && (
                        <span className="font-mono text-[11px]">
                          [{Math.round(area.ci_lower * 100)}% – {Math.round(area.ci_upper * 100)}%]
                        </span>
                      )}
                    </div>

                    <Link
                      href={area.action}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-semibold hover:bg-primary/20 transition-colors"
                    >
                      Estudar Área
                    </Link>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-2 border-t border-border/50 text-xs text-muted-foreground space-y-1">
            <p>{loadingReadiness ? "Atualizando escopo…" : localReadiness.disclaimer}</p>
            {localReadiness.limitations && localReadiness.limitations.length > 0 && (
              <ul className="list-disc list-inside text-[11px] text-muted-foreground/80 space-y-0.5 pt-1">
                {localReadiness.limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* Radar Comparativo de Bancas */}
        <InstitutionRadarSection
          initialData={institutionRadar}
          institutionOptions={institutionOptions}
          defaultInstitution={selectedInstitution || "USP-SP"}
        />
        
        {/* Predictive Dashboard */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-primary/10 rounded-lg">
              <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                <circle cx="12" cy="12" r="6" strokeWidth="2"/>
                <circle cx="12" cy="12" r="2" fill="currentColor"/>
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Dashboard Preditivo
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
            {/* Score Predictor */}
            <div className="bg-card border border-border shadow-sm rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-lg text-foreground">Estimativa de desempenho</h3>
                  <svg className="w-5 h-5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <p className="text-muted-foreground text-sm mb-6">
                  Indicador conservador com pesos históricos. Não substitui desempenho em simulados.
                </p>
              </div>
              
              {scoreReliable ? <>
                <div className="flex items-end gap-4">
                  <div className="text-5xl font-black text-primary">
                    {predictiveScore.projected_score}<span className="text-2xl text-muted-foreground font-medium">/100</span>
                  </div>
                  {predictiveScore.target_score != null && <div className="flex flex-col pb-1"><span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Alvo</span><span className="text-lg font-bold text-foreground">{predictiveScore.target_score}</span></div>}
                </div>
                <p className="text-xs text-muted-foreground mt-3">Amostra: {predictiveScore.total_attempts || 0} tentativas, com representação das cinco grandes áreas.</p>
              </> : <div className="rounded-xl border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground"><span className="font-semibold text-foreground">Estimativa ainda indisponível.</span><br />São necessárias pelo menos {predictiveScore.minimum_attempts_per_area || 20} tentativas em cada grande área para evitar uma projeção enganosa.</div>}

              {scoreReliable && predictiveScore.target_score != null && predictiveScore.target_score > 0 && (
                <div className="mt-6 w-full bg-secondary/20 h-3 rounded-full overflow-hidden relative">
                  <div 
                    className={clsx("h-full rounded-full transition-all duration-1000", predictiveScore.projected_score >= predictiveScore.target_score ? "bg-success" : "bg-primary")}
                    style={{ width: `${Math.min(100, (predictiveScore.projected_score / predictiveScore.target_score) * 100)}%` }}
                  />
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-foreground/50 z-10"
                    style={{ left: `${predictiveScore.target_score}%` }}
                  />
                </div>
              )}
            </div>

            {/* Radar de Esquecimento */}
            <div className="bg-card border border-border shadow-sm rounded-2xl p-6 flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                  <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2"/>
                  <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2"/>
                </svg>
                <h3 className="font-bold text-lg text-foreground">Radar de Esquecimento</h3>
              </div>
              <p className="text-muted-foreground text-sm mb-4">
                Tópicos que o algoritmo do FSRS indica que você está prestes a esquecer.
              </p>
              
              <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                {atRiskTopics && atRiskTopics.length > 0 ? (
                  atRiskTopics.map((topic, idx) => (
                    <Link key={idx} href={`/estudar?subtema=${encodeURIComponent(topic.subtema)}&status=srs_due&limit=20`} className="flex items-center justify-between p-3 bg-background rounded-lg border border-border hover:border-warning/50 transition-colors">
                      <div className="flex flex-col">
                        <span className="font-medium text-sm text-foreground leading-tight line-clamp-1" title={topic.subtema}>{topic.subtema}</span>
                        <span className="text-xs text-muted-foreground mt-0.5">{topic.items_count} cartões em risco</span>
                      </div>
                      <div className="flex flex-col items-end shrink-0 pl-3">
                        <span className="text-xs font-semibold text-warning">
                          {topic.retrievability !== undefined ? `${Math.round(topic.retrievability * 100)}% retenção` : "Baixa retenção"}
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="h-full flex items-center justify-center text-sm text-muted-foreground text-center p-4 border border-dashed border-border rounded-lg">
                    Sua memória está em dia! Continue fazendo suas revisões ativas.
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Breakdown by Institution */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-secondary/10 rounded-lg">
              <svg className="w-6 h-6 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 20V10M12 20V4M6 20v-6" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Desempenho por Instituição e Amostra
            </h2>
          </div>

          <div className="bg-card border border-border shadow-sm rounded-2xl p-6 h-[420px] relative overflow-hidden flex flex-col min-w-0">
            <div className="absolute top-0 right-0 w-64 h-64 bg-secondary/5 rounded-full blur-3xl -z-10" />
            <div className="flex-1 min-h-0 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartBreakdown}
                  layout="vertical"
                  margin={{ top: 10, right: 40, left: 10, bottom: 5 }}
                >
                  <defs>
                    <linearGradient id="colorSuccess" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="var(--success)" stopOpacity={0.8}/>
                      <stop offset="100%" stopColor="var(--success)" stopOpacity={1}/>
                    </linearGradient>
                    <linearGradient id="colorWarning" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="var(--warning)" stopOpacity={0.8}/>
                      <stop offset="100%" stopColor="var(--warning)" stopOpacity={1}/>
                    </linearGradient>
                    <linearGradient id="colorDestructive" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="var(--destructive)" stopOpacity={0.8}/>
                      <stop offset="100%" stopColor="var(--destructive)" stopOpacity={1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="4 4" horizontal={false} stroke="var(--border)" opacity={0.5} />
                  <XAxis type="number" domain={[0, 100]} hide />
                  <YAxis 
                    dataKey="shortLabel" 
                    type="category" 
                    axisLine={false} 
                    tickLine={false} 
                    width={220} 
                    tick={{ fill: 'var(--muted-foreground)', fontSize: 13, fontWeight: 500 }} 
                  />
                  <Tooltip 
                    cursor={{ fill: 'var(--muted)', opacity: 0.15 }}
                    contentStyle={{ borderRadius: '12px', border: '1px solid var(--border)', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-popover/95 backdrop-blur-md border border-border shadow-xl rounded-xl p-4 text-sm z-50 min-w-[200px]">
                            <p className="font-bold text-popover-foreground mb-3 text-base">{data.label}</p>
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-muted-foreground">Tentativas</span>
                              <span className="font-semibold text-foreground bg-muted px-2 py-0.5 rounded">{data.attempts}</span>
                            </div>
                            <div className="flex justify-between items-center mb-3">
                              <span className="text-muted-foreground">Acertos</span>
                              <span className="font-semibold text-success bg-success/10 px-2 py-0.5 rounded">{data.correct}</span>
                            </div>
                            <div className="pt-3 border-t border-border flex justify-between items-center">
                              <span className="text-muted-foreground font-medium">Acurácia</span>
                              <span className={clsx("font-bold text-lg", data.accPct >= 70 ? "text-success" : data.accPct >= 50 ? "text-warning" : "text-destructive")}>
                                {data.accPct}%
                              </span>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="accPct" radius={[0, 6, 6, 0]} barSize={20}>
                    {chartBreakdown.map((entry, index) => {
                      const acc = (entry.accuracy || 0) * 100;
                      const fillId = acc >= 70 ? 'url(#colorSuccess)' : acc >= 50 ? 'url(#colorWarning)' : 'url(#colorDestructive)';
                      return <Cell key={`cell-${index}`} fill={fillId} />;
                    })}
                    <LabelList dataKey="accPct" position="right" formatter={(val) => `${val ?? 0}%`} style={{ fill: 'var(--foreground)', fontSize: 13, fontWeight: 700 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* Timeline (Recharts ComposedChart) */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 fill-mode-both">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-success/10 rounded-lg">
                <svg className="w-6 h-6 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-foreground">
                Evolução: volume e acurácia diária
              </h2>
            </div>
            
            <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-lg border border-border">
              {[14, 30, 90].map(d => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  disabled={loadingTimeline}
                  className={clsx(
                    "px-3 py-1 text-sm font-medium rounded-md transition-colors cursor-pointer",
                    days === d 
                      ? "bg-background text-foreground shadow-sm" 
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/80",
                    loadingTimeline && "opacity-50 cursor-not-allowed"
                  )}
                >
                  {d}D
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs text-muted-foreground -mt-3 mb-3">Acurácia por dia oscila com amostras pequenas; use a tendência junto com o volume de questões.</p>
          <div className="bg-card border border-border shadow-sm rounded-2xl p-6 h-[400px] relative overflow-hidden flex flex-col min-w-0">
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-success/5 to-transparent opacity-50 pointer-events-none" />
            {localTimeline.length > 0 ? (
              <div className="flex-1 min-h-0 w-full mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={chartTimeline}
                    margin={{ top: 10, right: 10, bottom: 10, left: -20 }}
                  >
                    <defs>
                      <linearGradient id="colorAcc" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--success)" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="var(--success)" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="barAttempts" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.4}/>
                        <stop offset="100%" stopColor="var(--primary)" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="var(--border)" opacity={0.5} />
                    <XAxis 
                      dataKey="dateShort" 
                      axisLine={false} 
                      tickLine={false}
                      tick={{ fill: 'var(--muted-foreground)', fontSize: 12, fontWeight: 500 }} 
                      dy={10}
                    />
                    <YAxis 
                      yAxisId="left" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} 
                    />
                    <YAxis 
                      yAxisId="right" 
                      orientation="right" 
                      domain={[0, 100]} 
                      axisLine={false} 
                      tickLine={false} 
                      hide 
                    />
                    <Tooltip 
                      cursor={{ fill: 'var(--muted)', opacity: 0.15 }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-popover/95 backdrop-blur-md border border-border shadow-xl rounded-xl p-4 text-sm z-50 min-w-[200px]">
                              <p className="font-bold text-popover-foreground mb-3 text-base border-b border-border/50 pb-2 flex items-center gap-2">
                                <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                {data.day}
                              </p>
                              <div className="flex justify-between items-center mb-2">
                                <div className="flex items-center gap-2">
                                  <div className="w-2.5 h-2.5 rounded-sm bg-primary/40"></div>
                                  <span className="text-muted-foreground">Volume</span>
                                </div>
                                <span className="font-semibold text-foreground">{data.attempts} q.</span>
                              </div>
                              <div className="flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                  <div className="w-2.5 h-2.5 rounded-sm bg-success"></div>
                                  <span className="text-muted-foreground">Acurácia</span>
                                </div>
                                <span className="font-bold text-success">{data.accPct}%</span>
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar yAxisId="left" dataKey="attempts" fill="url(#barAttempts)" radius={[6, 6, 0, 0]} barSize={28} />
                    <Area yAxisId="right" type="monotone" dataKey="accPct" stroke="none" fill="url(#colorAcc)" />
                    <Line yAxisId="right" type="monotone" dataKey="accPct" stroke="var(--success)" strokeWidth={4} dot={{ r: 5, fill: "var(--background)", strokeWidth: 3, stroke: "var(--success)" }} activeDot={{ r: 8, fill: "var(--success)", stroke: "var(--background)", strokeWidth: 3 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-3">
                <svg className="w-10 h-10 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <p>Dados insuficientes para gerar a linha do tempo.</p>
              </div>
            )}
          </div>
        </section>

        {/* Heatmap de Consistência (Últimos 6 meses) */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-400 fill-mode-both">
          <div className="bg-card border border-border shadow-sm rounded-2xl p-6 relative overflow-hidden flex flex-col">
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-2 text-foreground">
                <span className="material-symbols-outlined text-[20px] text-primary" data-icon="calendar_month">calendar_month</span>
                <h3 className="text-lg font-bold text-foreground">Histórico de Atividade (Últimos 6 meses)</h3>
              </div>
              <span className="text-xs text-muted-foreground hidden sm:inline-block">Consistência e volume diário</span>
            </div>

            {(() => {
              const hData = (timeline180 && timeline180.length > 0) ? timeline180 : localTimeline;
              if (!hData || hData.length === 0) {
                return (
                  <p className="text-sm text-muted-foreground py-6 text-center">Nenhuma atividade registrada nos últimos 6 meses.</p>
                );
              }
              const today = new Date();
              const daysCount = 180;
              const startDate = new Date(today.getTime() - (daysCount - 1) * 24 * 60 * 60 * 1000);
              startDate.setDate(startDate.getDate() - startDate.getDay());
              const totalDays = Math.floor((today.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000)) + 1;
              
              const activityMap = new Map<string, number>();
              hData.forEach(t => {
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
                    className={clsx("w-[13px] h-[13px] rounded-[3px] transition-colors hover:ring-2 ring-primary/50", colorClass)}
                  />
                );
              }

              return (
                <div className="w-full overflow-x-auto pb-2 scrollbar-thin">
                  <div className="flex flex-col flex-wrap gap-1 h-[105px] min-w-max content-start">
                    {grid}
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground mt-3 pt-2 border-t border-border/50">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-xs bg-muted/50"></span> 0
                      <span className="w-2.5 h-2.5 rounded-xs bg-primary/30 ml-2"></span> 1-10
                      <span className="w-2.5 h-2.5 rounded-xs bg-primary/50 ml-1"></span> 11-30
                      <span className="w-2.5 h-2.5 rounded-xs bg-primary/70 ml-1"></span> 31-60
                      <span className="w-2.5 h-2.5 rounded-xs bg-primary ml-1"></span> 60+
                    </span>
                    <span>180 dias</span>
                  </div>
                </div>
              );
            })()}
          </div>
        </section>
      </div>

      {/* Right Column (1/3 on xl screens) */}
      <div className="flex flex-col gap-8 min-w-0">
        
        {/* Weak Topics */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-200">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-warning/10 rounded-lg">
              <svg className="w-6 h-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Tópicos Fracos & Armadilhas
            </h2>
          </div>
          <div className="bg-card/50 backdrop-blur-xl border border-white/10 shadow-sm rounded-2xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border/50 bg-muted/20">
              <p className="text-sm text-muted-foreground leading-relaxed">
                Ordenados por acurácia, com a amostra visível. Use como sinal de investigação, não como diagnóstico definitivo.
              </p>
            </div>
            <div className="divide-y divide-border/50">
              {weakTopics && weakTopics.length > 0 ? (
                weakTopics.slice(0, 8).map((wt) => {
                  const distractor = Array.isArray(distractors) ? distractors.find(d => d.subtema === wt.topic) : undefined;
                  const worstChoice = distractor?.wrong_choices?.[0];
                  
                  return (
                    <Link key={wt.topic} href={`/estudar?subtema=${encodeURIComponent(wt.topic)}&status=all&limit=50`} className="p-4 hover:bg-muted/30 transition-colors flex items-center justify-between gap-4 group">
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-foreground truncate group-hover:text-primary transition-colors" title={wt.topic}>{wt.topic}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{wt.correct} acertos em {wt.attempts} tentativas{wt.attempts < 10 ? " · amostra inicial" : ""}</p>
                        
                        {worstChoice && worstChoice.count >= 2 && wt.attempts >= 5 && (
                          <div className="mt-2 flex items-center gap-1.5 flex-wrap bg-destructive/5 w-fit p-1.5 rounded-md border border-destructive/10">
                            <svg className="w-3 h-3 text-destructive" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                              <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2"/>
                              <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2"/>
                            </svg>
                            <span className="text-xs text-muted-foreground">Você costuma errar marcando a</span>
                            <span className="inline-flex items-center justify-center bg-background font-bold text-foreground w-5 h-5 rounded text-[10px] uppercase border border-border">
                              {worstChoice.letter}
                            </span>
                            <span className="font-semibold text-destructive text-xs">({worstChoice.count}x)</span>
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <span className={clsx("font-bold text-lg", (wt.accuracy || 0) < 0.5 ? "text-destructive" : "text-warning")}>
                          {((wt.accuracy || 0) * 100).toFixed(0)}%
                        </span>
                        <svg className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </Link>
                  );
                })
              ) : (
                <div className="p-8 text-center text-muted-foreground flex flex-col items-center gap-3">
                  <svg className="w-8 h-8 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                    <circle cx="12" cy="12" r="6" strokeWidth="2"/>
                    <circle cx="12" cy="12" r="2" fill="currentColor"/>
                  </svg>
                  <p>Nenhum tópico fraco identificado ainda.</p>
                </div>
              )}
            </div>
          </div>
        </section>


      </div>
    </div>
  );
}
