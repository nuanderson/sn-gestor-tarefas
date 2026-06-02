/**
 * SN Gestor v2.0 — API Client
 * Funções base para comunicação com o backend Django REST.
 */

// ── CSRF Token ──────────────────────────────────────────────────────────────
function getCsrf() {
  return document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith('csrftoken='))
    ?.split('=')[1] || '';
}

// ── Fetch base ───────────────────────────────────────────────────────────────
async function apiFetch(url, options = {}) {
  const defaults = {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrf(),
    },
    credentials: 'same-origin',
  };

  const config = {
    ...defaults,
    ...options,
    headers: { ...defaults.headers, ...(options.headers || {}) },
  };

  const res = await fetch(url, config);

  if (res.status === 401) {
    window.location.href = '/login/';
    return;
  }

  if (res.status === 204) return null;  // No content

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const erro = data?.detail || data?.erro || JSON.stringify(data) || `Erro ${res.status}`;
    throw new Error(erro);
  }

  return data;
}

// Atalhos HTTP
const api = {
  get:    (url, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(qs ? `${url}?${qs}` : url);
  },
  post:   (url, body) => apiFetch(url, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (url, body) => apiFetch(url, { method: 'PUT',    body: JSON.stringify(body) }),
  patch:  (url, body) => apiFetch(url, { method: 'PATCH',  body: JSON.stringify(body) }),
  delete: (url)       => apiFetch(url, { method: 'DELETE' }),
};

// ── Toast ────────────────────────────────────────────────────────────────────
function toast(msg, tipo = 'default', duracao = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const el = document.createElement('div');
  el.className = `toast toast-${tipo}`;

  const icones = {
    success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
    error:   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    default: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  };

  el.innerHTML = `${icones[tipo] || icones.default}<span>${msg}</span>`;
  container.appendChild(el);

  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(100%)';
    el.style.transition = '.3s ease';
    setTimeout(() => el.remove(), 300);
  }, duracao);
}

// ── Modal helpers ─────────────────────────────────────────────────────────────
function modalAbrir(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function modalFechar(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

// Fecha modal ao clicar no overlay
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// Fecha modal ao pressionar ESC
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open')
      .forEach(m => m.classList.remove('open'));
  }
});

// ── Utilitários ───────────────────────────────────────────────────────────────
function formatarData(iso) {
  if (!iso) return '—';
  const d = new Date(iso + (iso.includes('T') ? '' : 'T00:00:00'));
  return d.toLocaleDateString('pt-BR');
}

function formatarDataHora(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' });
}

function tempoRelativo(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60)   return 'agora mesmo';
  if (diff < 3600) return `há ${Math.floor(diff/60)} min`;
  if (diff < 86400) return `há ${Math.floor(diff/3600)}h`;
  const d = Math.floor(diff/86400);
  return `há ${d} dia${d > 1 ? 's' : ''}`;
}

function initiais(nome) {
  if (!nome) return 'SN';
  const p = nome.trim().split(' ');
  return p.length >= 2
    ? (p[0][0] + p[p.length-1][0]).toUpperCase()
    : nome.substring(0, 2).toUpperCase();
}

function badgeStatus(status) {
  const map = {
    done:     ['Concluída',    'badge-done'],
    pending:  ['Pendente',     'badge-pending'],
    progress: ['Em Andamento', 'badge-progress'],
    late:     ['Atrasada',     'badge-late'],
  };
  const [label, cls] = map[status] || [status, ''];
  return `<span class="badge ${cls}">${label}</span>`;
}

function badgePerfil(perfil) {
  const map = {
    admin:     ['Administrador', 'badge-admin'],
    manager:   ['Gestor',        'badge-manager'],
    analyst:   ['Analista',      'badge-analyst'],
    assistant: ['Assistente',    'badge-assistant'],
    client:    ['Cliente',       'badge-client'],
  };
  const [label, cls] = map[perfil] || [perfil, ''];
  return `<span class="badge ${cls}">${label}</span>`;
}

// ── Sidebar mobile toggle ─────────────────────────────────────────────────────
function toggleSidebar() {
  document.querySelector('.sn-sidebar')?.classList.toggle('open');
}

// ── Notificações ──────────────────────────────────────────────────────────────
let notifPanelAberto = false;

function toggleNotificacoes() {
  const panel = document.getElementById('notif-panel');
  if (!panel) return;
  notifPanelAberto = !notifPanelAberto;
  panel.classList.toggle('open', notifPanelAberto);
  if (notifPanelAberto) carregarNotificacoes();
}

async function carregarNotificacoes() {
  const lista = document.getElementById('notif-lista');
  const badge = document.getElementById('notif-badge');
  if (!lista) return;

  try {
    const data = await api.get('/api/v1/notificacoes/');

    // Atualiza badge
    if (badge) {
      badge.textContent = data.total_nao_lidas;
      badge.style.display = data.total_nao_lidas > 0 ? 'block' : 'none';
    }

    const dot = document.getElementById('notif-dot');
    if (dot) dot.style.display = data.total_nao_lidas > 0 ? 'block' : 'none';

    if (data.notificacoes.length === 0) {
      lista.innerHTML = '<div class="empty-state" style="padding:40px 20px;"><p>Nenhuma notificação.</p></div>';
      return;
    }

    lista.innerHTML = data.notificacoes.map(n => `
      <div class="notif-item ${n.lida ? '' : 'nao-lida'}" onclick="marcarLida(${n.id}, this)">
        <div class="notif-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
        </div>
        <div>
          <div class="notif-texto"><strong>${n.titulo}</strong><br>${n.mensagem}</div>
          <div class="notif-tempo">${tempoRelativo(n.criado_em)}</div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    lista.innerHTML = '<div style="padding:20px;color:var(--muted);font-size:13px;">Erro ao carregar notificações.</div>';
  }
}

async function marcarLida(id, el) {
  try {
    await api.patch(`/api/v1/notificacoes/${id}/lida/`);
    el.classList.remove('nao-lida');
    await carregarNotificacoes();
  } catch {}
}

async function marcarTodasLidas() {
  try {
    await api.post('/api/v1/notificacoes/todas-lidas/');
    await carregarNotificacoes();
    toast('Todas as notificações marcadas como lidas.', 'success');
  } catch {}
}

// Carrega contagem de notificações ao abrir qualquer página
document.addEventListener('DOMContentLoaded', () => {
  api.get('/api/v1/notificacoes/', { nao_lidas: 'true' })
    .then(data => {
      const dot   = document.getElementById('notif-dot');
      const badge = document.getElementById('notif-badge');
      if (dot)   dot.style.display   = data?.total_nao_lidas > 0 ? 'block' : 'none';
      if (badge) badge.textContent   = data?.total_nao_lidas || 0;
    })
    .catch(() => {});
});
