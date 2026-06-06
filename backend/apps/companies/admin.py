from django.contrib import admin
from .models import Empresa, Pagamento


class PagamentoInline(admin.TabularInline):
    model  = Pagamento
    extra  = 0
    fields = ('data', 'valor', 'status', 'referencia')


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'cnpj', 'data_entrada', 'mensalidade', 'responsavel', 'status')
    list_filter   = ('status',)
    search_fields = ('nome', 'cnpj')
    inlines       = [PagamentoInline]
    readonly_fields = ('criado_em', 'atualizado_em')


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display  = ('empresa', 'data', 'valor', 'status', 'referencia')
    list_filter   = ('status', 'empresa')
    search_fields = ('empresa__nome', 'referencia')
