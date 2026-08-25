"use client";

import { useMemo, useState, useEffect, useRef } from "react";
import { TimelineStat, WeakTopic, BreakdownStat, DistractorStat, PredictiveScore, AtRiskTopic, LearningProfile, ExamReadiness } from "@/types/api";
import { AlertTriangle, TrendingUp, Brain, ChevronRight, BarChart3, AlertCircle, Target, Activity } from "lucide-react";
import Link from "next/link";
import clsx from "clsx";
import { api } from "@/lib/api";
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Cell, LabelList, Area
} from 'recharts';
import { motion } from 'framer-motion';

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

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 pb-10">
      {/* Left Column (2/3 on xl screens) */}
      <div className="xl:col-span-2 flex flex-col gap-8 min-w-0">

        {/* Adaptive Goal Banner */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card border border-primary/30 shadow-sm rounded-2xl p-6"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Brain size={22} className="text-primary" />
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
              Iniciar sessão personalizada <ChevronRight size={18} />
            </Link>
          </div>
        </motion.section>

        {/* Exam readiness with an explicit scope */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card border border-border shadow-sm rounded-2xl p-6"
        >
          <div className="flex items-start justify-between gap-4 mb-5">
            <div>
              <h2 className="text-xl font-bold text-foreground">Prontidão por instituição</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Cobertura: {Math.round(localReadiness.coverage * 100)}% ({localReadiness.answered} de {localReadiness.available} questões no escopo selecionado).
              </p>
            </div>
            <label className="text-xs font-semibold text-muted-foreground flex flex-col gap-1">
              Instituição
              <select value={selectedInstitution} onChange={(event) => setSelectedInstitution(event.target.value)} className="bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground" aria-label="Selecionar instituição">
                <option value="">Banco geral</option>
                {institutionOptions.map(option => <option key={option.key} value={option.key}>{option.label}</option>)}
              </select>
            </label>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {localReadiness.areas.slice(0, 6).map(area => (
              <Link key={area.area} href={area.action} className="rounded-xl border border-border p-4 hover:border-primary/40 transition-colors">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold text-foreground">{area.area}</span>
                  <span className="text-sm text-primary">{Math.round(area.coverage * 100)}%</span>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {area.sample === "limited" ? `${area.attempts} tentativas — amostra limitada.` : `${area.attempts} tentativas · ${Math.round((area.accuracy || 0) * 100)}% de acurácia.`}
                </p>
              </Link>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-4">{loadingReadiness ? "Atualizando escopo…" : localReadiness.disclaimer}</p>
        </motion.section>
        
        {/* Predictive Dashboard */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Target size={24} className="text-primary" />
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
                  <Activity className="text-muted-foreground" size={20} />
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
                <AlertCircle className="text-warning" size={20} />
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
        </motion.section>

        {/* Breakdown by Institution */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-secondary/10 rounded-lg">
              <BarChart3 size={24} className="text-secondary" />
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
        </motion.section>

        {/* Timeline (Recharts ComposedChart) */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 fill-mode-both">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-success/10 rounded-lg">
                <TrendingUp size={24} className="text-success" />
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
                                <Activity size={16} className="text-muted-foreground" />
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
                <Activity size={40} className="text-muted-foreground/50" />
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
        <motion.section 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-warning/10 rounded-lg">
              <AlertTriangle size={24} className="text-warning" />
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
                            <AlertCircle size={12} className="text-destructive" />
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
                        <ChevronRight size={16} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </Link>
                  );
                })
              ) : (
                <div className="p-8 text-center text-muted-foreground flex flex-col items-center gap-3">
                  <Target size={32} className="text-muted-foreground/50" />
                  <p>Nenhum tópico fraco identificado ainda.</p>
                </div>
              )}
            </div>
          </div>
        </motion.section>

      </div>
    </div>
  );
}
