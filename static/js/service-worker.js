const CACHE_NAME = 'eat-nearby-v1';
const urlsToCache = [
    '/',
    '/static/css/output.css',
    '/static/css/style.css',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    '/static/manifest.json'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});