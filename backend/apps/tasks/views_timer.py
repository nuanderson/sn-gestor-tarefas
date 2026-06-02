"""
Views do Timer de Produtividade.
Controla sessões de trabalho: iniciar, pausar, retomar, finalizar.
"""
from datetime import date
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Tarefa, SessaoTarefa, PausaSessao, HistoricoTarefa
from .serializers import SessaoTarefaSerializer


def _sessao_ativa(usuario, tarefa):
    """Retorna a sessão ativa ou pausada do usuário na tarefa, se existir."""
    return SessaoTarefa.objects.filter(
        usuario=usuario,
        tarefa=tarefa,
        status__in=('ativa', 'pausada')
    ).first()


class TimerView(APIView):
    """
    GET  /api/v1/tarefas/{id}/timer/          → sessão atual
    POST /api/v1/tarefas/{id}/timer/iniciar/  → inicia
    POST /api/v1/tarefas/{id}/timer/pausar/   → pausa
    POST /api/v1/tarefas/{id}/timer/retomar/  → retoma
    POST /api/v1/tarefas/{id}/timer/finalizar/→ finaliza e salva duração
    """
    permission_classes = [IsAuthenticated]

    def _get_tarefa(self, pk):
        try:
            return Tarefa.objects.get(pk=pk)
        except Tarefa.DoesNotExist:
            return None

    def post(self, request, pk, acao=None):
        """Despacha para o método correto conforme a ação na URL."""
        if acao == 'iniciar':
            return self.post_iniciar(request, pk)
        if acao == 'pausar':
            return self.post_pausar(request, pk)
        if acao == 'retomar':
            return self.post_retomar(request, pk)
        if acao == 'finalizar':
            return self.post_finalizar(request, pk)
        return Response({'erro': 'Ação inválida.'}, status=400)

    # ── GET — sessão atual ──────────────────────────────────────
    def get(self, request, pk, acao=None):
        tarefa = self._get_tarefa(pk)
        if not tarefa:
            return Response({'erro': 'Tarefa não encontrada.'}, status=404)

        sessao = _sessao_ativa(request.user, tarefa)
        if not sessao:
            return Response({'sessao_ativa': False, 'sessao': None})

        return Response({
            'sessao_ativa': True,
            'sessao': SessaoTarefaSerializer(sessao).data,
        })

    # ── POST /iniciar/ ──────────────────────────────────────────
    def post_iniciar(self, request, pk):
        tarefa = self._get_tarefa(pk)
        if not tarefa:
            return Response({'erro': 'Tarefa não encontrada.'}, status=404)

        # Verifica se já tem sessão ativa
        existente = _sessao_ativa(request.user, tarefa)
        if existente:
            return Response({
                'erro': f'Já existe uma sessão {existente.get_status_display().lower()} para esta tarefa.',
                'sessao': SessaoTarefaSerializer(existente).data,
            }, status=400)

        # Verifica se há outra tarefa com timer ativo para este usuário
        outra = SessaoTarefa.objects.filter(
            usuario=request.user, status='ativa'
        ).exclude(tarefa=tarefa).first()
        if outra:
            return Response({
                'erro': f'Você já tem um timer ativo em "{outra.tarefa.titulo}". Pause ou finalize antes de iniciar outro.',
                'sessao_ativa': SessaoTarefaSerializer(outra).data,
            }, status=400)

        sessao = SessaoTarefa.objects.create(
            tarefa=tarefa,
            usuario=request.user,
            status='ativa',
        )

        # Muda status da tarefa para "em andamento" se estava pendente
        if tarefa.status == 'pending':
            tarefa.status = 'progress'
            tarefa.save()

        HistoricoTarefa.objects.create(
            tarefa=tarefa, usuario=request.user,
            acao='timer', detalhe='Timer iniciado.',
        )

        return Response({
            'mensagem': '⏱ Timer iniciado!',
            'sessao': SessaoTarefaSerializer(sessao).data,
        }, status=201)

    # ── POST /pausar/ ───────────────────────────────────────────
    def post_pausar(self, request, pk):
        tarefa = self._get_tarefa(pk)
        if not tarefa:
            return Response({'erro': 'Tarefa não encontrada.'}, status=404)

        sessao = _sessao_ativa(request.user, tarefa)
        if not sessao:
            return Response({'erro': 'Nenhum timer ativo para esta tarefa.'}, status=400)
        if sessao.status == 'pausada':
            return Response({'erro': 'Timer já está pausado.'}, status=400)

        PausaSessao.objects.create(sessao=sessao)
        sessao.status = 'pausada'
        sessao.save()

        return Response({
            'mensagem': '⏸ Timer pausado.',
            'sessao': SessaoTarefaSerializer(sessao).data,
        })

    # ── POST /retomar/ ──────────────────────────────────────────
    def post_retomar(self, request, pk):
        tarefa = self._get_tarefa(pk)
        if not tarefa:
            return Response({'erro': 'Tarefa não encontrada.'}, status=404)

        sessao = _sessao_ativa(request.user, tarefa)
        if not sessao:
            return Response({'erro': 'Nenhum timer para esta tarefa.'}, status=400)
        if sessao.status != 'pausada':
            return Response({'erro': 'Timer não está pausado.'}, status=400)

        # Fecha a pausa aberta
        pausa = sessao.pausas.filter(retomado_em__isnull=True).last()
        if pausa:
            pausa.retomado_em = timezone.now()
            pausa.save()

        sessao.status = 'ativa'
        sessao.save()

        return Response({
            'mensagem': '▶ Timer retomado.',
            'sessao': SessaoTarefaSerializer(sessao).data,
        })

    # ── POST /finalizar/ ────────────────────────────────────────
    def post_finalizar(self, request, pk):
        tarefa = self._get_tarefa(pk)
        if not tarefa:
            return Response({'erro': 'Tarefa não encontrada.'}, status=404)

        sessao = _sessao_ativa(request.user, tarefa)
        if not sessao:
            return Response({'erro': 'Nenhum timer ativo para esta tarefa.'}, status=400)

        # Fecha pausa aberta (se estava pausado e finalizou direto)
        pausa = sessao.pausas.filter(retomado_em__isnull=True).last()
        if pausa:
            pausa.retomado_em = timezone.now()
            pausa.save()

        sessao.status        = 'finalizada'
        sessao.finalizado_em = timezone.now()
        sessao.duracao_minutos = sessao.calcular_duracao()
        sessao.save()

        HistoricoTarefa.objects.create(
            tarefa=tarefa, usuario=request.user,
            acao='timer',
            detalhe=f'Sessão finalizada — {sessao.duracao_formatada}',
        )

        return Response({
            'mensagem': f'⏹ Timer finalizado! Tempo registrado: {sessao.duracao_formatada}',
            'sessao': SessaoTarefaSerializer(sessao).data,
        })


