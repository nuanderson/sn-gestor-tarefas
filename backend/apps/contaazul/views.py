"""
Views da integração Conta Azul.

Fluxo OAuth:
  GET /contaazul/connect/<empresa_id>/  → redireciona para autenticação no Conta Azul
  GET /contaazul/callback/              → recebe o code, salva tokens

API REST:
  POST /api/v1/contaazul/sync/<empresa_id>/   → sincronização manual
  GET  /api/v1/contaazul/vencimentos/         → lista de vencimentos com filtros
  GET  /api/v1/contaazul/status/              → status de conexão por empresa
"""
import secrets
from datetime import date, timedelta

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsEquipeInterna, IsGestorOuAcima
from apps.companies.models import Empresa

from .models import ContaAzulToken, ContaAzulVencimento
from .serializers import ContaAzulTokenStatusSerializer, ContaAzulVencimentoSerializer
from .services import ContaAzulClient

_client = ContaAzulClient()


# ── OAuth ────────────────────────────────────────────────────────

@login_required
def oauth_connect(request, empresa_id):
    """Inicia o fluxo OAuth 2.0 — redireciona o usuário para o Conta Azul."""
    get_object_or_404(Empresa, pk=empresa_id)

    state = secrets.token_urlsafe(16)
    request.session['contaazul_state']      = state
    request.session['contaazul_empresa_id'] = empresa_id

    return redirect(_client.get_authorization_url(state))


@login_required
def oauth_callback(request):
    """Recebe o authorization code, troca por tokens e salva."""
    code  = request.GET.get('code')
    state = request.GET.get('state')

    if not code or state != request.session.get('contaazul_state'):
        messages.error(request, 'Autorização inválida ou sessão expirada. Tente novamente.')
        return redirect('/empresas/')

    empresa_id = request.session.pop('contaazul_empresa_id', None)
    request.session.pop('contaazul_state', None)

    if not empresa_id:
        messages.error(request, 'Sessão expirada. Tente novamente.')
        return redirect('/empresas/')

    empresa = get_object_or_404(Empresa, pk=empresa_id)

    try:
        data = _client.exchange_code(code)
    except requests.HTTPError as exc:
        messages.error(request, f'Erro ao conectar com o Conta Azul: {exc}')
        return redirect('/empresas/')

    # Valida que o CNPJ da conta ContaAzul autenticada bate com a empresa do SN Gestor
    try:
        info_ca = _client.fetch_empresa_info(data['access_token'])
        cnpj_ca    = ''.join(filter(str.isdigit, info_ca.get('cnpj', '')))
        cnpj_local = ''.join(filter(str.isdigit, empresa.cnpj))
        if cnpj_ca and cnpj_local and cnpj_ca != cnpj_local:
            messages.error(
                request,
                f'CNPJ divergente: a conta Conta Azul autenticada pertence ao CNPJ '
                f'{info_ca.get("cnpj", cnpj_ca)}, mas a empresa "{empresa.nome}" '
                f'está cadastrada com o CNPJ {empresa.cnpj}. Conexão cancelada.',
            )
            return redirect('/empresas/')
    except requests.HTTPError:
        # Se o endpoint não retornar os dados da empresa, registra aviso mas não bloqueia
        messages.warning(
            request,
            'Não foi possível verificar o CNPJ junto ao Conta Azul. '
            'Confirme manualmente que a conta conectada é a correta.',
        )

    expires_at = timezone.now() + timedelta(seconds=data.get('expires_in', 3600))
    ContaAzulToken.objects.update_or_create(
        empresa=empresa,
        defaults={
            'access_token':  data['access_token'],
            'refresh_token': data['refresh_token'],
            'expires_at':    expires_at,
        },
    )

    messages.success(request, f'Conta Azul conectado com sucesso para {empresa.nome}!')
    return redirect('/empresas/')


# ── API REST ─────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsGestorOuAcima])
def sync_empresa(request, empresa_id):
    """Dispara a sincronização manual de vencimentos de uma empresa."""
    empresa = get_object_or_404(Empresa, pk=empresa_id)

    try:
        criados, atualizados = _client.sync_empresa(empresa)
    except ValueError as exc:
        return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response(
            {'erro': f'Falha na sincronização: {exc}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({
        'mensagem':    'Sincronização concluída.',
        'criados':     criados,
        'atualizados': atualizados,
    })


class VencimentoListView(APIView):
    """
    GET /api/v1/contaazul/vencimentos/

    Filtros disponíveis:
      empresa_id, tipo (pagar|receber), status,
      proximos_dias (inteiro — vencimentos de hoje até N dias)
    """
    permission_classes = [IsEquipeInterna]

    def get(self, request):
        qs = ContaAzulVencimento.objects.select_related('empresa').order_by('data_vencimento')

        empresa_id   = request.query_params.get('empresa_id')
        tipo         = request.query_params.get('tipo')
        status_param = request.query_params.get('status')
        proximos_dias = request.query_params.get('proximos_dias')

        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if status_param:
            qs = qs.filter(status=status_param)
        if proximos_dias:
            try:
                limite = date.today() + timedelta(days=int(proximos_dias))
                qs = qs.filter(data_vencimento__gte=date.today(), data_vencimento__lte=limite)
            except ValueError:
                pass

        serializer = ContaAzulVencimentoSerializer(qs, many=True)
        return Response(serializer.data)


class ConnectionStatusView(APIView):
    """
    GET /api/v1/contaazul/status/
    Lista o status de conexão de todas as empresas.
    """
    permission_classes = [IsGestorOuAcima]

    def get(self, request):
        tokens = ContaAzulToken.objects.select_related('empresa').all()
        serializer = ContaAzulTokenStatusSerializer(tokens, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsGestorOuAcima])
def status_empresa(request, empresa_id):
    """
    GET /api/v1/contaazul/status/<empresa_id>/
    Retorna o status de conexão de uma empresa específica.
    """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    try:
        token = empresa.contaazul_token
        return Response({
            'conectado':   True,
            'ativo':       token.ativo,
            'expires_at':  token.expires_at,
            'atualizado_em': token.atualizado_em,
        })
    except ContaAzulToken.DoesNotExist:
        return Response({'conectado': False})
