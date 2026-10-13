'use strict';
const CACHE = 'science-pencil-static-v2';
const CORE = ['./','index.html','style.css','app.js','questions.json','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png'];
function valid(response) { return response && response.ok && !response.redirected && response.type !== 'opaque'; }
self.addEventListener('install', event => event.waitUntil((async () => {
  const cache = await caches.open(CACHE);
  for (const url of CORE) {
    const response = await fetch(new URL(url,self.registration.scope),{cache:'reload'});
    if (!valid(response)) throw new Error('App shell unavailable');
    await cache.put(new URL(url,self.registration.scope),response);
  }
  await self.skipWaiting();
})()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url), scope = new URL(self.registration.scope);
  if (event.request.method !== 'GET' || url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  const relative = url.pathname.slice(scope.pathname.length);
  const isAsset = /^(questions|pages)\/\d{3}\.webp$/.test(relative) || CORE.includes(relative) || relative === '';
  if (!isAsset) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(event.request,{ignoreSearch:true});
    if (cached) return cached;
    const response = await fetch(event.request);
    if (valid(response)) await cache.put(event.request,response.clone());
    return response;
  })());
});
self.addEventListener('message', event => {
  if (event.data?.type !== 'cache-all' || !event.ports[0]) return;
  const port = event.ports[0];
  event.waitUntil((async () => {
    try {
      const urls = event.data.urls;
      if (!Array.isArray(urls) || urls.length > 600 || !urls.every(url => /^(questions|pages)\/\d{3}\.webp$/.test(url))) throw new Error('잘못된 파일 목록입니다.');
      const cache = await caches.open(CACHE); let current = 0;
      for (const path of urls) {
        const url = new URL(path,self.registration.scope);
        if (!await cache.match(url)) {
          const response = await fetch(url);
          if (!valid(response) || !response.headers.get('content-type')?.startsWith('image/')) throw new Error('문제를 저장하지 못했습니다. 로그인과 인터넷 연결을 확인하고 다시 시도하세요.');
          await cache.put(url,response);
        }
        port.postMessage({current:++current,total:urls.length});
      }
      port.postMessage({done:true});
    } catch (error) { port.postMessage({error:error.message}); }
  })());
});
