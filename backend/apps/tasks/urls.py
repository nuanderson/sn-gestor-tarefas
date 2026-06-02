from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TagViewSet, TarefaViewSet
from .views_timer import TimerView, ProdutividadeView
from .views_notificacoes import (
    NotificacaoListView, NotificacaoDetalheView, MarcarTodasLidasView
)

router = DefaultRouter()
router.register('tags',    TagViewSet,    basename='tag')
router.register('tarefas', TarefaViewSet, basename='tarefa')

urlpatterns = [
    path('', include(router.urls)),

    # ── Timer ────────────────────────────────────
    path('tarefas/<int:pk>/timer/',           TimerView.as_view(),               name='timer'),
    path('tarefas/<int:pk>/timer/iniciar/',   TimerView.as_view(),               name='timer-iniciar',   kwargs={'acao': 'iniciar'}),
    path('tarefas/<int:pk>/timer/pausar/',    TimerView.as_view(),               name='timer-pausar',    kwargs={'acao': 'pausar'}),
    path('tarefas/<int:pk>/timer/retomar/',   TimerView.as_view(),               name='timer-retomar',   kwargs={'acao': 'retomar'}),
    path('tarefas/<int:pk>/timer/finalizar/', TimerView.as_view(),               name='timer-finalizar', kwargs={'acao': 'finalizar'}),

    # ── Produtividade ─────────────────────────────
    path('usuarios/<int:usuario_id>/produtividade/', ProdutividadeView.as_view(), name='produtividade'),

    # ── Notificações ──────────────────────────────
    path('notificacoes/',                  NotificacaoListView.as_view(),    name='notificacoes'),
    path('notificacoes/todas-lidas/',      MarcarTodasLidasView.as_view(),   name='notificacoes-todas-lidas'),
    path('notificacoes/<int:pk>/',         NotificacaoDetalheView.as_view(), name='notificacao-detalhe'),
    path('notificacoes/<int:pk>/lida/',    NotificacaoDetalheView.as_view(), name='notificacao-lida'),
]
