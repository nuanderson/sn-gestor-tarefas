"""
Configurações de PRODUÇÃO — Hostinger VPS.
Usadas no deploy final.
"""
from .base import *  # noqa

# ── Segurança ──────────────────────────────────
DEBUG = False

# ── CORS restrito para o domínio da SN ─────────
CORS_ALLOWED_ORIGINS = [
    # Adicionar o domínio real aqui no deploy
    # 'https://seudominio.com.br',
]

# ── Segurança HTTPS ────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ── E-mails em produção (AWS SES) ──────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.sa-east-1.amazonaws.com'  # ajustar região
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# EMAIL_HOST_USER e EMAIL_HOST_PASSWORD virão do .env de produção

# ── Cache (pode adicionar Redis futuramente) ───
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── Logs em arquivo no servidor ────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/app/logs/sn_gestor.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
}
