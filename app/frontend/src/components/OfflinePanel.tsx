"use client";

import { useState, useEffect } from "react";
import { CloudOff, Download, RefreshCw, CheckCircle, Database } from "lucide-react";
import { localDb } from "@/lib/db";
import { api } from "@/lib/api";

export function OfflinePanel() {
  const [isOffline, setIsOffline] = useState(false);
  const [stats, setStats] = useState({ questions: 0, flashcards: 0, queue: 0 });
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    // Determine online status
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    
    setIsOffline(!navigator.onLine);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // Initial stats
    updateStats();

    // Listen to queue updates
    const handleQueueUpdate = () => updateStats();
    window.addEventListener("sync-queue-updated", handleQueueUpdate);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("sync-queue-updated", handleQueueUpdate);
    };
  }, []);

  const updateStats = async () => {
    if (!localDb) return;
    try {
      const questions = await localDb.questions.count();
      const flashcards = await localDb.flashcards.count();
      const queue = await localDb.syncQueue.count();
      setStats({ questions, flashcards, queue });
    } catch (e) {
      console.error("Failed to read local stats", e);
    }
  };

  const downloadForShift = async () => {
    if (isDownloading) return;
    setIsDownloading(true);
    try {
      // Baixar flashcards do dia
      const flashcards = await api.flashcards.getDue();
      if (flashcards && flashcards.length > 0 && localDb) {
        await localDb.flashcards.bulkPut(flashcards);
      }
      
      // Baixar 50 questões pseudo-aleatórias para plantão
      // Idealmente, a API deveria ter um endpoint `/api/questions/shift`
      // Como não temos, vamos simular buscando um simulado ou lista rápida
      const questions = await api.questions.getSimuladoUSP();
      if (questions && questions.length > 0) {
        const ids = questions.slice(0, 50).map(q => q.id);
        const detailResponse = await api.questions.getBatch(ids, true);
        if (detailResponse.questions && localDb) {
          await localDb.questions.bulkPut(Object.values(detailResponse.questions));
        }
      }

      await updateStats();
    } catch (e) {
      console.error("Erro ao baixar dados para o plantão:", e);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="bg-surface border border-outline-variant rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-outline-variant">
        <h3 className="font-headline-md text-headline-md text-on-surface flex items-center gap-2">
          {isOffline ? (
            <CloudOff className="text-warning" size={24} />
          ) : (
            <Database className="text-primary" size={24} />
          )}
          Modo Plantão (Offline)
        </h3>
        <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${isOffline ? 'bg-warning/20 text-warning' : 'bg-success/20 text-success'}`}>
          {isOffline ? 'Desconectado' : 'Online'}
        </div>
      </div>
      
      <p className="text-sm text-on-surface-variant mb-6">
        Baixe questões e flashcards para estudar sem internet durante seus plantões. Suas respostas serão sincronizadas automaticamente quando reconectar.
      </p>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-surface-container-low rounded-lg p-3 text-center">
          <p className="text-xs text-on-surface-variant uppercase font-semibold">Questões</p>
          <p className="font-display-sm text-on-surface">{stats.questions}</p>
        </div>
        <div className="bg-surface-container-low rounded-lg p-3 text-center">
          <p className="text-xs text-on-surface-variant uppercase font-semibold">Flashcards</p>
          <p className="font-display-sm text-on-surface">{stats.flashcards}</p>
        </div>
        <div className="bg-surface-container-low rounded-lg p-3 text-center">
          <p className="text-xs text-on-surface-variant uppercase font-semibold">Fila (Envios)</p>
          <p className="font-display-sm text-on-surface">{stats.queue}</p>
        </div>
      </div>

      <button 
        onClick={downloadForShift}
        disabled={isDownloading || isOffline}
        className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-primary text-on-primary font-semibold hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isDownloading ? (
          <><RefreshCw className="animate-spin" size={20} /> Baixando Carga...</>
        ) : (
          <><Download size={20} /> Baixar Pacote de Plantão</>
        )}
      </button>
    </div>
  );
}
