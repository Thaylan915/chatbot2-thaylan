"""
View para operações sobre documentos.
Usa DocumentFactory (Factory Method) para obter o caso de uso.
Requer autenticação JWT — apenas administradores podem excluir documentos.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from Backend.app.api.factories import DocumentFactory


class DocumentListView(APIView):
    """
    GET /api/documents/
    Lista os arquivos enviados à API do Gemini via genai.list_files().
    Requer token JWT de administrador no header:
        Authorization: Bearer <access_token>
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        caso_de_uso = DocumentFactory.make_list()

        try:
            resultado = caso_de_uso.executar()
            return Response({"documentos": resultado}, status=status.HTTP_200_OK)

        except RuntimeError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """
        POST /api/documents/
        Cadastra um novo documento: faz upload para o Gemini e salva no banco.

        Body (multipart/form-data):
            nome    — nome do documento (obrigatório)
            tipo    — portaria | resolucao | rod (obrigatório)
            arquivo — arquivo a ser enviado (obrigatório)
        """
        nome = request.data.get("nome", "").strip()
        tipo = request.data.get("tipo", "").strip()
        arquivo = request.FILES.get("arquivo")

        if not arquivo:
            return Response(
                {"error": "O campo 'arquivo' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        caso_de_uso = DocumentFactory.make_create()

        try:
            resultado = caso_de_uso.executar(
                nome=nome,
                tipo=tipo,
                conteudo_arquivo=arquivo.read(),
                nome_arquivo=arquivo.name,
            )
            return Response(resultado, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDeleteView(APIView):
    """
    PATCH   /api/documents/<id>/  — Edita nome, tipo e/ou arquivo do documento.
    DELETE  /api/documents/<id>/  — Passo 1: solicita exclusão e retorna token de confirmação.
    Requer token JWT de administrador no header:
        Authorization: Bearer <access_token>
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, id_documento: int):
        """
        Atualiza parcialmente um documento.

        Body (multipart/form-data, todos os campos são opcionais):
            nome    — novo nome do documento
            tipo    — portaria | resolucao | rod
            arquivo — novo arquivo (substitui o atual no Gemini)
        """
        nome = request.data.get("nome") or None
        tipo = request.data.get("tipo") or None
        arquivo = request.FILES.get("arquivo")

        conteudo_arquivo = None
        nome_arquivo = None
        if arquivo:
            conteudo_arquivo = arquivo.read()
            nome_arquivo = arquivo.name

        caso_de_uso = DocumentFactory.make_update()

        try:
            resultado = caso_de_uso.executar(
                id_documento=id_documento,
                nome=nome,
                tipo=tipo,
                conteudo_arquivo=conteudo_arquivo,
                nome_arquivo=nome_arquivo,
            )
            return Response(resultado, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id_documento: int):
        """
        Passo 1 da exclusão com confirmação.
        Retorna um token válido por 5 minutos que deve ser enviado para /confirm/.
        """
        caso_de_uso = DocumentFactory.make_delete()

        try:
            resultado = caso_de_uso.solicitar_exclusao(id_documento)
            return Response(resultado, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class DocumentConfirmDeleteView(APIView):
    """
    POST /api/documents/<id>/confirm/
    Passo 2: confirma a exclusão com o token recebido no passo anterior.
    Requer token JWT de administrador no header:
        Authorization: Bearer <access_token>
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id_documento: int):
        """
        Body (JSON ou form-data):
            token — token retornado pelo DELETE /api/documents/<id>/
        """
        token = request.data.get("token", "")
        caso_de_uso = DocumentFactory.make_delete()

        try:
            resultado = caso_de_uso.confirmar_exclusao(id_documento, token)
            return Response(resultado, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)