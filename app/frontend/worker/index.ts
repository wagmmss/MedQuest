export {};

interface ExtendableEvent extends Event {
  waitUntil(fn: Promise<unknown>): void;
}

interface FetchEvent extends Event {
  request: Request;
  respondWith(response: Promise<Response> | Response): void;
}

const LEGACY_CACHES = [
  "apis",
  "start-url",
  "pages",
  "pages-rsc",
  "pages-rsc-prefetch",
  "static-data-assets",
  "cross-origin"
];

const OFFLINE_STUDY_SHELL_CACHE = "medquest-study-shell";
const OFFLINE_STUDY_SHELL_PATH = "/estudar";

function getOfflineFallbackHtml(): Response {
  const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>MedQuest - Modo Plantão (Offline)</title>
  <style>
    :root {
      --bg: #090d16;
      --card: #131b2e;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --primary: #0284c7;
      --primary-hover: #0369a1;
      --border: rgba(255,255,255,0.1);
    }
    @media (prefers-color-scheme: light) {
      :root {
        --bg: #f8fafc;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --primary: #0284c7;
        --primary-hover: #0369a1;
        --border: rgba(0,0,0,0.1);
      }
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 24px; padding: 32px 24px; max-width: 440px; width: 100%; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .icon { width: 56px; height: 56px; border-radius: 16px; background: rgba(2,132,199,0.15); color: var(--primary); display: inline-flex; align-items: center; justify-content: center; margin: 0 auto 16px; font-size: 28px; }
    h1 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
    p { font-size: 14px; color: var(--muted); margin-bottom: 24px; line-height: 1.5; }
    .btn-group { display: flex; flex-direction: column; gap: 10px; }
    a.btn, button.btn { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 13px; border-radius: 14px; font-size: 14px; font-weight: 600; text-decoration: none; cursor: pointer; border: none; transition: all 0.2s; }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-secondary { background: rgba(2,132,199,0.1); color: var(--primary); border: 1px solid var(--border); }
    .btn-secondary:hover { background: rgba(2,132,199,0.2); }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">⚡</div>
    <h1>Modo Plantão Ativo</h1>
    <p>Você está sem conexão de rede. Você pode continuar resolvendo simulados e questões salvos neste aparelho sem interrupção.</p>
    <div class="btn-group">
      <a href="/estudar" class="btn btn-primary">Abrir Questões Offline</a>
      <a href="/simulado" class="btn btn-secondary">Abrir Simulados Offline</a>
      <a href="/revisao-ativa" class="btn btn-secondary">Revisar Flashcards Offline</a>
      <button onclick="window.location.reload()" class="btn btn-secondary" style="margin-top: 6px;">Tentar Reconectar</button>
    </div>
  </div>
</body>
</html>`;

  return new Response(html, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

async function getOfflineStudyShell(): Promise<Response> {
  try {
    const cache = await caches.open(OFFLINE_STUDY_SHELL_CACHE);
    const shell = await cache.match(OFFLINE_STUDY_SHELL_PATH, {
      ignoreSearch: true,
      ignoreVary: true,
    });
    if (shell) return shell;
  } catch {
    // Cache indisponível
  }
  return getOfflineFallbackHtml();
}

async function fetchNavigationWithTimeout(request: Request, timeoutMs: number = 3000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(request, { signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timer);
  }
}

// Intercepta navegações com timeout de 3s para impedir que o celular trave
// quando a conexão cai ou oscila.
self.addEventListener("fetch", (rawEvent: Event) => {
  const event = rawEvent as FetchEvent;
  if (event.request.mode !== "navigate") return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  // Rotas de estudo/simulado/revisão ou raiz
  event.respondWith((async () => {
    try {
      return await fetchNavigationWithTimeout(event.request, 2800);
    } catch {
      // Se a conexão falhar ou expirar o tempo limite:
      if (url.pathname === "/estudar" || url.pathname === "/") {
        const shell = await getOfflineStudyShell();
        return shell;
      }
      // Para outras rotas em modo offline, retorna a casca ou fallback amigável
      return getOfflineStudyShell();
    }
  })());
});

// Question images served from third-party CDNs are stored explicitly while a
// package is downloaded. Workbox's same-origin API rule cannot serve those
// entries on a later offline render, so answer them from that cache here.
self.addEventListener("fetch", (rawEvent: Event) => {
  const event = rawEvent as FetchEvent;
  if (event.request.destination !== "image") return;

  const url = new URL(event.request.url);
  if (url.origin === self.location.origin) return;

  event.respondWith((async () => {
    const imageCache = await caches.open("medquest-image-cache");
    const cached = await imageCache.match(event.request);
    return cached || fetch(event.request);
  })());
});

async function primeOfflineShellOnActivate(): Promise<void> {
  try {
    const cache = await caches.open(OFFLINE_STUDY_SHELL_CACHE);
    const existing = await cache.match(OFFLINE_STUDY_SHELL_PATH, { ignoreSearch: true, ignoreVary: true });
    if (!existing) {
      const response = await fetch(OFFLINE_STUDY_SHELL_PATH);
      if (response && response.ok) {
        await cache.put(OFFLINE_STUDY_SHELL_PATH, response);
        console.log("[ServiceWorker] Casca offline /estudar pré-aquecida com sucesso.");
      }
    }
  } catch (err) {
    console.warn("[ServiceWorker] Não foi possível pré-aquecer a casca no activate:", err);
  }
}

// Clean up any legacy or unwanted caches during ServiceWorker activation and prime study shell
self.addEventListener("activate", (rawEvent: Event) => {
  const event = rawEvent as ExtendableEvent;
  if (typeof caches !== "undefined") {
    event.waitUntil(
      Promise.all([
        caches.keys().then((keys) => {
          return Promise.all(
            keys
              .filter((key) => LEGACY_CACHES.some((legacy) => key.includes(legacy)))
              .map((key) => {
                console.log(`[ServiceWorker] Removing legacy cache: ${key}`);
                return caches.delete(key);
              })
          );
        }),
        primeOfflineShellOnActivate(),
      ])
    );
  }
});

interface PushEvent extends ExtendableEvent {
  data?: {
    json(): Record<string, unknown>;
    text(): string;
  } | null;
}

interface NotificationEvent extends ExtendableEvent {
  notification: Notification;
}

interface WindowClient {
  url: string;
  focus(): Promise<WindowClient>;
  navigate(url: string): Promise<WindowClient>;
}

interface Clients {
  matchAll(options?: { type?: string; includeUncontrolled?: boolean }): Promise<WindowClient[]>;
  openWindow(url: string): Promise<WindowClient | null>;
}

interface ServiceWorkerRegistrationWithNotif {
  showNotification(title: string, options?: NotificationOptions): Promise<void>;
}

interface CustomWorkerScope {
  registration: ServiceWorkerRegistrationWithNotif;
  clients: Clients;
  location: Location;
}

// Handler de eventos Web Push
self.addEventListener("push", (rawEvent: Event) => {
  const event = rawEvent as PushEvent;
  let title = "MedQuest";
  let body = "Você tem revisões pendentes para hoje. Mantenha seu ritmo de estudos!";
  let url = "/revisao-ativa";
  let tag = "medquest-fsrs-review";

  if (event.data) {
    try {
      const data = event.data.json();
      if (typeof data.title === "string") title = data.title;
      if (typeof data.body === "string") body = data.body;
      if (typeof data.url === "string") url = data.url;
      if (typeof data.tag === "string") tag = data.tag;
    } catch {
      const text = event.data.text();
      if (text) body = text;
    }
  }

  const options: NotificationOptions = {
    body,
    icon: "/icon.svg",
    badge: "/icon.svg",
    tag,
    data: { url },
  };

  const sw = self as unknown as CustomWorkerScope;
  if (sw.registration && sw.registration.showNotification) {
    event.waitUntil(sw.registration.showNotification(title, options));
  }
});

function getSafeInternalUrl(rawUrl: unknown): string {
  if (
    typeof rawUrl === "string" &&
    rawUrl.startsWith("/") &&
    !rawUrl.startsWith("//") &&
    !rawUrl.includes("\\")
  ) {
    return rawUrl;
  }
  return "/revisao-ativa";
}

// Handler de clique na notificação
self.addEventListener("notificationclick", (rawEvent: Event) => {
  const event = rawEvent as NotificationEvent;
  event.notification.close();

  const rawDataUrl = event.notification.data && event.notification.data.url;
  const targetUrl = getSafeInternalUrl(rawDataUrl);
  const sw = self as unknown as CustomWorkerScope;

  if (sw.clients) {
    event.waitUntil(
      sw.clients
        .matchAll({ type: "window", includeUncontrolled: true })
        .then((clientList: WindowClient[]) => {
          for (const client of clientList) {
            if (client.url.includes(sw.location.origin) && "focus" in client) {
              if ("navigate" in client) {
                client.navigate(targetUrl);
              }
              return client.focus();
            }
          }
          if (sw.clients.openWindow) {
            return sw.clients.openWindow(targetUrl);
          }
        })
    );
  }
});
