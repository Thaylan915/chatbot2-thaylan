"""
Endpoints administrativos sobre conversas e métricas do chatbot.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q

from Backend.app.api.permissions import IsAdminProfile
from Backend.app.documents.models import Conversa, Mensagem


class AdminConversasListView(APIView):
    """
    GET /api/admin/conversas/
    Lista TODAS as conversas (de todos os usuários), com título derivado da
    primeira pergunta. Apenas admins.
    """
    permission_classes = [IsAuthenticated, IsAdminProfile]

    def get(self, request):
        conversas = (
            Conversa.objects
            .select_related("user")
            .prefetch_related("mensagens")
            .order_by("-iniciada_em")
        )
        data = []
        for c in conversas:
            primeira = c.mensagens.filter(role="user").order_by("criada_em").first()
            titulo = (primeira.conteudo_original if primeira else "(vazio)")[:80]
            data.append({
                "id": c.id,
                "titulo": titulo,
                "usuario": c.user.username if c.user else "—",
                "iniciada_em": c.iniciada_em,
                "qtd_mensagens": c.mensagens.count(),
            })
        return Response({"conversas": data})


class AdminMetricsView(APIView):
    """
    GET /api/admin/metrics/
    Retorna métricas globais do chatbot.
    """
    permission_classes = [IsAuthenticated, IsAdminProfile]

    def get(self, request):
        respostas = Mensagem.objects.filter(role="assistant")
        total_respostas = respostas.count()

        feedback_counts = respostas.aggregate(
            positivos=Count("id", filter=Q(feedback="positive")),
            negativos=Count("id", filter=Q(feedback="negative")),
            avaliadas=Count("id", filter=Q(feedback__isnull=False)),
        )
        positivos = feedback_counts["positivos"] or 0
        negativos = feedback_counts["negativos"] or 0
        avaliadas = feedback_counts["avaliadas"] or 0
        pct_positivo = round((positivos / avaliadas) * 100, 1) if avaliadas else 0
        pct_negativo = round((negativos / avaliadas) * 100, 1) if avaliadas else 0

        refatoracoes = respostas.filter(foi_reformulada=True).count()

        total_conversas = Conversa.objects.count()
        total_mensagens_usuario = Mensagem.objects.filter(role="user").count()

        # Taxa de acurácia = % de respostas avaliadas que receberam feedback positivo.
        # Definição: positivos / (positivos + negativos).
        taxa_acuracia = round((positivos / avaliadas) * 100, 1) if avaliadas else None

        # Taxa de sucesso = % do total de respostas que NÃO foram negativas e
        # NÃO foram regeneradas (o usuário aceitou a primeira resposta).
        nao_sucesso = respostas.filter(
            Q(feedback="negative") | Q(foi_reformulada=True)
        ).count()
        sucesso = max(total_respostas - nao_sucesso, 0)
        taxa_sucesso = (
            round((sucesso / total_respostas) * 100, 1) if total_respostas else None
        )

        return Response({
            "total_respostas":         total_respostas,
            "feedback_positivos":      positivos,
            "feedback_negativos":      negativos,
            "feedback_avaliadas":      avaliadas,
            "feedback_pct_positivo":   pct_positivo,
            "feedback_pct_negativo":   pct_negativo,
            "taxa_acuracia":           taxa_acuracia,
            "taxa_sucesso":            taxa_sucesso,
            "respostas_bem_sucedidas": sucesso,
            "respostas_nao_sucesso":   nao_sucesso,
            "refatoracoes":            refatoracoes,
            "total_conversas":         total_conversas,
            "total_perguntas":         total_mensagens_usuario,
        })
