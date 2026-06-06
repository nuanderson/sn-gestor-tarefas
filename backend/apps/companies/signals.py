import calendar
from datetime import date
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Empresa, Pagamento

MESES = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


def _adicionar_meses(d, n):
    mes = d.month - 1 + n
    ano = d.year + mes // 12
    mes = mes % 12 + 1
    dia = min(d.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


@receiver(post_save, sender=Empresa)
def criar_recorrencia_pagamentos(sender, instance, created, **kwargs):
    """Ao criar uma empresa, gera 12 meses de pagamentos a partir de data_entrada."""
    if not created:
        return
    if instance.pagamentos.exists():
        return

    hoje = date.today()
    dia_venc = min(instance.data_entrada.day, 28)
    inicio = date(instance.data_entrada.year, instance.data_entrada.month, dia_venc)

    pagamentos = []
    for i in range(12):
        vencimento = _adicionar_meses(inicio, i)
        status = 'late' if vencimento < hoje else 'pending'
        referencia = f'{MESES[vencimento.month]} {vencimento.year}'

        pagamentos.append(Pagamento(
            empresa=instance,
            data=vencimento,
            valor=instance.mensalidade,
            status=status,
            referencia=referencia,
        ))

    Pagamento.objects.bulk_create(pagamentos)
