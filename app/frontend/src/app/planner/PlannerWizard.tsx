"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Calendar, Clock, BookOpen, ArrowRight } from "lucide-react";

export function PlannerWizard() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [examDate, setExamDate] = useState("");
  const [startDate, setStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [daysPerWeek, setDaysPerWeek] = useState(5);
  const [hoursPerDay, setHoursPerDay] = useState(4);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    if (!examDate) {
      setError("Por favor, insira a data da sua prova principal.");
      return;
    }
    
    if (new Date(examDate) <= new Date(startDate)) {
      setError("A data da prova deve ser posterior à data de início.");
      return;
    }

    setLoading(true);
    try {
      // Cria a ISO string normalizada (meio-dia pra evitar fusos na conversão)
      const examIso = new Date(`${examDate}T12:00:00Z`).toISOString();
      const startIso = new Date(`${startDate}T12:00:00Z`).toISOString();

      await api.planner.saveConfig({
        exam_date: examIso,
        start_date: startIso,
        days_per_week: daysPerWeek,
        hours_per_day: hoursPerDay
      });

      router.refresh();
    } catch (err: any) {
      setError(err.message || "Erro ao salvar a configuração.");
      setLoading(false);
    }
  };

  return (
    <div className="bg-card border border-border shadow-1 rounded-xl p-8 max-w-2xl mx-auto w-full">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 bg-primary/20 text-primary rounded-xl flex items-center justify-center shrink-0">
          <Calendar size={24} />
        </div>
        <div>
          <h2 className="text-h2 font-bold text-foreground">Configure seu Plano de Estudos</h2>
          <p className="text-muted-foreground text-sm">Insira seus dados para gerarmos um cronograma baseado nos pesos da USP.</p>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md mb-6 border border-destructive/20">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Data de Início</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input 
                type="date"
                required
                className="w-full bg-input border border-border rounded-md py-2 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Data da Prova Alvo</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input 
                type="date"
                required
                className="w-full bg-input border border-border rounded-md py-2 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Dias de Estudo por Semana</label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input 
                type="number"
                min="1"
                max="7"
                required
                className="w-full bg-input border border-border rounded-md py-2 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={daysPerWeek}
                onChange={(e) => setDaysPerWeek(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Horas de Estudo por Dia</label>
            <div className="relative">
              <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input 
                type="number"
                min="1"
                max="24"
                required
                className="w-full bg-input border border-border rounded-md py-2 pl-10 pr-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(Number(e.target.value))}
              />
            </div>
          </div>
        </div>

        <button 
          type="submit"
          disabled={loading}
          className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium py-3 rounded-md transition-colors flex items-center justify-center gap-2 w-full mt-2 disabled:opacity-50"
        >
          {loading ? "Gerando..." : "Gerar Cronograma"}
          {!loading && <ArrowRight size={18} />}
        </button>
      </form>
    </div>
  );
}
