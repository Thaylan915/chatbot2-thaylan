from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from Backend.app.api.views.auth import LoginView
from Backend.app.api.views.chat import ChatIniciarView, ChatPerguntaView, ChatHistoricoView
from Backend.app.api.views.documents import (
    DocumentListView,
    DocumentCreateView,
    DocumentDetailView,
    DocumentDeleteView,
    DocumentConfirmDeleteView,
)
from Backend.app.api.views.admin_logs import AdminLogListView
from Backend.app.api.views.users import UserListView, UserRoleUpdateView, MeView, UserRegisterView

urlpatterns = [
    # Auth
    path("auth/login/",   LoginView.as_view(),        name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Chat
    path("chat/iniciar/",                        ChatIniciarView.as_view(),   name="chat_iniciar"),   # #34
    path("chat/pergunta/",                       ChatPerguntaView.as_view(),  name="chat_pergunta"),  # #35 #36 #37
    path("chat/<int:conversa_id>/historico/",    ChatHistoricoView.as_view(), name="chat_historico"),

    # Documents
    path("documents/",                            DocumentListView.as_view(),          name="document_list"),
    path("documents/create/",                     DocumentCreateView.as_view(),        name="document_create"),
    path("documents/<int:id_documento>/",         DocumentDetailView.as_view(),        name="document_detail"),
    path("documents/<int:id_documento>/delete/",  DocumentDeleteView.as_view(),        name="document_delete"),
    path("documents/<int:id_documento>/confirm/", DocumentConfirmDeleteView.as_view(), name="document_confirm_delete"),

    # Admin Logs
    path("admin-logs/", AdminLogListView.as_view(), name="admin_logs"),

    # Users & Profiles
    path("users/register/",           UserRegisterView.as_view(),   name="user_register"),
    path("users/",                    UserListView.as_view(),       name="user_list"),
    path("users/me/",                 MeView.as_view(),             name="user_me"),
    path("users/<int:user_id>/role/", UserRoleUpdateView.as_view(), name="user_role_update"),
]