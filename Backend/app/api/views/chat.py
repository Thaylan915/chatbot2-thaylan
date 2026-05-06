from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from Backend.app.application.answer_question import (
    iniciar_conversa,
    registrar_mensagem,
    gerar_resposta,
    registrar_resposta,
)
from Backend.app.documents.models import Conversa, Mensagem


class ChatIniciarView(APIView):
    """
    POST /api/chat/iniciar/
    Cria uma nova conversa e retorna o id da sessão. #34
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        conversa = iniciar_conversa(user=user)
        return Response(
            {
                "conversa_id": conversa.id,
                "iniciada_em": conversa.iniciada_em,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatPerguntaView(APIView):
    """
    POST /api/chat/pergunta/
    Recebe uma pergunta, registra original e processada, retorna resposta. #35 #36 #37
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversa_id = request.data.get("conversa_id")
        question    = request.data.get("question", "").strip()

        if not question:
            return Response(
                {"error": "O campo 'question' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Busca conversa existente ou cria uma nova (sempre vinculada ao user)
        if conversa_id:
            try:
                conversa = Conversa.objects.get(id=conversa_id, user=request.user)
            except Conversa.DoesNotExist:
                return Response(
                    {"error": "Conversa não encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            conversa = iniciar_conversa(user=request.user)

        # Registra pergunta original (#36) e processada (#37)
        mensagem = registrar_mensagem(conversa, question)

        # Gera e registra resposta
        resposta = gerar_resposta(mensagem.conteudo_processado)
        msg_assistente = registrar_resposta(conversa, resposta)

        return Response(
            {
                "conversa_id":          conversa.id,
                "pergunta_original":    mensagem.conteudo_original,
                "pergunta_processada":  mensagem.conteudo_processado,
                "answer":               resposta,
                "answer_id":            msg_assistente.id,
            },
            status=status.HTTP_200_OK,
        )


class ChatConversasView(APIView):
    """
    GET /api/chat/conversas/
    Lista as conversas do usuário autenticado, com um título derivado da
    primeira mensagem do usuário em cada conversa.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversas = (
            Conversa.objects
            .filter(user=request.user)
            .order_by("-iniciada_em")
            .prefetch_related("mensagens")
        )

        data = []
        for c in conversas:
            primeira = c.mensagens.filter(role="user").order_by("criada_em").first()
            titulo = (primeira.conteudo_original if primeira else "(vazio)")[:60]
            data.append({
                "id": c.id,
                "titulo": titulo,
                "iniciada_em": c.iniciada_em,
            })
        return Response({"conversas": data})


class MensagemRegenerarView(APIView):
    """
    POST /api/chat/mensagens/<id>/regenerar/
    Regenera a resposta do assistente para a pergunta imediatamente anterior,
    marca a antiga como `foi_reformulada=True` e cria uma nova resposta.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, mensagem_id: int):
        try:
            antiga = Mensagem.objects.select_related("conversa").get(
                id=mensagem_id,
                conversa__user=request.user,
                role="assistant",
            )
        except Mensagem.DoesNotExist:
            return Response({"error": "Mensagem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        # encontra a pergunta do usuário imediatamente antes da resposta
        pergunta = (
            Mensagem.objects
            .filter(conversa=antiga.conversa, role="user", criada_em__lte=antiga.criada_em)
            .order_by("-criada_em")
            .first()
        )
        if pergunta is None:
            return Response({"error": "Pergunta original não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        antiga.foi_reformulada = True
        antiga.save(update_fields=["foi_reformulada"])

        nova_resposta = gerar_resposta(pergunta.conteudo_processado or pergunta.conteudo_original)
        nova_msg = registrar_resposta(antiga.conversa, nova_resposta)
        return Response({
            "id": nova_msg.id,
            "conversa_id": antiga.conversa_id,
            "answer": nova_resposta,
        })


class MensagemFeedbackView(APIView):
    """
    POST /api/chat/mensagens/<id>/feedback/
    Body: { "feedback": "positive" | "negative" | null }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, mensagem_id: int):
        feedback = request.data.get("feedback")
        if feedback not in ("positive", "negative", None, ""):
            return Response(
                {"error": "feedback deve ser 'positive', 'negative' ou null."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            msg = Mensagem.objects.select_related("conversa").get(
                id=mensagem_id,
                conversa__user=request.user,
                role="assistant",
            )
        except Mensagem.DoesNotExist:
            return Response({"error": "Mensagem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        msg.feedback = feedback or None
        msg.save(update_fields=["feedback"])
        return Response({"id": msg.id, "feedback": msg.feedback})


class ChatHistoricoView(APIView):
    """
    GET /api/chat/<conversa_id>/historico/
    Retorna o histórico completo de uma conversa. O dono da conversa sempre
    tem acesso; admins podem visualizar qualquer conversa.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, conversa_id: int):
        # Admin pode ver qualquer conversa, usuário comum só as próprias
        profile = getattr(request.user, "profile", None)
        eh_admin = (
            request.user.is_superuser
            or request.user.is_staff
            or (profile is not None and profile.role == "admin")
        )

        try:
            if eh_admin:
                conversa = Conversa.objects.select_related("user").get(id=conversa_id)
            else:
                conversa = Conversa.objects.get(id=conversa_id, user=request.user)
        except Conversa.DoesNotExist:
            return Response(
                {"error": "Conversa não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        mensagens = conversa.mensagens.all()
        data = [
            {
                "id":                   m.id,
                "role":                 m.role,
                "conteudo_original":    m.conteudo_original,
                "conteudo_processado":  m.conteudo_processado,
                "feedback":             m.feedback,
                "foi_reformulada":      m.foi_reformulada,
                "criada_em":            m.criada_em,
            }
            for m in mensagens
        ]
        return Response({
            "conversa_id": conversa_id,
            "usuario": conversa.user.username if conversa.user else "—",
            "mensagens": data,
        })