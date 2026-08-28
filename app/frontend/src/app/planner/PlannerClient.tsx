"use client";
import { useRouter } from "next/navigation";

import { useState, useEffect, memo } from "react";
import Link from "next/link";
import { PlannerWeek, PlannerProgressMap, PlannerTopic, PlannerConfig, PlannerTopicProgressMap } from "@/types/api";
import { api } from "@/lib/api";
import { getSubtemaDetails } from "@/lib/plannerData";
import { Check, CalendarDays, Clock, Activity, Loader2, RotateCcw, AlertTriangle, Zap, X, Play, Flame, Settings2, ExternalLink, Download } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import { PlannerWizard } from "./PlannerWizard";
import { syncPlanToGoogleCalendarDirectly, SyncProgress } from "@/lib/googleCalendar";

const getAreaColorClass = (areaName: string) => {
  const name = areaName.toLowerCase();
  if (name.includes("preventiva")) return "bg-area-preventiva text-area-preventiva";
  if (name.includes("pediatria")) return "bg-area-pediatria text-area-pediatria";
  if (name.includes("go") || name.includes("ginecologia")) return "bg-area-go text-area-go";
  if (name.includes("cirurgia")) return "bg-area-cirurgia text-area-cirurgia";
  return "bg-area-clinica text-area-clinica";
};

const formatHours = (hours: number) => hours.toLocaleString("pt-BR", {
  minimumFractionDigits: Number.isInteger(hours) ? 0 : 1,
  maximumFractionDigits: 1,
});

