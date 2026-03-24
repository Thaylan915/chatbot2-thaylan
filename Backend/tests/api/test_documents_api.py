"""
Testes de integração para os endpoints de documentos.

Os casos de uso são mockados via unittest.mock.patch para isolar a camada
de view das dependências externas (PostgreSQL, Gemini API).

Endpoints cobertos:
    GET    /api/documents/               — listar documentos
    POST   /api/documents/               — criar documento
    PATCH  /api/documents/<id>/          — editar documento
    DELETE /api/documents/<id>/          — solicitar exclusão (retorna token)
    POST   /api/documents/<id>/confirm/  — confirmar exclusão com token
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

DOCUMENTS_URL = "/api/documents/"
DOCUMENT_URL = "/api/documents/{id}/"
CONFIRM_URL = "/api/documents/{id}/confirm/"


def _auth_header(user: User) -> str:
    token = RefreshToken.for_user(user)
    return f"Bearer {token.access_token}"


# ---------------------------------------------------------------------------
# GET /api/documents/
# ---------------------------------------------------------------------------

class TestDocumentListView(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_list", password="pass123", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="user_list", password="pass123", is_staff=False
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DOCUMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_returns_403(self):
        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.regular))
        response = self.client.get(DOCUMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_list")
    def test_list_returns_documents(self, mock_make_list):
        mock_uc = MagicMock()
        mock_uc.executar.return_value = [
            {"id": 1, "nome": "Portaria 01", "tipo": "portaria"}
        ]
        mock_make_list.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.get(DOCUMENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("documentos", response.data)
        self.assertEqual(len(response.data["documentos"]), 1)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_list")
    def test_list_propagates_runtime_error(self, mock_make_list):
        mock_uc = MagicMock()
        mock_uc.executar.side_effect = RuntimeError("Gemini indisponível")
        mock_make_list.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.get(DOCUMENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)


# ---------------------------------------------------------------------------
# POST /api/documents/
# ---------------------------------------------------------------------------

class TestDocumentCreateView(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_create", password="pass123", is_staff=True
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.post(DOCUMENTS_URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_arquivo_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.post(
            DOCUMENTS_URL, {"nome": "Doc", "tipo": "portaria"}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_create")
    def test_create_returns_201(self, mock_make_create):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_uc = MagicMock()
        mock_uc.executar.return_value = {
            "id": 1,
            "nome": "Portaria 01",
            "tipo": "portaria",
            "caminho_arquivo": "files/portaria_01.pdf",
        }
        mock_make_create.return_value = mock_uc

        arquivo = SimpleUploadedFile("portaria.pdf", b"%PDF-test", content_type="application/pdf")
        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.post(
            DOCUMENTS_URL,
            {"nome": "Portaria 01", "tipo": "portaria", "arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome"], "Portaria 01")

    @patch("Backend.app.api.views.documents.DocumentFactory.make_create")
    def test_create_value_error_returns_400(self, mock_make_create):
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_uc = MagicMock()
        mock_uc.executar.side_effect = ValueError("Tipo inválido.")
        mock_make_create.return_value = mock_uc

        arquivo = SimpleUploadedFile("doc.pdf", b"%PDF-test")
        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.post(
            DOCUMENTS_URL,
            {"nome": "Doc", "tipo": "invalido", "arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# PATCH /api/documents/<id>/
# ---------------------------------------------------------------------------

class TestDocumentUpdateView(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_update", password="pass123", is_staff=True
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(DOCUMENT_URL.format(id=1), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_update")
    def test_patch_returns_updated_document(self, mock_make_update):
        mock_uc = MagicMock()
        mock_uc.executar.return_value = {
            "id": 1,
            "nome": "Novo Nome",
            "tipo": "resolucao",
            "caminho_arquivo": "files/resolucao.pdf",
            "atualizado_em": "2026-03-24T10:00:00",
        }
        mock_make_update.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.patch(
            DOCUMENT_URL.format(id=1),
            {"nome": "Novo Nome"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], "Novo Nome")

    @patch("Backend.app.api.views.documents.DocumentFactory.make_update")
    def test_patch_not_found_returns_404(self, mock_make_update):
        mock_uc = MagicMock()
        mock_uc.executar.side_effect = LookupError("Documento não encontrado.")
        mock_make_update.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.patch(
            DOCUMENT_URL.format(id=999),
            {"nome": "X"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# DELETE /api/documents/<id>/  — Passo 1: solicitar exclusão
# ---------------------------------------------------------------------------

class TestDocumentDeleteView(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_delete", password="pass123", is_staff=True
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DOCUMENT_URL.format(id=1))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_delete")
    def test_delete_returns_token(self, mock_make_delete):
        mock_uc = MagicMock()
        mock_uc.solicitar_exclusao.return_value = {
            "message": "Confirme a exclusão do documento 'Portaria 01'.",
            "token": "abc123",
            "expires_in": 300,
        }
        mock_make_delete.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.delete(DOCUMENT_URL.format(id=1))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("expires_in", response.data)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_delete")
    def test_delete_not_found_returns_404(self, mock_make_delete):
        mock_uc = MagicMock()
        mock_uc.solicitar_exclusao.side_effect = LookupError("Documento não encontrado.")
        mock_make_delete.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.delete(DOCUMENT_URL.format(id=999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_delete")
    def test_delete_invalid_id_returns_400(self, mock_make_delete):
        mock_uc = MagicMock()
        mock_uc.solicitar_exclusao.side_effect = ValueError("ID do documento inválido.")
        mock_make_delete.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.delete(DOCUMENT_URL.format(id=0))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# POST /api/documents/<id>/confirm/  — Passo 2: confirmar exclusão
# ---------------------------------------------------------------------------

class TestDocumentConfirmDeleteView(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_confirm", password="pass123", is_staff=True
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.post(CONFIRM_URL.format(id=1), {"token": "abc"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_delete")
    def test_confirm_with_valid_token_returns_200(self, mock_make_delete):
        mock_uc = MagicMock()
        mock_uc.confirmar_exclusao.return_value = {
            "message": "Documento 'Portaria 01' excluído com sucesso.",
            "id": 1,
        }
        mock_make_delete.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.post(
            CONFIRM_URL.format(id=1), {"token": "abc123"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["id"], 1)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_delete")
    def test_confirm_with_invalid_token_returns_403(self, mock_make_delete):
        mock_uc = MagicMock()
        mock_uc.confirmar_exclusao.side_effect = PermissionError("Token de confirmação inválido.")
        mock_make_delete.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.post(
            CONFIRM_URL.format(id=1), {"token": "wrong"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_delete")
    def test_confirm_not_found_returns_404(self, mock_make_delete):
        mock_uc = MagicMock()
        mock_uc.confirmar_exclusao.side_effect = LookupError("Documento não encontrado.")
        mock_make_delete.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.post(
            CONFIRM_URL.format(id=999), {"token": "abc"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("Backend.app.api.views.documents.DocumentFactory.make_delete")
    def test_confirm_expired_token_returns_403(self, mock_make_delete):
        mock_uc = MagicMock()
        mock_uc.confirmar_exclusao.side_effect = PermissionError("Token expirado.")
        mock_make_delete.return_value = mock_uc

        self.client.credentials(HTTP_AUTHORIZATION=_auth_header(self.admin))
        response = self.client.post(
            CONFIRM_URL.format(id=1), {"token": "expired"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
