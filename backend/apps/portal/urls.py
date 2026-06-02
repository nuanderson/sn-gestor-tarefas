from django.urls import path
from . import views

urlpatterns = [
    path('portal/resumo/',      views.PortalResumoView.as_view(),      name='portal-resumo'),
    path('portal/documentos/',  views.DocumentoListCreateView.as_view(), name='portal-documentos'),
    path('portal/documentos/<int:pk>/', views.DocumentoDetalheView.as_view(), name='portal-documento-detalhe'),
    path('portal/pagamentos/',  views.PortalPagamentosView.as_view(),   name='portal-pagamentos'),
    path('portal/boletos/',          views.BoletoListCreateView.as_view(), name='portal-boletos'),
    path('portal/boletos/<int:pk>/', views.BoletoDetalheView.as_view(),   name='portal-boleto-detalhe'),
    path('portal/recorrencia/',      views.RecorrenciaView.as_view(),      name='portal-recorrencia'),
]
