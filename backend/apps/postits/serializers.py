from rest_framework import serializers
from .models import PostIt


class PostItSerializer(serializers.ModelSerializer):
    autor_nome    = serializers.CharField(source='autor.nome', read_only=True)
    autor_iniciais = serializers.CharField(source='autor.iniciais', read_only=True)
    e_meu         = serializers.SerializerMethodField()

    class Meta:
        model  = PostIt
        fields = [
            'id', 'texto', 'cor', 'visibilidade',
            'fixado', 'ordem',
            'autor', 'autor_nome', 'autor_iniciais', 'e_meu',
            'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['autor', 'criado_em', 'atualizado_em']

    def get_e_meu(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.autor_id == request.user.id
        return False
