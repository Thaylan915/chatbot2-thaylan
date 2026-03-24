from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from Backend.app.api.views.chat import ChatView
from Backend.app.api.views.auth import LoginView
from Backend.app.api.views.documents import DocumentDeleteView, DocumentListView, DocumentConfirmDeleteView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("chat/", ChatView.as_view(), name="chat"),
    path("documents/", DocumentListView.as_view(), name="document_list"),
    path("documents/<int:id_documento>/", DocumentDeleteView.as_view(), name="document_delete"),
    path("documents/<int:id_documento>/confirm/", DocumentConfirmDeleteView.as_view(), name="document_confirm_delete"),
]