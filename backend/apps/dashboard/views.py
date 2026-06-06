"""
Views do Dashboard — Fase 5.

Endpoints:
  GET /api/v1/dashboard/geral/        → visão consolidada (Admin/Gestor)
  GET /api/v1/dashboard/individual/   → visão pessoal de qualquer usuário
  GET /api/v1/dashboard/colaboradores/→ resumo de todos os colaboradores com metas (Admin/Gestor)
  GET/POST /api/v1/dashboard/metas/   → CRUD de metas mensais
  GET/PUT/DELETE /api/v1/dashboard/metas/<id>/
"""
from datetime import date

from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsGestorOuAcima
from apps.tasks.models import Tarefa, SessaoTarefa
from apps.accounts.models import Usuario
from .models import MetaMensal
from .serializers import MetaMensalSerializer


def _resumo_tarefas_usuario(usuario, mes, ano):
    """Calcula métricas de tarefas de um usuário em um mês/ano."""
    inicio = date(ano, mes, 1)
    # último dia do mês
    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)

    qs = Tarefa.objects.filter(responsavel=usuario)

    concluidas_mes = qs.filter(
        status='done',
        concluida_em__date__gte=inicio,
        concluida_em__date__lt=fim,
    ).count()

    atrasadas = qs.filter(status='late').count()
    atrasadas += qs.filter(
        status__in=['pending', 'progress'],
        prazo__lt=date.today(),
    ).count()

    em_aberto = qs.filter(status__in=['pending', 'progress']).count()

    # Tempo registrado no mês (minutos → horas)
    minutos_mes = SessaoTarefa.objects.filter(
        usuario=usuario,
        status='finalizada',
        iniciado_em__date__gte=inicio,
        iniciado_em__date__lt=fim,
    ).aggregate(total=Sum('duracao_minutos'))['total'] or 0

    horas_mes = round(minutos_mes / 60, 1)

    # Tempo hoje
    hoje = date.today()
    minutos_hoje = SessaoTarefa.objects.filter(
        usuario=usuario,
        status='finalizada',
        iniciado_em__date=hoje,
    ).aggregate(total=Sum('duracao_minutos'))['total'] or 0
    horas_hoje = round(minutos_hoje / 60, 1)

    return {
        'tarefas_concluidas_mes': concluidas_mes,
        'tarefas_em_aberto': em_aberto,
        'tarefas_atrasadas': atrasadas,
        'horas_registradas_mes': horas_mes,
        'horas_registradas_hoje': horas_hoje,
    }


