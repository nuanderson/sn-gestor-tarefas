"""
Views do Frontend — servem as páginas HTML do sistema.
Toda view requer autenticação via login_required.
O JavaScript de cada página consome a API REST já existente.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


def login_redirect(request):
    """Redireciona para login, portal do cliente ou dashboard interno."""
    if request.user.is_authenticated:
        if request.user.is_cliente:
            return redirect('portal-page')
        return redirect('dashboard-individual-page')
    return redirect('login')


@login_required(login_url='/login/')
def dashboard_individual(request):
    return render(request, 'dashboard/individual.html')


@login_required(login_url='/login/')
def dashboard_geral(request):
    if not request.user.is_gestor_ou_acima:
        return redirect('dashboard-individual-page')
    return render(request, 'dashboard/geral.html')


@login_required(login_url='/login/')
def colaboradores(request):
    if not request.user.is_gestor_ou_acima:
        return redirect('dashboard-individual-page')
    return render(request, 'dashboard/colaboradores.html')


@login_required(login_url='/login/')
def tarefa_list(request):
    return render(request, 'tarefas/lista.html')


@login_required(login_url='/login/')
def tarefa_detalhe(request, pk):
    return render(request, 'tarefas/detalhe.html', {'tarefa_id': pk})


@login_required(login_url='/login/')
def empresa_list(request):
    return render(request, 'empresas/lista.html')


@login_required(login_url='/login/')
def empresa_detalhe(request, pk):
    return render(request, 'empresas/detalhe.html', {'empresa_id': pk})


@login_required(login_url='/login/')
def vencimentos_contaazul(request):
    if not request.user.is_gestor_ou_acima:
        return redirect('dashboard-individual-page')
    return render(request, 'financeiro/vencimentos.html')


@login_required(login_url='/login/')
def postit_quadro(request):
    return render(request, 'postits/quadro.html')


@login_required(login_url='/login/')
def relatorios(request):
    if not request.user.is_gestor_ou_acima:
        return redirect('dashboard-individual-page')
    return render(request, 'relatorios/index.html')


@login_required(login_url='/login/')
def usuarios(request):
    if not request.user.is_admin:
        return redirect('dashboard-individual-page')
    return render(request, 'usuarios/lista.html')


@login_required(login_url='/login/')
def perfil(request):
    return render(request, 'usuarios/perfil.html')


# ── Portal do Cliente ────────────────────────────────────────────────────────

def _requer_cliente(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    if not request.user.is_cliente:
        return redirect('dashboard-individual-page')
    return None


@login_required(login_url='/login/')
def portal_dashboard(request):
    if not request.user.is_cliente:
        return redirect('dashboard-individual-page')
    return render(request, 'portal/dashboard.html')


@login_required(login_url='/login/')
def portal_documentos(request):
    if not request.user.is_cliente:
        return redirect('dashboard-individual-page')
    return render(request, 'portal/documentos.html')


@login_required(login_url='/login/')
def portal_pagamentos(request):
    if not request.user.is_cliente:
        return redirect('dashboard-individual-page')
    return render(request, 'portal/pagamentos.html')


@login_required(login_url='/login/')
def portal_boletos(request):
    if not request.user.is_cliente:
        return redirect('dashboard-individual-page')
    return render(request, 'portal/boletos.html')
