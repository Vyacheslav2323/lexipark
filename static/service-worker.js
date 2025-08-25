const CACHE_NAME = 'lexipark-cache-v2'
const CORE_ASSETS = [
  '/',
  '/static/css/theme.css'
]

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting())
  )
})

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.map(k => k !== CACHE_NAME ? caches.delete(k) : null))).then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', event => {
  const req = event.request
  if (req.method !== 'GET') return
  const accept = req.headers.get('accept') || ''
  const isHTML = accept.includes('text/html')
  if (isHTML) {
    return
  }
  event.respondWith(
    caches.match(req).then(cached => cached || fetch(req).then(res => {
      const copy = res.clone()
      caches.open(CACHE_NAME).then(cache => cache.put(req, copy)).catch(() => {})
      return res
    }).catch(() => cached))
  )
})