# ── Produtividade por usuário ───────────────────────────────────
class ProdutividadeView(APIView):
    """
    GET /api/v1/usuarios/{id}/produtividade/
    Parâmetros: ?periodo=mes (padrão) | semana | hoje
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, usuario_id):
        from apps.accounts.models import Usuario
        from datetime import timedelta

        try:
            usuario = Usuario.objects.get(pk=usuario_id)
        except Usuario.DoesNotExist:
            return Response({'erro': 'Usuário não encontrado.'}, status=404)

        # Apenas o próprio usuário ou gestor/admin podem ver
        if not request.user.is_gestor_ou_acima and request.user.id != usuario.id:
            return Response({'erro': 'Acesso negado.'}, status=403)

        # Filtro de período
        periodo = request.query_params.get('periodo', 'mes')
        hoje    = date.today()
        if periodo == 'hoje':
            data_inicio = hoje
        elif periodo == 'semana':
            data_inicio = hoje - timedelta(days=hoje.weekday())
        else:  # mês
            data_inicio = hoje.replace(day=1)

        tarefas = Tarefa.objects.filter(responsavel=usuario)
        tarefas_periodo = tarefas.filter(prazo__gte=data_inicio)

        concluidas  = tarefas_periodo.filter(status='done').count()
        atrasadas   = tarefas_periodo.filter(
            Q(status='late') | Q(status='pending', prazo__lt=hoje)
        ).count()
        total       = tarefas_periodo.count()
        taxa        = round(concluidas / total * 100, 1) if total else 0

        # Tempo total do período
        sessoes     = SessaoTarefa.objects.filter(
            usuario=usuario,
            status='finalizada',
            iniciado_em__date__gte=data_inicio,
        )
        tempo_total = sessoes.aggregate(t=Sum('duracao_minutos'))['t'] or 0
        media       = round(tempo_total / concluidas, 1) if concluidas else 0

        # Por categoria
        por_categoria = {}
        for cat_key, cat_label in Tarefa.CATEGORIA_CHOICES:
            cat_sessoes = sessoes.filter(tarefa__categoria=cat_key)
            minutos = cat_sessoes.aggregate(t=Sum('duracao_minutos'))['t'] or 0
            qtd     = tarefas_periodo.filter(categoria=cat_key, status='done').count()
            if minutos or qtd:
                horas = minutos // 60
                mins  = minutos % 60
                por_categoria[cat_label] = {
                    'tarefas_concluidas': qtd,
                    'tempo_minutos': minutos,
                    'tempo_formatado': f'{horas:02d}h{mins:02d}min',
                }

        horas_total = tempo_total // 60
        mins_total  = tempo_total % 60

        return Response({
            'usuario_id':            usuario.id,
            'usuario_nome':          usuario.nome,
            'periodo':               periodo,
            'data_inicio':           data_inicio,
            'total_tarefas':         total,
            'tarefas_concluidas':    concluidas,
            'tarefas_atrasadas':     atrasadas,
            'taxa_conclusao':        taxa,
            'tempo_total_minutos':   tempo_total,
            'tempo_total_formatado': f'{horas_total:02d}h{mins_total:02d}min',
            'media_minutos_tarefa':  media,
            'por_categoria':         por_categoria,
        })
