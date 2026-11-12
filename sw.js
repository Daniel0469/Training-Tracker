"use strict";
const VERSION = "2.2.0";
const CACHE_NAME = "tt-" + VERSION;
const CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js";
const SUPABASE_JS_URL = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.3/dist/umd/supabase.js";
const QR_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js";
const APP_SHELL = [
  "./",
  "./index.html",
  "./css/styles.css",
  "./js/family.js",
  "./js/app.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-512-maskable.png",
  "./icons/apple-touch-icon.png",
  "./fonts/manrope-latin-wght.woff2",
  "./fonts/jetbrains-mono-latin-wght.woff2"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      cache.addAll(APP_SHELL)
        // Chart.js, supabase-js and the QR library are cross-origin: cache them best-effort so a blocked CDN
        // can't abort the whole install and cost us local offline support.
        .then(() => cache.add(CHART_JS_URL).catch(() => {}))
        .then(() => cache.add(SUPABASE_JS_URL).catch(() => {}))
        .then(() => cache.add(QR_JS_URL).catch(() => {}))
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
// VERSION bump). Anything else - future sync/API calls included - goes
// straight to the network untouched.
function isShellRequest(request){
  if (request.url === CHART_JS_URL || request.url === SUPABASE_JS_URL || request.url === QR_JS_URL) return true;
  const url = new URL(request.url);
  return url.origin === self.location.origin;
}

// A request that gets no answer must still settle, or the page waits on it forever (the storage
// library script is the one that matters: the Connect button waits on it).
const NETWORK_TIMEOUT_MS = 10000;
function fetchWithTimeout(request){
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout")), NETWORK_TIMEOUT_MS);
    fetch(request).then(resolve, reject).finally(() => clearTimeout(timer));
  });
}

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET" || !isShellRequest(event.request)) return;
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetchWithTimeout(event.request).then(response => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        }
        return response;
      }).catch(() => Promise.resolve(event.request.mode === "navigate" ? caches.match("./index.html") : null).then(page => page || Response.error()));
    })
  );
});
