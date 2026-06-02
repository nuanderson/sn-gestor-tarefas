"""
Views de Relatórios em PDF — Fase 5.

Endpoints:
  GET /api/v1/relatorios/tarefas/pdf/   → PDF de tarefas filtrado
  GET /api/v1/relatorios/colaborador/pdf/ → PDF de produtividade por colaborador

Parâmetros (query string):
  data_inicio, data_fim    → filtro de período (formato: YYYY-MM-DD)
  empresa_id               → filtrar por empresa
  colaborador_id           → filtrar por colaborador
  status                   → filtrar por status (done, pending, progress, late)
"""
import io
from datetime import date, datetime

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Count, Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

try:
    import weasyprint
    WEASYPRINT_DISPONIVEL = True
except ImportError:
    WEASYPRINT_DISPONIVEL = False

from apps.tasks.models import Tarefa, SessaoTarefa
from apps.accounts.models import Usuario
from apps.companies.models import Empresa
from apps.accounts.permissions import IsGestorOuAcima


def _parse_date(valor, padrao=None):
    if not valor:
        return padrao
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return padrao


class RelatorioTarefasPDFView(APIView):
    """
    Gera PDF com lista de tarefas filtrada.
    Apenas Admin e Gestores.
    """
    permission_classes = [IsGestorOuAcima]

    def get(self, request):
        if not WEASYPRINT_DISPONIVEL:
            return Response(
                {'erro': 'WeasyPrint não está instalado no servidor.'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        hoje = date.today()
        data_inicio    = _parse_date(request.query_params.get('data_inicio'), date(hoje.year, hoje.month, 1))
        data_fim       = _parse_date(request.query_params.get('data_fim'), hoje)
        empresa_id     = request.query_params.get('empresa_id')
        colaborador_id = request.query_params.get('colaborador_id')
        status_filtro  = request.query_params.get('status')

        qs = Tarefa.objects.select_related('empresa', 'responsavel').order_by('prazo', 'empresa__nome')

        # Filtros de período: usa criado_em quando não há prazo definido
        qs = qs.filter(
            Q(prazo__gte=data_inicio) | Q(prazo__isnull=True, criado_em__date__gte=data_inicio)
        ).filter(
            Q(prazo__lte=data_fim) | Q(prazo__isnull=True, criado_em__date__lte=data_fim)
        )

        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        if colaborador_id:
            qs = qs.filter(responsavel_id=colaborador_id)
        if status_filtro:
            qs = qs.filter(status=status_filtro)

        empresa_nome = None
        if empresa_id:
            try:
                empresa_nome = Empresa.objects.get(pk=empresa_id).nome
            except Empresa.DoesNotExist:
                pass

        colaborador_nome = None
        if colaborador_id:
            try:
                colaborador_nome = Usuario.objects.get(pk=colaborador_id).nome
            except Usuario.DoesNotExist:
                pass

        context = {
            'tarefas': qs,
            'total': qs.count(),
            'concluidas': qs.filter(status='done').count(),
            'atrasadas': qs.filter(status='late').count() + qs.filter(
                status__in=['pending', 'progress'], prazo__lt=hoje
            ).count(),
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'empresa_nome': empresa_nome,
            'colaborador_nome': colaborador_nome,
            'gerado_em': datetime.now(),
            'gerado_por': request.user.nome,
        }

        html = render_to_string('relatorios/relatorio_tarefas.html', context)
        pdf_file = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="relatorio_tarefas_{data_inicio}_{data_fim}.pdf"'
        )
        return response


class RelatorioColaboradorPDFView(APIView):
    """
    Gera PDF de produtividade por colaborador no mês.
    Apenas Admin e Gestores.
    Parâmetros: ?mes=6&ano=2026&colaborador_id=X
    """
    permission_classes = [IsGestorOuAcima]

    def get(self, request):
        if not WEASYPRINT_DISPONIVEL:
            return Response(
                {'erro': 'WeasyPrint não está instalado no servidor.'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        hoje = date.today()
        mes  = int(request.query_params.get('mes', hoje.month))
        ano  = int(request.query_params.get('ano', hoje.year))

        inicio = date(ano, mes, 1)
        fim    = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)

        colaborador_id = request.query_params.get('colaborador_id')

        if colaborador_id:
            colaboradores = Usuario.objects.filter(pk=colaborador_id)
        else:
            colaboradores = Usuario.objects.filter(
                perfil__in=['analyst', 'assistant', 'manager'],
                is_active=True,
            ).order_by('nome')

        dados_colaboradores = []
        for colab in colaboradores:
            concluidas = Tarefa.objects.filter(
                responsavel=colab,
                status='done',
                concluida_em__date__gte=inicio,
                concluida_em__date__lt=fim,
            ).count()

            minutos = SessaoTarefa.objects.filter(
                usuario=colab,
                status='finalizada',
                iniciado_em__date__gte=inicio,
                iniciado_em__date__lt=fim,
            ).aggregate(total=Sum('duracao_minutos'))['total'] or 0

            tarefas_colab = Tarefa.objects.filter(
                responsavel=colab,
                status='done',
                concluida_em__date__gte=inicio,
                concluida_em__date__lt=fim,
            ).select_related('empresa').order_by('concluida_em')

            dados_colaboradores.append({
                'colaborador': colab,
                'tarefas_concluidas': concluidas,
                'horas_trabalhadas': round(minutos / 60, 1),
                'minutos_trabalhados': minutos,
                'tarefas': tarefas_colab,
            })

        meses_pt = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
        ]
        context = {
            'dados_colaboradores': dados_colaboradores,
            'mes_nome': meses_pt[mes],
            'mes': mes,
            'ano': ano,
            'gerado_em': datetime.now(),
            'gerado_por': request.user.nome,
        }

        html = render_to_string('relatorios/relatorio_colaborador.html', context)
        pdf_file = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="relatorio_colaboradores_{mes:02d}_{ano}.pdf"'
        )
        return response
