"""
Permissões customizadas que se alinham com o sistema de papéis baseado em Profile.role.
"""

from rest_framework.permissions import BasePermission


class IsAdminProfile(BasePermission):
    """
    Permite acesso apenas a usuários autenticados cujo Profile.role == 'admin'.
    """

    message = "Acesso restrito a administradores."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Superusers do Django sempre passam
        if user.is_superuser or user.is_staff:
            return True
        profile = getattr(user, "profile", None)
        return bool(profile and profile.role == "admin")
