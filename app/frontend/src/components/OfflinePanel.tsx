"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { CloudOff, Download, RefreshCw, Database, AlertCircle, Trash2, CheckCircle2, Play, BookOpen, Layers } from "lucide-react";
import { localDb, getLocalOwnerId, SyncItem } from "@/lib/db";
import { api } from "@/lib/api";
import { syncManager } from "@/lib/sync";
import toast from "react-hot-toast";

export function OfflinePanel({ onClose }: { onClose?: () => void } = {}) {
  const [isOffline, setIsOffline] = useState(false);
  const [stats, setStats] = useState({ questions: 0, flashcards: 0, queue: 0 });
  const [failedItems, setFailedItems] = useState<SyncItem[]>([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadStatus, setDownloadStatus] = useState<string>("");
  const [questionCount, setQuestionCount] = useState<number>(50);
  const [lastDownloadDate, setLastDownloadDate] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const downloadResetTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (downloadResetTimerRef.current) clearTimeout(downloadResetTimerRef.current);
  }, []);

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

      const savedDate = localStorage.getItem("medquest_last_offline_download");
      if (savedDate) {
        setLastDownloadDate(savedDate);
      }
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

  const prefetchImages = async (imageUrls: string[]) => {
    const uniqueUrls = Array.from(new Set(imageUrls.filter(Boolean)));
    const imageFetches = uniqueUrls.map(async (url) => {
      try {
        const fullUrl = url.startsWith("http") ? url : `${url.startsWith("/") ? "" : "/"}${url}`;
        await fetch(fullUrl, { cache: "force-cache" });
      } catch {
        // Falha no pré-carregamento de imagem individual não interrompe o pacote
      }
    });
    await Promise.allSettled(imageFetches);
  };

  const downloadForShift = async () => {
    if (isDownloading) return;
    setIsDownloading(true);
    setDownloadProgress(0);
    setDownloadStatus("Buscando flashcards...");
    try {
      setDownloadProgress(10);
      const flashcards = await api.flashcards.getDue(true);
      if (flashcards && flashcards.length > 0 && localDb) {
        const uid = getLocalOwnerId();
        await localDb.flashcards.bulkPut(flashcards.map(f => ({ ...f, _owner_id: uid })));
      }
      setDownloadProgress(30);
      setDownloadStatus("Buscando questões do simulado...");
      
      const questions = await api.questions.getSimuladoUSP();
      if (questions && questions.length > 0) {
        setDownloadProgress(40);
        const ids = questions.slice(0, questionCount).map(q => q.id);
        const chunkSize = 10;
        let loaded = 0;
        const allImageUrls: string[] = [];

        for (let i = 0; i < ids.length; i += chunkSize) {
          const chunk = ids.slice(i, i + chunkSize);
          setDownloadStatus(`Baixando questões (${Math.min(i + chunkSize, ids.length)}/${ids.length})...`);
          
          const detailResponse = await api.questions.getBatch(chunk, true);
          if (detailResponse.questions && localDb) {
            const uid = getLocalOwnerId();
            const questionsList = Object.values(detailResponse.questions);
            await localDb.questions.bulkPut(questionsList.map(q => ({ ...q, _owner_id: uid })));

            // Coleta URLs de imagens para pré-carregamento offline
            for (const q of questionsList) {
              if (q.images && Array.isArray(q.images)) {
                allImageUrls.push(...q.images.map(img => `/api/images/${img}`));
              }
              if (q.clinical_case?.images && Array.isArray(q.clinical_case.images)) {
                allImageUrls.push(...q.clinical_case.images.map(img => `/api/images/${img}`));
              }
            }
          }
          loaded += chunk.length;
          setDownloadProgress(40 + (loaded / ids.length) * 45);
        }

        if (allImageUrls.length > 0) {
          setDownloadStatus("Armazenando imagens médicas em cache...");
          setDownloadProgress(90);
          await prefetchImages(allImageUrls);
        }
      }

      setDownloadProgress(100);
      setDownloadStatus("Pacote offline pronto!");
      // Prime the only cached navigation shell while the device is online.
      // This is deliberately limited to /estudar; API responses are never
      // stored by the service worker and continue to use IndexedDB instead.
      try {
        await fetch("/estudar", { cache: "reload" });
      } catch (error) {
        // The question package is still usable if the shell was already
        // cached; a transient navigation failure must not discard the download.
        console.warn("Não foi possível atualizar a tela offline de estudo:", error);
      }
      const nowStr = new Date().toISOString();
      localStorage.setItem("medquest_last_offline_download", nowStr);
      setLastDownloadDate(nowStr);

      await updateStats();
      toast.success("Pacote de Plantão baixado com sucesso!");
    } catch (e) {
      console.error("Erro ao baixar dados para o plantão:", e);
      toast.error("Erro ao baixar pacote. Verifique sua conexão e tente novamente.");
    } finally {
      downloadResetTimerRef.current = setTimeout(() => {
        setIsDownloading(false);
        setDownloadProgress(0);
        setDownloadStatus("");
      }, 1200);
    }
  };

  const handleClearOfflineData = async () => {
    if (!localDb) return;
    if (!window.confirm("Deseja realmente limpar as questões e flashcards salvos neste dispositivo? A fila de envios pendentes não será afetada.")) {
      return;
    }

    try {
      const uid = getLocalOwnerId();
      await Promise.all([
        localDb.questions.where({ _owner_id: uid }).delete(),
        localDb.flashcards.where({ _owner_id: uid }).delete(),
      ]);
      localStorage.removeItem("medquest_last_offline_download");
      setLastDownloadDate(null);
      await updateStats();
      toast.success("Dados offline limpos deste dispositivo.");
    } catch (err) {
      console.error("Erro ao limpar dados offline:", err);
      toast.error("Erro ao limpar dados locais.");
    }
  };

  const handleManualSync = async () => {
    if (isSyncing || isOffline) return;
    setIsSyncing(true);
    try {
      await syncManager.sync(true);
      await updateStats();
      toast.success("Sincronização concluída com sucesso!");
    } catch {
      toast.error("Erro ao sincronizar. Tente novamente.");
    } finally {
      setIsSyncing(false);
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

  const formattedLastDate = lastDownloadDate ? new Date(lastDownloadDate).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }) : null;

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col gap-6">
      <div>
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-border">
          <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
            {isOffline ? (
              <CloudOff className="text-warning" size={24} />
            ) : (
              <Database className="text-primary" size={24} />
            )}
            Modo Plantão (Offline)
          </h3>
          <div className="flex items-center gap-2">
            <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${isOffline ? 'bg-warning/20 text-warning' : 'bg-success/20 text-success'}`}>
              {isOffline ? 'Desconectado' : 'Online'}
            </div>
          </div>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Baixe questões e flashcards com antecedência para estudar sem internet durante seus plantões. Suas respostas serão salvas com segurança e sincronizadas automaticamente quando reconectar.
        </p>

        {formattedLastDate && (
          <p className="text-xs text-muted-foreground mb-6 flex items-center gap-1.5 font-medium">
            <CheckCircle2 size={14} className="text-success" />
            Última atualização local: <strong className="text-foreground">{formattedLastDate}</strong>
          </p>
        )}

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-muted/50 rounded-lg p-3 text-center border border-border">
            <p className="text-xs text-muted-foreground uppercase font-semibold">Questões</p>
            <p className="text-2xl font-bold text-foreground">{stats.questions}</p>
          </div>
          <div className="bg-muted/50 rounded-lg p-3 text-center border border-border">
            <p className="text-xs text-muted-foreground uppercase font-semibold">Flashcards</p>
            <p className="text-2xl font-bold text-foreground">{stats.flashcards}</p>
          </div>
          <div className="bg-muted/50 rounded-lg p-3 text-center border border-border relative">
            <p className="text-xs text-muted-foreground uppercase font-semibold">Fila (Envios)</p>
            <p className="text-2xl font-bold text-foreground">{stats.queue}</p>
            {stats.queue > 0 && !isOffline && (
              <button
                onClick={handleManualSync}
                disabled={isSyncing}
                title="Sincronizar fila agora"
                className="absolute top-2 right-2 text-primary hover:text-primary/80 transition-colors p-1 rounded"
              >
                <RefreshCw size={14} className={isSyncing ? "animate-spin" : ""} />
              </button>
            )}
          </div>
        </div>

        {/* Seleção do tamanho do pacote quando online */}
        {!isOffline && !isDownloading && (
          <div className="flex items-center justify-between gap-4 mb-4 p-3 bg-muted/30 border border-border/60 rounded-lg text-xs">
            <span className="font-semibold text-muted-foreground">Tamanho do pacote:</span>
            <div className="flex items-center gap-2">
              {[25, 50, 100].map((count) => (
                <button
                  key={count}
                  onClick={() => setQuestionCount(count)}
                  className={`px-2.5 py-1 rounded font-bold transition-colors ${
                    questionCount === count
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {count} Questões
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={downloadForShift}
            disabled={isDownloading || isOffline}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isDownloading ? (
              <><RefreshCw className="animate-spin" size={20} /> Baixando Carga...</>
            ) : (
              <><Download size={20} /> Baixar Pacote de Plantão ({questionCount} Qs)</>
            )}
          </button>

          {(stats.questions > 0 || stats.flashcards > 0) && !isDownloading && (
            <button
              onClick={handleClearOfflineData}
              title="Limpar questões e flashcards salvos neste dispositivo"
              className="flex items-center justify-center gap-1.5 px-4 py-3 rounded-lg border border-border bg-card hover:bg-destructive/10 hover:border-destructive/30 hover:text-destructive text-muted-foreground font-medium text-xs transition-colors"
            >
              <Trash2 size={16} /> Limpar
            </button>
          )}
        </div>

        {isDownloading && (
          <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex justify-between text-xs text-muted-foreground mb-1.5 font-medium">
              <span>{downloadStatus || "Progresso"}</span>
              <span>{Math.round(downloadProgress)}%</span>
            </div>
            <div className="w-full bg-muted h-2 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-300 ease-out"
                style={{ width: `${downloadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Atalhos para estudo quando há conteúdo baixado */}
        {(stats.questions > 0 || stats.flashcards > 0) && (
          <div className="mt-6 pt-5 border-t border-border/80 flex flex-col gap-3">
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Acesso Rápido ao Conteúdo Local:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Link
                href="/simulado"
                onClick={() => onClose?.()}
                className="flex items-center justify-center gap-2 p-2.5 rounded-lg bg-muted/40 hover:bg-muted text-foreground border border-border font-medium text-xs transition-colors"
              >
                <Play size={14} className="text-secondary" />
                Simulado Offline
              </Link>
              <Link
                href="/estudar"
                onClick={() => onClose?.()}
                className="flex items-center justify-center gap-2 p-2.5 rounded-lg bg-muted/40 hover:bg-muted text-foreground border border-border font-medium text-xs transition-colors"
              >
                <BookOpen size={14} className="text-primary" />
                Banco de Questões
              </Link>
              <Link
                href="/revisao-ativa"
                onClick={() => onClose?.()}
                className="flex items-center justify-center gap-2 p-2.5 rounded-lg bg-muted/40 hover:bg-muted text-foreground border border-border font-medium text-xs transition-colors"
              >
                <Layers size={14} className="text-purple-500" />
                Flashcards Offline
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Falhas Terminais de Sincronização */}
      {failedItems.length > 0 && (
        <div className="border-t border-border pt-4 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-destructive font-bold text-sm">
            <AlertCircle size={18} />
            <span>Itens com Falha de Sincronização ({failedItems.length})</span>
          </div>
          <p className="text-xs text-muted-foreground">
            As seguintes operações não puderam ser sincronizadas com o servidor. Você pode tentar novamente ou descartá-las.
          </p>
          <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
            {failedItems.map((item) => (
              <div key={item.id} className="bg-muted/40 border border-border rounded-lg p-3 flex items-center justify-between gap-3 text-xs">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-foreground truncate">{item.method} {item.endpoint}</p>
                  <p className="text-destructive font-medium truncate">{item.last_error || "Erro de sincronização"}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleRetryItem(item.id)}
                    className="flex items-center gap-1 bg-card hover:bg-muted border border-border px-2.5 py-1.5 rounded text-primary font-bold transition-colors"
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
