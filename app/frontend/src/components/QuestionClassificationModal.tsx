"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, Loader2, Tag, Search, AlertCircle, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";

const CANONICAL_AREAS = [
  "Cirurgia",
  "Clínica Médica",
  "Ginecologia e Obstetrícia",
  "Medicina Preventiva",
  "Pediatria"
];

interface QuestionClassificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  questionId: number;
  currentArea: string;
  currentSubtema: string;
  currentTopic?: string;
  onSuccess: (updated: { area: string; subtema: string; topic: string }) => void;
}

export function QuestionClassificationModal({
  isOpen,
  onClose,
  questionId,
  currentArea,
  currentSubtema,
  currentTopic,
  onSuccess,
}: QuestionClassificationModalProps) {
  const [area, setArea] = useState(currentArea || CANONICAL_AREAS[1]);
  const [subtema, setSubtema] = useState(currentSubtema || "");
  const [topic, setTopic] = useState(currentTopic || currentSubtema || "");
  const [taxonomy, setTaxonomy] = useState<Record<string, Record<string, string>>>({});
  const [searchFilter, setSearchFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync state when props change
  useEffect(() => {
    if (isOpen) {
      setArea(currentArea || CANONICAL_AREAS[1]);
      setSubtema(currentSubtema || "");
      setTopic(currentTopic || currentSubtema || "");
      setError(null);
      setSearchFilter("");
    }
  }, [isOpen, currentArea, currentSubtema, currentTopic]);

  // Load taxonomy from backend
  useEffect(() => {
    if (isOpen && Object.keys(taxonomy).length === 0) {
      setLoading(true);
      api.questions.getTaxonomy()
        .then((data) => {
          if (data && typeof data === "object") {
            setTaxonomy(data);
          }
        })
        .catch((err) => {
          console.warn("Erro ao buscar taxonomia:", err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [isOpen, taxonomy]);

  // Available subtemas for selected area
  const availableSubtemas = useMemo(() => {
    if (!taxonomy || !taxonomy[area]) return [];
    return Object.keys(taxonomy[area]).sort((a, b) => a.localeCompare(b, "pt-BR"));
  }, [taxonomy, area]);

  // Filtered subtemas by search string
  const filteredSubtemas = useMemo(() => {
    if (!searchFilter.trim()) return availableSubtemas;
    const q = searchFilter.toLowerCase();
    return availableSubtemas.filter((s) => s.toLowerCase().includes(q));
  }, [availableSubtemas, searchFilter]);

  const handleAreaChange = (newArea: string) => {
    setArea(newArea);
    setSearchFilter("");
    const subList = taxonomy[newArea] ? Object.keys(taxonomy[newArea]) : [];
    if (subList.length > 0 && !subList.includes(subtema)) {
      setSubtema(subList[0]);
      setTopic(subList[0]);
    }
  };

  const handleSubtemaSelect = (selectedSub: string) => {
    setSubtema(selectedSub);
    setTopic(selectedSub);
  };

  const handleSave = async () => {
    if (!area || !subtema) {
      setError("Selecione a área e o subtema canônico.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const res = await api.questions.updateClassification(questionId, {
        area,
        subtema,
        topic: topic.trim() || subtema,
      });

      if (res.success) {
        onSuccess({
          area: res.question.area,
          subtema: res.question.subtema,
          topic: res.question.topic,
        });
        onClose();
      } else {
        setError("Não foi possível atualizar a questão.");
      }
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Erro ao salvar classificação. Verifique suas permissões.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !saving && onClose()}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
          />

          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 15 }}
            transition={{ type: "spring", duration: 0.35, bounce: 0.12 }}
            className="bg-card border border-border rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden z-10 flex flex-col relative max-h-[90vh]"
            role="dialog"
            aria-modal="true"
          >
            {/* Header */}
            <div className="flex justify-between items-center px-6 py-4 border-b border-border bg-muted/30">
              <div className="flex items-center gap-2">
                <Tag className="text-primary shrink-0" size={20} />
                <div>
                  <h2 className="text-base font-bold text-foreground leading-tight">
                    Curadoria: Classificação da Questão #{questionId}
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Ajuste de grande área, subtema canônico e tópico da questão.
                  </p>
                </div>
              </div>
              <button
                onClick={() => !saving && onClose()}
                disabled={saving}
                className="text-muted-foreground hover:bg-muted rounded-full p-1.5 transition-colors cursor-pointer disabled:opacity-50"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 flex-1 overflow-y-auto flex flex-col gap-5 text-sm">
              {/* Select Grande Área */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  1. Grande Área
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {CANONICAL_AREAS.map((a) => {
                    const isSelected = area === a;
                    return (
                      <button
                        key={a}
                        type="button"
                        onClick={() => handleAreaChange(a)}
                        className={`px-3 py-2 rounded-xl text-xs font-bold border transition-all text-left truncate cursor-pointer ${
                          isSelected
                            ? "bg-primary text-primary-foreground border-primary shadow-sm"
                            : "bg-muted/40 text-foreground border-border hover:bg-muted hover:border-border/80"
                        }`}
                      >
                        {a}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Search & Select Subtema */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    2. Subtema Canônico ({availableSubtemas.length} módulos)
                  </label>
                  {loading && (
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <RefreshCw size={12} className="animate-spin" /> Carregando taxonomia...
                    </span>
                  )}
                </div>

                <div className="relative">
                  <Search
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                  />
                  <input
                    type="text"
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    placeholder="Filtrar subtema..."
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                </div>

                <div className="border border-border rounded-xl bg-background max-h-48 overflow-y-auto divide-y divide-border/40 p-1">
                  {filteredSubtemas.length === 0 ? (
                    <div className="p-4 text-center text-xs text-muted-foreground">
                      Nenhum subtema encontrado para o filtro.
                    </div>
                  ) : (
                    filteredSubtemas.map((s) => {
                      const isSelected = subtema === s;
                      return (
                        <button
                          key={s}
                          type="button"
                          onClick={() => handleSubtemaSelect(s)}
                          className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-colors cursor-pointer ${
                            isSelected
                              ? "bg-primary/10 text-primary font-bold"
                              : "hover:bg-muted/60 text-foreground"
                          }`}
                        >
                          <span className="line-clamp-1">{s}</span>
                          {isSelected && <Check size={14} className="text-primary shrink-0 ml-2" />}
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Subtema Selecionado Info */}
              {subtema && (
                <div className="p-3 bg-primary/5 border border-primary/20 rounded-xl text-xs flex flex-col gap-1">
                  <span className="text-muted-foreground font-semibold">Subtema selecionado:</span>
                  <span className="text-foreground font-bold">{subtema}</span>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-xl text-destructive text-xs font-bold flex items-center gap-2">
                  <AlertCircle size={16} className="shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border bg-muted/20">
              <button
                type="button"
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 rounded-xl text-xs font-bold border border-border text-foreground hover:bg-muted transition-colors cursor-pointer disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving || !subtema}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {saving ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Check size={14} />
                    Salvar Alteração
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
