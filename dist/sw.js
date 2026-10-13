'use strict';
// Self-unregistering cleanup worker for root portal scope
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    // Delete legacy root caches
    const keys = await caches.keys();
    for (const key of keys) {
      if (key.includes('science-pencil-static-v1') || key === 'science-pencil-v1') {
        try { await caches.delete(key); } catch (e) {}
      }
    }
    // Unregister root scope service worker
    try {
      await self.registration.unregister();
    } catch (e) {}
    // Claim and reload active window clients
    try {
      const clients = await self.clients.matchAll({ type: 'window' });
      for (const client of clients) {
        client.navigate(client.url);
      }
    } catch (e) {}
  })());
});
