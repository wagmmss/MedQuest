export {};

interface ExtendableEvent extends Event {
  waitUntil(fn: Promise<unknown>): void;
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
