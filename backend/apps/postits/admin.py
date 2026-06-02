from django.contrib import admin
from .models import PostIt


@admin.register(PostIt)
class PostItAdmin(admin.ModelAdmin):
    list_display  = ('autor', 'visibilidade', 'cor', 'fixado', 'texto_resumido', 'criado_em')
    list_filter   = ('visibilidade', 'cor', 'fixado')
    search_fields = ('texto', 'autor__nome')
    ordering      = ('-criado_em',)

    def texto_resumido(self, obj):
        return obj.texto[:60] + ('...' if len(obj.texto) > 60 else '')
    texto_resumido.short_description = 'Texto'
