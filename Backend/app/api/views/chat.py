from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

    def post(self, request):
        conversa_id = request.data.get("conversa_id")
        question    = request.data.get("question", "").strip()

        if not question:
            return Response(
                {"error": "O campo 'question' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Busca conversa existente ou cria uma nova
        if conversa_id:
            try:
                conversa = Conversa.objects.get(id=conversa_id)
            except Conversa.DoesNotExist:
                return Response(
                    {"error": "Conversa não encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            user = request.user if request.user.is_authenticated else None
            conversa = iniciar_conversa(user=user)

        # Registra pergunta original (#36) e processada (#37)
        mensagem = registrar_mensagem(conversa, question)

        # Gera e registra resposta
        resposta = gerar_resposta(mensagem.conteudo_processado)
        registrar_resposta(conversa, resposta)

        return Response(
            {
                "conversa_id":          conversa.id,
                "pergunta_original":    mensagem.conteudo_original,
                "pergunta_processada":  mensagem.conteudo_processado,
                "answer":               resposta,
            },
            status=status.HTTP_200_OK,
        )


class ChatHistoricoView(APIView):
    """
    GET /api/chat/<conversa_id>/historico/
    Retorna o histórico completo de uma conversa.
    """

    def get(self, request, conversa_id: int):
        try:
            conversa = Conversa.objects.get(id=conversa_id)
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
                "criada_em":            m.criada_em,
            }
            for m in mensagens
        ]
        return Response({"conversa_id": conversa_id, "mensagens": data})