class DashboardGeralView(APIView):
    """
    Visão consolidada da operação. Apenas Admin e Gestores.
    Parâmetros opcionais: ?mes=6&ano=2026
    """
    permission_classes = [IsGestorOuAcima]

    def get(self, request):
        hoje = date.today()
        mes = int(request.query_params.get('mes', hoje.month))
        ano = int(request.query_params.get('ano', hoje.year))

        todas = Tarefa.objects.all()

        # ── Totais por status ────────────────────────
        por_status = (
            todas
            .values('status')
            .annotate(total=Count('id'))
            .order_by('status')
        )
        status_map = {item['status']: item['total'] for item in por_status}

        # ── Tarefas atrasadas (status late + pending/progress com prazo vencido) ──
        atrasadas_count = (
            todas.filter(status='late').count()
            + todas.filter(
                status__in=['pending', 'progress'],
                prazo__lt=hoje,
            ).count()
        )

        # ── Por categoria ────────────────────────────
        por_categoria = (
            todas
            .exclude(categoria='')
            .values('categoria')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        # ── Por empresa (top 10) ─────────────────────
        por_empresa = (
            todas
            .values('empresa__id', 'empresa__nome')
            .annotate(total=Count('id'), concluidas=Count('id', filter=Q(status='done')))
            .order_by('-total')[:10]
        )

        # ── Concluídas no mês ────────────────────────
        if mes == 12:
            prox = date(ano + 1, 1, 1)
        else:
            prox = date(ano, mes + 1, 1)
        inicio_mes = date(ano, mes, 1)

        concluidas_mes = todas.filter(
            status='done',
            concluida_em__date__gte=inicio_mes,
            concluida_em__date__lt=prox,
        ).count()

        # ── Horas registradas no mês ─────────────────
        minutos_mes = SessaoTarefa.objects.filter(
            status='finalizada',
            iniciado_em__date__gte=inicio_mes,
            iniciado_em__date__lt=prox,
        ).aggregate(total=Sum('duracao_minutos'))['total'] or 0
        horas_mes = round(minutos_mes / 60, 1)

        # ── Tempo por colaborador no mês ─────────────
        tempo_por_colaborador = (
            SessaoTarefa.objects.filter(
                status='finalizada',
                iniciado_em__date__gte=inicio_mes,
                iniciado_em__date__lt=prox,
            )
            .values('usuario__id', 'usuario__nome')
            .annotate(total_minutos=Sum('duracao_minutos'))
            .order_by('-total_minutos')
        )

        return Response({
            'periodo': {'mes': mes, 'ano': ano},
            'resumo': {
                'total_tarefas': todas.count(),
                'pendentes': status_map.get('pending', 0),
                'em_andamento': status_map.get('progress', 0),
                'concluidas': status_map.get('done', 0),
                'atrasadas': atrasadas_count,
                'concluidas_no_mes': concluidas_mes,
                'horas_registradas_no_mes': horas_mes,
            },
            'por_categoria': list(por_categoria),
            'por_empresa': list(por_empresa),
            'tempo_por_colaborador': [
                {
                    'usuario_id': item['usuario__id'],
                    'nome': item['usuario__nome'],
                    'horas': round((item['total_minutos'] or 0) / 60, 1),
                    'minutos': item['total_minutos'] or 0,
                }
                for item in tempo_por_colaborador
            ],
        })


class DashboardIndividualView(APIView):
    """
    Visão pessoal do colaborador logado.
    Admin/Gestor pode consultar outro usuário via ?usuario_id=X.
    Parâmetros: ?mes=6&ano=2026&usuario_id=X
    """

    def get(self, request):
        hoje = date.today()
        mes = int(request.query_params.get('mes', hoje.month))
        ano = int(request.query_params.get('ano', hoje.year))

        usuario_id = request.query_params.get('usuario_id')
        if usuario_id and request.user.is_gestor_ou_acima:
            try:
                usuario = Usuario.objects.get(pk=usuario_id)
            except Usuario.DoesNotExist:
                return Response({'erro': 'Usuário não encontrado.'}, status=404)
        else:
            usuario = request.user

        metricas = _resumo_tarefas_usuario(usuario, mes, ano)

        # Busca meta do mês se existir
        meta = None
        try:
            meta_obj = MetaMensal.objects.get(colaborador=usuario, mes=mes, ano=ano)
            meta = {
                'meta_tarefas': meta_obj.meta_tarefas,
                'meta_horas': meta_obj.meta_horas,
                'progresso_tarefas_pct': (
                    round(metricas['tarefas_concluidas_mes'] / meta_obj.meta_tarefas * 100)
                    if meta_obj.meta_tarefas else None
                ),
                'progresso_horas_pct': (
                    round(metricas['horas_registradas_mes'] / meta_obj.meta_horas * 100)
                    if meta_obj.meta_horas else None
                ),
            }
        except MetaMensal.DoesNotExist:
            pass

        # Últimas 5 tarefas concluídas
        ultimas_concluidas = (
            Tarefa.objects.filter(responsavel=usuario, status='done')
            .order_by('-concluida_em')
            .values('id', 'titulo', 'empresa__nome', 'concluida_em')[:5]
        )

        # Próximas tarefas com prazo
        proximas = (
            Tarefa.objects.filter(
                responsavel=usuario,
                status__in=['pending', 'progress'],
                prazo__isnull=False,
            )
            .order_by('prazo')
            .values('id', 'titulo', 'empresa__nome', 'prazo', 'prioridade', 'status')[:5]
        )

        return Response({
            'usuario': {
                'id': usuario.id,
                'nome': usuario.nome,
                'iniciais': usuario.iniciais,
                'perfil': usuario.get_perfil_display(),
            },
            'periodo': {'mes': mes, 'ano': ano},
            'metricas': metricas,
            'meta': meta,
            'ultimas_concluidas': list(ultimas_concluidas),
            'proximas_tarefas': list(proximas),
        })


class DashboardColaboradoresView(APIView):
    """
    Resumo de todos os colaboradores ativos com suas metas no mês.
    Apenas Admin e Gestores.
    Parâmetros: ?mes=6&ano=2026
    """
    permission_classes = [IsGestorOuAcima]

    def get(self, request):
        hoje = date.today()
        mes = int(request.query_params.get('mes', hoje.month))
        ano = int(request.query_params.get('ano', hoje.year))

        colaboradores = Usuario.objects.filter(
            perfil__in=['analyst', 'assistant', 'manager'],
            is_active=True,
        ).order_by('nome')

        resultado = []
        for colab in colaboradores:
            metricas = _resumo_tarefas_usuario(colab, mes, ano)
            meta_obj = MetaMensal.objects.filter(
                colaborador=colab, mes=mes, ano=ano
            ).first()

            item = {
                'id': colab.id,
                'nome': colab.nome,
                'iniciais': colab.iniciais,
                'perfil': colab.get_perfil_display(),
                **metricas,
                'meta_tarefas': meta_obj.meta_tarefas if meta_obj else None,
                'meta_horas': meta_obj.meta_horas if meta_obj else None,
            }
            if meta_obj and meta_obj.meta_tarefas:
                item['progresso_tarefas_pct'] = round(
                    metricas['tarefas_concluidas_mes'] / meta_obj.meta_tarefas * 100
                )
            if meta_obj and meta_obj.meta_horas:
                item['progresso_horas_pct'] = round(
                    metricas['horas_registradas_mes'] / meta_obj.meta_horas * 100
                )
            resultado.append(item)

        return Response({'periodo': {'mes': mes, 'ano': ano}, 'colaboradores': resultado})


# ── Evolução mensal — últimos 6 meses ────────────────────────────────────────

class DashboardEvolucaoView(APIView):
    """
    GET /api/v1/dashboard/evolucao/
    Retorna concluídas e atrasadas dos últimos 6 meses para o gráfico de linha.
    """
    permission_classes = [IsGestorOuAcima]

    def get(self, request):
        from dateutil.relativedelta import relativedelta
        hoje = date.today()
        meses_pt = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

        labels, concluidas_data, atrasadas_data = [], [], []

        for i in range(5, -1, -1):
            ref = hoje - relativedelta(months=i)
            inicio = date(ref.year, ref.month, 1)
            if ref.month == 12:
                fim = date(ref.year + 1, 1, 1)
            else:
                fim = date(ref.year, ref.month + 1, 1)

            concluidas = Tarefa.objects.filter(
                status='done',
                concluida_em__date__gte=inicio,
                concluida_em__date__lt=fim,
            ).count()

            atrasadas = Tarefa.objects.filter(
                prazo__gte=inicio,
                prazo__lt=fim,
            ).filter(
                Q(status='late') | Q(status__in=['pending','progress'], prazo__lt=hoje)
            ).count()

            labels.append(f"{meses_pt[ref.month - 1]}/{str(ref.year)[2:]}")
            concluidas_data.append(concluidas)
            atrasadas_data.append(atrasadas)

        return Response({
            'labels': labels,
            'concluidas': concluidas_data,
            'atrasadas': atrasadas_data,
        })


# ── CRUD de Metas Mensais ─────────────────────────────────────────────────────

class MetaMensalListCreateView(generics.ListCreateAPIView):
    serializer_class   = MetaMensalSerializer
    permission_classes = [IsGestorOuAcima]

    def get_queryset(self):
        qs = MetaMensal.objects.select_related('colaborador', 'criado_por')
        mes = self.request.query_params.get('mes')
        ano = self.request.query_params.get('ano')
        colaborador_id = self.request.query_params.get('colaborador_id')
        if mes:
            qs = qs.filter(mes=mes)
        if ano:
            qs = qs.filter(ano=ano)
        if colaborador_id:
            qs = qs.filter(colaborador_id=colaborador_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)


class MetaMensalDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = MetaMensal.objects.select_related('colaborador', 'criado_por')
    serializer_class   = MetaMensalSerializer
    permission_classes = [IsGestorOuAcima]
