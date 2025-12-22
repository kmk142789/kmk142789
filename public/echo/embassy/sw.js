const CACHE_NAME = 'echo-embassy-cache-v2';
const ASSETS = [
  './',
  './index.html',
  './embassy.css',
  './embassy.js',
  'https://aframe.io/releases/1.5.0/aframe.min.js',
  'https://cdn.aframe.io/360-image-gallery-boilerplate/img/sechelt.jpg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
          return null;
        })
      )
    )
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
