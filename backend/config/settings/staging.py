"""
Configurações de STAGING — AWS sem HTTPS ainda.
Usar enquanto não houver certificado SSL configurado.
"""
from .base import *  # noqa

# ── Debug desligado (comportamento de produção) ──
DEBUG = False

# ── CORS restrito para o IP do servidor ─────────
CORS_ALLOW_ALL_ORIGINS = False

# ── Sem forçar HTTPS (ainda não tem SSL) ─────────
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ── Segurança básica ─────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ── E-mails em produção ─────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ── Logs no terminal (docker logs) ──────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
