from django.db import models
from django.conf import settings


class Documento(models.Model):
    TIPO_CHOICES = [
        ('contrato',  'Contrato'),
        ('relatorio', 'Relatório'),
        ('outro',     'Outro'),
    ]

    empresa    = models.ForeignKey(
        'companies.Empresa',
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Empresa',
    )
    titulo     = models.CharField('Título', max_length=200)
    tipo       = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='outro')
    url        = models.URLField('Link (Drive)', max_length=500)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_criados',
        verbose_name='Criado por',
    )
    criado_em  = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name        = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering            = ['-criado_em']

    def __str__(self):
        return f'{self.empresa.nome} — {self.titulo}'


class SolicitacaoBoleto(models.Model):
    STATUS_CHOICES = [
        ('pendente',   'Pendente'),
        ('em_analise', 'Em análise'),
        ('enviado',    'Enviado'),
        ('cancelado',  'Cancelado'),
    ]

    empresa      = models.ForeignKey(
        'companies.Empresa',
        on_delete=models.CASCADE,
        related_name='solicitacoes_boleto',
        verbose_name='Empresa',
    )
    referencia   = models.CharField('Referência', max_length=200, blank=True)
    valor        = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2, null=True, blank=True)
    vencimento   = models.DateField('Vencimento desejado', null=True, blank=True)
    observacoes  = models.TextField('Observações', blank=True)
    status       = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pendente')
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='solicitacoes_boleto',
        verbose_name='Solicitado por',
    )
    criado_em    = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name        = 'Solicitação de Boleto'
        verbose_name_plural = 'Solicitações de Boleto'
        ordering            = ['-criado_em']

    def __str__(self):
        return f'{self.empresa.nome} — {self.referencia or self.criado_em.date()}'
