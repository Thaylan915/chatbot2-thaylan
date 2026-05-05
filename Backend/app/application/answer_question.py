"""Caso de uso: responder pergunta do usuário usando o banco de documentos."""
import math
import re
from typing import List, Optional

import google.generativeai as genai
from django.conf import settings

from Backend.app.application.embedding_provider import EmbeddingProvider
from Backend.app.documents.models import Conversa, Mensagem, Documento, ChunkDocumento
from Backend.app.domain.repositories.chunk_repository import ChunkRepository

# Instrui o modelo a responder sempre com citações explícitas do documento de origem
_PROMPT_TEMPLATE = """\
Você é um assistente especializado em documentos institucionais do IFES.
Responda à pergunta usando exclusivamente os trechos abaixo, em português.

Regras obrigatórias:
1. Sempre cite o documento de origem na resposta, usando o formato:
   "Segundo o documento [NOME DO DOCUMENTO], página [N], ..."
   ou "Conforme [NOME DO DOCUMENTO] (pág. [N]), ..."
2. Se uma informação vier de mais de um documento, cite todos.
3. Se a informação não estiver no contexto, responda EXATAMENTE:
   "Não encontrei a informação nos documentos disponíveis."

Contexto:
{contexto}

Pergunta: {pergunta}

Resposta:"""

# Frases que indicam que o modelo não soube responder
_FRASES_SEM_RESPOSTA = [
    "não encontrei a informação", "não encontrou a informação", "não há informações",
    "não tenho informações", "não está no contexto", "não foi encontrado",
    "não consta", "sem informações", "não possuo informações", "não disponho de informações",
]
_MENSAGEM_SEM_RESPOSTA = (
    "Não encontrei informações suficientes nos documentos disponíveis para responder "
    "a essa pergunta. Tente reformular ou consulte diretamente os documentos institucionais."
)
_MENSAGEM_SEM_DOCUMENTOS = (
    "Ainda não há documentos indexados na base de conhecimento. "
    "Adicione documentos antes de fazer perguntas."
)
_MENSAGEM_ERRO_API = (
    "Não foi possível processar sua pergunta no momento. "
    "Verifique sua conexão e tente novamente."
)
_MENSAGEM_CLARIFICACAO = (
    "Sua pergunta pode se referir a mais de um documento. "
    "Para responder com precisão, por favor escolha o contexto desejado:"
)
_MENSAGEM_COTA_API = (
    "A cota da API Gemini foi excedida no momento. "
    "Aguarde alguns minutos e tente novamente."
)

# Tamanho máximo do trecho de citação exibido no frontend
_TRECHO_MAX_CHARS = 220

# Parâmetros de detecção de ambiguidade
_AMBIG_TOP_N             = 3      # nº de candidatos inspecionados
_AMBIG_SCORE_MIN         = 0.55   # mínimo de relevância do top-1 para considerar ambíguo
_AMBIG_GAP_MAX           = 0.08   # diferença máxima de score entre top-1 e top-N
_AMBIG_MIN_DOCS          = 2      # nº mínimo de documentos distintos nos top-N
_AMBIG_MAX_OPCOES        = 4      # máximo de opções oferecidas ao usuário
_AMBIG_TRECHO_CHARS      = 160    # tamanho do preview de cada opção


# ─── Pré-processamento ────────────────────────────────────────────────────────

def preprocessar_pergunta(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'[^\w\s\?\!\.\,\á\é\í\ó\ú\ã\õ\â\ê\ô\ç]', '', texto)
    return texto


def gerar_titulo_conversa(pergunta: str, max_palavras: int = 8) -> str:
    """Gera um título curto e legível a partir da primeira pergunta útil."""
    pergunta = preprocessar_pergunta(pergunta)
    palavras_pra_ignorar = {
        "oi", "olá", "ola", "bom", "dia", "boa", "tarde", "noite",
        "obrigado", "obrigada", "valeu", "por", "favor", "me",
        "qual", "quais", "quando", "onde", "como", "quem", "que",
        "o", "a", "os", "as", "um", "uma", "pra", "pro", "para",
    }
    palavras = [
        palavra for palavra in re.findall(r"[\wáéíóúãõâêôç]+", pergunta, flags=re.IGNORECASE)
        if palavra not in palavras_pra_ignorar
    ]
    if not palavras:
        return "Nova conversa"
    titulo = " ".join(palavras[:max_palavras]).strip()
    if len(palavras) > max_palavras:
        titulo += "..."
    titulo = titulo.rstrip("?!.:,;")
    return titulo[:1].upper() + titulo[1:]


def _nao_soube_responder(texto: str) -> bool:
    """Verifica se o modelo indicou que não encontrou resposta no contexto."""
    texto_lower = texto.lower()
    return any(frase in texto_lower for frase in _FRASES_SEM_RESPOSTA)


