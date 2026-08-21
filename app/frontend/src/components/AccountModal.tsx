"use client";

import { useState } from "react";
import { useUser, useClerk } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { localDb, getLocalOwnerId } from "@/lib/db";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { clearLearningSessions } from "@/lib/sessionState";

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
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !isLoading && resetStateAndClose()}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 15 }}
            transition={{ type: "spring", duration: 0.4, bounce: 0.15 }}
            className="bg-surface border border-outline-variant rounded-3xl shadow-2xl w-full max-w-md overflow-hidden z-10 flex flex-col relative"
          >
            {/* Header */}
            <div className="flex justify-between items-center px-6 py-4 border-b border-outline-variant bg-surface-container-low">
              <h2 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                {step === "profile" ? "Minha Conta" : "Resetar Progresso"}
              </h2>
              <button
                onClick={() => !isLoading && resetStateAndClose()}
                disabled={isLoading}
                className="text-on-surface-variant hover:bg-surface-container-high rounded-full p-1.5 transition-colors flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Fechar"
              >
                <span className="material-symbols-outlined" data-icon="close" aria-hidden="true">close</span>
              </button>
            </div>

            {/* Content Body */}
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
                    {/* User Info Card */}
                    <div className="flex items-center gap-4 bg-surface-container-lowest p-4 rounded-2xl border border-outline-variant">
                      <div className="relative w-16 h-16 rounded-2xl bg-surface-container-high overflow-hidden flex-shrink-0 border-2 border-primary/10 shadow-[0px_2px_8px_rgba(0,0,0,0.05)]">
                        {isLoaded && user?.imageUrl ? (
                          <Image src={user.imageUrl} alt="Avatar" fill sizes="64px" className="object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-primary-container text-on-primary-container">
                            <span className="material-symbols-outlined text-3xl" data-icon="person">person</span>
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-title-lg text-title-lg font-bold text-on-surface truncate">
                          {isLoaded ? (user?.fullName || "Usuário MedQuest") : "Carregando..."}
                        </h3>
                        <p className="font-body-sm text-body-sm text-on-surface-variant truncate">
                          {isLoaded ? (user?.primaryEmailAddress?.emailAddress || "") : ""}
                        </p>
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 mt-2 rounded-full text-xs font-medium bg-primary-container text-on-primary-container">
                          <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                          Preparação USP
                        </span>
                      </div>
                    </div>

                    {/* Actions Stack */}
                    <div className="flex flex-col gap-3">
                      <button
                        onClick={() => setStep("confirm_reset")}
                        className="flex items-center gap-3 px-4 py-3.5 rounded-2xl bg-error-container text-on-error-container hover:bg-error/15 border border-error/20 hover:border-error/30 transition-all duration-200 font-label-md text-left w-full cursor-pointer group shadow-[0_1px_2px_rgba(0,0,0,0.05)]"
                      >
                        <span className="material-symbols-outlined text-error" data-icon="delete_forever">delete_forever</span>
                        <div className="flex-1">
                          <p className="font-bold">Resetar Todo o Progresso</p>
                          <p className="text-[11px] opacity-80 mt-0.5">Apagar histórico de questões, planos e revisões</p>
                        </div>
                        <span className="material-symbols-outlined text-error/60 group-hover:translate-x-0.5 transition-transform" data-icon="chevron_right">chevron_right</span>
                      </button>

                      <button
                        onClick={() => signOut({ redirectUrl: "/" })}
                        className="flex items-center gap-3 px-4 py-3.5 rounded-2xl bg-surface-container-low text-on-surface hover:bg-surface-container-high border border-outline-variant hover:border-outline transition-all duration-200 font-label-md text-left w-full cursor-pointer group"
                      >
                        <span className="material-symbols-outlined text-on-surface-variant" data-icon="logout">logout</span>
                        <div className="flex-1">
                          <p className="font-semibold">Sair da Conta</p>
                          <p className="text-[11px] text-on-surface-variant mt-0.5">Fazer logout da sessão atual</p>
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
                    {/* Warning Box */}
                    <div className="bg-error-container/20 border border-error/25 rounded-2xl p-4 flex gap-3">
                      <span className="material-symbols-outlined text-error text-2xl flex-shrink-0" data-icon="warning">warning</span>
                      <div className="flex flex-col gap-1">
                        <p className="font-bold text-error text-label-lg">Atenção! Esta ação é irreversível.</p>
                        <p className="text-body-sm text-on-surface-variant leading-relaxed">
                          Ao prosseguir, todo o seu histórico de simulados, estatísticas de acertos, favoritos, 
                          cronograma de estudos semanal (Planner) e flashcards serão permanentemente excluídos.
                        </p>
                      </div>
                    </div>

                    {/* Confirmation Input */}
                    <div className="flex flex-col gap-2">
                      <label htmlFor="confirm-reset-input" className="text-label-md font-semibold text-on-surface">
                        Para confirmar, digite <span className="text-error font-bold">RESETAR</span> no campo abaixo:
                      </label>
                      <input
                        id="confirm-reset-input"
                        type="text"
                        autoFocus
                        value={confirmText}
                        onChange={(e) => setConfirmText(e.target.value)}
                        placeholder="Digite RESETAR"
                        disabled={isLoading}
                        className="w-full px-4 py-3 rounded-xl border border-outline-variant bg-surface text-on-surface focus:outline-none focus:border-error focus:ring-1 focus:ring-error transition-all font-mono tracking-wider text-center"
                      />
                    </div>

                    {error && (
                      <p className="text-error text-body-sm font-semibold flex items-center gap-1.5 justify-center">
                        <span className="material-symbols-outlined text-sm" data-icon="error">error</span>
                        {error}
                      </p>
                    )}

                    {/* Buttons Footer (In-Body) */}
                    <div className="flex gap-3 mt-2">
                      <button
                        onClick={() => {
                          setStep("profile");
                          setConfirmText("");
                          setError(null);
                        }}
                        disabled={isLoading}
                        className="flex-1 py-3 px-4 rounded-xl border border-outline-variant text-on-surface hover:bg-surface-container-low transition-colors text-center font-bold text-label-md cursor-pointer disabled:opacity-50"
                      >
                        Voltar
                      </button>
                      <button
                        onClick={handleResetProgress}
                        disabled={confirmText.toUpperCase() !== "RESETAR" || isLoading}
                        className="flex-1 py-3 px-4 rounded-xl bg-error text-on-error hover:bg-error/90 disabled:bg-surface-container-highest disabled:text-on-surface/30 disabled:cursor-not-allowed transition-all text-center font-bold text-label-md cursor-pointer flex items-center justify-center gap-2 shadow-md shadow-error/10"
                      >
                        {isLoading ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
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
