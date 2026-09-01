"use client";

import { useEffect, useState } from "react";
import { syncManager } from "@/lib/sync";
import { localDb } from "@/lib/db";
import { downloadSimuladoPackage, getReadySimuladoPackage, listSimuladoPackages, deleteSimuladoPackage } from "@/lib/simuladoPackage";
import { CloudOff } from "lucide-react";

export function SyncProvider() {
  const [queueCount, setQueueCount] = useState(0);

  useEffect(() => {
    let isActive = true;
    (window as unknown as { syncManager: typeof syncManager }).syncManager = syncManager;
    (window as unknown as { localDb: typeof localDb }).localDb = localDb;
    (window as unknown as { simuladoPackage: unknown }).simuladoPackage = {
      downloadSimuladoPackage,
      getReadySimuladoPackage,
      listSimuladoPackages,
      deleteSimuladoPackage,
    };
    syncManager.init();

    
    // Sync UI with queue length
    const handleUpdate = (e: Event) => {
      const customEvent = e as CustomEvent<number>;
      setQueueCount(customEvent.detail);
    };

    window.addEventListener('sync-queue-updated', handleUpdate);
    // Setup initial count
    void syncManager.getPendingCount().then(count => {
      if (isActive) setQueueCount(count);
    });

    return () => {
      isActive = false;
      window.removeEventListener('sync-queue-updated', handleUpdate);
      syncManager.cleanup();
    };
  }, []);

  const [isManualSyncing, setIsManualSyncing] = useState(false);

  const handleTriggerSync = async () => {
    if (isManualSyncing) return;
    setIsManualSyncing(true);
    try {
      await syncManager.sync(true);
    } finally {
      setIsManualSyncing(false);
    }
  };

  if (queueCount === 0) return null;

  return (
    <button
      onClick={handleTriggerSync}
      disabled={isManualSyncing}
      title="Clique para forçar a sincronização de dados"
      className="fixed bottom-4 right-4 bg-warning text-warning-foreground hover:bg-warning/90 px-4 py-2 rounded-full shadow-lg flex items-center gap-2 z-50 animate-in fade-in slide-in-from-bottom-4 cursor-pointer transition-all active:scale-95 disabled:opacity-75"
    >
      <CloudOff size={18} className={isManualSyncing ? "animate-spin" : "animate-pulse"} />
      <span className="text-sm font-semibold">
        {isManualSyncing ? "Sincronizando..." : `${queueCount} ${queueCount === 1 ? 'item offline' : 'itens offline'}`}
      </span>
    </button>
  );
}
