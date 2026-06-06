"""
Modelo de Post-it — Fase 7.
Cada post-it pode ser privado (só o dono vê) ou de equipe (todos veem).
Apenas o autor pode editar ou excluir o próprio post-it.
"""
from django.db import models
from django.conf import settings


class PostIt(models.Model):

    COR_CHOICES = [
        ('amarelo', 'Amarelo'),
        ('verde',   'Verde'),
        ('azul',    'Azul'),
        ('rosa',    'Rosa'),
        ('roxo',    'Roxo'),
    ]

    VISIBILIDADE_CHOICES = [
        ('privado', 'Privado — só eu vejo'),
        ('equipe',  'Equipe — todos veem'),
    ]

    # ── Conteúdo ────────────────────────────────
    texto        = models.TextField('Texto')
    cor          = models.CharField(
        'Cor', max_length=10,
        choices=COR_CHOICES, default='amarelo',
    )

    # ── Visibilidade ─────────────────────────────
    visibilidade = models.CharField(
        'Visibilidade', max_length=10,
        choices=VISIBILIDADE_CHOICES, default='privado',
    )

    # ── Organização ──────────────────────────────
    fixado       = models.BooleanField(
        'Fixado', default=False,
        help_text='Post-its fixados aparecem sempre no topo',
    )
    ordem        = models.PositiveSmallIntegerField(
        'Ordem', default=0,
        help_text='Posição no quadro (menor = mais à esquerda/topo)',
    )

    # ── Controle ─────────────────────────────────
    autor        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='postits',
        verbose_name='Autor',
    )
    criado_em    = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Post-it'
        verbose_name_plural = 'Post-its'
        ordering            = ['-fixado', 'ordem', '-criado_em']

    def __str__(self):
        vis = '🔒' if self.visibilidade == 'privado' else '👥'
        return f'{vis} {self.autor.primeiro_nome}: {self.texto[:50]}'
