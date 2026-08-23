/**
 * Offline Sync Manager
 * Gerencia a fila de requisições falhas com Dexie, idempotência e backoff exponencial com jitter.
 */

import { localDb, SyncItem, getLocalOwnerId } from "./db";

let isInitialized = false;
let onlineHandler: (() => void) | null = null;
let visibilityHandler: (() => void) | null = null;
let syncTimer: ReturnType<typeof setTimeout> | null = null;
let syncPromise: Promise<void> | null = null;

function serializeBody(body: unknown): string | null {
  if (body === null || body === undefined) {
    return null;
  }
  if (typeof body === "string") {
    return body;
  }
  if (
    typeof FormData !== "undefined" && body instanceof FormData ||
    typeof Blob !== "undefined" && body instanceof Blob ||
    typeof URLSearchParams !== "undefined" && body instanceof URLSearchParams ||
    typeof ArrayBuffer !== "undefined" && body instanceof ArrayBuffer ||
    typeof ReadableStream !== "undefined" && body instanceof ReadableStream
  ) {
    throw new Error("Formato de body não suportado para sincronização offline");
  }
  if (typeof body === "object") {
    return JSON.stringify(body);
  }
  throw new Error("Formato de body não suportado para sincronização offline");
}

function extractContentType(headers?: HeadersInit): string {
  if (!headers) return "application/json";
  if (headers instanceof Headers) {
    return headers.get("content-type") || "application/json";
  }
  if (Array.isArray(headers)) {
    const found = headers.find(([k]) => k.toLowerCase() === "content-type");
    return found ? found[1] : "application/json";
  }
  if (typeof headers === "object") {
    for (const [k, v] of Object.entries(headers)) {
      if (k.toLowerCase() === "content-type" && typeof v === "string") {
        return v;
      }
    }
  }
  return "application/json";
}

