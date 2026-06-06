from rest_framework import serializers
from .models import ContaAzulToken, ContaAzulVencimento


class ContaAzulVencimentoSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    tipo_display   = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContaAzulVencimento
        fields = [
            'id', 'empresa', 'empresa_nome',
            'contaazul_id', 'tipo', 'tipo_display',
            'descricao', 'valor',
            'data_vencimento', 'data_pagamento',
            'status', 'status_display',
            'pessoa_nome', 'parcela_numero', 'parcela_total',
            'tarefa_id', 'sincronizado_em',
        ]
        read_only_fields = fields


class ContaAzulTokenStatusSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    ativo        = serializers.BooleanField(read_only=True)

    class Meta:
        model = ContaAzulToken
        fields = ['id', 'empresa', 'empresa_nome', 'expires_at', 'ativo', 'atualizado_em']
        read_only_fields = fields
