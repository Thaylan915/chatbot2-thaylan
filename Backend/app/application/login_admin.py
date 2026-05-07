from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class LoginAdmin:
    """
    Caso de uso: autenticar um administrador e retornar tokens JWT.
    Factory Method — ConcreteProduct criado por AuthFactory.
    """

    def executar(self, username: str, password: str) -> dict:
        if not username or not password:
            raise ValueError("Usuário e senha são obrigatórios.")

        usuario = authenticate(username=username, password=password)

        if usuario is None:
            raise PermissionError("Credenciais inválidas.")

        refresh = RefreshToken.for_user(usuario)
        profile = getattr(usuario, "profile", None)
        role = profile.role if profile else "user"

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": usuario.username,
            "email": usuario.email,
            "role": role,
        }