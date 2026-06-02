"""
Modelos de Tarefas do SN Gestor — Fase 4.
Inclui: Tarefa, Tag, ChecklistItem, Comentario,
        HistoricoTarefa, TarefaDependencia,
        SessaoTarefa, PausaSessao, Notificacao.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


# ════════════════════════════════════════════════
# TAG
# ════════════════════════════════════════════════
class Tag(models.Model):
    nome      = models.CharField('Nome', max_length=50, unique=True)
    cor       = models.CharField('Cor (hex)', max_length=7, default='#C8A45E')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, related_name='tags_criadas',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Tag'
        verbose_name_plural = 'Tags'
        ordering            = ['nome']

    def __str__(self):
        return self.nome


# ════════════════════════════════════════════════
# TAREFA
# ════════════════════════════════════════════════
class Tarefa(models.Model):

    PRAZO_TIPO_CHOICES = [
        ('fixed',      'Data fixa'),
        ('continuous', 'Contínua (sem prazo)'),
        ('days',       'Em X dias'),
    ]

    RECORRENCIA_CHOICES = [
        ('none',     'Sem recorrência'),
        ('weekdays', 'Dias Úteis (seg–sex)'),
        ('daily',    'Diária'),
        ('weekly',   'Semanal'),
        ('biweekly', 'Quinzenal'),
        ('monthly',  'Mensal'),
        ('yearly',   'Anual'),
    ]

    STATUS_CHOICES = [
        ('pending',  'Pendente'),
        ('progress', 'Em Andamento'),
        ('done',     'Concluída'),
        ('late',     'Atrasada'),
    ]

    PRIORIDADE_CHOICES = [
        ('low',    'Baixa'),
        ('medium', 'Média'),
        ('high',   'Alta'),
        ('urgent', 'Urgente'),
    ]

    CATEGORIA_CHOICES = [
        ('fiscal',     'Fiscal'),
        ('financeiro', 'Financeiro'),
        ('contabil',   'Contábil'),
        ('folha',      'Folha de Pagamento'),
        ('juridico',   'Jurídico'),
        ('outros',     'Outros'),
    ]

    # ── Identificação ───────────────────────────
    titulo      = models.CharField('Título', max_length=300)
    empresa     = models.ForeignKey(
        'companies.Empresa', on_delete=models.CASCADE,
        related_name='tarefas', verbose_name='Empresa',
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tarefas',
        verbose_name='Responsável',
    )

    # ── Prazo ───────────────────────────────────
    prazo_tipo  = models.CharField(
        'Tipo de Prazo', max_length=12,
        choices=PRAZO_TIPO_CHOICES, default='fixed',
    )
    prazo       = models.DateField('Prazo', null=True, blank=True)
    prazo_dias  = models.PositiveSmallIntegerField(
        'Prazo em dias', null=True, blank=True,
        help_text='Usado quando prazo_tipo = "days"',
    )

    # ── Classificação ───────────────────────────
    prioridade  = models.CharField('Prioridade', max_length=10,
                                   choices=PRIORIDADE_CHOICES, default='medium')
    recorrencia = models.CharField('Recorrência', max_length=15,
                                   choices=RECORRENCIA_CHOICES, default='none')
    categoria   = models.CharField('Categoria', max_length=20,
                                   choices=CATEGORIA_CHOICES, blank=True)
    status      = models.CharField('Status', max_length=10,
                                   choices=STATUS_CHOICES, default='pending')
    tags        = models.ManyToManyField(Tag, blank=True, related_name='tarefas',
                                         verbose_name='Tags')

    # ── Conteúdo ────────────────────────────────
    observacoes    = models.TextField('Observações', blank=True)
    link_documento = models.URLField(
        'Link do Documento (Drive)', blank=True,
        help_text='Cole aqui o link do Google Drive',
    )

    # ── Recorrência ─────────────────────────────
    tarefa_origem = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recorrencias_geradas',
        verbose_name='Gerada a partir de',
    )

    # ── Controle ────────────────────────────────
    concluida_em  = models.DateTimeField('Concluída em', null=True, blank=True)
    criado_por    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='tarefas_criadas',
        verbose_name='Criado por',
    )
    criado_em     = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name        = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering            = ['prazo', '-prioridade']

    def __str__(self):
        return f'{self.titulo} — {self.empresa.nome}'

    # ── Propriedades ────────────────────────────
    @property
    def esta_atrasada(self):
        from datetime import date
        if self.status == 'done' or not self.prazo:
            return False
        return self.prazo < date.today()

    @property
    def e_continua(self):
        return self.prazo_tipo == 'continuous'

    @property
    def checklist_total(self):
        return self.checklist.count()

    @property
    def checklist_concluidos(self):
        return self.checklist.filter(concluido=True).count()

    @property
    def checklist_percentual(self):
        total = self.checklist_total
        return int((self.checklist_concluidos / total) * 100) if total else 0

    @property
    def tempo_total_minutos(self):
        """Soma de todas as sessões finalizadas."""
        return self.sessoes.filter(
            status='finalizada'
        ).aggregate(
            total=models.Sum('duracao_minutos')
        )['total'] or 0


# ════════════════════════════════════════════════
# DEPENDÊNCIA ENTRE TAREFAS
# ════════════════════════════════════════════════
class TarefaDependencia(models.Model):
    """
    Tarefa A depende de Tarefa B — só pode começar quando B estiver concluída.
    """
    tarefa     = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE,
        related_name='dependencias', verbose_name='Tarefa',
    )
    depende_de = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE,
        related_name='requerida_por', verbose_name='Depende de',
    )
    criado_em  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Dependência'
        verbose_name_plural = 'Dependências'
        unique_together     = ('tarefa', 'depende_de')

    def __str__(self):
        return f'"{self.tarefa.titulo}" depende de "{self.depende_de.titulo}"'


# ════════════════════════════════════════════════
# CHECKLIST
# ════════════════════════════════════════════════
class ChecklistItem(models.Model):
    tarefa    = models.ForeignKey(Tarefa, on_delete=models.CASCADE,
                                  related_name='checklist')
    titulo    = models.CharField('Item', max_length=200)
    concluido = models.BooleanField('Concluído', default=False)
    ordem     = models.PositiveSmallIntegerField('Ordem', default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'criado_em']

    def __str__(self):
        return f'[{"x" if self.concluido else " "}] {self.titulo}'


# ════════════════════════════════════════════════
# COMENTÁRIOS
# ════════════════════════════════════════════════
class Comentario(models.Model):
    tarefa    = models.ForeignKey(Tarefa, on_delete=models.CASCADE,
                                  related_name='comentarios')
    autor     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='comentarios',
    )
    texto     = models.TextField('Comentário')
    editado   = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']


# ════════════════════════════════════════════════
# HISTÓRICO
# ════════════════════════════════════════════════
class HistoricoTarefa(models.Model):
    ACAO_CHOICES = [
        ('criou',    'Criou a tarefa'),
        ('editou',   'Editou a tarefa'),
        ('concluiu', 'Concluiu a tarefa'),
        ('reabriu',  'Reabriu a tarefa'),
        ('comentou', 'Comentou na tarefa'),
        ('checklist','Atualizou checklist'),
        ('timer',    'Registrou tempo'),
    ]

    tarefa    = models.ForeignKey(Tarefa, on_delete=models.CASCADE,
                                  related_name='historico')
    usuario   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='historico_tarefas',
    )
    acao      = models.CharField('Ação', max_length=20, choices=ACAO_CHOICES)
    detalhe   = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']


# ════════════════════════════════════════════════
# TIMER — SESSÕES DE TRABALHO
# ════════════════════════════════════════════════
class SessaoTarefa(models.Model):
    """
    Registra uma sessão de trabalho em uma tarefa.
    Uma sessão pode ter várias pausas.
    """
    STATUS_CHOICES = [
        ('ativa',      'Ativa'),
        ('pausada',    'Pausada'),
        ('finalizada', 'Finalizada'),
    ]

    tarefa           = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE,
        related_name='sessoes', verbose_name='Tarefa',
    )
    usuario          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sessoes_trabalho', verbose_name='Usuário',
    )
    status           = models.CharField('Status', max_length=12,
                                        choices=STATUS_CHOICES, default='ativa')
    iniciado_em      = models.DateTimeField('Iniciado em', auto_now_add=True)
    finalizado_em    = models.DateTimeField('Finalizado em', null=True, blank=True)
    duracao_minutos  = models.PositiveIntegerField(
        'Duração (minutos)', null=True, blank=True,
        help_text='Calculado automaticamente ao finalizar',
    )

    class Meta:
        verbose_name        = 'Sessão de Trabalho'
        verbose_name_plural = 'Sessões de Trabalho'
        ordering            = ['-iniciado_em']

    def __str__(self):
        return f'{self.usuario.nome} — {self.tarefa.titulo} ({self.status})'

    def calcular_duracao(self):
        """
        Calcula duração total em minutos descontando as pausas.
        """
        fim = self.finalizado_em or timezone.now()
        total = (fim - self.iniciado_em).total_seconds()

        # Desconta cada pausa
        for pausa in self.pausas.all():
            retomado = pausa.retomado_em or timezone.now()
            total -= (retomado - pausa.pausado_em).total_seconds()

        return max(0, int(total / 60))

    @property
    def duracao_formatada(self):
        minutos = self.duracao_minutos or self.calcular_duracao()
        horas   = minutos // 60
        mins    = minutos % 60
        return f'{horas:02d}h{mins:02d}min'

    @property
    def tempo_decorrido_segundos(self):
        """Para o frontend atualizar o timer em tempo real."""
        if self.status == 'finalizada':
            return (self.finalizado_em - self.iniciado_em).total_seconds()
        fim = timezone.now()
        total = (fim - self.iniciado_em).total_seconds()
        for pausa in self.pausas.all():
            retomado = pausa.retomado_em or timezone.now()
            total -= (retomado - pausa.pausado_em).total_seconds()
        return max(0, total)


class PausaSessao(models.Model):
    """Registra cada pausa dentro de uma sessão de trabalho."""
    sessao      = models.ForeignKey(SessaoTarefa, on_delete=models.CASCADE,
                                    related_name='pausas')
    pausado_em  = models.DateTimeField('Pausado em', auto_now_add=True)
    retomado_em = models.DateTimeField('Retomado em', null=True, blank=True)

    class Meta:
        ordering = ['pausado_em']

    @property
    def duracao_pausa_minutos(self):
        if not self.retomado_em:
            return None
        return int((self.retomado_em - self.pausado_em).total_seconds() / 60)


# ════════════════════════════════════════════════
# NOTIFICAÇÕES INTERNAS
# ════════════════════════════════════════════════
class Notificacao(models.Model):
    TIPO_CHOICES = [
        ('tarefa_vencendo',  'Tarefa vencendo em breve'),
        ('tarefa_atrasada',  'Tarefa atrasada'),
        ('comentario_novo',  'Novo comentário'),
        ('tarefa_concluida', 'Tarefa concluída'),
        ('tarefa_criada',    'Nova tarefa atribuída'),
        ('timer_lembrete',   'Lembrete de timer ativo'),
    ]

    usuario   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notificacoes', verbose_name='Usuário',
    )
    tipo      = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    titulo    = models.CharField('Título', max_length=200)
    mensagem  = models.TextField('Mensagem')
    tarefa    = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE,
        null=True, blank=True, related_name='notificacoes',
    )
    lida      = models.BooleanField('Lida', default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering            = ['-criado_em']

    def __str__(self):
        return f'{self.usuario.nome} — {self.titulo}'
