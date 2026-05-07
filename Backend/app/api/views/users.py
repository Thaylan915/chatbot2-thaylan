from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from Backend.app.api.permissions import IsAdminProfile as IsAdminUser
from django.contrib.auth.models import User
from Backend.app.application.manage_profile import (
    list_users_with_profiles,
    set_user_role,
    get_or_create_profile,
)
from Backend.app.application.log_action import log_action


class UserRegisterView(APIView):
    """
    POST /api/users/register/  → cria um novo usuário.
    Não requer autenticação.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        email    = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        password2 = request.data.get("password2", "")

        if not username:
            return Response({"error": "O campo 'username' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({"error": "O campo 'email' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"error": "O campo 'password' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if password != password2:
            return Response({"error": "As senhas não coincidem."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "Nome de usuário já está em uso."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"error": "E-mail já cadastrado."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        get_or_create_profile(user)

        return Response({
            "id":       user.id,
            "username": user.username,
            "email":    user.email,
        }, status=status.HTTP_201_CREATED)


class UserListView(APIView):
    """
    GET /api/users/  → lista todos os usuários com seus perfis.
    Requer autenticação JWT e is_staff=True.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            users = list_users_with_profiles()
            return Response(users, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRoleUpdateView(APIView):
    """
    PATCH /api/users/<id>/role/  → altera o papel de um usuário.

    Body JSON:
        { "role": "admin" }   ou   { "role": "user" }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, user_id: int):
        role = request.data.get("role", "").strip()

        if not role:
            return Response({"error": "O campo 'role' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = set_user_role(user_id, role)

            log_action(
                user=request.user,
                action="UPDATE",
                resource_type="user",
                resource_id=user_id,
                resource_name=profile.user.username,
                details=f"Role alterado para: {role}",
            )

            return Response({
                "id":       profile.user.id,
                "username": profile.user.username,
                "role":     profile.role,
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MeView(APIView):
    """
    GET /api/users/me/  → retorna os dados do usuário autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = get_or_create_profile(user)
        return Response({
            "id":       user.id,
            "username": user.username,
            "email":    user.email,
            "role":     profile.role,
            "is_staff": user.is_staff,
        })