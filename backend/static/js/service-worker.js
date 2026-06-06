const CACHE_NAME = 'sn-gestor-v1';

// Arquivos essenciais para funcionar offline
const CACHE_STATIC = [
  '/',
  '/dashboard/',
  '/tarefas/',
  '/static/css/sn-gestor.css',
  '/static/js/api.js',
  '/static/img/logo-sn.png',
  '/static/img/icons/icon-192x192.png',
  '/static/img/icons/icon-512x512.png',
  '/static/manifest.json',
];

// ── Instalação: faz cache dos arquivos estáticos ──────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[SW] Cache inicial criado');
      return cache.addAll(CACHE_STATIC);
    }).then(() => self.skipWaiting())
  );
});

// ── Ativação: remove caches antigos ──────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => {
          console.log('[SW] Removendo cache antigo:', k);
          return caches.delete(k);
        })
      )
    ).then(() => self.clients.claim())
  );
});

// ── Interceptação de requisições ─────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Requisições da API: sempre vai para a rede (não faz cache)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ erro: 'Sem conexão com a internet.' }), {
          headers: { 'Content-Type': 'application/json' },
          status: 503,
        })
      )
    );
    return;
  }

  // Arquivos estáticos: cache primeiro, rede como fallback
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      }))
    );
    return;
  }

  // Páginas HTML: rede primeiro, cache como fallback (mostra offline page)
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request).then(cached => {
        if (cached) return cached;
        // Fallback genérico para páginas não cacheadas
        return caches.match('/dashboard/');
      }))
  );
});

// ── Notificações Push ────────────────────────────────────────────────────────
self.addEventListener('push', event => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body:    data.body    || 'Você tem uma nova notificação.',
    icon:    data.icon    || '/static/img/icons/icon-192x192.png',
    badge:   data.badge   || '/static/img/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data:    { url: data.url || '/dashboard/' },
    actions: [
      { action: 'abrir',   title: 'Abrir' },
      { action: 'fechar',  title: 'Fechar' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'SN Gestor', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'fechar') return;

  const url = event.notification.data?.url || '/dashboard/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url.includes(url) && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
