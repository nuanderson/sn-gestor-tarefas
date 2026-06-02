from django.contrib import admin
from .models import Documento, SolicitacaoBoleto


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'empresa', 'tipo', 'criado_por', 'criado_em')
    list_filter   = ('tipo', 'empresa')
    search_fields = ('titulo', 'empresa__nome')


@admin.register(SolicitacaoBoleto)
class SolicitacaoBoletoAdmin(admin.ModelAdmin):
    list_display  = ('empresa', 'referencia', 'valor', 'vencimento', 'status', 'criado_em')
    list_filter   = ('status', 'empresa')
    search_fields = ('empresa__nome', 'referencia')
    list_editable = ('status',)
