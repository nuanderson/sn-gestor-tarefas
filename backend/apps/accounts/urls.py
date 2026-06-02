"""URLs do módulo de autenticação e usuários."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('usuarios', views.UsuarioViewSet, basename='usuario')

urlpatterns = [
    # ── Autenticação ─────────────────────────
    path('auth/login/',  views.LoginAPIView.as_view(),   name='api-login'),
    path('auth/logout/', views.LogoutAPIView.as_view(),  name='api-logout'),
    path('auth/me/',     views.MeAPIView.as_view(),      name='api-me'),
    path('auth/senha/',  views.AlterarSenhaAPIView.as_view(), name='api-senha'),

    # ── CRUD de usuários ─────────────────────
    path('', include(router.urls)),
]
