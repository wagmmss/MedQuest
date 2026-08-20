/**
 * Offline Sync Manager
 * Gerencia a fila de requisições POST/PUT falhas para sincronização em background usando Dexie (IndexedDB)
 */

import { localDb, SyncItem, getUserId } from "./db";

export const syncManager = {
  async getQueue(): Promise<SyncItem[]> {
    if (typeof window === "undefined" || !localDb) return [];
    try {
      const uid = getUserId();
      return await localDb.syncQueue.where({ user_id: uid }).toArray();
    } catch {
      return [];
    }
  },

  async enqueue(endpoint: string, options: RequestInit) {
    if (typeof window === "undefined" || !localDb) return;
    
    try {
      const uid = getUserId();
      await localDb.syncQueue.add({
        id: crypto.randomUUID(),
        user_id: uid,
        endpoint,
        options,
        timestamp: Date.now()
      });
      
      const count = await localDb.syncQueue.count();
      window.dispatchEvent(new CustomEvent('sync-queue-updated', { detail: count }));
    } catch (err) {
      console.error("[Sync] Erro ao enfileirar no Dexie:", err);
    }
  },

  async sync() {
    if (typeof window === "undefined" || !navigator.onLine || !localDb) return;
    
    const queue = await this.getQueue();
    if (queue.length === 0) return;

    console.log(`[Sync] Sincronizando ${queue.length} requisições pendentes...`);
    
    // Notify UI that sync is starting
    window.dispatchEvent(new CustomEvent('sync-queue-updated', { detail: queue.length }));

    for (const item of queue) {
      try {
        const response = await fetch(item.endpoint, item.options);
        if (!response.ok) {
          // Keep 5xx and 429 in queue
          if (response.status >= 500 || response.status === 429) {
             throw new Error(`Temporary error: ${response.status}`);
          }
        }
        // Success or non-retryable error (e.g. 400), remove from queue
        await localDb.syncQueue.delete(item.id);
      } catch (err) {
        console.warn("[Sync] Falha ao sincronizar, item será mantido na fila:", err);
      }
    }
    
    const remainingCount = await localDb.syncQueue.count();
    window.dispatchEvent(new CustomEvent('sync-queue-updated', { detail: remainingCount }));
  },

  init() {
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => this.sync());
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") this.sync();
      });
      // Initial attempt
      setTimeout(() => this.sync(), 2000);
    }
  }
};
