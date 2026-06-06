from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('',                          views.login_redirect,        name='home'),
    path('dashboard/',                views.dashboard_individual,  name='dashboard-individual-page'),
    path('dashboard/geral/',          views.dashboard_geral,       name='dashboard-geral-page'),
    path('dashboard/colaboradores/',  views.colaboradores,         name='colaboradores-page'),

    # Tarefas
    path('tarefas/',                  views.tarefa_list,           name='tarefa-list'),
    path('tarefas/<int:pk>/',         views.tarefa_detalhe,        name='tarefa-detalhe'),

    # Empresas
    path('empresas/',                 views.empresa_list,          name='empresa-list'),
    path('empresas/<int:pk>/',        views.empresa_detalhe,       name='empresa-detalhe'),

    # Financeiro — Conta Azul
    path('financeiro/',              views.vencimentos_contaazul, name='financeiro-vencimentos'),

    # Post-its
    path('postits/',                  views.postit_quadro,         name='postit-list-page'),

    # Relatórios
    path('relatorios/',               views.relatorios,            name='relatorios-page'),

    # Usuários
    path('usuarios/',                 views.usuarios,              name='usuarios-page'),
    path('perfil/',                   views.perfil,                name='perfil-page'),

    # Portal do Cliente
    path('portal/',                   views.portal_dashboard,      name='portal-page'),
    path('portal/documentos/',        views.portal_documentos,     name='portal-documentos-page'),
    path('portal/pagamentos/',        views.portal_pagamentos,     name='portal-pagamentos-page'),
    path('portal/boletos/',           views.portal_boletos,        name='portal-boletos-page'),
]
