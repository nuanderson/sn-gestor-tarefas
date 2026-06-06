from django.contrib import admin
from .models import Tarefa, ChecklistItem, Comentario, HistoricoTarefa


class ChecklistInline(admin.TabularInline):
    model  = ChecklistItem
    extra  = 0
    fields = ('titulo', 'concluido', 'ordem')


class ComentarioInline(admin.TabularInline):
    model      = Comentario
    extra      = 0
    fields     = ('autor', 'texto', 'criado_em')
    readonly_fields = ('criado_em',)


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'empresa', 'responsavel', 'prazo', 'prioridade', 'status', 'recorrencia')
    list_filter   = ('status', 'prioridade', 'recorrencia', 'categoria', 'empresa')
    search_fields = ('titulo', 'empresa__nome', 'responsavel__nome')
    readonly_fields = ('criado_em', 'atualizado_em', 'concluida_em')
    inlines       = [ChecklistInline, ComentarioInline]
    date_hierarchy = 'prazo'


@admin.register(HistoricoTarefa)
class HistoricoAdmin(admin.ModelAdmin):
    list_display  = ('tarefa', 'usuario', 'acao', 'criado_em')
    list_filter   = ('acao',)
    readonly_fields = ('tarefa', 'usuario', 'acao', 'detalhe', 'criado_em')
