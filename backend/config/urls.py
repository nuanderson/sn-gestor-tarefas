"""URLs principais do SN Gestor."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

from apps.accounts.views import login_page


def health_check(request):
    return JsonResponse({'status': 'ok', 'sistema': 'SN Gestor', 'versao': '2.0'})


urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Health check
    path('health/', health_check, name='health-check'),

    # Login
    path('login/', login_page, name='login'),

    # Frontend — páginas HTML (inclui a rota raiz '/')
    path('', include('apps.frontend.urls')),

    # API v1
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.companies.urls')),
    path('api/v1/', include('apps.tasks.urls')),
    path('api/v1/', include('apps.dashboard.urls')),
    path('api/v1/', include('apps.relatorios.urls')),
    path('api/v1/', include('apps.postits.urls')),
    path('api/v1/', include('apps.portal.urls')),

    # Conta Azul — OAuth + API
    path('', include('apps.contaazul.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
