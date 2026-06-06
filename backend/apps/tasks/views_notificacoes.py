"""
Views de Notificações Internas — sino 🔔 no topo do sistema.
"""
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Notificacao
from .serializers import NotificacaoSerializer


def criar_notificacao(usuario, tipo, titulo, mensagem, tarefa=None):
    """Função utilitária para criar notificações de qualquer parte do sistema."""
    Notificacao.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        tarefa=tarefa,
    )


class NotificacaoListView(APIView):
    """
    GET  /api/v1/notificacoes/        → lista notificações do usuário logado
    POST /api/v1/notificacoes/todas-lidas/ → marca todas como lidas
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        apenas_nao_lidas = request.query_params.get('nao_lidas') == 'true'
        qs = Notificacao.objects.filter(usuario=request.user)
        if apenas_nao_lidas:
            qs = qs.filter(lida=False)
        qs = qs[:50]  # Máximo 50 mais recentes
        return Response({
            'total_nao_lidas': Notificacao.objects.filter(
                usuario=request.user, lida=False
            ).count(),
            'notificacoes': NotificacaoSerializer(qs, many=True).data,
        })


class NotificacaoDetalheView(APIView):
    """
    PATCH /api/v1/notificacoes/{id}/lida/  → marca como lida
    DELETE /api/v1/notificacoes/{id}/      → remove
    """
    permission_classes = [IsAuthenticated]

    def _get(self, request, pk):
        try:
            return Notificacao.objects.get(pk=pk, usuario=request.user)
        except Notificacao.DoesNotExist:
            return None

    def patch(self, request, pk):
        notif = self._get(request, pk)
        if not notif:
            return Response({'erro': 'Não encontrada.'}, status=404)
        notif.lida = True
        notif.save()
        return Response({'mensagem': 'Marcada como lida.'})

    def delete(self, request, pk):
        notif = self._get(request, pk)
        if not notif:
            return Response({'erro': 'Não encontrada.'}, status=404)
        notif.delete()
        return Response({'mensagem': 'Notificação removida.'})


class MarcarTodasLidasView(APIView):
    """POST /api/v1/notificacoes/todas-lidas/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notificacao.objects.filter(
            usuario=request.user, lida=False
        ).update(lida=True)
        return Response({'mensagem': f'{count} notificação(ões) marcada(s) como lida(s).'})
