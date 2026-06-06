from rest_framework import serializers
from .models import MetaMensal


class MetaMensalSerializer(serializers.ModelSerializer):
    colaborador_nome  = serializers.CharField(source='colaborador.nome', read_only=True)
    colaborador_iniciais = serializers.CharField(source='colaborador.iniciais', read_only=True)
    periodo           = serializers.CharField(source='periodo_display', read_only=True)

    class Meta:
        model  = MetaMensal
        fields = [
            'id', 'colaborador', 'colaborador_nome', 'colaborador_iniciais',
            'mes', 'ano', 'periodo',
            'meta_tarefas', 'meta_horas',
            'observacao',
            'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']
