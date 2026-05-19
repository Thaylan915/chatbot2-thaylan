from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from Backend.app.api.permissions import IsAdminProfile as IsAdminUser

from Backend.app.api.factories import DocumentFactory
from Backend.app.application.log_action import log_action
from Backend.app.documents.models import Documento, VersaoDocumento
from Backend.app.application.document_versioning import ativar_versao


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            tipo        = request.query_params.get("tipo") or None
            data_inicio = request.query_params.get("data_inicio") or None
            data_fim    = request.query_params.get("data_fim") or None

            if tipo and tipo not in ("portaria", "resolucao", "rod"):
                return Response(
                    {"error": "Tipo inválido. Use 'portaria', 'resolucao' ou 'rod'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            documentos = DocumentFactory.make_list().executar(
                tipo=tipo,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
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


# ─── NOVA CLASSE ──────────────────────────────────────────────────────────────

class DocumentMetadataView(APIView):
    """
    GET /api/documents/<id>/metadata/

    Expõe os metadados completos de um documento:
      - Dados básicos (id, nome, tipo, caminho_arquivo)
      - Timestamps (indexado_em, atualizado_em)
      - Resumo de versões (total, versão ativa e seu número)
      - Resumo de chunks (total indexado, por versão ativa)
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, id_documento: int):
        try:
            doc = Documento.objects.get(id=id_documento)
        except Documento.DoesNotExist:
            return Response(
                {"error": "Documento não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        versao_ativa = doc.versoes.filter(ativa=True).first()

        total_chunks = doc.chunks.count()
        chunks_versao_ativa = (
            versao_ativa.chunks.count() if versao_ativa else 0
        )

        metadata = {
            "id": doc.id,
            "nome": doc.nome,
            "tipo": doc.tipo,
            "tipo_display": doc.get_tipo_display(),
            "caminho_arquivo": doc.caminho_arquivo,
            "indexado_em": doc.indexado_em,
            "atualizado_em": doc.atualizado_em,
            "versoes": {
                "total": doc.versoes.count(),
                "versao_ativa": versao_ativa.numero if versao_ativa else None,
                "caminho_versao_ativa": versao_ativa.caminho_arquivo if versao_ativa else None,
            },
            "chunks": {
                "total": total_chunks,
                "na_versao_ativa": chunks_versao_ativa,
            },
        }

        return Response(metadata, status=status.HTTP_200_OK)


# ─── NOVA CLASSE ──────────────────────────────────────────────────────────────

class DocumentAdminActionView(APIView):
    """
    POST /api/documents/<id>/admin-action/

    Registra manualmente uma ação administrativa sobre um documento.

    Body JSON esperado:
        action   (str, obrigatório) — "CREATE" | "UPDATE" | "DELETE" | "REINDEX"
        details  (str, opcional)   — Descrição livre da ação realizada
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    ACOES_VALIDAS = {"CREATE", "UPDATE", "DELETE", "REINDEX"}

    def post(self, request, id_documento: int):
        action  = (request.data.get("action") or "").strip().upper()
        details = (request.data.get("details") or "").strip()

        if not action:
            return Response(
                {"error": "O campo 'action' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action not in self.ACOES_VALIDAS:
            return Response(
                {
                    "error": (
                        f"Ação inválida: '{action}'. "
                        f"Use uma de: {', '.join(sorted(self.ACOES_VALIDAS))}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            doc = Documento.objects.get(id=id_documento)
        except Documento.DoesNotExist:
            return Response(
                {"error": "Documento não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        log_action(
            user=request.user,
            action=action,
            resource_type="document",
            resource_id=doc.id,
            resource_name=doc.nome,
            details=details or f"Ação administrativa manual: {action}",
        )

        return Response(
            {
                "mensagem": "Ação registrada com sucesso.",
                "documento": {"id": doc.id, "nome": doc.nome},
                "action": action,
                "details": details,
                "registrado_por": request.user.username,
            },
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────────────────────────────────────

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


class DocumentVersoesView(APIView):
    """
    GET  /api/documents/<id>/versoes/         → lista versões
    POST /api/documents/<id>/versoes/<n>/ativar/ → ativa uma versão específica
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, id_documento: int):
        try:
            doc = Documento.objects.get(id=id_documento)
        except Documento.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        versoes = doc.versoes.all().order_by("-numero")
        data = [
            {
                "numero": v.numero,
                "nome": v.nome,
                "tipo": v.tipo,
                "caminho_arquivo": v.caminho_arquivo,
                "ativa": v.ativa,
                "criada_em": v.criada_em,
                "qtd_chunks": v.chunks.count(),
            }
            for v in versoes
        ]
        return Response({"versoes": data})


class DocumentVersaoAtivarView(APIView):
    """
    POST /api/documents/<id>/versoes/<n>/ativar/  → ativa a versão de número n
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id_documento: int, numero: int):
        try:
            versao = VersaoDocumento.objects.get(documento_id=id_documento, numero=numero)
        except VersaoDocumento.DoesNotExist:
            return Response({"error": "Versão não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        ativar_versao(versao)
        log_action(
            user=request.user,
            action="UPDATE",
            resource_type="document",
            resource_id=id_documento,
            resource_name=versao.documento.nome,
            details=f"Versão ativa alterada para v{versao.numero}",
        )
        return Response({
            "id_documento": id_documento,
            "versao_ativa": versao.numero,
            "nome": versao.nome,
            "tipo": versao.tipo,
        })


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