"""
Views de categorias — issue #21.
As categorias são os tipos de documento: portaria, resolucao, rod.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from Backend.app.documents.models import Documento, TipoDocumento
from Backend.app.api.factories import DocumentFactory


class CategoryListView(APIView):
    """
    GET /api/categories/
    Lista as categorias disponíveis com contagem de documentos.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categorias = []
        for tipo_value, tipo_label in TipoDocumento.choices:
            total = Documento.objects.filter(tipo=tipo_value).count()
            categorias.append({
                "tipo":              tipo_value,
                "label":             tipo_label,
                "total_documentos":  total,
            })

        return Response({"categorias": categorias}, status=status.HTTP_200_OK)


class CategoryDocumentListView(APIView):
    """
    GET /api/categories/<tipo>/
    Lista documentos de uma categoria com origem, data e versão ativa (#24).
    Aceita filtros: ?data_inicio=YYYY-MM-DD&data_fim=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, tipo: str):
        tipos_validos = [t[0] for t in TipoDocumento.choices]
        if tipo not in tipos_validos:
            return Response(
                {"error": f"Categoria inválida. Use: {', '.join(tipos_validos)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_inicio = request.query_params.get("data_inicio") or None
        data_fim    = request.query_params.get("data_fim") or None

        documentos = DocumentFactory.make_list().executar(
            tipo=tipo,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        return Response(
            {
                "categoria":  tipo,
                "label":      dict(TipoDocumento.choices)[tipo],
                "total":      len(documentos),
                "documentos": documentos,
            },
            status=status.HTTP_200_OK,
        )