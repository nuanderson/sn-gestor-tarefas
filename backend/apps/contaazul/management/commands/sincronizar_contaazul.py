"""
Comando: python manage.py sincronizar_contaazul

Sincroniza as contas a pagar e a receber do Conta Azul para todas as
empresas conectadas (ou apenas a empresa indicada por --empresa-id).

Recomendado via cron: diariamente às 06h.
  0 6 * * * cd /app && python manage.py sincronizar_contaazul
"""
from django.core.management.base import BaseCommand

from apps.companies.models import Empresa
from apps.contaazul.services import ContaAzulClient


class Command(BaseCommand):
    help = 'Sincroniza vencimentos do Conta Azul para todas as empresas conectadas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id', type=int, default=None,
            help='Sincroniza apenas a empresa com este ID',
        )
        parser.add_argument(
            '--dias-atras', type=int, default=30,
            help='Quantos dias atrás incluir na busca (padrão: 30)',
        )
        parser.add_argument(
            '--dias-frente', type=int, default=90,
            help='Quantos dias à frente incluir na busca (padrão: 90)',
        )

    def handle(self, *args, **options):
        client = ContaAzulClient()

        if options['empresa_id']:
            empresas = Empresa.objects.filter(id=options['empresa_id'])
        else:
            empresas = Empresa.objects.filter(
                contaazul_token__isnull=False,
                status='active',
            )

        total = empresas.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('Nenhuma empresa conectada ao Conta Azul encontrada.'))
            return

        self.stdout.write(f'Sincronizando {total} empresa(s)...\n')

        sucesso = 0
        erros   = 0

        for empresa in empresas:
            try:
                criados, atualizados = client.sync_empresa(
                    empresa,
                    dias_atras=options['dias_atras'],
                    dias_frente=options['dias_frente'],
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {empresa.nome}: {criados} novo(s), {atualizados} atualizado(s)'
                    )
                )
                sucesso += 1
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f'  ✗ {empresa.nome}: ERRO — {exc}')
                )
                erros += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSincronização concluída: {sucesso} empresa(s) ok, {erros} erro(s).'
            )
        )
