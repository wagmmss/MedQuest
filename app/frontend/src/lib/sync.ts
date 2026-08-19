/**
 * Offline Sync Manager
 * Gerencia a fila de requisições POST/PUT falhas para sincronização em background
 */

type SyncItem = {
  id: string;
  endpoint: string;
  options: RequestInit;
  timestamp: number;
};

const SYNC_KEY = "medquest_offline_sync";

export const syncManager = {
  getQueue(): SyncItem[] {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem(SYNC_KEY) || "[]");
    } catch {
      return [];
    }
  },

  enqueue(endpoint: string, options: RequestInit) {
    if (typeof window === "undefined") return;
    const queue = this.getQueue();
    queue.push({
      id: crypto.randomUUID(),
      endpoint,
      options,
      timestamp: Date.now()
    });
    localStorage.setItem(SYNC_KEY, JSON.stringify(queue));
    
    // Emit event for UI
    window.dispatchEvent(new CustomEvent('sync-queue-updated', { detail: queue.length }));
  },

  async sync() {
    if (typeof window === "undefined" || !navigator.onLine) return;
    const queue = this.getQueue();
    if (queue.length === 0) return;

    console.log(`[Sync] Sincronizando ${queue.length} requisições pendentes...`);
    
    // Clear queue so we don't duplicate on parallel syncs
    localStorage.removeItem(SYNC_KEY);
    window.dispatchEvent(new CustomEvent('sync-queue-updated', { detail: 0 }));

    const failed = [];
    for (const item of queue) {
      try {
        const response = await fetch(item.endpoint, item.options);
        if (!response.ok) {
          // Keep 5xx and 429 in queue
          if (response.status >= 500 || response.status === 429) {
             throw new Error(`Temporary error: ${response.status}`);
          }
        }
      } catch (err) {
        console.warn("[Sync] Falha ao sincronizar, requeuing:", err);
        failed.push(item);
      }
    }
    
    if (failed.length > 0) {
      const current = this.getQueue();
      localStorage.setItem(SYNC_KEY, JSON.stringify([...current, ...failed]));
      window.dispatchEvent(new CustomEvent('sync-queue-updated', { detail: failed.length + current.length }));
    }
  },

  init() {
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => this.sync());
      // Also try to sync on visibility change if we come back
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") this.sync();
      });
      // Initial attempt
      setTimeout(() => this.sync(), 2000);
    }
  }
};
