"""
Utilitários de recorrência de tarefas.
"""
import calendar
from datetime import date, timedelta


def proximo_prazo(data_atual: date, recorrencia: str) -> date | None:
    """
    Calcula o próximo prazo com base na recorrência.

    Regras:
    - weekdays → próximo dia útil (seg–sex), pulando sáb e dom
    - daily     → +1 dia (inclui fins de semana)
    - weekly    → +7 dias
    - biweekly  → +14 dias
    - monthly   → mesmo dia no mês seguinte (ajusta fim de mês)
    - yearly    → mesmo dia no ano seguinte
    - none/None → retorna None (sem próxima ocorrência)
    """
    if not recorrencia or recorrencia == 'none':
        return None

    d = data_atual

    if recorrencia == 'weekdays':
        d += timedelta(days=1)
        # Pula sábado (5) e domingo (6)
        while d.weekday() >= 5:
            d += timedelta(days=1)

    elif recorrencia == 'daily':
        d += timedelta(days=1)

    elif recorrencia == 'weekly':
        d += timedelta(weeks=1)

    elif recorrencia == 'biweekly':
        d += timedelta(weeks=2)

    elif recorrencia == 'monthly':
        mes  = d.month + 1
        ano  = d.year
        if mes > 12:
            mes = 1
            ano += 1
        # Garante dia válido no novo mês (ex: 31/jan → 28/fev)
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        dia = min(d.day, ultimo_dia)
        d = date(ano, mes, dia)

    elif recorrencia == 'yearly':
        try:
            d = date(d.year + 1, d.month, d.day)
        except ValueError:
            # 29/fev em ano não bissexto → 28/fev
            d = date(d.year + 1, d.month, d.day - 1)

    else:
        return None

    return d


def label_recorrencia(recorrencia: str) -> str:
    labels = {
        'none':     'Sem recorrência',
        'weekdays': 'Dias Úteis (seg–sex)',
        'daily':    'Diária',
        'weekly':   'Semanal',
        'biweekly': 'Quinzenal',
        'monthly':  'Mensal',
        'yearly':   'Anual',
    }
    return labels.get(recorrencia, recorrencia)
