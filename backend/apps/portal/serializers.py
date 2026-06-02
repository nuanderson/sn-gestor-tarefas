from rest_framework import serializers
from apps.companies.models import Pagamento
from .models import Documento, SolicitacaoBoleto


class PagamentoRecorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Pagamento
        fields = ['id', 'referencia', 'data', 'valor', 'status']


class DocumentoSerializer(serializers.ModelSerializer):
    criado_por_nome = serializers.CharField(source='criado_por.nome', read_only=True)
    tipo_display    = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = Documento
        fields = [
            'id', 'empresa', 'titulo', 'tipo', 'tipo_display',
            'url', 'criado_por', 'criado_por_nome', 'criado_em',
        ]
        read_only_fields = ['criado_por', 'criado_em']


class SolicitacaoBoletoSerializer(serializers.ModelSerializer):
    status_display      = serializers.CharField(source='get_status_display', read_only=True)
    solicitado_por_nome = serializers.CharField(source='solicitado_por.nome', read_only=True)

    class Meta:
        model  = SolicitacaoBoleto
        fields = [
            'id', 'empresa', 'referencia', 'valor', 'vencimento',
            'observacoes', 'status', 'status_display',
            'solicitado_por', 'solicitado_por_nome', 'criado_em',
        ]
        read_only_fields = ['empresa', 'solicitado_por', 'criado_em', 'status']
