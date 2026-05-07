from django.db.models import Count, Max

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from Backend.app.application.answer_question import (
    iniciar_conversa,
    gerar_titulo_conversa,
    gerar_resposta,
    registrar_mensagem,
    registrar_resposta,
)
from Backend.app.application.intent_classifier import (
    RESPOSTAS_DIRETAS,
    classificar_intencao,
)
from Backend.app.api.factories import ChatFactory
from Backend.app.documents.models import Conversa, Mensagem
from django.utils.dateparse import parse_date
from django.db.models import Count, Avg
from django.utils import timezone
import datetime

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
    Recebe uma pergunta, registra original e processada, retorna resposta.

    Body JSON:
        {
            "conversa_id":          1,
            "question":             "Qual o prazo?",
            "documento_id_filtro":  5     # opcional — após o usuário escolher
                                          # o contexto na tela de clarificação
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversa_id          = request.data.get("conversa_id")
        question             = request.data.get("question", "").strip()
        documento_id_filtro  = request.data.get("documento_id_filtro")

        if not question:
            return Response(
                {"error": "O campo 'question' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not question or len(question) < 2:
            return Response(
                {"error": "A pergunta não pode estar vazia ou ser muito curta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        intencao = classificar_intencao(question)

        if intencao in RESPOSTAS_DIRETAS:
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

            mensagem = registrar_mensagem(conversa, question)
            resposta_msg = registrar_resposta(
                conversa,
                RESPOSTAS_DIRETAS[intencao],
                respondida=True,  # saudação/agradecimento sempre tem resposta direta
            )

            return Response(
                {
                    "conversa_id": conversa.id,
                    "mensagem_id": resposta_msg.id,
                    "pergunta_original": mensagem.conteudo_original,
                    "pergunta_processada": mensagem.conteudo_processado,
                    "answer": RESPOSTAS_DIRETAS[intencao],
                    "fontes": [],
                    "citacoes": [],
                    "respondida": True,
                    "intencao": intencao,
                },
                status=status.HTTP_200_OK,
            )

        # Normaliza o filtro (pode vir como string do front)
        if documento_id_filtro is not None:
            try:
                documento_id_filtro = int(documento_id_filtro)
            except (TypeError, ValueError):
                documento_id_filtro = None

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

        if not conversa.titulo or conversa.titulo == "Nova conversa":
            conversa.titulo = gerar_titulo_conversa(question)
            conversa.save(update_fields=["titulo"])

        # Gera e registra resposta via pipeline RAG
        responder = ChatFactory.make_responder()
        resultado = responder.executar(
            mensagem.conteudo_processado,
            documento_id_filtro=documento_id_filtro,
        )
        # Captura a Mensagem persistida para expor seu ID (necessário para o feedback)
        resposta_msg = registrar_resposta(
            conversa,
            resultado["resposta"],
            ids_fontes=[f["id"] for f in resultado["fontes"]],
            respondida=resultado["respondida"],
        )

        return Response(
            {
                "conversa_id":          conversa.id,
                "mensagem_id":          resposta_msg.id,  # 2. ADICIONE ESSA LINHA PARA O REACT LER
                "pergunta_original":    mensagem.conteudo_original,
                "pergunta_processada":  mensagem.conteudo_processado,
                "answer":               resultado["resposta"],
                "answer_id":            resposta_msg.id,
                "fontes":               resultado["fontes"],
                "citacoes":             resultado["citacoes"],
                "respondida":           resultado["respondida"],
                "intencao":             resultado["intencao"],
                "opcoes_clarificacao":  resultado.get("opcoes_clarificacao", []),
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
    POST/PATCH /api/chat/mensagens/<id>/feedback/
    Body (qualquer combinação dos campos):
        { "feedback": "positive" | "negative" | null,
          "nota": -1 | 1 | 1..5,
          "comentario": "..." }
    """
    permission_classes = [IsAuthenticated]

    def _gravar(self, request, mensagem_id):
        feedback   = request.data.get("feedback")
        nota       = request.data.get("nota")
        comentario = request.data.get("comentario")

        if feedback is not None and feedback not in ("positive", "negative", "", None):
            return Response(
                {"error": "feedback deve ser 'positive', 'negative' ou null."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            msg = Mensagem.objects.select_related("conversa").get(
                id=mensagem_id,
                role="assistant",
            )
        except Mensagem.DoesNotExist:
            return Response({"error": "Mensagem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if feedback is not None:
            msg.feedback = feedback or None
        if nota is not None:
            try:
                msg.nota = int(nota)
            except (TypeError, ValueError):
                return Response({"error": "nota deve ser inteiro."}, status=status.HTTP_400_BAD_REQUEST)
        if comentario is not None:
            msg.comentario = str(comentario)
        msg.save()

        return Response({
            "id": msg.id,
            "feedback": msg.feedback,
            "nota": msg.nota,
            "comentario": msg.comentario,
        })

    def post(self, request, mensagem_id: int):
        return self._gravar(request, mensagem_id)

    def patch(self, request, mensagem_id: int):
        return self._gravar(request, mensagem_id)


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

        mensagens = conversa.mensagens.prefetch_related("fontes").all()
        data = [
            {
                "id":                   m.id,
                "role":                 m.role,
                "conteudo_original":    m.conteudo_original,
                "conteudo_processado":  m.conteudo_processado,
                "feedback":             m.feedback,
                "foi_reformulada":      m.foi_reformulada,
                "criada_em":            m.criada_em,
                "fontes": [
                    {"id": d.id, "nome": d.nome}
                    for d in m.fontes.all()
                ],
            }
            for m in mensagens
        ]
        return Response({
            "conversa_id": conversa_id,
            "usuario":     conversa.user.username if conversa.user else "—",
            "titulo":      getattr(conversa, "titulo", None),
            "mensagens":   data,
        })


class ConversasUsuarioView(APIView):
    """
    GET /api/chat/conversas/
    Lista todas as conversas do usuário autenticado, da mais recente para a
    mais antiga. Usada para alimentar o histórico na sidebar.

    Resposta:
        {
            "conversas": [
                {
                    "id":                 12,
                    "iniciada_em":        "...",
                    "ultima_atualizacao": "...",
                    "total_mensagens":    8,
                    "titulo":             "Qual o prazo de matrícula?"
                },
                ...
            ]
        }
    """
    permission_classes = [IsAuthenticated]

    _TITULO_MAX_CHARS = 60

    def get(self, request):
        conversas = (
            Conversa.objects
            .filter(user=request.user)
            .annotate(
                ultima_atualizacao=Max("mensagens__criada_em"),
                total_mensagens=Count("mensagens"),
            )
            .order_by("-iniciada_em")
        )

        data = []
        for conv in conversas:
            primeira = (
                conv.mensagens
                .filter(role="user")
                .order_by("criada_em")
                .first()
            )
            if primeira:
                texto = primeira.conteudo_original.strip()
                titulo = texto[: self._TITULO_MAX_CHARS]
                if len(texto) > self._TITULO_MAX_CHARS:
                    titulo += "…"
            else:
                titulo = "Nova conversa"

            data.append({
                "id":                 conv.id,
                "iniciada_em":        conv.iniciada_em,
                "ultima_atualizacao": conv.ultima_atualizacao,
                "total_mensagens":    conv.total_mensagens,
                "titulo":             titulo,
            })

        return Response({"conversas": data})


class ChatHistoricoPeriodoView(APIView):
    permission_classes = [AllowAny] # Mude para IsAuthenticated se apenas admins puderem ver

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        conversas = Conversa.objects.all()

        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start:
                conversas = conversas.filter(iniciada_em__date__gte=parsed_start)

        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end:
                conversas = conversas.filter(iniciada_em__date__lte=parsed_end)

        # Retorna as conversas ordenadas da mais recente para a mais antiga
        data = [
            {
                "id": c.id,
                "titulo": c.titulo,
                "iniciada_em": c.iniciada_em,
                "total_mensagens": c.mensagens.count()
            } for c in conversas.order_by('-iniciada_em')
        ]

        return Response({"conversas": data}, status=status.HTTP_200_OK)
    
class ChatMetricasView(APIView):
    """
    GET /api/chat/metricas/
    Retorna estatísticas gerais para o dashboard de métricas.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        total_conversas = Conversa.objects.count()
        total_mensagens = Mensagem.objects.count()

        # Média das notas (Issue 4)
        media_notas = Mensagem.objects.filter(role="assistant").exclude(nota=None).aggregate(Avg('nota'))['nota__avg'] or 0

        # Contagem de feedbacks positivos e negativos
        positivos = Mensagem.objects.filter(role="assistant", nota=1).count()
        negativos = Mensagem.objects.filter(role="assistant", nota=-1).count()

        # Estatística de conversas nos últimos 7 dias para o gráfico
        sete_dias_atras = timezone.now() - datetime.timedelta(days=7)
        conversas_por_dia = (
            Conversa.objects.filter(iniciada_em__gte=sete_dias_atras)
            .values('iniciada_em__date')
            .annotate(total=Count('id'))
            .order_by('iniciada_em__date')
        )

        # ─── Taxa de sucesso de respostas ─────────────────────────────────────
        # Considera apenas mensagens do assistente com `respondida` instrumentado
        # (registros antigos têm NULL e ficam fora do cálculo).
        respostas_instrumentadas = Mensagem.objects.filter(
            role="assistant",
            respondida__isnull=False,
        )
        total_respostas = respostas_instrumentadas.count()
        respondidas_ok = respostas_instrumentadas.filter(respondida=True).count()
        taxa_sucesso = (
            round(respondidas_ok / total_respostas * 100, 1)
            if total_respostas else 0.0
        )

        # ─── Taxa de reformulação ─────────────────────────────────────────────
        # Reformulação = pergunta do usuário enviada logo após o assistente
        # ter declarado que não encontrou resposta (respondida=False).
        # Numerador: nº dessas perguntas. Denominador: total de perguntas (user).
        total_perguntas = Mensagem.objects.filter(role="user").count()
        reformulacoes = self._contar_reformulacoes()
        taxa_reformulacao = (
            round(reformulacoes / total_perguntas * 100, 1)
            if total_perguntas else 0.0
        )

        return Response({
            "total_conversas":     total_conversas,
            "total_mensagens":     total_mensagens,
            "media_notas":         round(float(media_notas), 2),
            "feedbacks_positivos": positivos,
            "feedbacks_negativos": negativos,
            "grafico":             list(conversas_por_dia),

            # Taxa de sucesso
            "taxa_sucesso":        taxa_sucesso,
            "respostas_ok":        respondidas_ok,
            "respostas_total":     total_respostas,

            # Taxa de reformulação
            "taxa_reformulacao":   taxa_reformulacao,
            "reformulacoes":       reformulacoes,
            "perguntas_total":     total_perguntas,
        }, status=status.HTTP_200_OK)

    @staticmethod
    def _contar_reformulacoes() -> int:
        """
        Conta perguntas do usuário que vieram logo após uma resposta do
        assistente marcada como `respondida=False` (mesma conversa).

        Implementação em Python: percorre cada conversa em ordem cronológica
        e detecta o padrão [assistant respondida=False] → [user]. É O(n) sobre
        o total de mensagens; suficiente para os volumes esperados aqui.
        """
        reformulacoes = 0
        conversas = Conversa.objects.prefetch_related("mensagens").all()
        for conversa in conversas:
            msgs = list(conversa.mensagens.all().order_by("criada_em"))
            for i in range(1, len(msgs)):
                anterior = msgs[i - 1]
                atual = msgs[i]
                if (
                    atual.role == "user"
                    and anterior.role == "assistant"
                    and anterior.respondida is False
                ):
                    reformulacoes += 1
        return reformulacoes
