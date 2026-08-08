"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Activity, BookOpen, BrainCircuit, Calendar, Target, Trophy } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5050";

interface PlanTopic {
  area: string;
  subtema: string;
  questions_available: number;
}

interface PlanWeek {
  week: number;
  date: string;
  topics: PlanTopic[];
  recommended_hours: number;
}

export default function Dashboard() {
  const [plan, setPlan] = useState<PlanWeek[]>([]);
  const [loading, setLoading] = useState(false);
  const [examDate, setExamDate] = useState("2027-01-15");

  const generatePlan = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/generate_plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          exam_date: examDate,
          hours_per_week: 25,
        }),
      });
      const data = await res.json();
      if (data.plan) {
        setPlan(data.plan);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto space-y-12">
      <header className="flex justify-between items-center animate-fade-in">
        <div>
          <h1 className="text-4xl font-bold text-white flex items-center gap-3">
            <Activity className="text-primary w-8 h-8" />
            MedQuest
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Sua preparação premium para a Residência Médica USP.
          </p>
        </div>
        <div className="flex gap-4 items-center">
          <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-full border border-border">
            <Trophy className="text-accent w-5 h-5" />
            <span className="font-bold text-white">12 Dias Ofensiva</span>
          </div>
          <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center font-bold text-white shadow-lg">
            WM
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-slide-up">
        {/* Planner Config Card */}
        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="bg-card p-6 rounded-2xl border border-border shadow-xl flex flex-col justify-between"
        >
          <div>
            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              <Calendar className="text-secondary w-5 h-5" />
              Alvo USP
            </h3>
            <p className="text-muted-foreground text-sm mb-4">
              Defina a data da prova para gerarmos o seu cronograma ideal de estudos.
            </p>
            <input 
              type="date"
              value={examDate}
              onChange={(e) => setExamDate(e.target.value)}
              className="w-full bg-background border border-border rounded-lg p-3 text-white focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <button 
            onClick={generatePlan}
            disabled={loading}
            className="mt-6 w-full bg-primary text-primary-foreground font-bold py-3 rounded-xl hover:bg-emerald-400 transition-colors flex justify-center items-center gap-2"
          >
            {loading ? "Gerando..." : "Gerar Plano Anual"}
            <Target className="w-4 h-4" />
          </button>
        </motion.div>

        {/* Stats Summary */}
        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="bg-card p-6 rounded-2xl border border-border shadow-xl col-span-2 flex flex-col justify-center relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-8 opacity-10">
            <BrainCircuit className="w-32 h-32 text-primary" />
          </div>
          <h3 className="text-2xl font-bold text-white mb-6">Desempenho Geral</h3>
          <div className="grid grid-cols-3 gap-4 relative z-10">
            <div>
              <p className="text-muted-foreground text-sm">Questões Resolvidas</p>
              <p className="text-4xl font-bold text-white mt-1">1,245</p>
            </div>
            <div>
              <p className="text-muted-foreground text-sm">Precisão Média</p>
              <p className="text-4xl font-bold text-secondary mt-1">78.4%</p>
            </div>
            <div>
              <p className="text-muted-foreground text-sm">Assuntos Dominados</p>
              <p className="text-4xl font-bold text-primary mt-1">34</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Generated Plan */}
      {plan.length > 0 && (
        <div className="animate-slide-up space-y-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <BookOpen className="text-accent w-6 h-6" />
            Seu Roteiro de Estudos
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {plan.map((weekData) => (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: weekData.week * 0.05 }}
                key={weekData.week} 
                className="bg-background border border-border p-5 rounded-xl hover:border-primary transition-colors group cursor-pointer"
              >
                <div className="flex justify-between items-center mb-4">
                  <span className="bg-muted text-white text-xs font-bold px-2 py-1 rounded-md">
                    Semana {weekData.week}
                  </span>
                  <span className="text-muted-foreground text-sm">
                    {new Date(weekData.date).toLocaleDateString('pt-BR')}
                  </span>
                </div>
                <ul className="space-y-3">
                  {weekData.topics.map((t: PlanTopic, i: number) => (
                    <li key={i} className="flex flex-col gap-1">
                      <span className="text-sm font-semibold text-white group-hover:text-primary transition-colors">
                        {t.subtema}
                      </span>
                      <span className="text-xs text-muted-foreground flex justify-between">
                        {t.area} <span>{t.questions_available} q</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
