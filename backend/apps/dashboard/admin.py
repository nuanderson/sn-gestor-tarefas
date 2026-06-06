from django.contrib import admin
from .models import MetaMensal


@admin.register(MetaMensal)
class MetaMensalAdmin(admin.ModelAdmin):
    list_display  = ('colaborador', 'mes', 'ano', 'meta_tarefas', 'meta_horas', 'criado_por')
    list_filter   = ('ano', 'mes')
    search_fields = ('colaborador__nome',)
    ordering      = ('-ano', '-mes')
