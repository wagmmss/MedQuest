"use client";

import { useEffect, useState } from "react";
import { syncManager } from "@/lib/sync";
import { localDb } from "@/lib/db";
import { CloudOff } from "lucide-react";

export function SyncProvider() {
  const [queueCount, setQueueCount] = useState(0);

  useEffect(() => {
    (window as unknown as { syncManager: typeof syncManager }).syncManager = syncManager;
    (window as unknown as { localDb: typeof localDb }).localDb = localDb;
    syncManager.init();
    
    // Sync UI with queue length
    const handleUpdate = (e: Event) => {
      const customEvent = e as CustomEvent<number>;
      setQueueCount(customEvent.detail);
    };

    window.addEventListener('sync-queue-updated', handleUpdate);
    // Setup initial count
    syncManager.getPendingCount().then(count => setQueueCount(count));

    return () => {
      window.removeEventListener('sync-queue-updated', handleUpdate);
      syncManager.cleanup();
    };
  }, []);

  if (queueCount === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-warning text-warning-foreground px-4 py-2 rounded-full shadow-lg flex items-center gap-2 z-50 animate-in fade-in slide-in-from-bottom-4">
      <CloudOff size={18} className="animate-pulse" />
      <span className="text-sm font-semibold">
        {queueCount} {queueCount === 1 ? 'item offline' : 'itens offline'}
      </span>
    </div>
  );
}
