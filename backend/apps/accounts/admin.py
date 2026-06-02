"""
Configuração do painel administrativo para Usuários.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Colunas exibidas na listagem
    list_display  = ('nome', 'email', 'perfil', 'cargo', 'is_active', 'criado_em')
    list_filter   = ('perfil', 'is_active', 'is_staff')
    search_fields = ('nome', 'email', 'cargo')
    ordering      = ('nome',)

    # Campos exibidos na edição
    fieldsets = (
        ('Identificação', {'fields': ('email', 'password')}),
        ('Dados pessoais', {'fields': ('nome', 'cargo', 'telefone')}),
        ('Acesso',         {'fields': ('perfil', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissões',     {'fields': ('groups', 'user_permissions')}),
        ('Datas',          {'fields': ('last_login', 'criado_em', 'atualizado_em'),
                            'classes': ('collapse',)}),
    )
    readonly_fields = ('criado_em', 'atualizado_em', 'last_login')

    # Campos ao criar um novo usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'perfil', 'cargo', 'password1', 'password2'),
        }),
    )
