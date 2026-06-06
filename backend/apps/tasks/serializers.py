from rest_framework import serializers
from .models import (
    Tag, Tarefa, TarefaDependencia, ChecklistItem,
    Comentario, HistoricoTarefa,
    SessaoTarefa, PausaSessao, Notificacao,
)
from .utils import label_recorrencia


# ── Tags ────────────────────────────────────────────────────────
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tag
        fields = ['id', 'nome', 'cor', 'criado_em']
        read_only_fields = ['id', 'criado_em']


# ── Checklist ───────────────────────────────────────────────────
class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ChecklistItem
        fields = ['id', 'tarefa', 'titulo', 'concluido', 'ordem', 'criado_em']
        read_only_fields = ['id', 'criado_em']


# ── Comentários ─────────────────────────────────────────────────
class ComentarioSerializer(serializers.ModelSerializer):
    autor_nome     = serializers.CharField(source='autor.nome', read_only=True)
    autor_iniciais = serializers.CharField(source='autor.iniciais', read_only=True)

    class Meta:
        model  = Comentario
        fields = ['id', 'tarefa', 'autor', 'autor_nome', 'autor_iniciais',
                  'texto', 'editado', 'criado_em']
        read_only_fields = ['id', 'autor', 'editado', 'criado_em']


# ── Histórico ───────────────────────────────────────────────────
class HistoricoTarefaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    acao_display = serializers.CharField(source='get_acao_display', read_only=True)

    class Meta:
        model  = HistoricoTarefa
        fields = ['id', 'acao', 'acao_display', 'usuario_nome', 'detalhe', 'criado_em']
        read_only_fields = fields


# ── Dependências ────────────────────────────────────────────────
class TarefaDependenciaSerializer(serializers.ModelSerializer):
    depende_de_titulo  = serializers.CharField(source='depende_de.titulo', read_only=True)
    depende_de_status  = serializers.CharField(source='depende_de.status', read_only=True)
    depende_de_empresa = serializers.CharField(source='depende_de.empresa.nome', read_only=True)

    class Meta:
        model  = TarefaDependencia
        fields = ['id', 'depende_de', 'depende_de_titulo',
                  'depende_de_status', 'depende_de_empresa']
        read_only_fields = ['id']

    def validate(self, data):
        tarefa     = self.context.get('tarefa')
        depende_de = data.get('depende_de')
        if tarefa and depende_de and tarefa.id == depende_de.id:
            raise serializers.ValidationError('Uma tarefa não pode depender de si mesma.')
        return data


# ── Timer ───────────────────────────────────────────────────────
class PausaSessaoSerializer(serializers.ModelSerializer):
    duracao_pausa_minutos = serializers.IntegerField(read_only=True)

    class Meta:
        model  = PausaSessao
        fields = ['id', 'pausado_em', 'retomado_em', 'duracao_pausa_minutos']
        read_only_fields = fields


class SessaoTarefaSerializer(serializers.ModelSerializer):
    usuario_nome          = serializers.CharField(source='usuario.nome', read_only=True)
    duracao_formatada     = serializers.CharField(read_only=True)
    tempo_decorrido_segundos = serializers.FloatField(read_only=True)
    pausas                = PausaSessaoSerializer(many=True, read_only=True)
    status_display        = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = SessaoTarefa
        fields = [
            'id', 'tarefa', 'usuario', 'usuario_nome', 'status', 'status_display',
            'iniciado_em', 'finalizado_em', 'duracao_minutos', 'duracao_formatada',
            'tempo_decorrido_segundos', 'pausas',
        ]
        read_only_fields = fields


# ── Notificações ─────────────────────────────────────────────────
class NotificacaoSerializer(serializers.ModelSerializer):
    tipo_display   = serializers.CharField(source='get_tipo_display', read_only=True)
    tarefa_titulo  = serializers.CharField(source='tarefa.titulo', read_only=True)

    class Meta:
        model  = Notificacao
        fields = ['id', 'tipo', 'tipo_display', 'titulo', 'mensagem',
                  'tarefa', 'tarefa_titulo', 'lida', 'criado_em']
        read_only_fields = fields


