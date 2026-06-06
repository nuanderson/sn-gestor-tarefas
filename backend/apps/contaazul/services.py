"""
Cliente HTTP para a API do Conta Azul (v2).
Gerencia OAuth 2.0 (troca de código, refresh automático) e sincronização de dados.
"""
import base64
from datetime import date, timedelta

import requests
from django.conf import settings
from django.utils import timezone

CONTAAZUL_AUTH_BASE = 'https://auth.contaazul.com'
CONTAAZUL_API_BASE  = 'https://api-v2.contaazul.com'


class ContaAzulClient:

    def __init__(self):
        self.client_id     = settings.CONTAAZUL_CLIENT_ID
        self.client_secret = settings.CONTAAZUL_CLIENT_SECRET
        self.redirect_uri  = settings.CONTAAZUL_REDIRECT_URI

    # ── Autenticação ─────────────────────────────────────────────

    def _basic_auth_header(self):
        raw = f'{self.client_id}:{self.client_secret}'
        return 'Basic ' + base64.b64encode(raw.encode()).decode()

    def get_authorization_url(self, state: str) -> str:
        params = '&'.join([
            'response_type=code',
            f'client_id={self.client_id}',
            f'redirect_uri={self.redirect_uri}',
            f'state={state}',
            'scope=openid+profile+aws.cognito.signin.user.admin',
        ])
        return f'{CONTAAZUL_AUTH_BASE}/login?{params}'

    def exchange_code(self, code: str) -> dict:
        """Troca o authorization code por access_token + refresh_token."""
        resp = requests.post(
            f'{CONTAAZUL_AUTH_BASE}/oauth2/token',
            headers={
                'Authorization': self._basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={
                'grant_type':   'authorization_code',
                'code':         code,
                'redirect_uri': self.redirect_uri,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def _refresh_token(self, token_obj) -> None:
        """Renova o access_token usando o refresh_token. Atualiza o objeto no banco."""
        resp = requests.post(
            f'{CONTAAZUL_AUTH_BASE}/oauth2/token',
            headers={
                'Authorization': self._basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={
                'grant_type':    'refresh_token',
                'refresh_token': token_obj.refresh_token,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        token_obj.access_token = data['access_token']
        # Refresh tokens do Conta Azul são de uso único — guarda o novo se vier
        if 'refresh_token' in data:
            token_obj.refresh_token = data['refresh_token']
        token_obj.expires_at = timezone.now() + timedelta(seconds=data.get('expires_in', 3600))
        token_obj.save(update_fields=['access_token', 'refresh_token', 'expires_at', 'atualizado_em'])

    def get_valid_token(self, empresa) -> str:
        """Retorna um access_token válido, renovando-o se necessário."""
        from .models import ContaAzulToken
        try:
            token_obj = empresa.contaazul_token
        except ContaAzulToken.DoesNotExist:
            raise ValueError(
                f"A empresa '{empresa.nome}' não está conectada ao Conta Azul. "
                "Acesse Empresas → Conectar Conta Azul."
            )

        if token_obj.expires_at <= timezone.now() + timedelta(minutes=5):
            self._refresh_token(token_obj)

        return token_obj.access_token

    # ── Chamadas à API ───────────────────────────────────────────

    def _get(self, access_token: str, path: str, params: dict = None) -> dict | list:
        resp = requests.get(
            f'{CONTAAZUL_API_BASE}{path}',
            headers={'Authorization': f'Bearer {access_token}'},
            params=params or {},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch_empresa_info(self, access_token: str) -> dict:
        """Retorna os dados da empresa autenticada no Conta Azul (inclui CNPJ)."""
        return self._get(access_token, '/v1/empresa')

    def fetch_contas_a_pagar(self, access_token: str, **params):
        return self._get(access_token, '/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar', params)

    def fetch_contas_a_receber(self, access_token: str, **params):
        return self._get(access_token, '/v1/financeiro/eventos-financeiros/contas-a-receber/buscar', params)

    # ── Sincronização ────────────────────────────────────────────

    STATUS_MAP = {
        'EM_ABERTO': 'pendente',
        'PENDING':   'pendente',
        'VENCIDO':   'atrasado',
        'OVERDUE':   'atrasado',
        'PAGO':      'pago',
        'RECEBIDO':  'pago',
        'PAID':      'pago',
        'CANCELADO': 'cancelado',
        'CANCELLED': 'cancelado',
    }

    def _prioridade_por_prazo(self, data_vencimento) -> str:
        dias = (data_vencimento - date.today()).days
        if dias <= 3:
            return 'urgent'
        if dias <= 7:
            return 'high'
        if dias <= 30:
            return 'medium'
        return 'low'

    def _criar_tarefa(self, empresa, vencimento) -> 'Tarefa | None':
        """Cria uma tarefa automática para uma conta a pagar recém-sincronizada."""
        from apps.tasks.models import Tarefa

        parcela = ''
        if vencimento.parcela_numero and vencimento.parcela_total:
            parcela = f' ({vencimento.parcela_numero}/{vencimento.parcela_total})'

        titulo = (
            f'[ContaAzul] {vencimento.descricao}{parcela} '
            f'— R$ {vencimento.valor:.2f}'
        )

        obs_linhas = [
            f'Conta a pagar importada automaticamente do Conta Azul.',
            f'Fornecedor: {vencimento.pessoa_nome}' if vencimento.pessoa_nome else '',
            f'Vencimento: {vencimento.data_vencimento.strftime("%d/%m/%Y")}',
            f'Valor: R$ {vencimento.valor:.2f}',
            f'ID Conta Azul: {vencimento.contaazul_id}',
        ]
        observacoes = '\n'.join(l for l in obs_linhas if l)

        try:
            return Tarefa.objects.create(
                titulo=titulo,
                empresa=empresa,
                responsavel=empresa.responsavel,
                prazo_tipo='fixed',
                prazo=vencimento.data_vencimento,
                categoria='financeiro',
                prioridade=self._prioridade_por_prazo(vencimento.data_vencimento),
                observacoes=observacoes,
                status='pending',
            )
        except Exception:
            return None

    def _sincronizar_status_tarefa(self, vencimento) -> None:
        """Fecha a tarefa se a conta foi paga ou cancelada."""
        from django.utils import timezone as tz
        from apps.tasks.models import Tarefa

        tarefa = vencimento.tarefa
        if not tarefa or tarefa.status == 'done':
            return

        if vencimento.status in ('pago', 'cancelado'):
            tarefa.status = 'done'
            tarefa.concluida_em = tz.now()
            tarefa.save(update_fields=['status', 'concluida_em', 'atualizado_em'])

    def sync_empresa(self, empresa, dias_atras: int = 30, dias_frente: int = 90) -> tuple[int, int]:
        """
        Busca contas a pagar e a receber no intervalo dado e salva localmente.
        Para cada nova conta a pagar cria uma tarefa automática.
        Retorna (criados, atualizados).
        """
        from .models import ContaAzulVencimento

        access_token = self.get_valid_token(empresa)
        hoje         = date.today()
        inicio       = (hoje - timedelta(days=dias_atras)).isoformat()
        fim          = (hoje + timedelta(days=dias_frente)).isoformat()

        total_criados     = 0
        total_atualizados = 0

        endpoints = [
            ('pagar',   self.fetch_contas_a_pagar),
            ('receber', self.fetch_contas_a_receber),
        ]

        for tipo, fetch_fn in endpoints:
            pagina = 1
            while True:
                try:
                    resposta = fetch_fn(
                        access_token,
                        data_vencimento_de=inicio,
                        data_vencimento_ate=fim,
                        pagina=pagina,
                        tamanho_pagina=100,
                    )
                except requests.HTTPError as exc:
                    raise RuntimeError(f'Erro HTTP ao buscar contas a {tipo}: {exc}') from exc

                if isinstance(resposta, list):
                    itens    = resposta
                    has_more = False
                else:
                    itens    = resposta.get('itens') or resposta.get('items') or []
                    has_more = len(itens) == 100

                for item in itens:
                    contaazul_id = str(item.get('id', ''))
                    if not contaazul_id:
                        continue

                    pessoa = item.get('cliente') or item.get('fornecedor') or {}
                    status_api   = (item.get('status_traduzido') or item.get('status') or '').upper()
                    status_local = self.STATUS_MAP.get(status_api, 'pendente')

                    defaults = {
                        'descricao':       item.get('descricao') or '',
                        'valor':           item.get('total', item.get('valor', 0)),
                        'data_vencimento': item.get('data_vencimento'),
                        'data_pagamento':  item.get('data_pagamento') or None,
                        'status':          status_local,
                        'pessoa_nome':     pessoa.get('nome', ''),
                        'parcela_numero':  item.get('numero_parcela'),
                        'parcela_total':   item.get('total_parcelas'),
                    }

                    vencimento, created = ContaAzulVencimento.objects.update_or_create(
                        empresa=empresa,
                        contaazul_id=contaazul_id,
                        tipo=tipo,
                        defaults=defaults,
                    )

                    if created:
                        total_criados += 1
                        # Cria tarefa automática apenas para contas a pagar novas e ativas
                        if tipo == 'pagar' and status_local not in ('pago', 'cancelado'):
                            tarefa = self._criar_tarefa(empresa, vencimento)
                            if tarefa:
                                vencimento.tarefa = tarefa
                                vencimento.save(update_fields=['tarefa'])
                    else:
                        total_atualizados += 1
                        # Fecha a tarefa se o status mudou para pago/cancelado
                        if tipo == 'pagar':
                            self._sincronizar_status_tarefa(vencimento)

                if not has_more:
                    break
                pagina += 1

        return total_criados, total_atualizados
