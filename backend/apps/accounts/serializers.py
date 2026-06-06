"""
Serializers de Usuário — convertem objetos Python em JSON e vice-versa.
"""
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer completo — usado para listar e detalhar usuários."""
    perfil_display = serializers.CharField(
        source='get_perfil_display', read_only=True
    )
    iniciais = serializers.CharField(read_only=True)

    class Meta:
        model  = Usuario
        fields = [
            'id', 'email', 'nome', 'perfil', 'perfil_display',
            'cargo', 'telefone', 'is_active', 'iniciais',
            'empresa_cliente', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class UsuarioCriarSerializer(serializers.ModelSerializer):
    """Serializer para criar um novo usuário (inclui senha)."""
    senha = serializers.CharField(
        write_only=True, min_length=8,
        error_messages={'min_length': 'A senha deve ter ao menos 8 caracteres.'}
    )
    confirmar_senha = serializers.CharField(write_only=True)

    class Meta:
        model  = Usuario
        fields = [
            'email', 'nome', 'perfil', 'cargo',
            'telefone', 'empresa_cliente', 'senha', 'confirmar_senha',
        ]

    def validate(self, data):
        if data['senha'] != data.pop('confirmar_senha'):
            raise serializers.ValidationError({'confirmar_senha': 'As senhas não conferem.'})
        return data

    def create(self, validated_data):
        senha = validated_data.pop('senha')
        usuario = Usuario(**validated_data)
        usuario.set_password(senha)
        usuario.save()
        return usuario


class UsuarioAtualizarSerializer(serializers.ModelSerializer):
    """Serializer para editar dados do usuário (sem senha)."""
    class Meta:
        model  = Usuario
        fields = ['nome', 'perfil', 'cargo', 'telefone', 'is_active', 'empresa_cliente']


class AlterarSenhaSerializer(serializers.Serializer):
    """Serializer para troca de senha."""
    senha_atual    = serializers.CharField(write_only=True)
    nova_senha     = serializers.CharField(write_only=True, min_length=8)
    confirmar_nova = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['nova_senha'] != data['confirmar_nova']:
            raise serializers.ValidationError({'confirmar_nova': 'As senhas não conferem.'})
        return data

    def validate_senha_atual(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer para autenticação."""
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').lower().strip()
        senha = data.get('senha', '')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=senha,
        )

        if not user:
            raise serializers.ValidationError(
                {'non_field_errors': 'E-mail ou senha incorretos.'}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {'non_field_errors': 'Usuário inativo. Contate o administrador.'}
            )

        data['user'] = user
        return data


class MeSerializer(serializers.ModelSerializer):
    """Dados do usuário logado — retornados após o login."""
    perfil_display = serializers.CharField(source='get_perfil_display', read_only=True)
    iniciais       = serializers.CharField(read_only=True)
    primeiro_nome  = serializers.CharField(read_only=True)

    class Meta:
        model  = Usuario
        fields = [
            'id', 'email', 'nome', 'primeiro_nome', 'iniciais',
            'perfil', 'perfil_display', 'cargo', 'telefone',
        ]
