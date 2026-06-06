"""
Modelos do Dashboard — Fase 5.
MetaMensal: metas de produtividade por colaborador/mês.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class MetaMensal(models.Model):
    """
    Define metas mensais de produtividade para um colaborador.
    A Suzane cadastra: "Em junho/2026, o João deve concluir 20 tarefas e registrar 80h."
    O dashboard calcula o progresso automaticamente comparando com os dados reais.
    """
    colaborador      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='metas_mensais',
        verbose_name='Colaborador',
    )
    mes              = models.PositiveSmallIntegerField(
        'Mês',
        validators=[MinValueValidator(1)],
        help_text='1 = Janeiro, 12 = Dezembro',
    )
    ano              = models.PositiveSmallIntegerField('Ano')
    meta_tarefas     = models.PositiveSmallIntegerField(
        'Meta de tarefas concluídas',
        default=0,
        help_text='Quantas tarefas o colaborador deve concluir neste mês',
    )
    meta_horas       = models.PositiveSmallIntegerField(
        'Meta de horas registradas',
        default=0,
        help_text='Quantas horas de timer o colaborador deve registrar',
    )
    observacao       = models.TextField('Observação', blank=True)
    criado_por       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='metas_criadas',
        verbose_name='Criado por',
    )
    criado_em        = models.DateTimeField(auto_now_add=True)
    atualizado_em    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Meta Mensal'
        verbose_name_plural = 'Metas Mensais'
        ordering            = ['-ano', '-mes', 'colaborador__nome']
        unique_together     = ('colaborador', 'mes', 'ano')

    def __str__(self):
        return f'{self.colaborador.nome} — {self.mes:02d}/{self.ano}'

    @property
    def periodo_display(self):
        from calendar import month_name
        meses_pt = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
        ]
        return f'{meses_pt[self.mes]}/{self.ano}'