const TopicRow = memo(function TopicRow({ 
  t, 
  completed,
  toggleTopic,
  week,
  weekDate,
  topicIndex,
  daysPerWeek
}: { 
  t: PlannerTopic; 
  completed: boolean;
  toggleTopic: (week: number, subtema: string, completed: boolean) => void;
  week: number;
  weekDate?: Date;
  topicIndex?: number;
  daysPerWeek?: number;
}) {
  const info = getSubtemaDetails(t.subtema);
  const key = `planner-topic-${week}-${t.subtema}`;
  const isChecked = completed;

  // Cálculo de Link 1-Clique para o Google Agenda
  const gcalUrl = (() => {
    if (!weekDate) return null;
    const studyDays = Math.max(1, Math.min(7, daysPerWeek || 6));
    const dayOffset = (topicIndex || 0) % studyDays;
    const topicDt = new Date(weekDate.getTime() + dayOffset * 86400000);
    const dtStart = new Date(topicDt);
    dtStart.setHours(8, 0, 0, 0);
    const durationMinutes = Math.max(30, Math.round(t.estimated_hours * 60));
    const dtEnd = new Date(dtStart.getTime() + durationMinutes * 60000);

    const formatGCalDate = (d: Date) => d.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
    const startStr = formatGCalDate(dtStart);
    const endStr = formatGCalDate(dtEnd);

    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const title = `[MedQuest] 📖 ${t.subtema} (${t.area})`;
    const details = `📚 Carga: ${t.estimated_hours}h (Teoria: ${t.estimated_theory_hours}h + Questões: ${t.estimated_practice_hours}h)\nSemana ${weekDate.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })} • ${t.area}${origin ? `\n\n🔗 Questões: ${origin}/estudar?subtema=${encodeURIComponent(t.subtema)}&limit=25` : ""}`;

    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${startStr}/${endStr}&details=${encodeURIComponent(details)}&location=MedQuest`;
  })();

  return (
    <div className="flex items-start gap-3 py-2.5 px-3 rounded-xl border border-transparent hover:border-border/50 hover:bg-muted/20 transition-all group">
      <div className="relative flex items-center mt-0.5 shrink-0">
        <input 
          type="checkbox"
          id={key}
          className="peer sr-only"
          checked={isChecked}
          onChange={() => toggleTopic(week, t.subtema, isChecked)}
        />
        <label 
          htmlFor={key}
          className="w-4 h-4 border border-muted-foreground/40 rounded transition-colors peer-checked:bg-primary peer-checked:border-primary flex items-center justify-center cursor-pointer hover:border-primary/60"
        >
          <Check size={10} className={clsx("text-primary-foreground transition-opacity", isChecked ? "opacity-100" : "opacity-0")} strokeWidth={4} />
        </label>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <label 
            htmlFor={key}
            className={clsx(
              "font-semibold text-sm leading-snug cursor-pointer transition-colors", 
              isChecked ? "text-muted-foreground line-through opacity-70" : "text-foreground group-hover:text-primary"
            )}
          >
            {t.subtema}
          </label>
          {info?.highYield && (
            <span title="Tema de Alto Rendimento na USP" className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[11px] font-bold bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
              <Flame size={12} className="fill-current text-orange-500" /> Foco USP
            </span>
          )}
        </div>

        <div className="text-xs text-muted-foreground flex items-center flex-wrap gap-1.5 mt-1.5">
          <span className={clsx("font-medium", getAreaColorClass(t.area).split(" ")[1])}>{t.area}</span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Clock size={11} /> {formatHours(t.estimated_theory_hours)}h teóricas + {formatHours(t.estimated_practice_hours)}h questões = {formatHours(t.estimated_hours)}h
          </span>
          <span>•</span>
          <span>{t.questions_available} questões disponíveis</span>
        </div>

        <div className="mt-2.5 flex items-center gap-2 flex-wrap">
          <Link 
            href={`/estudar?subtema=${encodeURIComponent(t.subtema)}&limit=25`}
            className="inline-flex items-center gap-1.5 px-3 py-1 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-semibold rounded-lg transition-colors border border-primary/20"
          >
            <Play size={11} className="fill-primary" /> Praticar Questões
          </Link>
          {gcalUrl && (
            <a
              href={gcalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground text-xs font-medium rounded-lg transition-colors border border-border"
              title="Adicionar esta aula à sua agenda pessoal do Google (100% editável e móvel)"
            >
              <CalendarDays size={12} className="text-primary" />
              + Google Agenda
            </a>
          )}
        </div>
      </div>
    </div>
  );
});
TopicRow.displayName = "TopicRow";

interface PlannerClientProps {
  plan: PlannerWeek[];
  initialProgress: PlannerProgressMap;
  initialTopicProgress: PlannerTopicProgressMap;
  warning?: string;
  isIntensive?: boolean;
  config?: PlannerConfig | null;
}

export function PlannerClient({ plan, initialProgress, initialTopicProgress, warning, isIntensive, config }: PlannerClientProps) {
  const router = useRouter();
  const [progress, setProgress] = useState<PlannerProgressMap>(initialProgress);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [topicProgress, setTopicProgress] = useState<PlannerTopicProgressMap>(initialTopicProgress);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showCalendarModal, setShowCalendarModal] = useState(false);
  const [exportingIcs, setExportingIcs] = useState(false);
  const [googleSyncing, setGoogleSyncing] = useState(false);
  const [googleSyncProgress, setGoogleSyncProgress] = useState<SyncProgress | null>(null);

  const handleExportIcs = async () => {
    setExportingIcs(true);
    try {
      await api.planner.exportIcs();
      toast.success("Arquivo de calendário (.ics) gerado com sucesso!");
    } catch {
      toast.error("Erro ao exportar cronograma.");
    } finally {
      setExportingIcs(false);
    }
  };

  const handleDirectGoogleSync = async () => {
    setGoogleSyncing(true);
    setGoogleSyncProgress({ current: 0, total: 100, status: "Iniciando conexão com sua conta Google..." });
    try {
      const res = await syncPlanToGoogleCalendarDirectly(
        plan,
        config?.days_per_week || 6,
        (p) => setGoogleSyncProgress(p)
      );
      if (res.success) {
        toast.success("Agenda MedQuest criada e eventos exportados com sucesso no seu Google Agenda!");
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      if (errMsg === "GOOGLE_CLIENT_ID_MISSING") {
        // Fallback rápido: baixa o .ics e abre o Google Calendar Import em 1 clique
        toast("Baixando arquivo e abrindo o importador do Google Agenda...", { icon: "📅" });
        await handleExportIcs();
        window.open("https://calendar.google.com/calendar/r/settings/export", "_blank");
      } else {
        toast.error("Erro na sincronização: " + errMsg);
      }
    } finally {
      setGoogleSyncing(false);
      setGoogleSyncProgress(null);
    }
  };

  const handleQuickImportFlow = async () => {
    toast.success("Baixando arquivo e abrindo o importador do Google Agenda...");
    await handleExportIcs();
    window.open("https://calendar.google.com/calendar/r/settings/export", "_blank");
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setProgress(initialProgress);
    }, 0);
    return () => clearTimeout(timer);
  }, [initialProgress]);

  useEffect(() => {
    const timer = setTimeout(() => setTopicProgress(initialTopicProgress), 0);
    return () => clearTimeout(timer);
  }, [initialTopicProgress]);

  const toggleTopic = async (week: number, subtema: string, currentStatus: boolean) => {
    const key = `${week}:${subtema}`;
    const completed = !currentStatus;
    setTopicProgress(prev => ({ ...prev, [key]: completed }));
    try {
      await api.planner.markTopic(week, subtema, completed);
    } catch {
      setTopicProgress(prev => ({ ...prev, [key]: currentStatus }));
      toast.error("Erro ao salvar o tema concluído.");
    }
  };

  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const handleResetConfig = async () => {
    setShowResetConfirm(false);
    setLoadingAction("reset");
    try {
      await api.planner.resetConfig();
      toast.success("Progresso reiniciado com sucesso.");
      router.refresh();
    } catch {
      toast.error("Erro ao reiniciar progresso.");
      setLoadingAction(null);
    }
  };

  const handleToggleIntensive = () => {
    if (isIntensive) {
      router.push("/planner");
    } else {
      router.push("/planner?intensive=true");
    }
  };



  const handleToggleStudy = async (week: number, currentStatus: boolean) => {
    const actionKey = `study-${week}`;
    if (loadingAction) return;
    setLoadingAction(actionKey);

    const newStatus = !currentStatus;
    // Optimistic UI
    setProgress(prev => ({
      ...prev,
      [week.toString()]: { ...prev[week.toString()], studied: newStatus, studied_at: newStatus ? new Date().toISOString() : null }
    }));

    try {
      await api.planner.markStudy(week, newStatus);
    } catch {
      toast.error("Erro ao salvar progresso.");
      // Revert on error
      setProgress(prev => ({
        ...prev,
        [week.toString()]: {
          ...prev[week.toString()],
          studied: currentStatus,
          studied_at: currentStatus ? prev[week.toString()]?.studied_at ?? null : null,
        }
      }));
    } finally {
      setLoadingAction(null);
    }
  };

  const today = new Date();
  const totalTopics = plan.reduce((total, week) => total + week.topics.length, 0);
  const completedTopics = Object.values(topicProgress).filter(Boolean).length;

  return (
    <>
    <div className="flex flex-col gap-6 pb-12">
      {warning && !isIntensive && (
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 p-4 rounded-xl flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex gap-3">
            <AlertTriangle className="shrink-0 mt-0.5" size={20} />
            <div>
              <p className="font-semibold text-sm">Alerta de Tempo</p>
              <p className="text-sm opacity-90">{warning}</p>
            </div>
          </div>
          <button 
            onClick={handleToggleIntensive}
            className="shrink-0 bg-amber-500 text-white font-medium px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-amber-600 transition-colors"
          >
            <Zap size={16} /> Ativar Plano Intensivo
          </button>
        </div>
      )}

      {isIntensive && (
        <div className="bg-primary/10 border border-primary/20 text-primary p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Zap className="shrink-0" size={20} />
            <p className="text-sm font-medium">Modo Intensivo Ativado: Exibindo apenas temas de Alto Rendimento.</p>
          </div>
          <button 
            onClick={handleToggleIntensive}
            className="text-xs font-medium hover:underline opacity-80"
          >
            Voltar ao plano normal
          </button>
        </div>
      )}

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <CalendarDays className="text-primary" size={28} />
            Seu Cronograma de Estudos
          </h2>
          <p className="text-muted-foreground text-sm">Cronograma estruturado por carga, cobertura e temas de alta incidência.</p>
          {config?.target_institution && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1.5 flex-wrap">
              {config.target_institution.split(",").map((instName, idx) => (
                <span key={idx} className="font-bold text-foreground bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-md">
                  {instName.trim()}
                </span>
              ))}
              {config.target_specialty && (
                <>
                  <span>•</span>
                  <span><strong className="text-foreground">Especialidade:</strong> {config.target_specialty}</span>
                </>
              )}
              {config.target_score && (
                <>
                  <span>•</span>
                  <span><strong className="text-foreground">Meta:</strong> {config.target_score}%</span>
                </>
              )}
              {config.days_per_week && config.hours_per_day && (
                <>
                  <span>•</span>
                  <span>{config.days_per_week} dias/sem ({config.hours_per_day}h/dia)</span>
                </>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3 sm:gap-4 w-full sm:w-auto flex-wrap justify-between sm:justify-end">
          <div className="flex-1 sm:w-44">
            <div className="flex justify-between text-[11px] uppercase tracking-wider font-semibold mb-1">
              <span className="text-muted-foreground">Temas concluídos</span>
              <span className="text-primary">{completedTopics} / {totalTopics}</span>
            </div>
            <div className="h-2 w-full bg-muted rounded-full overflow-hidden ring-1 ring-inset ring-black/5 dark:ring-white/5">
              <div 
                className="h-full bg-primary transition-all duration-500 shadow-inner" 
                style={{ width: `${(completedTopics / Math.max(1, totalTopics)) * 100}%` }}
              />
            </div>
          </div>
          <button 
            onClick={() => setShowSettingsModal(true)}
            className="flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-primary bg-primary/10 hover:bg-primary/20 border border-primary/25 px-3 py-1.5 rounded-lg transition-colors shadow-sm"
          >
            <Settings2 size={15} />
            Calibrar Perfil
          </button>
          <button 
            onClick={() => setShowCalendarModal(true)}
            className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-foreground bg-muted hover:bg-muted/80 px-2.5 py-1.5 rounded-lg border border-border transition-colors shadow-sm"
            title="Sincronizar cronograma com Google Agenda, Apple Calendar ou baixar arquivo .ics"
          >
            <CalendarDays size={15} className="text-primary" />
            Sincronizar com Agenda
          </button>
          <button 
            onClick={() => setShowResetConfirm(true)}
            disabled={loadingAction === "reset"}
            className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-muted-foreground hover:text-foreground bg-muted hover:bg-muted/80 px-2.5 py-1.5 rounded-lg transition-colors"
          >
            {loadingAction === "reset" ? <Loader2 size={15} className="animate-spin" /> : <RotateCcw size={15} />}
            Refazer
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {plan.map((week) => {
          const weekProgress = progress[week.week.toString()] || { studied: false, rev24h: false, rev7d: false, rev30d: false };
          const completedInWeek = week.topics.filter(topic => topicProgress[`${week.week}:${topic.subtema}`]).length;
          const weekDate = new Date(week.date);
          // Highlight current week if it falls within this week's 7 days
          const isCurrentWeek = weekDate <= today && new Date(weekDate.getTime() + 7 * 24 * 60 * 60 * 1000) > today;

          return (
            <div 
              key={week.week} 
              className={clsx(
                "bg-card border rounded-xl overflow-hidden shadow-1 flex flex-col md:flex-row transition-colors",
                isCurrentWeek ? "border-primary ring-1 ring-primary/20" : "border-border",
                weekProgress.studied ? "opacity-75" : "opacity-100"
              )}
            >
              {/* Left Column (Info) */}
              <div className="p-5 flex-1 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-muted-foreground bg-muted px-2.5 py-1 rounded-md">
                      Semana {week.week}
                    </span>
                    <span className="text-sm text-muted-foreground flex items-center gap-2">
                      {weekDate.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
                      <span className="text-xs px-2 py-0.5 rounded-full bg-secondary/50 text-secondary-foreground font-medium">
                       {week.allocated_hours}h / {week.recommended_hours}h
                      </span>
                    </span>
                    {isCurrentWeek && (
                      <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Activity size={12} /> Atual
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground">{completedInWeek}/{week.topics.length} temas</span>
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  {week.topics.map((t, idx) => (
                    <TopicRow 
                      key={idx} 
                      t={t} 
                       completed={Boolean(topicProgress[`${week.week}:${t.subtema}`])}
                       toggleTopic={toggleTopic}
                       week={week.week}
                      weekDate={weekDate}
                      topicIndex={idx}
                      daysPerWeek={config?.days_per_week || 6}
                    />
                  ))}
                  {week.topics.length === 0 && (
                    <div className="text-sm text-muted-foreground italic">Semana de revisão geral ou descanso.</div>
                  )}
                </div>
              </div>

              {/* Right Column (Checklist) */}
              <div className="bg-card-2 p-5 border-t md:border-t-0 md:border-l border-border md:w-72 shrink-0 flex flex-col justify-center">
                <h3 className="text-sm font-semibold text-foreground mb-2 uppercase tracking-wider">Status da semana</h3>
                <p className="text-xs text-muted-foreground mb-4">As revisões são gerenciadas pela Revisão Ativa conforme o FSRS.</p>
                <div className="flex flex-col gap-3">
                  
                  {/* Master Study Checkbox */}
                  <label className={clsx(
                    "flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors border",
                    weekProgress.studied ? "bg-primary/10 border-primary/20" : "bg-card border-border hover:bg-muted"
                  )}>
                    <div className="relative flex items-center">
                      <input 
                        type="checkbox"
                        className="peer sr-only"
                        checked={weekProgress.studied}
                        onChange={() => handleToggleStudy(week.week, weekProgress.studied)}
                        disabled={loadingAction === `study-${week.week}`}
                      />
                      <div className="w-5 h-5 border-2 border-muted-foreground rounded transition-colors peer-checked:bg-primary peer-checked:border-primary flex items-center justify-center">
                        {loadingAction === `study-${week.week}` ? (
                          <Loader2 size={12} className="text-primary-foreground animate-spin" />
                        ) : (
                          <Check size={14} className={clsx("text-primary-foreground transition-opacity", weekProgress.studied ? "opacity-100" : "opacity-0")} strokeWidth={3} />
                        )}
                      </div>
                    </div>
                    <span className={clsx("text-sm font-medium select-none", weekProgress.studied ? "text-primary" : "text-foreground")}>
                      Fechar semana
                    </span>
                  </label>


                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowResetConfirm(false)} />
          <div className="relative bg-card border border-border rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4 animate-in fade-in zoom-in-95 duration-200">
            <button onClick={() => setShowResetConfirm(false)} className="absolute top-4 right-4 p-1 rounded-full hover:bg-muted transition-colors text-muted-foreground">
              <X size={18} />
            </button>
            <div className="flex flex-col items-center text-center gap-4">
              <div className="p-3 bg-destructive/10 rounded-full">
                <AlertTriangle size={28} className="text-destructive" />
              </div>
              <h3 className="text-lg font-bold text-foreground">Resetar Progresso do Planner?</h3>
              <p className="text-sm text-muted-foreground">Isso apagará TODO o seu progresso no planner. Esta ação não pode ser desfeita.</p>
              <div className="flex gap-3 w-full mt-2">
                <button onClick={() => setShowResetConfirm(false)} className="flex-1 py-2.5 px-4 rounded-xl border border-border text-foreground hover:bg-muted transition-colors font-medium text-sm">Cancelar</button>
                <button onClick={handleResetConfig} className="flex-1 py-2.5 px-4 rounded-xl bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors font-bold text-sm">Sim, Apagar Tudo</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settings / Calibration Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowSettingsModal(false)} />
          <div className="relative z-10 max-h-[90vh] overflow-y-auto w-full max-w-2xl animate-in fade-in zoom-in-95 duration-200">
            <PlannerWizard
              initialConfig={config}
              onClose={() => setShowSettingsModal(false)}
              isModal
            />
          </div>
        </div>
      )}

      {/* Calendar Sync Modal */}
      {showCalendarModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowCalendarModal(false)} />
          <div className="relative bg-card border border-border rounded-2xl shadow-2xl p-6 md:p-8 max-w-lg w-full z-10 animate-in fade-in zoom-in-95 duration-200">
            <button 
              onClick={() => setShowCalendarModal(false)} 
              className="absolute top-4 right-4 p-1.5 rounded-full hover:bg-muted transition-colors text-muted-foreground"
            >
              <X size={18} />
            </button>

            <div className="flex items-center gap-3 mb-5">
              <div className="w-11 h-11 bg-primary/15 text-primary rounded-xl flex items-center justify-center border border-primary/20 shrink-0">
                <CalendarDays size={22} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground">Sincronizar com Calendário</h3>
                <p className="text-xs text-muted-foreground">Aulas e revisões separadas com a duração real de estudo.</p>
              </div>
            </div>

            <div className="space-y-4">
              {/* Opção 1: Agenda 100% Editável no Google Agenda */}
              <div className="border border-primary/30 bg-primary/5 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
                      G
                    </div>
                    <span className="font-bold text-sm text-foreground">Copiar para Minha Agenda do Google (100% Editável)</span>
                  </div>
                  <span className="text-[10px] uppercase font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full">
                    Móvel & Editável
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Cria uma cópia direta na sua conta Google. Você poderá <strong>arrastar aulas para outros horários, mudar dias, editar descrições e personalizar livremente</strong>.
                </p>

                {googleSyncProgress && (
                  <div className="space-y-1.5 bg-background/80 p-3 rounded-xl border border-border animate-in fade-in duration-200">
                    <div className="flex justify-between text-xs font-semibold text-foreground">
                      <span className="truncate pr-2">{googleSyncProgress.status}</span>
                      <span>{Math.round((googleSyncProgress.current / Math.max(1, googleSyncProgress.total)) * 100)}%</span>
                    </div>
                    <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary transition-all duration-300"
                        style={{ width: `${(googleSyncProgress.current / Math.max(1, googleSyncProgress.total)) * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="flex flex-col sm:flex-row gap-2 pt-1">
                  <button
                    onClick={handleDirectGoogleSync}
                    disabled={googleSyncing || exportingIcs}
                    className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-2.5 px-3 rounded-xl transition-all flex items-center justify-center gap-1.5 text-xs shadow-sm disabled:opacity-50"
                  >
                    {googleSyncing ? <Loader2 size={14} className="animate-spin" /> : <ExternalLink size={14} />}
                    {googleSyncing ? "Exportando para o Google..." : "1-Clique: Criar Cópia no Google Agenda"}
                  </button>
                  <button
                    onClick={handleQuickImportFlow}
                    disabled={exportingIcs}
                    className="bg-card hover:bg-muted text-foreground border border-border font-medium py-2.5 px-3 rounded-xl transition-all flex items-center justify-center gap-1.5 text-xs"
                    title="Baixa o arquivo .ics e abre o importador oficial do Google Agenda"
                  >
                    <Download size={14} />
                    Importar Arquivo (.ics)
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-5 text-[11px] text-muted-foreground text-center bg-muted/20 p-2.5 rounded-lg border border-border/50">
              💡 <strong>Dica:</strong> Você também pode clicar no botão <strong>+ Google Agenda</strong> ao lado de qualquer aula individual no Planner para adicioná-la diretamente à sua agenda pessoal com horário 100% editável.
            </div>
          </div>
        </div>
      )}
    </>
  );
}
