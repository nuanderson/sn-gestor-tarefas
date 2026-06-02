"""
Views de autenticação e gerenciamento de usuários.
"""
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Usuario
from .permissions import IsAdministrador, IsGestorOuAcima
from .serializers import (
    LoginSerializer, MeSerializer,
    UsuarioSerializer, UsuarioCriarSerializer,
    UsuarioAtualizarSerializer, AlterarSenhaSerializer,
)


# ── Página de Login (HTML) ──────────────────────────────────────
def login_page(request):
    """Renderiza a página de login. Se já estiver logado, redireciona."""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'accounts/login.html')


# ── API: Login ──────────────────────────────────────────────────
class LoginAPIView(APIView):
    """
    POST /api/v1/auth/login/
    Body: { "email": "...", "senha": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        login(request, user)

        return Response({
            'mensagem': f'Bem-vindo(a), {user.primeiro_nome}!',
            'usuario': MeSerializer(user).data,
        }, status=status.HTTP_200_OK)


# ── API: Logout ─────────────────────────────────────────────────
class LogoutAPIView(APIView):
    """POST /api/v1/auth/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'mensagem': 'Sessão encerrada com sucesso.'})


# ── API: Dados do usuário logado ────────────────────────────────
class MeAPIView(APIView):
    """GET /api/v1/auth/me/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        """Atualiza dados do próprio perfil."""
        serializer = UsuarioAtualizarSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(MeSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── API: Alterar senha ──────────────────────────────────────────
class AlterarSenhaAPIView(APIView):
    """POST /api/v1/auth/senha/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AlterarSenhaSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data['nova_senha'])
        request.user.save()
        return Response({'mensagem': 'Senha alterada com sucesso.'})


# ── API: CRUD de Usuários (apenas admins) ───────────────────────
class UsuarioViewSet(viewsets.ModelViewSet):
    """
    GET    /api/v1/usuarios/       → lista todos
    POST   /api/v1/usuarios/       → cria novo
    GET    /api/v1/usuarios/{id}/  → detalha
    PATCH  /api/v1/usuarios/{id}/  → edita
    DELETE /api/v1/usuarios/{id}/  → exclui
    """
    queryset = Usuario.objects.all().order_by('nome')
    permission_classes = [IsAdministrador]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCriarSerializer
        if self.action in ('update', 'partial_update'):
            return UsuarioAtualizarSerializer
        return UsuarioSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        perfil = self.request.query_params.get('perfil')
        ativo  = self.request.query_params.get('ativo')
        busca  = self.request.query_params.get('busca')

        if perfil:
            qs = qs.filter(perfil=perfil)
        if ativo is not None:
            qs = qs.filter(is_active=ativo.lower() == 'true')
        if busca:
            qs = qs.filter(nome__icontains=busca) | qs.filter(email__icontains=busca)
        return qs

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        if usuario == request.user:
            return Response(
                {'erro': 'Você não pode excluir sua própria conta.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        usuario.is_active = False
        usuario.save()
        return Response({'mensagem': 'Usuário desativado com sucesso.'})

    @action(detail=False, methods=['get'], permission_classes=[IsGestorOuAcima])
    def equipe(self, request):
        """GET /api/v1/usuarios/equipe/ — lista apenas colaboradores internos."""
        qs = Usuario.objects.filter(
            is_active=True
        ).exclude(perfil='client').order_by('nome')
        return Response(UsuarioSerializer(qs, many=True).data)