# ── Tarefa ───────────────────────────────────────────────────────
class TarefaSerializer(serializers.ModelSerializer):
    empresa_nome         = serializers.CharField(source='empresa.nome', read_only=True)
    responsavel_nome     = serializers.CharField(source='responsavel.nome', read_only=True)
    status_display       = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display   = serializers.CharField(source='get_prioridade_display', read_only=True)
    prazo_tipo_display   = serializers.CharField(source='get_prazo_tipo_display', read_only=True)
    categoria_display    = serializers.CharField(source='get_categoria_display', read_only=True)
    recorrencia_display  = serializers.SerializerMethodField()
    esta_atrasada        = serializers.BooleanField(read_only=True)
    e_continua           = serializers.BooleanField(read_only=True)
    checklist_total      = serializers.IntegerField(read_only=True)
    checklist_concluidos = serializers.IntegerField(read_only=True)
    checklist_percentual = serializers.IntegerField(read_only=True)
    tempo_total_minutos  = serializers.IntegerField(read_only=True)
    total_comentarios    = serializers.SerializerMethodField()
    tags                 = TagSerializer(many=True, read_only=True)
    tags_ids             = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True,
        source='tags', required=False,
    )

    class Meta:
        model  = Tarefa
        fields = [
            'id', 'titulo', 'empresa', 'empresa_nome',
            'responsavel', 'responsavel_nome',
            'prazo_tipo', 'prazo_tipo_display', 'prazo', 'prazo_dias',
            'prioridade', 'prioridade_display',
            'recorrencia', 'recorrencia_display',
            'categoria', 'categoria_display',
            'status', 'status_display',
            'observacoes', 'link_documento',
            'tags', 'tags_ids',
            'esta_atrasada', 'e_continua',
            'checklist_total', 'checklist_concluidos', 'checklist_percentual',
            'tempo_total_minutos', 'total_comentarios',
            'concluida_em', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['id', 'concluida_em', 'criado_em', 'atualizado_em']

    def get_recorrencia_display(self, obj):
        return label_recorrencia(obj.recorrencia)

    def get_total_comentarios(self, obj):
        return obj.comentarios.count()

    def validate(self, data):
        prazo_tipo = data.get('prazo_tipo', getattr(self.instance, 'prazo_tipo', 'fixed'))
        if prazo_tipo == 'fixed' and not data.get('prazo') and not getattr(self.instance, 'prazo', None):
            raise serializers.ValidationError({'prazo': 'Informe a data de prazo.'})
        if prazo_tipo == 'days' and not data.get('prazo_dias'):
            raise serializers.ValidationError({'prazo_dias': 'Informe o número de dias.'})
        return data


class TarefaDetalheSerializer(TarefaSerializer):
    """Detalhe completo — inclui listas aninhadas."""
    checklist   = ChecklistItemSerializer(many=True, read_only=True)
    comentarios = ComentarioSerializer(many=True, read_only=True)
    historico   = HistoricoTarefaSerializer(many=True, read_only=True)
    dependencias = TarefaDependenciaSerializer(many=True, read_only=True)
    sessoes     = SessaoTarefaSerializer(many=True, read_only=True)

    class Meta(TarefaSerializer.Meta):
        fields = TarefaSerializer.Meta.fields + [
            'checklist', 'comentarios', 'historico', 'dependencias', 'sessoes',
        ]


class TarefaCriarSerializer(TarefaSerializer):
    """Criação — registra histórico automaticamente."""

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        request = self.context.get('request')
        validated_data['criado_por'] = request.user if request else None

        # Tarefas em dias → calcula prazo
        if validated_data.get('prazo_tipo') == 'days' and validated_data.get('prazo_dias'):
            from datetime import date, timedelta
            validated_data['prazo'] = date.today() + timedelta(days=validated_data['prazo_dias'])

        tarefa = Tarefa.objects.create(**validated_data)
        if tags:
            tarefa.tags.set(tags)

        HistoricoTarefa.objects.create(
            tarefa=tarefa,
            usuario=request.user if request else None,
            acao='criou',
            detalhe=f'Tarefa criada — prazo: {tarefa.prazo or "sem prazo"}',
        )
        return tarefa


# ── Produtividade ─────────────────────────────────────────────────
class ProdutividadeUsuarioSerializer(serializers.Serializer):
    usuario_id           = serializers.IntegerField()
    usuario_nome         = serializers.CharField()
    total_tarefas        = serializers.IntegerField()
    tarefas_concluidas   = serializers.IntegerField()
    tarefas_atrasadas    = serializers.IntegerField()
    taxa_conclusao       = serializers.FloatField()
    tempo_total_minutos  = serializers.IntegerField()
    tempo_total_formatado = serializers.CharField()
    media_minutos_tarefa = serializers.FloatField()
    por_categoria        = serializers.DictField()
