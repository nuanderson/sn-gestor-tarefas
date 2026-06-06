from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsGestorOuAcima
from apps.companies.models import Pagamento
from .models import Documento, SolicitacaoBoleto
from .serializers import DocumentoSerializer, SolicitacaoBoletoSerializer, PagamentoRecorrenciaSerializer


class IsCliente(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_cliente


def get_empresa_cliente(user):
    """Retorna a empresa vinculada ao usuário cliente."""
    return getattr(user, 'empresa_cliente', None)


# ── Resumo do Portal ──────────────────────────────────────────────────────────

class PortalResumoView(APIView):
    permission_classes = [IsCliente]

    def get(self, request):
        empresa = get_empresa_cliente(request.user)
        if not empresa:
            return Response({'erro': 'Nenhuma empresa vinculada.'}, status=400)

        pagamentos = empresa.pagamentos.all()
        pendentes  = pagamentos.exclude(status='paid')
        docs       = empresa.documentos.all()
        boletos    = empresa.solicitacoes_boleto.all()

        return Response({
            'empresa': {
                'id':           empresa.id,
                'nome':         empresa.nome,
                'status':       empresa.status,
                'mensalidade':  str(empresa.mensalidade),
                'data_entrada': empresa.data_entrada,
            },
            'financeiro': {
                'total_pago':         str(empresa.total_recebido),
                'pagamentos_pendentes': pendentes.count(),
                'proximo_vencimento': pagamentos.exclude(status='paid').order_by('data').values_list('data', flat=True).first(),
            },
            'documentos_recentes': DocumentoSerializer(docs[:5], many=True).data,
            'boletos_abertos':     SolicitacaoBoletoSerializer(
                boletos.filter(status__in=['pendente', 'em_analise']), many=True
            ).data,
        })


# ── Documentos ────────────────────────────────────────────────────────────────

class DocumentoListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentoSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            # Cliente vê apenas os da própria empresa; equipe vê com filtro
            return [IsAuthenticated()]
        return [IsGestorOuAcima()]

    def get_queryset(self):
        user = self.request.user
        if user.is_cliente:
            empresa = get_empresa_cliente(user)
            if not empresa:
                return Documento.objects.none()
            qs = Documento.objects.filter(empresa=empresa)
        else:
            empresa_id = self.request.query_params.get('empresa')
            qs = Documento.objects.all()
            if empresa_id:
                qs = qs.filter(empresa=empresa_id)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)


class DocumentoDetalheView(generics.RetrieveDestroyAPIView):
    serializer_class   = DocumentoSerializer
    permission_classes = [IsGestorOuAcima]
    queryset           = Documento.objects.all()


# ── Pagamentos (leitura para o cliente) ───────────────────────────────────────

class PortalPagamentosView(APIView):
    permission_classes = [IsCliente]

    def get(self, request):
        empresa = get_empresa_cliente(request.user)
        if not empresa:
            return Response({'erro': 'Nenhuma empresa vinculada.'}, status=400)

        pags = empresa.pagamentos.order_by('-data')
        data = [
            {
                'id':         p.id,
                'data':       p.data,
                'valor':      str(p.valor),
                'status':     p.status,
                'referencia': p.referencia,
            }
            for p in pags
        ]
        return Response(data)


# ── Solicitações de Boleto ────────────────────────────────────────────────────

class BoletoListCreateView(generics.ListCreateAPIView):
    serializer_class = SolicitacaoBoletoSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_cliente:
            empresa = get_empresa_cliente(user)
            if not empresa:
                return SolicitacaoBoleto.objects.none()
            return SolicitacaoBoleto.objects.filter(empresa=empresa)
        # Equipe interna pode ver todos ou filtrar
        empresa_id = self.request.query_params.get('empresa')
        qs = SolicitacaoBoleto.objects.all()
        if empresa_id:
            qs = qs.filter(empresa=empresa_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        empresa = get_empresa_cliente(user)
        if not empresa:
            raise Exception('Nenhuma empresa vinculada.')
        serializer.save(solicitado_por=user, empresa=empresa)


class BoletoDetalheView(generics.RetrieveUpdateAPIView):
    serializer_class = SolicitacaoBoletoSerializer
    queryset         = SolicitacaoBoleto.objects.all()

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsGestorOuAcima()]
        return [IsAuthenticated()]


# ── Recorrência de pagamentos com status de solicitação ───────────────────────

class RecorrenciaView(APIView):
    """Retorna todos os pagamentos da empresa do cliente com info de solicitação de boleto."""
    permission_classes = [IsCliente]

    def get(self, request):
        empresa = get_empresa_cliente(request.user)
        if not empresa:
            return Response({'erro': 'Nenhuma empresa vinculada.'}, status=400)

        pagamentos = empresa.pagamentos.order_by('data')
        solicitacoes = {
            s.referencia: s
            for s in empresa.solicitacoes_boleto.all()
        }

        resultado = []
        for p in pagamentos:
            sol = solicitacoes.get(p.referencia)
            resultado.append({
                'id':               p.id,
                'referencia':       p.referencia,
                'data':             p.data,
                'valor':            str(p.valor),
                'status':           p.status,
                'boleto_solicitado': sol.status if sol else None,
                'boleto_id':        sol.id if sol else None,
            })

        return Response({
            'empresa': {'nome': empresa.nome, 'mensalidade': str(empresa.mensalidade)},
            'pagamentos': resultado,
        })

    def post(self, request):
        """Solicita boleto para um pagamento específico."""
        empresa = get_empresa_cliente(request.user)
        if not empresa:
            return Response({'erro': 'Nenhuma empresa vinculada.'}, status=400)

        pagamento_id = request.data.get('pagamento_id')
        try:
            pagamento = empresa.pagamentos.get(id=pagamento_id)
        except Pagamento.DoesNotExist:
            return Response({'erro': 'Pagamento não encontrado.'}, status=404)

        # Evita duplicata
        if empresa.solicitacoes_boleto.filter(referencia=pagamento.referencia, status__in=['pendente','em_analise']).exists():
            return Response({'erro': 'Já existe uma solicitação em aberto para este mês.'}, status=400)

        sol = SolicitacaoBoleto.objects.create(
            empresa=empresa,
            referencia=pagamento.referencia,
            valor=pagamento.valor,
            solicitado_por=request.user,
        )
        return Response({'mensagem': 'Solicitação enviada!', 'id': sol.id}, status=201)
