"""
Modelos de Empresas e Pagamentos do SN Gestor.
"""
from django.db import models
from django.conf import settings


class Empresa(models.Model):
    STATUS_CHOICES = [
        ('active',   'Ativo'),
        ('inactive', 'Inativo'),
    ]

    nome          = models.CharField('Razão Social', max_length=200)
    cnpj          = models.CharField('CNPJ', max_length=18, unique=True)
    data_entrada  = models.DateField('Data de Entrada')
    mensalidade   = models.DecimalField('Mensalidade (R$)', max_digits=10, decimal_places=2)
    responsavel   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='empresas_responsavel',
        verbose_name='Responsável Interno',
    )
    status        = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='active')
    colaboradores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='empresas_colaborador',
        verbose_name='Colaboradores',
    )
    observacoes   = models.TextField('Observações', blank=True)
    criado_em     = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name        = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering            = ['nome']

    def __str__(self):
        return self.nome

    @property
    def total_recebido(self):
        return self.pagamentos.filter(status='paid').aggregate(
            total=models.Sum('valor')
        )['total'] or 0

    @property
    def pagamentos_pendentes(self):
        return self.pagamentos.exclude(status='paid').count()


class Pagamento(models.Model):
    STATUS_CHOICES = [
        ('paid',    'Pago'),
        ('pending', 'Pendente'),
        ('late',    'Atrasado'),
    ]

    empresa    = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='pagamentos',
        verbose_name='Empresa',
    )
    data       = models.DateField('Data do Pagamento')
    valor      = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    status     = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='pending')
    referencia = models.CharField('Referência', max_length=200, blank=True)
    criado_em  = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name        = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering            = ['-data']

    def __str__(self):
        return f'{self.empresa.nome} — {self.data} — R$ {self.valor}'
