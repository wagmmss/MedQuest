"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { PlannerConfig } from "@/types/api";
import {
  Calendar,
  Clock,
  BookOpen,
  ArrowRight,
  Loader2,
  Target,
  Building2,
  Stethoscope,
  X,
  Sparkles,
  CheckCircle2,
  Globe,
  CheckSquare,
} from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";

interface InstitutionPreset {
  id: string;
  name: string;
  shortName: string;
  defaultDate: string;
  typicalCutoff: number;
}

const INSTITUTION_PRESETS: InstitutionPreset[] = [
  { id: "TODAS", name: "Todas as Bancas (Nacional + SP + Regionais)", shortName: "Todas as Bancas", defaultDate: "2026-11-15", typicalCutoff: 76 },
  { id: "USP-SP", name: "USP - São Paulo (FUVEST)", shortName: "USP-SP", defaultDate: "2026-11-15", typicalCutoff: 78 },
  { id: "ENARE", name: "ENARE (Exame Nacional)", shortName: "ENARE", defaultDate: "2026-10-25", typicalCutoff: 75 },
  { id: "SUS-SP", name: "SUS - São Paulo (Vunesp)", shortName: "SUS-SP", defaultDate: "2026-12-06", typicalCutoff: 76 },
  { id: "UNICAMP", name: "UNICAMP (Campinas)", shortName: "UNICAMP", defaultDate: "2026-11-22", typicalCutoff: 77 },
  { id: "UNIFESP", name: "UNIFESP (EPM)", shortName: "UNIFESP", defaultDate: "2026-12-13", typicalCutoff: 79 },
  { id: "USP-RP", name: "USP - Ribeirão Preto", shortName: "USP-RP", defaultDate: "2026-11-29", typicalCutoff: 77 },
  { id: "SCMSP", name: "Santa Casa de SP", shortName: "SCMSP", defaultDate: "2026-12-05", typicalCutoff: 76 },
  { id: "IAMSPE", name: "IAMSPE (São Paulo)", shortName: "IAMSPE", defaultDate: "2026-12-12", typicalCutoff: 75 },
  { id: "AMRIGS", name: "AMRIGS (Sul / Nacional)", shortName: "AMRIGS", defaultDate: "2026-11-15", typicalCutoff: 74 },
  { id: "OUTRA", name: "Outra Banca", shortName: "Personalizada", defaultDate: "2026-11-20", typicalCutoff: 75 },
];

const SPECIALTY_PRESETS: { name: string; suggestedCutoff: number }[] = [
  { name: "Clínica Médica", suggestedCutoff: 74 },
  { name: "Cirurgia Geral", suggestedCutoff: 76 },
  { name: "Pediatria", suggestedCutoff: 72 },
  { name: "Ginecologia e Obstetrícia", suggestedCutoff: 73 },
  { name: "Medicina de Família e Comunidade", suggestedCutoff: 68 },
  { name: "Anestesiologia", suggestedCutoff: 79 },
  { name: "Dermatologia", suggestedCutoff: 83 },
  { name: "Oftalmologia", suggestedCutoff: 81 },
  { name: "Ortopedia e Traumatologia", suggestedCutoff: 75 },
  { name: "Psiquiatria", suggestedCutoff: 78 },
  { name: "Radiologia", suggestedCutoff: 77 },
  { name: "Otorrinolaringologia", suggestedCutoff: 80 },
  { name: "Neurologia", suggestedCutoff: 76 },
  { name: "Outra Especialidade", suggestedCutoff: 75 },
];

interface PlannerWizardProps {
  initialConfig?: PlannerConfig | null;
  onClose?: () => void;
  isModal?: boolean;
}

