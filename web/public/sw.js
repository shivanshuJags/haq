// Haq service worker: makes the app installable and lets the app shell open even on a flaky connection.
// API calls are never cached — eligibility answers must always be fresh, and the profile is never stored.
const CACHE = 'haq-shell-v1'

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(['/', '/manifest.webmanifest'])))
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  // Remove caches from older versions of the app
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))),
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  // Only same-origin GETs of the app itself; the API lives on another origin anyway
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    // Pages: network first (always the latest version), fall back to the cached shell when offline
    event.respondWith(fetch(request).catch(() => caches.match('/')))
    return
  }
  // Built assets have content hashes in their names, so cache-first is safe
  event.respondWith(
    caches.match(request).then(
      (cached) =>
        cached ||
        fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone()
            caches.open(CACHE).then((cache) => cache.put(request, copy))
          }
          return response
        }),
    ),
  )
})
