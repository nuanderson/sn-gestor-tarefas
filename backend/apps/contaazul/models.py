"""
Modelos da integração Conta Azul.
ContaAzulToken  — armazena o par access/refresh token por empresa.
ContaAzulVencimento — espelho local das contas a pagar/receber sincronizadas.
"""
from django.db import models


class ContaAzulToken(models.Model):
    empresa = models.OneToOneField(
        'companies.Empresa',
        on_delete=models.CASCADE,
        related_name='contaazul_token',
        verbose_name='Empresa',
    )
    access_token  = models.TextField('Access Token')
    refresh_token = models.TextField('Refresh Token')
    expires_at    = models.DateTimeField('Expira em')
    criado_em     = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name        = 'Token Conta Azul'
        verbose_name_plural = 'Tokens Conta Azul'

    def __str__(self):
        return f'Token ContaAzul — {self.empresa.nome}'

    @property
    def ativo(self):
        from django.utils import timezone
        return self.expires_at > timezone.now()


class ContaAzulVencimento(models.Model):
    TIPO_CHOICES = [
        ('pagar',   'A Pagar'),
        ('receber', 'A Receber'),
    ]
    STATUS_CHOICES = [
        ('pendente',  'Pendente'),
        ('pago',      'Pago'),
        ('atrasado',  'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]

    empresa         = models.ForeignKey(
        'companies.Empresa',
        on_delete=models.CASCADE,
        related_name='vencimentos_contaazul',
        verbose_name='Empresa',
    )
    contaazul_id    = models.CharField('ID Conta Azul', max_length=100)
    tipo            = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    descricao       = models.CharField('Descrição', max_length=500)
    valor           = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento  = models.DateField('Data de Pagamento', null=True, blank=True)
    status          = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pendente')
    pessoa_nome     = models.CharField('Pessoa / Empresa', max_length=300, blank=True)
    parcela_numero  = models.PositiveSmallIntegerField('Parcela Nº', null=True, blank=True)
    parcela_total   = models.PositiveSmallIntegerField('Total de Parcelas', null=True, blank=True)
    sincronizado_em = models.DateTimeField('Sincronizado em', auto_now=True)
    tarefa          = models.OneToOneField(
        'tasks.Tarefa',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vencimento_contaazul',
        verbose_name='Tarefa gerada',
    )

    class Meta:
        verbose_name        = 'Vencimento Conta Azul'
        verbose_name_plural = 'Vencimentos Conta Azul'
        ordering            = ['data_vencimento']
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'contaazul_id', 'tipo'],
                name='unique_vencimento_por_empresa',
            )
        ]

    def __str__(self):
        return f'{self.empresa.nome} | {self.get_tipo_display()} | {self.descricao[:50]} | {self.data_vencimento}'
