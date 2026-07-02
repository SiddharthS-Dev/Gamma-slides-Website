// SlideVault Service Worker
// Strategies:
//   Static assets  → Cache-First (versioned by Vite content hash)
//   API metadata   → Network-First, fall back to IndexedDB (handled in app)
//   Thumbnails     → Stale-While-Revalidate

const CACHE_VERSION = 'slidevault-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const THUMB_CACHE = `${CACHE_VERSION}-thumbs`;

const STATIC_EXTENSIONS = ['.js', '.css', '.woff2', '.png', '.svg', '.ico'];

// ── Install: pre-cache shell ─────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) =>
      cache.addAll(['/', '/index.html'])
    ).then(() => self.skipWaiting())
  );
});

// ── Activate: clean old caches ───────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k.startsWith('slidevault-') && k !== STATIC_CACHE && k !== THUMB_CACHE)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch ────────────────────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin requests
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  // API calls → Network-First (app handles IndexedDB fallback)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Thumbnails → Stale-While-Revalidate
  if (url.pathname.startsWith('/storage/thumbnails/') || url.pathname.startsWith('/files/')) {
    event.respondWith(staleWhileRevalidate(request, THUMB_CACHE));
    return;
  }

  // Static assets (JS/CSS/fonts) → Cache-First
  const isStatic = STATIC_EXTENSIONS.some((ext) => url.pathname.endsWith(ext));
  if (isStatic) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // HTML / SPA routes → Network-First with cache fallback
  event.respondWith(networkFirst(request));
});

// ── Strategies ───────────────────────────────────────────────────────────────
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response('Offline', { status: 503 });
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) cache.put(request, response.clone());
    return response;
  }).catch(() => null);
  return cached || fetchPromise;
}
