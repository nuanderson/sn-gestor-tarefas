from django.urls import path
from . import views

urlpatterns = [
    # OAuth flow (views HTML com redirect)
    path('contaazul/connect/<int:empresa_id>/', views.oauth_connect, name='contaazul-connect'),
    path('contaazul/callback/',                 views.oauth_callback, name='contaazul-callback'),

    # API REST
    path('api/v1/contaazul/sync/<int:empresa_id>/', views.sync_empresa,             name='contaazul-sync'),
    path('api/v1/contaazul/vencimentos/',            views.VencimentoListView.as_view(), name='contaazul-vencimentos'),
    path('api/v1/contaazul/status/',                     views.ConnectionStatusView.as_view(), name='contaazul-status'),
    path('api/v1/contaazul/status/<int:empresa_id>/',    views.status_empresa,                 name='contaazul-status-empresa'),
]
