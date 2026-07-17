"use strict";
const CACHE_NAME = "tt-v34";
const CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js";
const APP_SHELL = [
  "./",
  "./index.html",
  "./css/styles.css",
  "./js/app.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-512-maskable.png",
  "./icons/apple-touch-icon.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      cache.addAll(APP_SHELL)
        // Chart.js is cross-origin: cache it best-effort so a blocked CDN
        // can't abort the whole install and cost us local offline support.
        .then(() => cache.add(CHART_JS_URL).catch(() => {}))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(names => Promise.all(names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

// Cache-first is only safe for the versioned app shell (invalidated by the
// CACHE_NAME bump). Anything else — future sync/API calls included — goes
// straight to the network untouched.
function isShellRequest(request){
  if (request.url === CHART_JS_URL) return true;
  const url = new URL(request.url);
  return url.origin === self.location.origin;
}

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET" || !isShellRequest(event.request)) return;
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        }
        return response;
      }).catch(() => {
        if (event.request.mode === "navigate") return caches.match("./index.html");
      });
    })
  );
});
