"""
Views principais de Tarefas — CRUD, tags, dependências, checklist, comentários.
"""
from datetime import date
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsGestorOuAcima, IsEquipeInterna
from .models import (
    Tag, Tarefa, TarefaDependencia,
    ChecklistItem, Comentario, HistoricoTarefa,
)
from .serializers import (
    TagSerializer,
    TarefaSerializer, TarefaDetalheSerializer, TarefaCriarSerializer,
    TarefaDependenciaSerializer,
    ChecklistItemSerializer, ComentarioSerializer, HistoricoTarefaSerializer,
)
from .utils import proximo_prazo
from .views_notificacoes import criar_notificacao


def registrar_historico(tarefa, usuario, acao, detalhe=''):
    HistoricoTarefa.objects.create(
        tarefa=tarefa, usuario=usuario, acao=acao, detalhe=detalhe
    )


# ── Tags ────────────────────────────────────────────────────────
class TagViewSet(viewsets.ModelViewSet):
    queryset           = Tag.objects.all()
    serializer_class   = TagSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsGestorOuAcima()]
        return [IsEquipeInterna()]

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)


# ── Tarefas ─────────────────────────────────────────────────────
class TarefaViewSet(viewsets.ModelViewSet):
    queryset = Tarefa.objects.select_related(
        'empresa', 'responsavel', 'criado_por'
    ).prefetch_related('checklist', 'comentarios', 'tags', 'dependencias')

    def get_permissions(self):
        if self.action in ('destroy',):
            return [IsGestorOuAcima()]
        return [IsEquipeInterna()]

    def get_serializer_class(self):
        if self.action == 'create':
            return TarefaCriarSerializer
        if self.action == 'retrieve':
            return TarefaDetalheSerializer
        return TarefaSerializer

    def get_queryset(self):
        from django.db.models import Q
        from apps.companies.models import Empresa

        qs     = super().get_queryset()
        user   = self.request.user
        params = self.request.query_params

        # Analistas e assistentes veem só tarefas das suas empresas
        if not user.is_gestor_ou_acima:
            ids = Empresa.objects.filter(
                Q(responsavel=user) | Q(colaboradores=user)
            ).values_list('id', flat=True)
            qs = qs.filter(empresa__in=ids)

        if params.get('empresa'):
            qs = qs.filter(empresa=params['empresa'])
        if params.get('responsavel'):
            qs = qs.filter(responsavel=params['responsavel'])
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('prioridade'):
            qs = qs.filter(prioridade=params['prioridade'])
        if params.get('categoria'):
            qs = qs.filter(categoria=params['categoria'])
        if params.get('tag'):
            qs = qs.filter(tags__id=params['tag'])
        if params.get('busca'):
            qs = qs.filter(titulo__icontains=params['busca'])
        if params.get('prazo_de'):
            qs = qs.filter(prazo__gte=params['prazo_de'])
        if params.get('prazo_ate'):
            qs = qs.filter(prazo__lte=params['prazo_ate'])
        return qs.distinct()

    def perform_update(self, serializer):
        tarefa = serializer.save()
        registrar_historico(tarefa, self.request.user, 'editou',
                            'Dados da tarefa atualizados.')

    # ── Concluir ────────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        tarefa = self.get_object()
        if tarefa.status == 'done':
            return Response({'erro': 'Tarefa já está concluída.'}, status=400)

        # Verifica dependências não concluídas
        deps_pendentes = tarefa.dependencias.exclude(depende_de__status='done')
        if deps_pendentes.exists():
            nomes = [d.depende_de.titulo for d in deps_pendentes[:3]]
            return Response({
                'erro': 'Esta tarefa tem dependências não concluídas.',
                'pendentes': nomes,
            }, status=400)

        tarefa.status       = 'done'
        tarefa.concluida_em = timezone.now()
        tarefa.save()
        registrar_historico(tarefa, request.user, 'concluiu',
                            f'Concluída em {tarefa.concluida_em.strftime("%d/%m/%Y %H:%M")}')

        # Cria próxima ocorrência se recorrente
        # — não cria se já foram pré-geradas via recorrencia_fim
        proxima = None
        ja_pre_geradas = tarefa.recorrencias_geradas.filter(status='pending').exists()
        if tarefa.recorrencia != 'none' and not ja_pre_geradas and not tarefa.recorrencia_fim:
            prazo_base = tarefa.prazo or date.today()
            novo_prazo = proximo_prazo(prazo_base, tarefa.recorrencia)
            if novo_prazo:
                proxima = Tarefa.objects.create(
                    titulo        = tarefa.titulo,
                    empresa       = tarefa.empresa,
                    responsavel   = tarefa.responsavel,
                    prazo_tipo    = tarefa.prazo_tipo,
                    prazo         = novo_prazo,
                    prazo_dias    = tarefa.prazo_dias,
                    prioridade    = tarefa.prioridade,
                    recorrencia   = tarefa.recorrencia,
                    categoria     = tarefa.categoria,
                    observacoes   = tarefa.observacoes,
                    link_documento= tarefa.link_documento,
                    status        = 'pending',
                    tarefa_origem = tarefa,
                    criado_por    = request.user,
                )
                proxima.tags.set(tarefa.tags.all())
                registrar_historico(proxima, request.user, 'criou',
                                    f'Gerada por recorrência de #{tarefa.id}')

                # Notifica responsável
                if tarefa.responsavel:
                    criar_notificacao(
                        usuario  = tarefa.responsavel,
                        tipo     = 'tarefa_criada',
                        titulo   = 'Nova tarefa recorrente criada',
                        mensagem = f'"{proxima.titulo}" foi criada automaticamente para {novo_prazo.strftime("%d/%m/%Y")}.',
                        tarefa   = proxima,
                    )

        resp = {'mensagem': 'Tarefa concluída!', 'tarefa': TarefaSerializer(tarefa).data}
        if proxima:
            resp['proxima_ocorrencia'] = TarefaSerializer(proxima).data
            resp['mensagem'] += f' Próxima criada para {proxima.prazo.strftime("%d/%m/%Y")}.'
        return Response(resp)

    # ── Reabrir ─────────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def reabrir(self, request, pk=None):
        tarefa = self.get_object()
        if tarefa.status != 'done':
            return Response({'erro': 'Tarefa não está concluída.'}, status=400)
        tarefa.status       = 'pending'
        tarefa.concluida_em = None
        tarefa.save()
        registrar_historico(tarefa, request.user, 'reabriu', 'Tarefa reaberta.')
        return Response({'mensagem': 'Tarefa reaberta.', 'tarefa': TarefaSerializer(tarefa).data})

    # ── Tarefas de hoje ─────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def hoje(self, request):
        qs = self.get_queryset().filter(prazo=date.today())
        return Response(TarefaSerializer(qs, many=True).data)

    # ── Tarefas atrasadas ───────────────────────────────────────
    @action(detail=False, methods=['get'])
    def atrasadas(self, request):
        qs = self.get_queryset().filter(
            prazo__lt=date.today()
        ).exclude(status='done')
        return Response(TarefaSerializer(qs, many=True).data)

    # ── Dependências ────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='dependencias')
    def dependencias(self, request, pk=None):
        tarefa = self.get_object()
        if request.method == 'GET':
            return Response(TarefaDependenciaSerializer(
                tarefa.dependencias.all(), many=True).data)

        serializer = TarefaDependenciaSerializer(
            data={**request.data, 'tarefa': tarefa.id},
            context={'tarefa': tarefa, 'request': request},
        )
        if serializer.is_valid():
            serializer.save(tarefa=tarefa)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['delete'],
            url_path=r'dependencias/(?P<dep_id>\d+)')
    def remover_dependencia(self, request, pk=None, dep_id=None):
        tarefa = self.get_object()
        try:
            dep = tarefa.dependencias.get(id=dep_id)
        except TarefaDependencia.DoesNotExist:
            return Response({'erro': 'Dependência não encontrada.'}, status=404)
        dep.delete()
        return Response({'mensagem': 'Dependência removida.'})

    # ── Checklist ───────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='checklist')
    def checklist(self, request, pk=None):
        tarefa = self.get_object()
        if request.method == 'GET':
            return Response(ChecklistItemSerializer(tarefa.checklist.all(), many=True).data)

        serializer = ChecklistItemSerializer(data={**request.data, 'tarefa': tarefa.id})
        if serializer.is_valid():
            serializer.save()
            registrar_historico(tarefa, request.user, 'checklist',
                                f'Item adicionado: {serializer.data["titulo"]}')
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['patch', 'delete'],
            url_path=r'checklist/(?P<item_id>\d+)')
    def checklist_item(self, request, pk=None, item_id=None):
        tarefa = self.get_object()
        try:
            item = tarefa.checklist.get(id=item_id)
        except ChecklistItem.DoesNotExist:
            return Response({'erro': 'Item não encontrado.'}, status=404)
        if request.method == 'DELETE':
            item.delete()
            return Response({'mensagem': 'Item removido.'})
        serializer = ChecklistItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            registrar_historico(tarefa, request.user, 'checklist',
                                f'Item atualizado: {item.titulo}')
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    # ── Comentários ─────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='comentarios')
    def comentarios(self, request, pk=None):
        tarefa = self.get_object()
        if request.method == 'GET':
            return Response(ComentarioSerializer(tarefa.comentarios.all(), many=True).data)

        serializer = ComentarioSerializer(data={**request.data, 'tarefa': tarefa.id})
        if serializer.is_valid():
            comentario = serializer.save(autor=request.user)
            registrar_historico(tarefa, request.user, 'comentou',
                                comentario.texto[:100])
            # Notifica o responsável se for outra pessoa comentando
            if tarefa.responsavel and tarefa.responsavel != request.user:
                criar_notificacao(
                    usuario  = tarefa.responsavel,
                    tipo     = 'comentario_novo',
                    titulo   = 'Novo comentário',
                    mensagem = f'{request.user.nome} comentou em "{tarefa.titulo}".',
                    tarefa   = tarefa,
                )
            return Response(ComentarioSerializer(comentario).data, status=201)
        return Response(serializer.errors, status=400)

    # ── Histórico ────────────────────────────────────────────────
    @action(detail=True, methods=['get'], url_path='historico')
    def historico(self, request, pk=None):
        tarefa = self.get_object()
        return Response(HistoricoTarefaSerializer(tarefa.historico.all(), many=True).data)
