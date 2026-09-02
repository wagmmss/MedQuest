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

// Existing Android installations can retain `/` as their launch target until
// Chrome refreshes the manifest. A redirect is not enough here: after a failed
// navigation Chrome may try to load the redirect target outside this fetch
// event and show its generic offline page. Return the cached shell itself.
// New installations start at `/estudar` (see manifest.json), which is handled
// by Workbox's NetworkFirst route below.
self.addEventListener("fetch", (rawEvent: Event) => {
  const event = rawEvent as FetchEvent;
  if (event.request.mode !== "navigate") return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname !== "/") return;

  event.respondWith((async () => {
    try {
      return await fetch(event.request);
    } catch {
      const cache = await caches.open(OFFLINE_STUDY_SHELL_CACHE);
      const shell = await cache.match(OFFLINE_STUDY_SHELL_PATH, { ignoreSearch: true });
      return shell || Response.error();
    }
  })());
});

// Clean up any legacy or unwanted caches during ServiceWorker activation
self.addEventListener("activate", (rawEvent: Event) => {
  const event = rawEvent as ExtendableEvent;
  if (typeof caches !== "undefined") {
    event.waitUntil(
      caches.keys().then((keys) => {
        return Promise.all(
          keys
            .filter((key) => LEGACY_CACHES.some((legacy) => key.includes(legacy)))
            .map((key) => {
              console.log(`[ServiceWorker] Removing legacy cache: ${key}`);
              return caches.delete(key);
            })
        );
      })
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
