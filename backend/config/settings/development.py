"""
Configurações de DESENVOLVIMENTO.
Nunca usar em produção.
"""
from .base import *  # noqa

# ── Debug ──────────────────────────────────────
DEBUG = True

# ── Hosts permitidos em dev ────────────────────
ALLOWED_HOSTS = ['*']

# ── CORS liberado para desenvolvimento ─────────
CORS_ALLOW_ALL_ORIGINS = True

# ── E-mails no console (não envia de verdade) ──
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Toolbar e debug (opcional) ─────────────────
INSTALLED_APPS += []  # noqa — pode adicionar debug_toolbar aqui futuramente

# ── Logs no terminal ───────────────────────────
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
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # mude para DEBUG para ver todas as queries SQL
            'propagate': False,
        },
    },
}
