from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsGestorOuAcima, IsEquipeInterna
from .models import Empresa, Pagamento
from .serializers import EmpresaSerializer, EmpresaDetalheSerializer, PagamentoSerializer


class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all().order_by('nome')

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsGestorOuAcima()]
        return [IsEquipeInterna()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmpresaDetalheSerializer
        return EmpresaSerializer

    def get_queryset(self):
        qs   = super().get_queryset()
        user = self.request.user

        # Analistas e assistentes veem só suas empresas
        if not user.is_gestor_ou_acima:
            qs = qs.filter(
                Q(responsavel=user) | Q(colaboradores=user)
            ).distinct()

        status_param = self.request.query_params.get('status')
        busca        = self.request.query_params.get('busca')
        if status_param:
            qs = qs.filter(status=status_param)
        if busca:
            qs = qs.filter(nome__icontains=busca) | qs.filter(cnpj__icontains=busca)
        return qs

    # ── Pagamentos ──────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='pagamentos')
    def pagamentos(self, request, pk=None):
        empresa = self.get_object()

        if request.method == 'GET':
            pags = empresa.pagamentos.all()
            return Response(PagamentoSerializer(pags, many=True).data)

        # POST — novo pagamento
        serializer = PagamentoSerializer(data={**request.data, 'empresa': empresa.id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch', 'delete'],
            url_path=r'pagamentos/(?P<pag_id>\d+)')
    def pagamento_detalhe(self, request, pk=None, pag_id=None):
        empresa = self.get_object()
        try:
            pag = empresa.pagamentos.get(id=pag_id)
        except Pagamento.DoesNotExist:
            return Response({'erro': 'Pagamento não encontrado.'}, status=404)

        if request.method == 'DELETE':
            pag.delete()
            return Response({'mensagem': 'Pagamento excluído.'})

        serializer = PagamentoSerializer(pag, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ── Resumo financeiro ───────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='resumo')
    def resumo(self, request):
        from django.db.models import Sum, Count
        qs = Empresa.objects.filter(status='active')
        return Response({
            'total_empresas':    qs.count(),
            'faturamento_mensal': qs.aggregate(t=Sum('mensalidade'))['t'] or 0,
            'pagamentos_pendentes': Pagamento.objects.exclude(status='paid').count(),
        })
