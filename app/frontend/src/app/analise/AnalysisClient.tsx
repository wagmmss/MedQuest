"use client";

import { useMemo, useState, useEffect } from "react";
import { TimelineStat, WeakTopic, Recommendation, BreakdownStat, DistractorStat } from "@/types/api";
import { AlertTriangle, TrendingUp, Compass, AlarmClock, Lightbulb, Brain, ChevronRight, BarChart3, AlertCircle, Target, Activity } from "lucide-react";
import Link from "next/link";
import clsx from "clsx";
import { api } from "@/lib/api";
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Cell, LabelList, Area
} from 'recharts';

export function AnalysisClient({
  timeline,
  weakTopics,
  recommendations,
  breakdown,
  distractors
}: {
  timeline: TimelineStat[];
  weakTopics: WeakTopic[];
  recommendations: Recommendation[];
  breakdown: BreakdownStat[];
  distractors: DistractorStat[];
}) {
  const getRecIcon = (type: string) => {
    switch (type) {
      case "srs_due": return <AlarmClock className="text-primary group-hover:scale-110 transition-transform" size={24} />;
      case "weak_topic":
      case "weak_area": return <AlertTriangle className="text-warning group-hover:scale-110 transition-transform" size={24} />;
      case "explore": return <Compass className="text-secondary group-hover:scale-110 transition-transform" size={24} />;
      case "praise": return <TrendingUp className="text-success group-hover:scale-110 transition-transform" size={24} />;
      default: return <Lightbulb className="text-muted-foreground group-hover:scale-110 transition-transform" size={24} />;
    }
  };

  const [days, setDays] = useState<number>(14);
  const [localTimeline, setLocalTimeline] = useState<TimelineStat[]>(timeline);
  const [loadingTimeline, setLoadingTimeline] = useState(false);

  useEffect(() => {
    // If it's the initial load for 14 days, we already have it in props
    if (days === 14 && timeline.length > 0 && localTimeline === timeline) return;
    
    const fetchTimeline = async () => {
      setLoadingTimeline(true);
      try {
        const data = await api.stats.getTimeline(days);
        setLocalTimeline(data);
      } catch (error) {
        console.error("Failed to fetch timeline:", error);
      } finally {
        setLoadingTimeline(false);
      }
    };
    fetchTimeline();
  }, [days, timeline, localTimeline]);

  const chartBreakdown = useMemo(() => {
    return breakdown.slice(0, 8).map(b => ({
      ...b,
      accPct: parseFloat((b.accuracy * 100).toFixed(1)),
      // Truncate long labels for Y-axis display
      shortLabel: b.label.length > 35 ? b.label.substring(0, 32) + "..." : b.label
    }));
  }, [breakdown]);

  const chartTimeline = useMemo(() => {
    return localTimeline.map(t => ({
      ...t,
      dateShort: t.day.split("-").slice(1).reverse().join("/"),
      accPct: parseFloat((t.accuracy * 100).toFixed(1))
    }));
  }, [localTimeline]);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 pb-10">
      {/* Left Column (2/3 on xl screens) */}
      <div className="xl:col-span-2 flex flex-col gap-8 min-w-0">
        
        {/* Recommendations */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100 fill-mode-both">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Brain size={24} className="text-primary" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Recomendações Inteligentes
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {recommendations.length > 0 ? (
              recommendations.map((rec, idx) => {
                const queryParams = new URLSearchParams(rec.filters).toString();
                const href = queryParams ? `/estudar?${queryParams}` : "/estudar";
                return (
                  <Link 
                    key={idx} 
                    href={href}
                    className="group relative bg-card border border-border shadow-sm hover:shadow-md hover:border-primary/50 rounded-2xl p-6 flex flex-col transition-all overflow-hidden isolation-auto"
                  >
                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -z-10 group-hover:bg-primary/10 transition-colors" />
                    
                    <div className="flex items-start gap-4 mb-4">
                      <div className="p-3 bg-background rounded-xl border border-border shadow-sm">
                        {getRecIcon(rec.type)}
                      </div>
                      <h3 className="font-bold text-lg text-foreground leading-tight mt-1 group-hover:text-primary transition-colors">{rec.title}</h3>
                    </div>
                    <p className="text-muted-foreground text-sm flex-1 mb-6 leading-relaxed">{rec.description}</p>
                    <div className="mt-auto flex items-center justify-between text-sm font-semibold text-primary">
                      <span>{rec.cta}</span>
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                        <ChevronRight size={16} />
                      </div>
                    </div>
                  </Link>
                );
              })
            ) : (
              <div className="col-span-full bg-card border border-border rounded-2xl p-8 text-center text-muted-foreground flex flex-col items-center justify-center gap-3">
                <Target size={40} className="text-muted-foreground/50" />
                <p>Responda mais algumas questões para receber recomendações personalizadas.</p>
              </div>
            )}
          </div>
        </section>

        {/* Breakdown by Institution */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200 fill-mode-both">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-secondary/10 rounded-lg">
              <BarChart3 size={24} className="text-secondary" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Desempenho por Instituição
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
                      const acc = entry.accuracy * 100;
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
                <TrendingUp size={24} className="text-success" />
              </div>
              <h2 className="text-2xl font-bold text-foreground">
                Evolução Recente
              </h2>
            </div>
            
            <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-lg border border-border">
              {[14, 30, 90].map(d => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  disabled={loadingTimeline}
                  className={clsx(
                    "px-3 py-1 text-sm font-medium rounded-md transition-colors",
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
                      content={({ active, payload, label }) => {
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
      </div>

      {/* Right Column (1/3 on xl screens) */}
      <div className="flex flex-col gap-8 min-w-0">
        
        {/* Weak Topics */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200 fill-mode-both">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-warning/10 rounded-lg">
              <AlertTriangle size={24} className="text-warning" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Tópicos Fracos
            </h2>
          </div>
          <div className="bg-card border border-border shadow-sm rounded-2xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border/50 bg-muted/20">
              <p className="text-sm text-muted-foreground leading-relaxed">Tópicos com menor índice de acertos. Priorize estudá-los.</p>
            </div>
            <div className="divide-y divide-border/50">
              {weakTopics.length > 0 ? (
                weakTopics.slice(0, 8).map((wt) => (
                  <Link key={wt.topic} href={`/estudar?subtema=${encodeURIComponent(wt.topic)}&limit=50`} className="p-4 hover:bg-muted/30 transition-colors flex items-center justify-between gap-4 group">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-foreground truncate group-hover:text-primary transition-colors" title={wt.topic}>{wt.topic}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{wt.correct} acertos de {wt.attempts} totais</p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className={clsx("font-bold text-lg", wt.accuracy < 0.5 ? "text-destructive" : "text-warning")}>
                        {(wt.accuracy * 100).toFixed(0)}%
                      </span>
                      <ChevronRight size={16} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </Link>
                ))
              ) : (
                <div className="p-8 text-center text-muted-foreground flex flex-col items-center gap-3">
                  <Target size={32} className="text-muted-foreground/50" />
                  <p>Nenhum tópico fraco identificado ainda.</p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Distractors (New Feature) */}
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 fill-mode-both">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-destructive/10 rounded-lg">
              <AlertCircle size={24} className="text-destructive" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Análise de Distratores
            </h2>
          </div>
          <div className="bg-card border border-border shadow-sm rounded-2xl overflow-hidden">
            <div className="p-4 border-b border-border/50 bg-muted/20">
              <p className="text-sm text-muted-foreground leading-relaxed">Alternativas incorretas que você mais assinala. Fique atento a essas armadilhas.</p>
            </div>
            <div className="divide-y divide-border/50">
              {distractors.length > 0 ? (
                distractors.slice(0, 5).map((d, i) => {
                  const worstChoice = d.wrong_choices[0];
                  if (!worstChoice) return null;
                  return (
                    <Link key={i} href={`/estudar?subtema=${encodeURIComponent(d.subtema)}&limit=50`} className="p-4 flex items-center justify-between gap-4 hover:bg-muted/30 transition-colors group">
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-foreground truncate group-hover:text-primary transition-colors" title={d.subtema}>{d.subtema}</div>
                        <div className="text-sm text-muted-foreground mt-1 flex items-center gap-1.5 flex-wrap">
                          <span>A alternativa</span>
                          <span className="inline-flex items-center justify-center bg-muted font-bold text-foreground w-6 h-6 rounded text-xs uppercase border border-border">
                            {worstChoice.letter}
                          </span>
                          <span>foi escolhida incorretamente</span>
                          <span className="font-bold text-destructive bg-destructive/10 px-1.5 py-0.5 rounded">{worstChoice.count} vez(es)</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <ChevronRight size={16} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </Link>
                  );
                })
              ) : (
                <div className="p-8 text-center text-muted-foreground flex flex-col items-center gap-3">
                  <AlertCircle size={32} className="text-muted-foreground/50" />
                  <p className="text-sm">Não há distratores suficientes mapeados.</p>
                </div>
              )}
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
