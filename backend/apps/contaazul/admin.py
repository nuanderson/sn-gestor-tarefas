from django.contrib import admin
from .models import ContaAzulToken, ContaAzulVencimento


@admin.register(ContaAzulToken)
class ContaAzulTokenAdmin(admin.ModelAdmin):
    list_display  = ['empresa', 'ativo', 'expires_at', 'atualizado_em']
    readonly_fields = ['access_token', 'refresh_token', 'expires_at', 'criado_em', 'atualizado_em']

    @admin.display(boolean=True, description='Ativo')
    def ativo(self, obj):
        return obj.ativo


@admin.register(ContaAzulVencimento)
class ContaAzulVencimentoAdmin(admin.ModelAdmin):
    list_display   = ['empresa', 'tipo', 'descricao', 'valor', 'data_vencimento', 'status', 'pessoa_nome']
    list_filter    = ['empresa', 'tipo', 'status']
    search_fields  = ['descricao', 'pessoa_nome']
    date_hierarchy = 'data_vencimento'
    readonly_fields = ['contaazul_id', 'sincronizado_em']
