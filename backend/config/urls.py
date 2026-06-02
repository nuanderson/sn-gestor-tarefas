"""URLs principais do SN Gestor."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import redirect

from apps.accounts.views import login_page


def health_check(request):
    return JsonResponse({
        'status': 'ok',
        'sistema': 'SN Gestor',
        'versao': '2.0',
    })


def home(request):
    """Redireciona para login se não autenticado."""
    if not request.user.is_authenticated:
        return redirect('/login/')
    # Dashboard será construído na Fase 5
    return JsonResponse({
        'mensagem': f'Olá, {request.user.primeiro_nome}! Sistema funcionando.',
        'usuario': request.user.email,
        'perfil': request.user.get_perfil_display(),
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('health/', health_check, name='health-check'),

    # Página de login (HTML)
    path('login/', login_page, name='login'),

    # Home (temporária — vira o dashboard na Fase 5)
    path('', home, name='home'),

    # API v1
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.companies.urls')),
    path('api/v1/', include('apps.tasks.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
