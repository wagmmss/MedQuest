"use client";

import { useState } from "react";
import { useUser, useClerk } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { localDb, getLocalOwnerId } from "@/lib/db";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { clearLearningSessions } from "@/lib/sessionState";
import { X, Trash2, LogOut, AlertTriangle, User, ShieldAlert } from "lucide-react";

interface AccountModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AccountModal({ isOpen, onClose }: AccountModalProps) {
  const { user, isLoaded } = useUser();
  const { signOut } = useClerk();
  const router = useRouter();
  
  const [step, setStep] = useState<"profile" | "confirm_reset">("profile");
  const [confirmText, setConfirmText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResetProgress = async () => {
    if (confirmText.toUpperCase() !== "RESETAR") return;
    
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.stats.resetProgress();
      if (res.success) {
        clearLearningSessions();
        for (const key of Object.keys(localStorage)) {
          if (key.startsWith("medquest_planner_topics_")) localStorage.removeItem(key);
        }
        if (localDb) {
          const uid = getLocalOwnerId();
          await Promise.all([
            localDb.questions.where({ _owner_id: uid }).delete(),
            localDb.flashcards.where({ _owner_id: uid }).delete(),
            localDb.syncQueue.where({ owner_id: uid }).delete()
          ]);
        }
        router.replace("/");
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
            className="bg-card border border-border rounded-3xl shadow-2xl w-full max-w-md overflow-hidden z-10 flex flex-col relative"
            role="dialog"
            aria-modal="true"
            aria-labelledby="account-modal-title"
          >
            <div className="flex justify-between items-center px-6 py-4 border-b border-border bg-muted/30">
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

            <div className="p-6 flex-1 flex flex-col min-h-[220px]">
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
