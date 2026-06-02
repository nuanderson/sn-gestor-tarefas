"""
Permissões customizadas do SN Gestor.
Usadas nas views para controlar quem pode fazer o quê.
"""
from rest_framework.permissions import BasePermission


class IsAdministrador(BasePermission):
    """Apenas usuários com perfil 'admin'."""
    message = 'Acesso restrito a administradores.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsGestorOuAcima(BasePermission):
    """Gestores e administradores."""
    message = 'Acesso restrito a gestores e administradores.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_gestor_ou_acima
        )


class IsEquipeInterna(BasePermission):
    """Qualquer colaborador interno (não cliente)."""
    message = 'Acesso restrito a colaboradores internos.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            not request.user.is_cliente
        )


class IsCliente(BasePermission):
    """Apenas clientes — para o portal do cliente."""
    message = 'Acesso restrito ao portal do cliente.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_cliente
        )
