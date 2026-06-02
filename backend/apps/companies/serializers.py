from rest_framework import serializers
from apps.accounts.serializers import UsuarioSerializer
from .models import Empresa, Pagamento


class PagamentoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = Pagamento
        fields = ['id', 'empresa', 'data', 'valor', 'status', 'status_display', 'referencia', 'criado_em']
        read_only_fields = ['id', 'criado_em']


class EmpresaSerializer(serializers.ModelSerializer):
    """Listagem — sem pagamentos aninhados."""
    status_display      = serializers.CharField(source='get_status_display', read_only=True)
    responsavel_nome    = serializers.CharField(source='responsavel.nome', read_only=True)
    total_recebido      = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pagamentos_pendentes = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Empresa
        fields = [
            'id', 'nome', 'cnpj', 'data_entrada', 'mensalidade',
            'responsavel', 'responsavel_nome', 'status', 'status_display',
            'observacoes', 'total_recebido', 'pagamentos_pendentes',
            'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class EmpresaDetalheSerializer(EmpresaSerializer):
    """Detalhe — inclui pagamentos aninhados."""
    pagamentos = PagamentoSerializer(many=True, read_only=True)

    class Meta(EmpresaSerializer.Meta):
        fields = EmpresaSerializer.Meta.fields + ['pagamentos']
