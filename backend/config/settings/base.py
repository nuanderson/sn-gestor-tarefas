"""
Configurações base do SN Gestor.
Compartilhadas entre desenvolvimento e produção.
"""
from pathlib import Path
from decouple import config

# ── Diretório raiz do projeto ──────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Segurança ──────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# ── Aplicações instaladas ──────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.companies',
    'apps.tasks',
    'apps.dashboard',
    'apps.relatorios',
    'apps.postits',
    'apps.portal',
    'apps.frontend',
    'apps.contaazul',
]

# ── Login URL ──────────────────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middlewares ────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ── URLs ───────────────────────────────────────
ROOT_URLCONF = 'config.urls'

# ── Templates ─────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ── Banco de Dados ─────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST', default='db'),
        'PORT': config('POSTGRES_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ── Validação de senhas ────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Idioma e Fuso Horário ──────────────────────
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = config('TIME_ZONE', default='America/Sao_Paulo')
USE_I18N = True
USE_TZ = True

# ── Arquivos estáticos ─────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# ── Arquivos de mídia (uploads) ────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Modelo de usuário customizado ─────────────
AUTH_USER_MODEL = 'accounts.Usuario'

# ── Chave padrão para modelos ──────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── E-mail ─────────────────────────────────────
EMAIL_BACKEND   = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST      = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT      = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS   = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default='SN Gestor <noreply@sngestor.com.br>')

# ── Conta Azul OAuth 2.0 ──────────────────────
CONTAAZUL_CLIENT_ID     = config('CONTAAZUL_CLIENT_ID', default='')
CONTAAZUL_CLIENT_SECRET = config('CONTAAZUL_CLIENT_SECRET', default='')
CONTAAZUL_REDIRECT_URI  = config('CONTAAZUL_REDIRECT_URI', default='http://localhost/contaazul/callback/')

# ── Django REST Framework ──────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%d/%m/%Y %H:%M',
    'DATE_FORMAT': 'iso-8601',
}
