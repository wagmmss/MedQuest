"use client";

import { useState, useEffect, useCallback } from "react";
import { CloudOff, Download, RefreshCw, Database, AlertCircle, Trash2 } from "lucide-react";
import { localDb, getLocalOwnerId, SyncItem } from "@/lib/db";
import { api } from "@/lib/api";
import { syncManager } from "@/lib/sync";

export function OfflinePanel() {
  const [isOffline, setIsOffline] = useState(false);
  const [stats, setStats] = useState({ questions: 0, flashcards: 0, queue: 0 });
  const [failedItems, setFailedItems] = useState<SyncItem[]>([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  const updateStats = useCallback(async () => {
    if (!localDb) return;
    try {
      const uid = getLocalOwnerId();
      const questions = await localDb.questions.where({ _owner_id: uid }).count();
      const flashcards = await localDb.flashcards.where({ _owner_id: uid }).count();
      const queue = await localDb.syncQueue.where({ owner_id: uid }).filter(i => i.status === "pending").count();
      const failed = await syncManager.getFailedItems();
      setStats({ questions, flashcards, queue });
      setFailedItems(failed);
    } catch (error) {
      console.error("Failed to read local stats", error);
    }
  }, []);

  useEffect(() => {
    // Determine online status
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    
    const initialStatusTimer = setTimeout(() => setIsOffline(!navigator.onLine), 0);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // Initial stats
    const initialStatsTimer = setTimeout(() => void updateStats(), 0);

    // Listen to queue updates
    const handleQueueUpdate = () => void updateStats();
    window.addEventListener("sync-queue-updated", handleQueueUpdate);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("sync-queue-updated", handleQueueUpdate);
      clearTimeout(initialStatusTimer);
      clearTimeout(initialStatsTimer);
    };
  }, [updateStats]);

  const downloadForShift = async () => {
    if (isDownloading) return;
    setIsDownloading(true);
    setDownloadProgress(0);
    try {
      setDownloadProgress(10);
      const flashcards = await api.flashcards.getDue();
      if (flashcards && flashcards.length > 0 && localDb) {
        const uid = getLocalOwnerId();
        await localDb.flashcards.bulkPut(flashcards.map(f => ({ ...f, _owner_id: uid })));
      }
      setDownloadProgress(30);
      
      const questions = await api.questions.getSimuladoUSP();
      if (questions && questions.length > 0) {
        setDownloadProgress(40);
        const ids = questions.slice(0, 50).map(q => q.id);
        const chunkSize = 10;
        let loaded = 0;
        for (let i = 0; i < ids.length; i += chunkSize) {
          const chunk = ids.slice(i, i + chunkSize);
          const detailResponse = await api.questions.getBatch(chunk, true);
          if (detailResponse.questions && localDb) {
            const uid = getLocalOwnerId();
            await localDb.questions.bulkPut(Object.values(detailResponse.questions).map(q => ({ ...q, _owner_id: uid })));
          }
          loaded += chunk.length;
          setDownloadProgress(40 + (loaded / ids.length) * 60);
        }
      } else {
        setDownloadProgress(100);
      }

      await updateStats();
    } catch (e) {
      console.error("Erro ao baixar dados para o plantão:", e);
    } finally {
      setTimeout(() => {
        setIsDownloading(false);
        setDownloadProgress(0);
      }, 800);
    }
  };

  const handleRetryItem = async (id: string) => {
    await syncManager.retryItem(id);
    await updateStats();
  };

  const handleDiscardItem = async (id: string) => {
    await syncManager.discardItem(id);
    await updateStats();
  };

  return (
    <div className="bg-surface border border-outline-variant rounded-xl p-6 shadow-sm flex flex-col gap-6">
      <div>
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

        {isDownloading && (
          <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex justify-between text-xs text-on-surface-variant mb-1.5 font-medium">
              <span>Progresso</span>
              <span>{Math.round(downloadProgress)}%</span>
            </div>
            <div className="w-full bg-surface-container h-2 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-300 ease-out"
                style={{ width: `${downloadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Falhas Terminais de Sincronização */}
      {failedItems.length > 0 && (
        <div className="border-t border-outline-variant pt-4 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-destructive font-bold text-sm">
            <AlertCircle size={18} />
            <span>Itens com Falha de Sincronização ({failedItems.length})</span>
          </div>
          <p className="text-xs text-on-surface-variant">
            As seguintes operações não puderam ser sincronizadas com o servidor. Você pode tentar novamente ou descartá-las.
          </p>
          <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
            {failedItems.map((item) => (
              <div key={item.id} className="bg-surface-container-low border border-outline-variant rounded-lg p-3 flex items-center justify-between gap-3 text-xs">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-on-surface truncate">{item.method} {item.endpoint}</p>
                  <p className="text-destructive font-medium truncate">{item.last_error || "Erro de sincronização"}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleRetryItem(item.id)}
                    className="flex items-center gap-1 bg-surface-container hover:bg-surface-container-high px-2.5 py-1.5 rounded text-primary font-bold transition-colors"
                  >
                    <RefreshCw size={14} /> Tentar
                  </button>
                  <button
                    onClick={() => handleDiscardItem(item.id)}
                    className="flex items-center gap-1 bg-destructive/10 hover:bg-destructive/20 px-2.5 py-1.5 rounded text-destructive font-bold transition-colors"
                  >
                    <Trash2 size={14} /> Descartar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
