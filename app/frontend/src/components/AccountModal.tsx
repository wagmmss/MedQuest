"use client";

import { useEffect, useState } from "react";
import { useUser, useClerk } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { NotificationConfig } from "@/types/api";
import { localDb, getLocalOwnerId } from "@/lib/db";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { clearLearningSessions } from "@/lib/sessionState";
import {
  X, Trash2, LogOut, AlertTriangle, User, ShieldAlert,
  Bell, BellOff, Check, AlertCircle, Loader2, Clock
} from "lucide-react";

interface AccountModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const WEEKDAYS = [
  { id: 0, label: "Seg" },
  { id: 1, label: "Ter" },
  { id: 2, label: "Qua" },
  { id: 3, label: "Qui" },
  { id: 4, label: "Sex" },
  { id: 5, label: "Sáb" },
  { id: 6, label: "Dom" },
];

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export function AccountModal({ isOpen, onClose }: AccountModalProps) {
  const { user, isLoaded } = useUser();
  const { signOut } = useClerk();
  const router = useRouter();

  const [step, setStep] = useState<"profile" | "confirm_reset">("profile");
  const [confirmText, setConfirmText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estados de Notificações
  const [notifConfig, setNotifConfig] = useState<NotificationConfig | null>(null);
  const [notifStatus, setNotifStatus] = useState<"loading" | "unsupported" | "denied" | "active" | "disabled" | "error">("loading");
  const [isNotifSubmitting, setIsNotifSubmitting] = useState(false);
  const [notifMessage, setNotifMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const loadNotificationConfig = async () => {
      // Verificar suporte a Web Push no navegador
      if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
        setNotifStatus("unsupported");
        return;
      }

      if (Notification.permission === "denied") {
        setNotifStatus("denied");
        return;
      }

      try {
        const config = await api.notifications.getConfig();
        setNotifConfig(config);
        if (config.enabled && config.has_active_subscription) {
          setNotifStatus("active");
        } else {
          setNotifStatus("disabled");
        }
      } catch (err) {
        console.warn("Erro ao carregar preferências de notificação:", err);
        setNotifStatus("disabled");
      }
    };

    loadNotificationConfig();
  }, [isOpen]);

  const handleSubscribePush = async () => {
    setIsNotifSubmitting(true);
    setNotifMessage(null);
    try {
      if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window)) {
        setNotifStatus("unsupported");
        return;
      }

      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setNotifStatus("denied");
        setNotifMessage("Permissão de notificações não foi concedida.");
        return;
      }

      const reg = await navigator.serviceWorker.ready;
      let subscription = await reg.pushManager.getSubscription();

      if (!subscription) {
        const vapidKey = notifConfig?.vapid_public_key;
        if (vapidKey) {
          const convertedKey = urlBase64ToUint8Array(vapidKey);
          subscription = await reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: convertedKey,
          });
        } else {
          // Fallback caso VAPID não esteja configurada no backend
          subscription = await reg.pushManager.subscribe({
            userVisibleOnly: true,
          });
        }
      }

      const subJson = subscription.toJSON();
      if (!subJson.endpoint || !subJson.keys?.p256dh || !subJson.keys?.auth) {
        throw new Error("Dados incompletos da assinatura Web Push.");
      }

      await api.notifications.subscribe({
        endpoint: subJson.endpoint,
        keys: {
          p256dh: subJson.keys.p256dh,
          auth: subJson.keys.auth,
        },
      });

      const updated = await api.notifications.getConfig();
      setNotifConfig(updated);
      setNotifStatus("active");
      setNotifMessage("Notificações diárias de revisão ativadas com sucesso!");
    } catch (err) {
      console.error("Erro ao assinar notificações:", err);
      setNotifStatus("error");
      setNotifMessage("Não foi possível ativar as notificações no momento.");
    } finally {
      setIsNotifSubmitting(false);
    }
  };

  const handleUnsubscribePush = async () => {
    setIsNotifSubmitting(true);
    setNotifMessage(null);
    try {
      if (typeof window !== "undefined" && "serviceWorker" in navigator) {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.getSubscription();
        if (sub) {
          await sub.unsubscribe();
        }
      }

      await api.notifications.unsubscribe();
      const updated = await api.notifications.getConfig();
      setNotifConfig(updated);
      setNotifStatus("disabled");
      setNotifMessage("Notificações revogadas com sucesso.");
    } catch (err) {
      console.error("Erro ao revogar notificações:", err);
      setNotifMessage("Erro ao revogar notificações.");
    } finally {
      setIsNotifSubmitting(false);
    }
  };

  const handleUpdatePreferences = async (hour: number, days: number[]) => {
    if (!notifConfig) return;
    try {
      await api.notifications.updateConfig({
        enabled: notifConfig.enabled,
        preferred_hour: hour,
        days_of_week: days,
      });
      setNotifConfig(prev => prev ? { ...prev, preferred_hour: hour, days_of_week: days } : null);
    } catch (err) {
      console.error("Erro ao salvar preferências de notificação:", err);
    }
  };

  const toggleDay = (dayId: number) => {
    if (!notifConfig) return;
    const current = notifConfig.days_of_week || [0, 1, 2, 3, 4, 5, 6];
    let next: number[];
    if (current.includes(dayId)) {
      if (current.length === 1) return; // Manter pelo menos 1 dia
      next = current.filter(d => d !== dayId);
    } else {
      next = [...current, dayId].sort();
    }
    handleUpdatePreferences(notifConfig.preferred_hour, next);
  };

  const handleResetProgress = async () => {
    if (confirmText.toUpperCase() !== "RESETAR") return;

    setIsLoading(true);
    setError(null);
    try {
      const res = await api.stats.resetProgress();
      if (res.success) {
        clearLearningSessions();
        localStorage.removeItem("medquest_simulado_config");
        localStorage.removeItem("mq_last_confetti");
        localStorage.removeItem("medquest_last_offline_download");
        for (const key of Object.keys(localStorage)) {
          if (key.startsWith("medquest_planner_topics_") || (key.startsWith("medquest_") && key !== "medquest_local_owner" && key !== "theme")) {
            localStorage.removeItem(key);
          }
        }
        if (localDb) {
          try {
            const uid = getLocalOwnerId();
            await Promise.all([
              localDb.questions.where('_owner_id').equals(uid).delete(),
              localDb.flashcards.where('_owner_id').equals(uid).delete(),
              localDb.simuladoPackages.where('owner_id').equals(uid).delete(),
              localDb.syncQueue.where('owner_id').equals(uid).delete()
            ]);

          } catch (dexieErr) {
            console.warn("Erro ao limpar dados locais no reset:", dexieErr);
          }
        }
        resetStateAndClose();
        router.push("/");
        router.refresh();
      } else {
        setError("Não foi possível resetar o progresso. Tente novamente.");
        setIsLoading(false);
      }
    } catch (err) {
      console.error(err);
      setError("Ocorreu um erro ao resetar o progresso.");
      setIsLoading(false);
    }
  };

  const resetStateAndClose = () => {
    setStep("profile");
    setConfirmText("");
    setError(null);
    setNotifMessage(null);
    setIsLoading(false);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !isLoading && resetStateAndClose()}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
          />

          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 15 }}
            transition={{ type: "spring", duration: 0.4, bounce: 0.15 }}
            className="bg-card border border-border rounded-3xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto z-10 flex flex-col relative"
            role="dialog"
            aria-modal="true"
            aria-labelledby="account-modal-title"
          >
            <div className="flex justify-between items-center px-6 py-4 border-b border-border bg-muted/30 sticky top-0 bg-card/95 backdrop-blur z-20">
              <h2 id="account-modal-title" className="text-lg font-bold text-foreground">
                {step === "profile" ? "Minha Conta" : "Resetar Progresso"}
              </h2>
              <button
                onClick={() => !isLoading && resetStateAndClose()}
                disabled={isLoading}
                className="text-muted-foreground hover:bg-muted rounded-full p-1.5 transition-colors flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 flex-1 flex flex-col gap-6">
              <AnimatePresence mode="wait">
                {step === "profile" ? (
                  <motion.div
                    key="profile"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    transition={{ duration: 0.2 }}
                    className="flex flex-col gap-6"
                  >
                    {/* Perfil Header */}
                    <div className="flex items-center gap-4 bg-muted/20 p-4 rounded-2xl border border-border">
                      <div className="relative w-16 h-16 rounded-2xl bg-muted overflow-hidden flex-shrink-0 border-2 border-primary/10 shadow-sm">
                        {isLoaded && user?.imageUrl ? (
                          <Image src={user.imageUrl} alt="Avatar" fill sizes="64px" className="object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-primary/10 text-primary">
                            <User size={32} />
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold text-foreground truncate">
                          {isLoaded ? (user?.fullName || "Usuário MedQuest") : "Carregando..."}
                        </h3>
                        <p className="text-sm text-muted-foreground truncate">
                          {isLoaded ? (user?.primaryEmailAddress?.emailAddress || "") : ""}
                        </p>
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 mt-2 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                          Preparação USP
                        </span>
                      </div>
                    </div>

                    {/* Seção: Notificações PWA / Web Push */}
                    <div className="flex flex-col gap-3 p-4 rounded-2xl bg-muted/20 border border-border">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-xl bg-primary/10 text-primary">
                            <Bell size={18} />
                          </div>
                          <div>
                            <p className="font-bold text-sm text-foreground">Lembretes de Revisão (PWA)</p>
                            <p className="text-xs text-muted-foreground">Notificações opt-in de revisões FSRS pendentes</p>
                          </div>
                        </div>

                        {notifStatus === "active" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <Check size={12} /> Ativado
                          </span>
                        ) : notifStatus === "denied" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-destructive/10 text-destructive border border-destructive/20">
                            <AlertCircle size={12} /> Bloqueado
                          </span>
                        ) : notifStatus === "unsupported" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted text-muted-foreground border border-border">
                            Indisponível
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted text-muted-foreground border border-border">
                            Desativado
                          </span>
                        )}
                      </div>

                      {notifMessage && (
                        <p className="text-xs font-medium text-primary bg-primary/10 p-2.5 rounded-xl border border-primary/20">
                          {notifMessage}
                        </p>
                      )}

                      {notifStatus === "denied" && (
                        <p className="text-xs text-muted-foreground bg-destructive/5 p-2.5 rounded-xl border border-destructive/20 leading-relaxed">
                          As notificações estão bloqueadas nas configurações do seu navegador. Permita o envio nas permissões do site para reativar.
                        </p>
                      )}

                      {notifStatus === "unsupported" && (
                        <p className="text-xs text-muted-foreground bg-muted/40 p-2.5 rounded-xl border border-border leading-relaxed">
                          Seu navegador atual não suporta Web Push. Instale o app PWA ou acesse pelo Chrome/Edge/Safari para receber lembretes.
                        </p>
                      )}

                      {notifStatus === "active" && notifConfig && (
                        <div className="flex flex-col gap-3 mt-2 pt-3 border-t border-border/60">
                          {/* Horário Preferencial */}
                          <div className="flex items-center justify-between">
                            <label htmlFor="pref-hour-select" className="text-xs font-bold text-foreground flex items-center gap-1.5">
                              <Clock size={14} className="text-muted-foreground" /> Horário preferencial:
                            </label>
                            <select
                              id="pref-hour-select"
                              value={notifConfig.preferred_hour}
                              onChange={(e) => handleUpdatePreferences(parseInt(e.target.value, 10), notifConfig.days_of_week || [0,1,2,3,4,5,6])}
                              className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-card border border-border text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                            >
                              {Array.from({ length: 24 }).map((_, i) => (
                                <option key={i} value={i}>
                                  {i.toString().padStart(2, "0")}:00
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Dias da Semana */}
                          <div className="flex flex-col gap-1.5">
                            <span className="text-xs font-bold text-foreground">Dias de envio:</span>
                            <div className="grid grid-cols-7 gap-1">
                              {WEEKDAYS.map(day => {
                                const isSelected = (notifConfig.days_of_week || [0,1,2,3,4,5,6]).includes(day.id);
                                return (
                                  <button
                                    key={day.id}
                                    type="button"
                                    onClick={() => toggleDay(day.id)}
                                    className={`py-1.5 text-xs font-bold rounded-lg border transition-all cursor-pointer ${
                                      isSelected
                                        ? "bg-primary text-primary-foreground border-primary"
                                        : "bg-card text-muted-foreground border-border hover:bg-muted"
                                    }`}
                                  >
                                    {day.label}
                                  </button>
                                );
                              })}
                            </div>
                          </div>

                          {/* Botão Revogar */}
                          <button
                            type="button"
                            onClick={handleUnsubscribePush}
                            disabled={isNotifSubmitting}
                            className="mt-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-bold text-muted-foreground hover:text-destructive hover:bg-destructive/10 border border-border hover:border-destructive/20 transition-colors cursor-pointer disabled:opacity-50"
                          >
                            {isNotifSubmitting ? <Loader2 size={14} className="animate-spin" /> : <BellOff size={14} />}
                            Revogar Notificações neste dispositivo
                          </button>
                        </div>
                      )}

                      {notifStatus === "disabled" && (
                        <button
                          type="button"
                          onClick={handleSubscribePush}
                          disabled={isNotifSubmitting}
                          className="mt-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-all cursor-pointer disabled:opacity-50 shadow-sm"
                        >
                          {isNotifSubmitting ? (
                            <>
                              <Loader2 size={14} className="animate-spin" />
                              Configurando...
                            </>
                          ) : (
                            <>
                              <Bell size={14} />
                              Ativar Notificações de Revisão
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Ações de Conta */}
                    <div className="flex flex-col gap-3">
                      <button
                        onClick={() => setStep("confirm_reset")}
                        className="flex items-center gap-3 px-4 py-3.5 rounded-2xl bg-destructive/5 text-destructive hover:bg-destructive/10 border border-destructive/20 hover:border-destructive/30 transition-all duration-200 text-left w-full cursor-pointer group shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive"
                      >
                        <Trash2 className="text-destructive shrink-0" size={20} />
                        <div className="flex-1">
                          <p className="font-bold text-sm">Resetar Todo o Progresso</p>
                          <p className="text-xs opacity-80 mt-0.5 font-medium">Apagar histórico de questões, planos e revisões</p>
                        </div>
                      </button>

                      <button
                        onClick={() => signOut({ redirectUrl: "/" })}
                        className="flex items-center gap-3 px-4 py-3.5 rounded-2xl bg-card text-foreground hover:bg-muted/50 border border-border hover:border-border/80 transition-all duration-200 text-left w-full cursor-pointer group shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      >
                        <LogOut className="text-muted-foreground shrink-0" size={20} />
                        <div className="flex-1">
                          <p className="font-bold text-sm">Sair da Conta</p>
                          <p className="text-xs text-muted-foreground mt-0.5 font-medium">Fazer logout da sessão atual</p>
                        </div>
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="confirm"
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                    className="flex flex-col gap-5"
                  >
                    <div className="bg-destructive/10 border border-destructive/20 rounded-2xl p-4 flex gap-3 shadow-sm">
                      <ShieldAlert className="text-destructive flex-shrink-0 mt-0.5" size={24} />
                      <div className="flex flex-col gap-1">
                        <p className="font-bold text-destructive text-sm uppercase tracking-wider">Atenção! Ação irreversível.</p>
                        <p className="text-sm text-foreground/80 leading-relaxed font-medium">
                          Ao prosseguir, todo o seu histórico de simulados, estatísticas de acertos, favoritos,
                          cronograma de estudos semanal (Planner) e flashcards serão permanentemente excluídos.
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 mt-2">
                      <label htmlFor="confirm-reset-input" className="text-sm font-bold text-foreground">
                        Para confirmar, digite <span className="text-destructive">RESETAR</span> no campo abaixo:
                      </label>
                      <input
                        id="confirm-reset-input"
                        type="text"
                        autoFocus
                        value={confirmText}
                        onChange={(e) => setConfirmText(e.target.value)}
                        placeholder="Digite RESETAR"
                        disabled={isLoading}
                        className="w-full px-4 py-3 rounded-xl border border-border bg-card text-foreground focus:outline-none focus:border-destructive focus:ring-1 focus:ring-destructive transition-all font-mono tracking-widest text-center shadow-sm"
                      />
                    </div>

                    {error && (
                      <p role="alert" className="text-destructive text-sm font-bold flex items-center gap-1.5 justify-center">
                        <AlertTriangle size={16} />
                        {error}
                      </p>
                    )}

                    <div className="flex gap-3 mt-4">
                      <button
                        onClick={() => {
                          setStep("profile");
                          setConfirmText("");
                          setError(null);
                        }}
                        disabled={isLoading}
                        className="flex-1 py-3 px-4 rounded-xl border border-border text-foreground hover:bg-muted/50 transition-colors text-center font-bold text-sm cursor-pointer disabled:opacity-50 shadow-sm"
                      >
                        Voltar
                      </button>
                      <button
                        onClick={handleResetProgress}
                        disabled={confirmText.toUpperCase() !== "RESETAR" || isLoading}
                        className="flex-1 py-3 px-4 rounded-xl bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed transition-all text-center font-bold text-sm cursor-pointer flex items-center justify-center gap-2 shadow-sm"
                      >
                        {isLoading ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Resetando...
                          </>
                        ) : (
                          "Confirmar Reset"
                        )}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