export function PlannerWizard({ initialConfig, onClose, isModal }: PlannerWizardProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [examError, setExamError] = useState(false);

  const initialExamDate = initialConfig?.exam_date ? initialConfig.exam_date.split("T")[0] : "";
  const initialStartDate = initialConfig?.start_date ? initialConfig.start_date.split("T")[0] : new Date().toISOString().split("T")[0];

  const initialInsts: string[] = (() => {
    if (initialConfig?.target_institutions && initialConfig.target_institutions.length > 0) {
      return initialConfig.target_institutions;
    }
    if (initialConfig?.target_institution) {
      if (initialConfig.target_institution === "Todas as Bancas") return ["TODAS"];
      const parts = initialConfig.target_institution.split(",").map(s => s.trim()).filter(Boolean);
      if (parts.length > 0) return parts;
    }
    return ["TODAS"];
  })();

  const [selectedInsts, setSelectedInsts] = useState<string[]>(initialInsts);
  const [selectedSpec, setSelectedSpec] = useState<string>(initialConfig?.target_specialty || "Clínica Médica");
  const [examDate, setExamDate] = useState(initialExamDate || "2026-11-15");
  const [startDate, setStartDate] = useState(initialStartDate);
  const [daysPerWeek, setDaysPerWeek] = useState(initialConfig?.days_per_week || 6);
  const [hoursPerDay, setHoursPerDay] = useState(initialConfig?.hours_per_day || 4);
  const [targetScore, setTargetScore] = useState<number | "">(initialConfig?.target_score ?? 78);

  const handleToggleInstitution = (presetId: string) => {
    if (presetId === "TODAS") {
      setSelectedInsts(["TODAS"]);
      setExamDate("2026-11-15");
      return;
    }

    let next = selectedInsts.filter(id => id !== "TODAS");
    if (next.includes(presetId)) {
      next = next.filter(id => id !== presetId);
    } else {
      next = [...next, presetId];
    }

    if (next.length === 0) {
      next = ["TODAS"];
      setExamDate("2026-11-15");
    } else {
      const firstPreset = INSTITUTION_PRESETS.find(p => p.id === next[0]);
      if (firstPreset && firstPreset.defaultDate) {
        setExamDate(firstPreset.defaultDate);
      }
    }

    setSelectedInsts(next);
  };

  const handleSelectSpecialty = (specName: string) => {
    setSelectedSpec(specName);
    const spec = SPECIALTY_PRESETS.find(s => s.name === specName);
    if (spec) {
      setTargetScore(spec.suggestedCutoff);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setExamError(false);

    if (!examDate) {
      setExamError(true);
      return;
    }

    if (new Date(examDate) <= new Date(startDate)) {
      setError("A data da prova deve ser posterior à data de início dos estudos.");
      return;
    }

    setLoading(true);
    try {
      const examIso = new Date(`${examDate}T12:00:00Z`).toISOString();
      const startIso = new Date(`${startDate}T12:00:00Z`).toISOString();

      const formattedInstStr = selectedInsts.includes("TODAS")
        ? "Todas as Bancas"
        : selectedInsts.join(", ");

      await api.planner.saveConfig({
        exam_date: examIso,
        start_date: startIso,
        days_per_week: daysPerWeek,
        hours_per_day: hoursPerDay,
        target_score: targetScore !== "" ? Number(targetScore) : undefined,
        target_institution: formattedInstStr,
        target_institutions: selectedInsts,
        target_specialty: selectedSpec,
      });

      toast.success("Perfil de estudos calibrado com sucesso!");
      if (onClose) {
        onClose();
      }
      router.refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao salvar a calibração.";
      setError(message);
      setLoading(false);
    }
  };

  const isAllSelected = selectedInsts.includes("TODAS");

  return (
    <div className={clsx(
      "bg-card border border-border shadow-2 rounded-2xl w-full transition-all",
      isModal ? "p-6 md:p-8 max-w-3xl" : "p-6 md:p-8 max-w-4xl mx-auto"
    )}>
      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 bg-primary/15 text-primary rounded-xl flex items-center justify-center shrink-0 border border-primary/20">
            <Building2 size={22} />
          </div>
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-foreground flex items-center gap-2">
              {isModal ? "Calibrar Perfil do Estudante" : "Configuração Inicial do Perfil"}
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-semibold border border-primary/20 flex items-center gap-1">
                <Sparkles size={11} /> 2026/2027
              </span>
            </h2>
            <p className="text-muted-foreground text-xs md:text-sm mt-0.5">
              Personalize as bancas do seu cronograma, especialidade e disponibilidade semanal.
            </p>
          </div>
        </div>
        {isModal && onClose && (
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground p-1.5 rounded-lg hover:bg-muted transition-colors"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Banner Informativo de Abrangência */}
      <div className="bg-primary/10 border border-primary/20 rounded-xl p-3.5 mb-6 text-xs text-primary flex items-center gap-2.5">
        <Globe size={18} className="shrink-0" />
        <div>
          <strong className="font-semibold">Acesso Universal a Todas as Bancas:</strong> Você terá acesso a todas as questões de todas as bancas do Brasil no banco de questões. A seleção abaixo calibra a distribuição de temas e pesos no seu cronograma.
        </div>
      </div>

      {error && !examError && (
        <div className="bg-destructive/10 text-destructive text-sm p-3.5 rounded-xl mb-6 border border-destructive/20 font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Multi-seleção de Bancas */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Building2 size={14} className="text-primary" /> 1. Banca(s) Alvo para os Temas do Cronograma
            </label>
            <span className="text-xs text-muted-foreground">
              {isAllSelected 
                ? "✨ Todas as bancas selecionadas" 
                : `${selectedInsts.length} banca${selectedInsts.length > 1 ? "s" : ""} selecionada${selectedInsts.length > 1 ? "s" : ""}`}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {INSTITUTION_PRESETS.map((preset) => {
              const isSelected = preset.id === "TODAS" 
                ? isAllSelected 
                : selectedInsts.includes(preset.id);

              return (
                <button
                  type="button"
                  key={preset.id}
                  onClick={() => handleToggleInstitution(preset.id)}
                  className={clsx(
                    "p-3 rounded-xl text-left border text-xs font-medium transition-all flex flex-col justify-between gap-1 relative",
                    isSelected
                      ? "border-primary bg-primary/10 text-foreground ring-1 ring-primary/40 shadow-sm"
                      : "border-border bg-muted/20 text-muted-foreground hover:border-border/80 hover:bg-muted/40"
                  )}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="font-bold text-sm text-foreground">{preset.shortName}</span>
                    {isSelected ? (
                      <CheckCircle2 size={15} className="text-primary fill-primary/20 shrink-0" />
                    ) : (
                      <div className="w-3.5 h-3.5 rounded border border-muted-foreground/30 shrink-0" />
                    )}
                  </div>
                  <span className="text-[11px] text-muted-foreground truncate">{preset.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Especialidade Pretendida */}
        <div className="space-y-2.5">
          <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
            <Stethoscope size={14} className="text-primary" /> 2. Especialidade Pretendida
          </label>
          <select
            value={selectedSpec}
            onChange={(e) => handleSelectSpecialty(e.target.value)}
            className="w-full bg-input border border-border rounded-xl py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary transition-colors cursor-pointer"
          >
            {SPECIALTY_PRESETS.map((spec) => (
              <option key={spec.name} value={spec.name}>
                {spec.name} (Nota de corte média ~{spec.suggestedCutoff}%)
              </option>
            ))}
          </select>
        </div>

        {/* Datas de Início e da Prova */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Calendar size={14} className="text-primary" /> Início dos Estudos
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input
                type="date"
                required
                className="w-full bg-input border border-border rounded-xl py-2.5 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Calendar size={14} className="text-primary" /> Data da Prova Principal
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input
                type="date"
                required
                className={clsx(
                  "w-full bg-input border rounded-xl py-2.5 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary transition-colors",
                  examError ? "border-destructive ring-1 ring-destructive" : "border-border"
                )}
                value={examDate}
                onChange={(e) => {
                  setExamDate(e.target.value);
                  if (examError) setExamError(false);
                }}
              />
            </div>
            {examError && (
              <p className="text-xs text-destructive mt-1 font-medium">Por favor, selecione a data da sua prova.</p>
            )}
          </div>
        </div>

        {/* Carga Horária e Nota Alvo */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Clock size={14} className="text-primary" /> Dias / Semana
            </label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input
                type="number"
                min="1"
                max="7"
                required
                className="w-full bg-input border border-border rounded-xl py-2.5 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={daysPerWeek}
                onChange={(e) => setDaysPerWeek(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <BookOpen size={14} className="text-primary" /> Horas / Dia
            </label>
            <div className="relative">
              <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input
                type="number"
                min="1"
                max="16"
                required
                className="w-full bg-input border border-border rounded-xl py-2.5 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Target size={14} className="text-primary" /> Nota Alvo (%)
            </label>
            <div className="relative">
              <Target className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input
                type="number"
                min="0"
                max="100"
                placeholder="Ex: 78"
                className="w-full bg-input border border-border rounded-xl py-2.5 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={targetScore}
                onChange={(e) => setTargetScore(e.target.value ? Number(e.target.value) : "")}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          {isModal && onClose && (
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-muted hover:bg-muted/80 text-foreground font-semibold py-3 rounded-xl transition-colors text-sm"
            >
              Cancelar
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2 text-sm shadow-md disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Salvando calibração...
              </>
            ) : (
              <>
                {isModal ? "Atualizar Perfil de Estudos" : "Gerar Cronograma de Estudos"}
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
