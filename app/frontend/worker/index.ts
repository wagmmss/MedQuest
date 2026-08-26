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

// Existing Android installations can retain `/` as their launch target until
// Chrome refreshes the manifest. When that happens offline, redirect the
// navigation to the cached study shell instead of letting the browser show its
// generic offline error page. The Workbox route for `/estudar` then serves the
// shell from `medquest-study-shell`.
self.addEventListener("fetch", (rawEvent: Event) => {
  const event = rawEvent as FetchEvent;
  if (event.request.mode !== "navigate") return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname !== "/") return;

  event.respondWith(
    fetch(event.request).catch(() =>
      Response.redirect(new URL("/estudar", self.location.origin).href, 302)
    )
  );
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
