"""
Comando: python manage.py contaazul_ativar

Uso no fluxo de desenvolvimento (redirect_uri = https://contaazul.com):

  1. Rode sem argumentos para obter a URL de autorização:
       python manage.py contaazul_ativar --empresa-id 1

  2. Abra a URL no navegador, faça login com as credenciais da conta de teste
     e copie o valor do parâmetro ?code=... da URL de destino.

  3. Passe o código para trocar pelos tokens:
       python manage.py contaazul_ativar --empresa-id 1 --code SEU_CODE_AQUI

  4. Opcionalmente, sincronize já:
       python manage.py contaazul_ativar --empresa-id 1 --code SEU_CODE_AQUI --sync
"""
import secrets

from django.core.management.base import BaseCommand, CommandError

from apps.companies.models import Empresa
from apps.contaazul.models import ContaAzulToken
from apps.contaazul.services import ContaAzulClient


class Command(BaseCommand):
    help = 'Ativa a integração Conta Azul para uma empresa (fluxo manual de dev)'

    def add_arguments(self, parser):
        parser.add_argument('--empresa-id', type=int, required=True,
                            help='ID da empresa no SN Gestor')
        parser.add_argument('--code', type=str, default=None,
                            help='Authorization code copiado da URL de redirect')
        parser.add_argument('--sync', action='store_true',
                            help='Sincroniza vencimentos imediatamente após ativar')

    def handle(self, *args, **options):
        try:
            empresa = Empresa.objects.get(pk=options['empresa_id'])
        except Empresa.DoesNotExist:
            raise CommandError(f"Empresa com ID {options['empresa_id']} não encontrada.")

        client = ContaAzulClient()

        # Sem código → mostra a URL para o usuário visitar
        if not options['code']:
            state = secrets.token_urlsafe(16)
            url = client.get_authorization_url(state)
            self.stdout.write('\n' + self.style.WARNING('=== PASSO 1: Autorize no Conta Azul ==='))
            self.stdout.write(f'\nEmpresa: {empresa.nome}')
            self.stdout.write('\nAbra a URL abaixo no navegador e faça login com a conta de teste:')
            self.stdout.write(self.style.HTTP_INFO(f'\n  {url}\n'))
            self.stdout.write('Após o redirecionamento para contaazul.com, copie o valor de ?code=...')
            self.stdout.write('\nEm seguida rode:')
            self.stdout.write(self.style.SUCCESS(
                f'  python manage.py contaazul_ativar --empresa-id {empresa.id} --code SEU_CODE_AQUI\n'
            ))
            return

        # Com código → troca pelo token
        self.stdout.write(f'\nTrocando código por tokens para "{empresa.nome}"...')
        try:
            from django.utils import timezone
            from datetime import timedelta
            import requests as req

            data = client.exchange_code(options['code'])
        except req.HTTPError as exc:
            raise CommandError(f'Erro na troca do código: {exc}\n'
                               f'Verifique se o código ainda é válido (expira em 3 minutos).')

        from django.utils import timezone
        from datetime import timedelta

        expires_at = timezone.now() + timedelta(seconds=data.get('expires_in', 3600))
        token_obj, created = ContaAzulToken.objects.update_or_create(
            empresa=empresa,
            defaults={
                'access_token':  data['access_token'],
                'refresh_token': data['refresh_token'],
                'expires_at':    expires_at,
            },
        )

        acao = 'criado' if created else 'atualizado'
        self.stdout.write(self.style.SUCCESS(
            f'\nToken {acao} com sucesso!'
            f'\n  Empresa:   {empresa.nome}'
            f'\n  Expira em: {expires_at.strftime("%d/%m/%Y %H:%M:%S")}'
        ))

        # Sincronização imediata opcional
        if options['sync']:
            self.stdout.write('\nSincronizando vencimentos...')
            try:
                criados, atualizados = client.sync_empresa(empresa)
                self.stdout.write(self.style.SUCCESS(
                    f'Sync concluído: {criados} novo(s), {atualizados} atualizado(s).'
                ))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Erro no sync: {exc}'))