def _extrair_trecho(conteudo: str, max_chars: int = _TRECHO_MAX_CHARS) -> str:
    """Extrai um trecho representativo do chunk para exibir como citação."""
    conteudo = conteudo.strip()
    if len(conteudo) <= max_chars:
        return conteudo
    trecho = conteudo[:max_chars]
    ultimo_espaco = trecho.rfind(' ')
    if ultimo_espaco > max_chars // 2:
        trecho = trecho[:ultimo_espaco]
    return trecho + "…"


def _label_pagina(numero_pagina: Optional[int]) -> str:
    """Retorna a label de página para o contexto do prompt."""
    return f"Página {numero_pagina}" if numero_pagina else "Página N/A"


# ─── Tratamento de cota da API e fallback textual ────────────────────────────

def _is_quota_error(exc: Exception) -> bool:
    texto = str(exc).lower()
    return "quota exceeded" in texto or "resource_exhausted" in texto or "429" in texto


def _candidates_by_keyword(pergunta: str, fetch_k: int) -> List[dict]:
    """Fallback semântico quando embedding está indisponível por cota."""
    tokens = [
        t for t in re.findall(r"[\wáéíóúãõâêôç]+", pergunta.lower(), flags=re.IGNORECASE)
        if len(t) >= 3
    ]
    if not tokens:
        return []

    seen_ids = set()
    candidatos: List[dict] = []

    for token in tokens:
        if len(candidatos) >= fetch_k:
            break
        chunks = (
            ChunkDocumento.objects
            .select_related("documento")
            .filter(conteudo__icontains=token)
            .exclude(id__in=seen_ids)
            .order_by("id")[: max(1, fetch_k // max(1, len(tokens)))]
        )
        for c in chunks:
            seen_ids.add(c.id)
            score = 0.4 + min(0.5, len(token) / 20)
            candidatos.append(
                {
                    "id": c.id,
                    "conteudo": c.conteudo,
                    "numero_pagina": c.numero_pagina,
                    "documento_id": c.documento_id,
                    "documento_nome": c.documento.nome,
                    "score": float(score),
                    "embedding": [],
                }
            )
            if len(candidatos) >= fetch_k:
                break

    return candidatos


# ─── Detecção de ambiguidade ─────────────────────────────────────────────────

def _detectar_ambiguidade(candidates: List[dict]) -> List[dict]:
    """
    Detecta se os top candidatos sinalizam uma pergunta ambígua — isto é,
    quando há múltiplos documentos distintos com scores comparáveis.

    Critérios (todos devem ser satisfeitos):
      1. Top-1 score >= _AMBIG_SCORE_MIN (existe relevância mínima)
      2. Gap (top-1 − top-N) <= _AMBIG_GAP_MAX (scores próximos)
      3. Top-N contém >= _AMBIG_MIN_DOCS documentos distintos

    Retorna:
      - Lista de opções de clarificação (uma por documento único), ordenadas
        por relevância, limitada a _AMBIG_MAX_OPCOES.
      - Lista vazia se a pergunta NÃO é ambígua.
    """
    if len(candidates) < _AMBIG_TOP_N:
        return []

    top = candidates[:_AMBIG_TOP_N]
    top1_score = top[0]["score"]
    topN_score = top[-1]["score"]

    if top1_score < _AMBIG_SCORE_MIN:
        return []  # sem relevância → não é ambiguidade, é falta de resposta

    if top1_score - topN_score > _AMBIG_GAP_MAX:
        return []  # top-1 claramente melhor que os demais

    docs_distintos = {c["documento_id"] for c in top}
    if len(docs_distintos) < _AMBIG_MIN_DOCS:
        return []  # todos do mesmo documento → pergunta clara

    # Ambíguo: monta opções (uma por documento, preservando ordem de relevância)
    opcoes: List[dict] = []
    seen: set = set()
    for c in candidates:
        if c["documento_id"] in seen:
            continue
        seen.add(c["documento_id"])
        opcoes.append({
            "documento_id":   c["documento_id"],
            "documento_nome": c["documento_nome"],
            "numero_pagina":  c.get("numero_pagina"),
            "trecho":         _extrair_trecho(c["conteudo"], max_chars=_AMBIG_TRECHO_CHARS),
        })
        if len(opcoes) >= _AMBIG_MAX_OPCOES:
            break
    return opcoes


# ─── MMR (Maximal Marginal Relevance) re-ranking ─────────────────────────────

def _cosine(a: List[float], b: List[float]) -> float:
    """Similaridade de cosseno entre dois vetores."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _mmr_rerank(
    candidates: List[dict],
    top_k: int,
    lambda_mult: float = 0.6,
) -> List[dict]:
    """
    Maximal Marginal Relevance: seleciona *top_k* chunks equilibrando
    relevância para a query (score pgvector) e diversidade entre si.
    """
    if len(candidates) <= top_k:
        selected = candidates
    else:
        selected: List[dict] = []
        remaining = list(candidates)

        while len(selected) < top_k and remaining:
            if not selected:
                best = max(remaining, key=lambda c: c["score"])
            else:
                def mmr_score(c: dict) -> float:
                    max_sim = max(
                        _cosine(c["embedding"], s["embedding"]) for s in selected
                    )
                    return lambda_mult * c["score"] - (1 - lambda_mult) * max_sim

                best = max(remaining, key=mmr_score)

            selected.append(best)
            remaining.remove(best)

    return [{k: v for k, v in c.items() if k != "embedding"} for c in selected]


# ─── Montagem do contexto com rótulos de documento/página ────────────────────

def _montar_contexto(chunks: List[dict]) -> str:
    """
    Monta o bloco de contexto para o prompt, rotulando cada trecho com
    o nome do documento e a página — informações que o modelo usará para
    produzir as citações.
    """
    blocos = []
    for chunk in chunks:
        pagina = _label_pagina(chunk.get("numero_pagina"))
        header = f"[Documento: {chunk['documento_nome']} | {pagina}]"
        blocos.append(f"{header}\n{chunk['conteudo']}")
    return "\n\n---\n\n".join(blocos)


def _construir_citacoes(chunks: List[dict]) -> List[dict]:
    """
    Constrói a lista de citações estruturadas a partir dos chunks usados.
    Cada citação representa um trecho relevante de um documento específico.
    """
    citacoes = []
    for ordem, chunk in enumerate(chunks, start=1):
        citacoes.append({
            "ordem":          ordem,
            "documento_id":   chunk["documento_id"],
            "documento_nome": chunk["documento_nome"],
            "numero_pagina":  chunk.get("numero_pagina"),
            "trecho":         _extrair_trecho(chunk["conteudo"]),
        })
    return citacoes


# ─── Caso de uso principal ────────────────────────────────────────────────────

class ResponderPergunta:
    """
    Caso de uso: pipeline RAG completo com citações de origem e
    tratamento de ambiguidade por confirmação do usuário.

    Fluxo:
        1. Gera embedding da pergunta com task_type='retrieval_query'.
        2. Busca os top RERANK_FETCH_K candidatos via pgvector.
        3. Se `documento_id_filtro` foi informado, restringe candidatos a esse
           documento (usuário já confirmou o contexto) e pula a detecção de
           ambiguidade.
        4. Caso contrário, detecta ambiguidade — se positiva, retorna
           intencao='clarificacao' com as opções de documentos.
        5. Re-ranking MMR para selecionar TOP_K chunks diversos e relevantes.
        6. Monta contexto rotulado (documento + página) e gera resposta.
        7. Detecta se o modelo não encontrou resposta.
        8. Retorna resposta + fontes + citacoes + respondida + intencao.
    """

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._chunk_repo = chunk_repository
        self._embedding_provider = embedding_provider

    def executar(
        self,
        pergunta_processada: str,
        documento_id_filtro: Optional[int] = None,
    ) -> dict:
        """
        Args:
            pergunta_processada: texto da pergunta já pré-processado.
            documento_id_filtro: ID do documento escolhido pelo usuário após
                                 clarificação (None no primeiro pedido).

        Retorna dict com:
            - resposta:              str
            - fontes:                list[dict]  — {id, nome}
            - citacoes:              list[dict]
            - respondida:            bool
            - intencao:              'rag' | 'clarificacao'
            - opcoes_clarificacao:   list[dict] (apenas quando intencao='clarificacao')
        """
        if not settings.GEMINI_API_KEY:
            return self._sem_resposta(_MENSAGEM_ERRO_API)

        try:
            fetch_k = getattr(settings, "RERANK_FETCH_K", settings.TOP_K * 4)

            # 1) Tenta embedding + busca vetorial; se quota estourar, cai para busca textual
            try:
                query_embedding = self._embedding_provider.embed(
                    pergunta_processada,
                    task_type="retrieval_query",
                )
                candidates = self._chunk_repo.buscar_candidatos(query_embedding, fetch_k)
            except Exception as exc:
                if _is_quota_error(exc):
                    candidates = _candidates_by_keyword(pergunta_processada, fetch_k)
                else:
                    return self._sem_resposta(_MENSAGEM_ERRO_API)

            if not candidates:
                return self._sem_resposta(_MENSAGEM_SEM_DOCUMENTOS)

            # 3. Se o usuário já escolheu um documento após clarificação,
            #    restringe a busca e pula a detecção de ambiguidade.
            if documento_id_filtro is not None:
                candidates = [
                    c for c in candidates
                    if c["documento_id"] == documento_id_filtro
                ]
                if not candidates:
                    return self._sem_resposta(_MENSAGEM_SEM_RESPOSTA)
            else:
                # 4. Detecção de ambiguidade (só na primeira passagem)
                opcoes = _detectar_ambiguidade(candidates)
                if opcoes:
                    return self._clarificacao(opcoes)

            # 5. Re-ranking MMR
            chunks = _mmr_rerank(candidates, top_k=settings.TOP_K)

            # 6. Monta contexto e gera resposta
            contexto = _montar_contexto(chunks)
            prompt = _PROMPT_TEMPLATE.format(
                contexto=contexto,
                pergunta=pergunta_processada,
            )

            genai.configure(api_key=settings.GEMINI_API_KEY)
            try:
                model = genai.GenerativeModel(settings.CHAT_MODEL)
                resposta_texto = model.generate_content(prompt).text
            except Exception as exc:
                if _is_quota_error(exc):
                    try:
                        model = genai.GenerativeModel("models/gemini-flash-latest")
                        resposta_texto = model.generate_content(prompt).text
                    except Exception as exc2:
                        if _is_quota_error(exc2):
                            return self._sem_resposta(_MENSAGEM_COTA_API)
                        return self._sem_resposta(_MENSAGEM_ERRO_API)
                else:
                    return self._sem_resposta(_MENSAGEM_ERRO_API)

            # 7. Detecta resposta vazia/negativa
            if _nao_soube_responder(resposta_texto):
                return self._sem_resposta(_MENSAGEM_SEM_RESPOSTA)

            # 8. Monta fontes (documentos únicos) e citações (trechos individuais)
            fontes = self._deduplicar_fontes(chunks)
            citacoes = _construir_citacoes(chunks)

            return {
                "resposta":            resposta_texto,
                "fontes":              fontes,
                "citacoes":            citacoes,
                "respondida":          True,
                "intencao":            "rag",
                "opcoes_clarificacao": [],
            }

        except Exception as exc:
            if _is_quota_error(exc):
                return self._sem_resposta(_MENSAGEM_COTA_API)
            return self._sem_resposta(_MENSAGEM_ERRO_API)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _sem_resposta(mensagem: str) -> dict:
        return {
            "resposta":            mensagem,
            "fontes":              [],
            "citacoes":            [],
            "respondida":          False,
            "intencao":            "rag",
            "opcoes_clarificacao": [],
        }

    @staticmethod
    def _clarificacao(opcoes: List[dict]) -> dict:
        return {
            "resposta":            _MENSAGEM_CLARIFICACAO,
            "fontes":              [],
            "citacoes":            [],
            "respondida":          False,
            "intencao":            "clarificacao",
            "opcoes_clarificacao": opcoes,
        }

    @staticmethod
    def _deduplicar_fontes(chunks: List[dict]) -> List[dict]:
        """Retorna lista de documentos únicos mantendo ordem de relevância."""
        seen: set = set()
        fontes: List[dict] = []
        for chunk in chunks:
            doc_id = chunk["documento_id"]
            if doc_id not in seen:
                seen.add(doc_id)
                fontes.append({"id": doc_id, "nome": chunk["documento_nome"]})
        return fontes


# ─── Helpers de conversa ──────────────────────────────────────────────────────

def iniciar_conversa(user=None) -> Conversa:
    """Cria e retorna uma nova conversa. #34"""
    return Conversa.objects.create(user=user)


def registrar_mensagem(conversa: Conversa, pergunta_original: str) -> Mensagem:
    """Registra a pergunta original (#36) e a processada (#37)."""
    pergunta_processada = preprocessar_pergunta(pergunta_original)
    mensagem = Mensagem.objects.create(
        conversa=conversa,
        role="user",
        conteudo_original=pergunta_original,
        conteudo_processado=pergunta_processada,
    )
    return mensagem


def registrar_resposta(
    conversa: Conversa,
    resposta: str,
    ids_fontes: List[int] | None = None,
    respondida: bool | None = None,
) -> Mensagem:
    """
    Registra a resposta do assistente e vincula os documentos de origem.

    Args:
        conversa:   sessão de chat.
        resposta:   texto gerado pelo modelo.
        ids_fontes: IDs dos Documentos usados como contexto RAG.
        respondida: True se o modelo encontrou resposta no contexto, False se
                    declarou desconhecimento, None para fluxos sem essa
                    semântica (saudações, agradecimentos etc., quando aplicável).
    """
    mensagem = Mensagem.objects.create(
        conversa=conversa,
        role="assistant",
        conteudo_original=resposta,
        conteudo_processado=resposta,
        respondida=respondida,
    )
    if ids_fontes:
        documentos = Documento.objects.filter(id__in=ids_fontes)
        mensagem.fontes.set(documentos)
    return mensagem