export const syncManager = {
  async getQueue(): Promise<SyncItem[]> {
    if (typeof window === "undefined" || !localDb) return [];
    try {
      const uid = getLocalOwnerId();
      return await localDb.syncQueue
        .where({ owner_id: uid })
        .filter((item) => item.status === "pending")
        .toArray();
    } catch {
      return [];
    }
  },

  async getFailedItems(): Promise<SyncItem[]> {
    if (typeof window === "undefined" || !localDb) return [];
    try {
      const uid = getLocalOwnerId();
      return await localDb.syncQueue
        .where({ owner_id: uid })
        .filter((item) => item.status === "failed")
        .toArray();
    } catch {
      return [];
    }
  },

  async enqueue(endpoint: string, options: RequestInit, providedIdempotencyKey?: string): Promise<string> {
    if (typeof window === "undefined" || !localDb) {
      throw new Error("Armazenamento local indisponível para fila offline");
    }

    const uid = getLocalOwnerId();
    const id = crypto.randomUUID();
    const bodyStr = serializeBody(options.body);
    const contentType = extractContentType(options.headers);

    await localDb.syncQueue.add({
      id,
      owner_id: uid,
      endpoint,
      method: options.method?.toUpperCase() || "POST",
      body: bodyStr,
      content_type: contentType,
      created_at: Date.now(),
      retry_count: 0,
      // The request has just failed once. Avoid an immediate duplicate retry;
      // explicit/manual sync and the browser online event may still force it.
      next_retry_at: Date.now() + 2000 + Math.random() * 1000,
      status: "pending",
      idempotency_key: providedIdempotencyKey || crypto.randomUUID(),
    });

    await this.scheduleNextSync();

    const pendingCount = await this.getPendingCount();
    window.dispatchEvent(new CustomEvent("sync-queue-updated", { detail: pendingCount }));
    return id;
  },

  async getPendingCount(): Promise<number> {
    if (typeof window === "undefined" || !localDb) return 0;
    try {
      const uid = getLocalOwnerId();
      return await localDb.syncQueue
        .where({ owner_id: uid })
        .filter((item) => item.status === "pending")
        .count();
    } catch {
      return 0;
    }
  },

  async scheduleNextSync(): Promise<void> {
    if (typeof window === "undefined" || !localDb) return;
    
    if (syncTimer) {
      clearTimeout(syncTimer);
      syncTimer = null;
    }

    try {
      const uid = getLocalOwnerId();
      const items = await localDb.syncQueue
        .where({ owner_id: uid })
        .filter((item) => item.status === "pending")
        .toArray();

      if (items.length === 0) return;

      const now = Date.now();
      let closestNextRetry = Infinity;

      for (const item of items) {
        if (item.next_retry_at < closestNextRetry) {
          closestNextRetry = item.next_retry_at;
        }
      }

      let delay = closestNextRetry - now;
      if (delay < 0) delay = 0;
      // Cap at 24 hours just to avoid overflow
      if (delay > 86400000) delay = 86400000;

      syncTimer = setTimeout(() => {
        this.sync();
      }, delay);

    } catch (err) {
      console.error("[Sync] Erro ao agendar próxima sincronização:", err);
    }
  },

  async sync(force = false): Promise<void> {
    if (typeof window === "undefined" || !navigator.onLine || !localDb) return;

    if (syncPromise) {
      return syncPromise;
    }

    syncPromise = this._doSync(force).finally(() => {
      syncPromise = null;
      this.scheduleNextSync();
    });

    return syncPromise;
  },

  async _doSync(force = false): Promise<void> {
    const uid = getLocalOwnerId();
    const now = Date.now();

    let items: SyncItem[] = [];
    try {
      items = await localDb.syncQueue
        .where({ owner_id: uid })
        .filter((item) => item.status === "pending" && (force || item.next_retry_at <= now))
        .toArray();
    } catch (err) {
      console.error("[Sync] Erro ao carregar itens da fila:", err);
      return;
    }

    if (items.length === 0) return;

    console.log(`[Sync] Sincronizando ${items.length} requisições pendentes...`);

    for (const item of items) {
      try {
        const fetchHeaders: HeadersInit = {
          "Content-Type": item.content_type,
          "X-Idempotency-Key": item.idempotency_key,
        };

        const response = await fetch(item.endpoint, {
          method: item.method,
          headers: fetchHeaders,
          body: item.body,
        });

        if (response.ok) {
          let responseData: unknown = null;
          try {
            const text = await response.text();
            if (text) {
              responseData = JSON.parse(text);
            }
          } catch {
            // ignore parse error if response is not JSON
          }
          await localDb.syncQueue.delete(item.id);
          window.dispatchEvent(new CustomEvent("sync-item-success", {
            detail: {
              id: item.id,
              endpoint: item.endpoint,
              method: item.method,
              data: responseData,
              idempotencyKey: item.idempotency_key,
            }
          }));
          continue;
        }

        const retryAfterHeader = response.headers.get("Retry-After");
        let retryAfterMs = 0;
        if (retryAfterHeader) {
          const parsed = parseInt(retryAfterHeader, 10);
          if (!isNaN(parsed)) {
            retryAfterMs = parsed * 1000;
          } else {
            const dateParsed = Date.parse(retryAfterHeader);
            if (!isNaN(dateParsed)) {
              retryAfterMs = Math.max(0, dateParsed - Date.now());
            }
          }
        }

        // Erros retentáveis: 408 (Request Timeout), 429 (Too Many Requests), >= 500 (Server Error)
        const isRetriable = response.status === 408 || response.status === 429 || response.status >= 500;

        if (isRetriable) {
          const newRetryCount = item.retry_count + 1;
          if (newRetryCount >= 5) {
            // Limite máximo atingido -> marcação como falha terminal
            await localDb.syncQueue.update(item.id, {
              status: "failed",
              retry_count: newRetryCount,
              last_error: `Falha temporária persistente (HTTP ${response.status}) após 5 tentativas`,
            });
          } else {
            // Backoff exponencial com jitter: base 1s * 2^(retry) + random(0-1000ms), max 60s
            let delay = Math.min(60000, 1000 * Math.pow(2, newRetryCount)) + Math.random() * 1000;
            if (retryAfterMs > delay) delay = retryAfterMs;
            await localDb.syncQueue.update(item.id, {
              retry_count: newRetryCount,
              next_retry_at: Date.now() + delay,
              last_error: `HTTP ${response.status}`,
            });
          }
        } else {
          // Erro 4xx não retentável -> move imediatamente para falha terminal
          await localDb.syncQueue.update(item.id, {
            status: "failed",
            retry_count: item.retry_count + 1,
            last_error: `Erro irrecuperável HTTP ${response.status}`,
          });
        }
      } catch (err) {
        // Erro de rede (offline, DNS, timeout de socket) -> retentável
        const newRetryCount = item.retry_count + 1;
        if (newRetryCount >= 5) {
          await localDb.syncQueue.update(item.id, {
            status: "failed",
            retry_count: newRetryCount,
            last_error: `Erro de rede persistente: ${err instanceof Error ? err.message : String(err)}`,
          });
        } else {
          const delay = Math.min(60000, 1000 * Math.pow(2, newRetryCount)) + Math.random() * 1000;
          await localDb.syncQueue.update(item.id, {
            retry_count: newRetryCount,
            next_retry_at: Date.now() + delay,
            last_error: err instanceof Error ? err.message : String(err),
          });
        }
      }
    }

    const remainingCount = await this.getPendingCount();
    window.dispatchEvent(new CustomEvent("sync-queue-updated", { detail: remainingCount }));
  },

  async retryItem(id: string): Promise<void> {
    if (typeof window === "undefined" || !localDb) return;
    const uid = getLocalOwnerId();
    const item = await localDb.syncQueue.get(id);
    if (!item || item.owner_id !== uid) return;

    await localDb.syncQueue.update(id, {
      status: "pending",
      retry_count: 0,
      next_retry_at: Date.now(),
      last_error: undefined,
    });
    const pendingCount = await this.getPendingCount();
    window.dispatchEvent(new CustomEvent("sync-queue-updated", { detail: pendingCount }));
    await this.scheduleNextSync();
    await this.sync();
  },

  async discardItem(id: string): Promise<void> {
    if (typeof window === "undefined" || !localDb) return;
    const uid = getLocalOwnerId();
    const item = await localDb.syncQueue.get(id);
    if (!item || item.owner_id !== uid) return;

    await localDb.syncQueue.delete(id);
    const pendingCount = await this.getPendingCount();
    window.dispatchEvent(new CustomEvent("sync-queue-updated", { detail: pendingCount }));
    await this.scheduleNextSync();
  },

  init(): void {
    if (typeof window === "undefined" || isInitialized) return;
    isInitialized = true;

    onlineHandler = () => {
      this.sync(true);
    };
    visibilityHandler = () => {
      if (document.visibilityState === "visible") {
        this.sync();
      }
    };

    window.addEventListener("online", onlineHandler);
    document.addEventListener("visibilitychange", visibilityHandler);

    this.scheduleNextSync();
  },

  cleanup(): void {
    if (typeof window === "undefined" || !isInitialized) return;

    if (syncTimer) {
      clearTimeout(syncTimer);
      syncTimer = null;
    }

    if (onlineHandler) {
      window.removeEventListener("online", onlineHandler);
      onlineHandler = null;
    }

    if (visibilityHandler) {
      document.removeEventListener("visibilitychange", visibilityHandler);
      visibilityHandler = null;
    }

    isInitialized = false;
  },
};

if (typeof window !== "undefined") {
  (window as unknown as { syncManager?: typeof syncManager }).syncManager = syncManager;
}
