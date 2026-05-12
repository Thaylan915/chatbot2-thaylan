"""
Endpoints administrativos sobre conversas e métricas do chatbot.
"""
import math
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.utils import timezone

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


class AdminMetricsByUserView(APIView):
    """
    GET /api/admin/metrics/usuarios/
    Retorna estatísticas agregadas por usuário (apenas admins).
    """
    permission_classes = [IsAuthenticated, IsAdminProfile]

    def get(self, request):
        usuarios = User.objects.all().order_by("username")
        linhas = []

        for u in usuarios:
            conversas_u = Conversa.objects.filter(user=u)
            respostas_u = Mensagem.objects.filter(role="assistant", conversa__user=u)
            perguntas_u = Mensagem.objects.filter(role="user", conversa__user=u)

            total_resp = respostas_u.count()
            positivos = respostas_u.filter(feedback="positive").count()
            negativos = respostas_u.filter(feedback="negative").count()
            avaliadas = positivos + negativos
            regeneradas = respostas_u.filter(foi_reformulada=True).count()

            acuracia = round((positivos / avaliadas) * 100, 1) if avaliadas else None
            nao_sucesso = respostas_u.filter(Q(feedback="negative") | Q(foi_reformulada=True)).count()
            sucesso = max(total_resp - nao_sucesso, 0)
            taxa_sucesso = round((sucesso / total_resp) * 100, 1) if total_resp else None

            ultima = perguntas_u.order_by("-criada_em").first()

            linhas.append({
                "user_id":           u.id,
                "username":          u.username,
                "total_conversas":   conversas_u.count(),
                "total_perguntas":   perguntas_u.count(),
                "total_respostas":   total_resp,
                "positivos":         positivos,
                "negativos":         negativos,
                "regeneradas":       regeneradas,
                "taxa_acuracia":     acuracia,
                "taxa_sucesso":      taxa_sucesso,
                "ultima_atividade":  ultima.criada_em if ultima else None,
            })

        return Response({"usuarios": linhas})


class AdminMetricsConsistencyView(APIView):
    """
    GET /api/admin/metrics/constancia/?dias=14
    Mede a constância dos indicadores ao longo dos últimos N dias.

    Para cada dia coleta a taxa de sucesso e a taxa de acurácia daquele dia,
    e retorna média, desvio-padrão e coeficiente de variação (CV).
    Quanto menor o CV, mais constante é o indicador.
    """
    permission_classes = [IsAuthenticated, IsAdminProfile]

    def get(self, request):
        try:
            dias = int(request.query_params.get("dias", 14))
        except (TypeError, ValueError):
            dias = 14
        dias = max(2, min(dias, 90))

        hoje = timezone.now().date()
        inicio = hoje - timedelta(days=dias - 1)

        serie_sucesso = []
        serie_acuracia = []

        for n in range(dias):
            dia = inicio + timedelta(days=n)
            respostas = Mensagem.objects.filter(
                role="assistant",
                criada_em__date=dia,
            )
            total = respostas.count()
            positivos = respostas.filter(feedback="positive").count()
            negativos = respostas.filter(feedback="negative").count()
            avaliadas = positivos + negativos
            regeneradas = respostas.filter(foi_reformulada=True).count()
            nao_sucesso = respostas.filter(Q(feedback="negative") | Q(foi_reformulada=True)).count()

            sucesso = (
                round(((total - nao_sucesso) / total) * 100, 1) if total else None
            )
            acuracia = (
                round((positivos / avaliadas) * 100, 1) if avaliadas else None
            )

            dia_iso = dia.isoformat()
            serie_sucesso.append({"dia": dia_iso, "valor": sucesso, "total": total})
            serie_acuracia.append({"dia": dia_iso, "valor": acuracia, "avaliadas": avaliadas})

        sucesso_stats = _estatisticas([p["valor"] for p in serie_sucesso])
        acuracia_stats = _estatisticas([p["valor"] for p in serie_acuracia])

        return Response({
            "dias": dias,
            "serie_sucesso":  serie_sucesso,
            "serie_acuracia": serie_acuracia,
            "estatisticas_sucesso":  sucesso_stats,
            "estatisticas_acuracia": acuracia_stats,
        })


def _estatisticas(valores):
    """
    Recebe lista de valores (alguns podem ser None quando não há dados no dia)
    e retorna média, desvio-padrão amostral e coeficiente de variação.
    """
    nums = [v for v in valores if v is not None]
    n = len(nums)
    if n == 0:
        return {
            "n": 0, "media": None, "desvio_padrao": None,
            "cv": None, "minimo": None, "maximo": None, "classificacao": None,
        }
    media = sum(nums) / n
    if n > 1:
        variancia = sum((v - media) ** 2 for v in nums) / (n - 1)
        desvio = math.sqrt(variancia)
    else:
        desvio = 0.0
    cv = (desvio / media * 100) if media else 0.0
    classificacao = _classificar_cv(cv)
    return {
        "n":               n,
        "media":           round(media, 1),
        "desvio_padrao":   round(desvio, 2),
        "cv":              round(cv, 1),
        "minimo":          round(min(nums), 1),
        "maximo":          round(max(nums), 1),
        "classificacao":   classificacao,
    }


def _classificar_cv(cv: float) -> str:
    """Classifica a constância pelo coeficiente de variação (em %)."""
    if cv < 10:  return "muito_constante"
    if cv < 20:  return "constante"
    if cv < 30:  return "moderado"
    return "instavel"
