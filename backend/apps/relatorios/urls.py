from django.urls import path
from . import views

urlpatterns = [
    path('relatorios/tarefas/pdf/',       views.RelatorioTarefasPDFView.as_view(),      name='relatorio-tarefas-pdf'),
    path('relatorios/colaborador/pdf/',   views.RelatorioColaboradorPDFView.as_view(),   name='relatorio-colaborador-pdf'),
]
