from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from Backend.app.api.factories import DocumentFactory
from Backend.app.application.log_action import log_action


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            documentos = DocumentFactory.make_list().executar()
            return Response({"documentos": documentos}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        arquivo = request.FILES.get("arquivo")
        nome    = request.data.get("nome", "").strip()
        tipo    = request.data.get("tipo", "").strip()

        if not arquivo:
            return Response({"error": "O campo 'arquivo' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if not nome:
            return Response({"error": "O campo 'nome' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if tipo not in ("portaria", "resolucao", "rod"):
            return Response({"error": "O campo 'tipo' deve ser 'portaria', 'resolucao' ou 'rod'."}, status=status.HTTP_400_BAD_REQUEST)
        if not arquivo.name.lower().endswith(".pdf"):
            return Response({"error": "Apenas arquivos PDF são aceitos."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = DocumentFactory.make_create().executar(
                nome=nome,
                tipo=tipo,
                conteudo_arquivo=arquivo.read(),
                nome_arquivo=arquivo.name,
            )

            log_action(
                user=request.user,
                action="CREATE",
                resource_type="document",
                resource_id=resultado.get("id"),
                resource_name=nome,
                details=f"Tipo: {tipo} | Arquivo: {arquivo.name}",
            )

            return Response(resultado, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        arquivo = request.FILES.get("arquivo")
        nome    = request.data.get("nome", "").strip()
        tipo    = request.data.get("tipo", "").strip()

        if not arquivo:
            return Response({"error": "O campo 'arquivo' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if not nome:
            return Response({"error": "O campo 'nome' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        if tipo not in ("portaria", "resolucao", "rod"):
            return Response({"error": "O campo 'tipo' deve ser 'portaria', 'resolucao' ou 'rod'."}, status=status.HTTP_400_BAD_REQUEST)
        if not arquivo.name.lower().endswith(".pdf"):
            return Response({"error": "Apenas arquivos PDF são aceitos."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = DocumentFactory.make_create().executar(
                nome=nome,
                tipo=tipo,
                conteudo_arquivo=arquivo.read(),
                nome_arquivo=arquivo.name,
            )

            log_action(
                user=request.user,
                action="CREATE",
                resource_type="document",
                resource_id=resultado.get("id"),
                resource_name=nome,
                details=f"Tipo: {tipo} | Arquivo: {arquivo.name}",
            )

            return Response(resultado, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, id_documento: int):
        try:
            resultado = DocumentFactory.make_delete().solicitar_exclusao(id_documento)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, id_documento: int):
        nome    = request.data.get("nome") or None
        tipo    = request.data.get("tipo") or None
        arquivo = request.FILES.get("arquivo")

        if tipo and tipo not in ("portaria", "resolucao", "rod"):
            return Response({"error": "Tipo inválido. Use 'portaria', 'resolucao' ou 'rod'."}, status=status.HTTP_400_BAD_REQUEST)
        if not nome and not tipo and not arquivo:
            return Response({"error": "Envie ao menos um campo para atualizar: nome, tipo ou arquivo."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = DocumentFactory.make_update().executar(
                id_documento=id_documento,
                nome=nome,
                tipo=tipo,
                conteudo_arquivo=arquivo.read() if arquivo else None,
                nome_arquivo=arquivo.name if arquivo else None,
            )

            log_action(
                user=request.user,
                action="UPDATE",
                resource_type="document",
                resource_id=id_documento,
                resource_name=nome or resultado.get("titulo", ""),
                details=f"Tipo: {tipo or '—'} | Novo arquivo: {'sim' if arquivo else 'não'}",
            )

            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, id_documento: int):
        try:
            resultado = DocumentFactory.make_delete().solicitar_exclusao(id_documento)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentConfirmDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id_documento: int):
        token = request.data.get("token", "").strip()

        if not token:
            return Response({"error": "O campo 'token' é obrigatório para confirmar a exclusão."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = DocumentFactory.make_delete().confirmar_exclusao(id_documento, token)

            log_action(
                user=request.user,
                action="DELETE",
                resource_type="document",
                resource_id=id_documento,
                resource_name=resultado.get("titulo", ""),
            )

            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except LookupError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)