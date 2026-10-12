// Refugee Radar v3.0 - Maritime Offline Service Worker
// Cache-First for static assets; Network-First with offline fallback for live telemetry

const CACHE_NAME = 'refugee-radar-v3.0.0';
const STATIC_ASSETS = [
  './',
  './index.html',
  './live_state.json',
  'https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js',
  'https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching maritime core assets...');
      return cache.addAll(STATIC_ASSETS).catch(err => console.warn('[SW] Cache addAll warning:', err));
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Purging legacy cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Strategy 1: Map tiles - Cache first with network fallback
  if (url.hostname.includes('tile.openstreetmap') || url.hostname.includes('openstreetmap.fr')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((res) => {
          if (!res || res.status !== 200) return res;
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return res;
        }).catch(() => cached || new Response('', { status: 408 }));
      })
    );
    return;
  }

  // Strategy 2: Live Telemetry State - Network first with cache fallback
  if (url.pathname.endsWith('live_state.json')) {
    event.respondWith(
      fetch(event.request).then((res) => {
        if (res && res.status === 200) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return res;
      }).catch(() => caches.match(event.request))
    );
    return;
  }

  // Strategy 3: Standard Navigation & Assets - Cache first with network fallback
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((res) => {
        if (event.request.method === 'GET' && res && res.status === 200 && url.origin === self.origin) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return res;
      });
    }).catch(() => caches.match('./index.html'))
  );
});
