"""
Testes unitários para o pipeline RAG com citações de origem.

Cobre os critérios de aceite:
- Resposta contém citações estruturadas (documento_nome, numero_pagina, trecho)
- Citações são geradas a partir de 3 tipos de documentos diferentes
  (portaria, resolução e ROD)
- Campos obrigatórios presentes em cada citação
- Comportamento correto quando não há documentos / API indisponível
"""
import math
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from Backend.app.application.answer_question import (
    ResponderPergunta,
    _construir_citacoes,
    _extrair_trecho,
    _montar_contexto,
    _nao_soube_responder,
    preprocessar_pergunta,
)

# ─── Helpers de fixture ───────────────────────────────────────────────────────

def _chunk(
    id: int,
    nome: str,
    pagina: int | None,
    conteudo: str,
    score: float = 0.9,
) -> dict:
    """Cria um dict de chunk como retornado por buscar_candidatos()."""
    return {
        "id":             id,
        "conteudo":       conteudo,
        "numero_pagina":  pagina,
        "documento_id":   id,
        "documento_nome": nome,
        "score":          score,
        "embedding":      [score] * 5,   # vetor fictício para MMR
    }


# Três chunks de tipos de documentos distintos usados em múltiplos testes
CHUNK_PORTARIA = _chunk(
    id=1,
    nome="PORTARIA Nº 1 - 2025",
    pagina=2,
    conteudo=(
        "Art. 1º Designar o servidor FULANO DE TAL, matrícula 123456, "
        "para substituir a servidora CICLANA DE TAL, matrícula 654321, "
        "no cargo de Chefe do Gabinete, durante o período de 10 a 20 de janeiro de 2025, "
        "por motivo de férias."
    ),
    score=0.92,
)

CHUNK_RESOLUCAO = _chunk(
    id=2,
    nome="Resolucao_CS_27_2020",
    pagina=5,
    conteudo=(
        "Art. 3º O NEABI tem por finalidade articular, implementar e acompanhar "
        "políticas de promoção da igualdade racial no âmbito do IFES, "
        "em consonância com as diretrizes e metas do Plano Nacional de Educação."
    ),
    score=0.85,
)

CHUNK_ROD = _chunk(
    id=3,
    nome="rod-graduacao-2023",
    pagina=None,          # ROD não possui numero_pagina neste cenário
    conteudo=(
        "O Relatório de Ação Docente (ROD) consolida as atividades de ensino, "
        "pesquisa e extensão desenvolvidas no ano letivo de 2023, "
        "em conformidade com o Plano de Trabalho Docente aprovado pelo Colegiado."
    ),
    score=0.78,
)

TRES_CHUNKS = [CHUNK_PORTARIA, CHUNK_RESOLUCAO, CHUNK_ROD]


# ─── Testes de funções auxiliares ─────────────────────────────────────────────

class TestFuncoesAuxiliares:
    def test_extrair_trecho_texto_curto_retorna_completo(self):
        texto = "Texto curto."
        assert _extrair_trecho(texto, max_chars=50) == "Texto curto."

    def test_extrair_trecho_texto_longo_trunca_com_reticencias(self):
        texto = "palavra " * 100
        trecho = _extrair_trecho(texto, max_chars=30)
        assert trecho.endswith("…")
        assert len(trecho) <= 35   # margem para a palavra final não ser cortada

    def test_nao_soube_responder_detecta_frase(self):
        assert _nao_soube_responder("Não encontrei a informação nos documentos.")

    def test_nao_soube_responder_retorna_false_para_resposta_valida(self):
        assert not _nao_soube_responder("Segundo o documento PORTARIA Nº 1 - 2025, página 2, o servidor foi designado.")

    def test_montar_contexto_inclui_nome_e_pagina(self):
        ctx = _montar_contexto([CHUNK_PORTARIA])
        assert "PORTARIA Nº 1 - 2025" in ctx
        assert "Página 2" in ctx
        assert CHUNK_PORTARIA["conteudo"] in ctx

    def test_montar_contexto_sem_pagina_usa_na(self):
        ctx = _montar_contexto([CHUNK_ROD])
        assert "Página N/A" in ctx


# ─── Testes de _construir_citacoes ────────────────────────────────────────────

class TestConstruirCitacoes:
    def test_retorna_uma_citacao_por_chunk(self):
        citacoes = _construir_citacoes(TRES_CHUNKS)
        assert len(citacoes) == 3

    def test_campos_obrigatorios_presentes(self):
        citacoes = _construir_citacoes(TRES_CHUNKS)
        campos = {"ordem", "documento_id", "documento_nome", "numero_pagina", "trecho"}
        for c in citacoes:
            assert campos <= c.keys(), f"Campos faltando em: {c}"

    def test_ordem_sequencial(self):
        citacoes = _construir_citacoes(TRES_CHUNKS)
        assert [c["ordem"] for c in citacoes] == [1, 2, 3]

    def test_numero_pagina_pode_ser_none(self):
        citacoes = _construir_citacoes([CHUNK_ROD])
        assert citacoes[0]["numero_pagina"] is None

    def test_tres_documentos_distintos(self):
        citacoes = _construir_citacoes(TRES_CHUNKS)
        nomes = {c["documento_nome"] for c in citacoes}
        assert nomes == {"PORTARIA Nº 1 - 2025", "Resolucao_CS_27_2020", "rod-graduacao-2023"}

    def test_trecho_nao_vazio(self):
        citacoes = _construir_citacoes(TRES_CHUNKS)
        for c in citacoes:
            assert c["trecho"], "Trecho não pode ser vazio"


# ─── Testes de ResponderPergunta.executar() ───────────────────────────────────

def _make_responder(chunks_retornados: list) -> tuple:
    """
    Cria uma instância de ResponderPergunta com dependências mockadas.
    Retorna (responder, mock_repo, mock_embedding).
    """
    mock_repo = MagicMock()
    mock_repo.buscar_candidatos.return_value = chunks_retornados

    mock_emb = MagicMock()
    mock_emb.embed.return_value = [0.5] * 5

    responder = ResponderPergunta(
        chunk_repository=mock_repo,
        embedding_provider=mock_emb,
    )
    return responder, mock_repo, mock_emb


class TestResponderPerguntaComCitacoes:
    """Testes com os três tipos de documento e mock da API Gemini."""

    @patch("Backend.app.application.answer_question.genai")
    @patch("Backend.app.application.answer_question.settings")
    def test_citacoes_retornadas_com_tres_documentos(self, mock_settings, mock_genai):
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.TOP_K = 3
        mock_settings.RERANK_FETCH_K = 12
        mock_settings.CHAT_MODEL = "gemini-1.5-flash"

        mock_genai.GenerativeModel.return_value.generate_content.return_value.text = (
            "Segundo o documento PORTARIA Nº 1 - 2025, página 2, o servidor foi designado. "
            "Conforme Resolucao_CS_27_2020 (pág. 5), o NEABI articula políticas de igualdade."
        )

        responder, _, _ = _make_responder(TRES_CHUNKS)
        resultado = responder.executar("quem foi designado e qual é o neabi")

        assert resultado["respondida"] is True
        assert len(resultado["citacoes"]) == 3

        nomes = {c["documento_nome"] for c in resultado["citacoes"]}
        assert "PORTARIA Nº 1 - 2025" in nomes
        assert "Resolucao_CS_27_2020" in nomes
        assert "rod-graduacao-2023" in nomes

    @patch("Backend.app.application.answer_question.genai")
    @patch("Backend.app.application.answer_question.settings")
    def test_citacao_portaria_tem_pagina(self, mock_settings, mock_genai):
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.TOP_K = 3
        mock_settings.RERANK_FETCH_K = 12
        mock_settings.CHAT_MODEL = "gemini-1.5-flash"

        mock_genai.GenerativeModel.return_value.generate_content.return_value.text = (
            "Segundo o documento PORTARIA Nº 1 - 2025, página 2, o servidor foi designado."
        )

        responder, _, _ = _make_responder(TRES_CHUNKS)
        resultado = responder.executar("quem foi designado")

        portaria_cit = next(
            c for c in resultado["citacoes"] if c["documento_nome"] == "PORTARIA Nº 1 - 2025"
        )
        assert portaria_cit["numero_pagina"] == 2

    @patch("Backend.app.application.answer_question.genai")
    @patch("Backend.app.application.answer_question.settings")
    def test_citacao_rod_pagina_none(self, mock_settings, mock_genai):
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.TOP_K = 3
        mock_settings.RERANK_FETCH_K = 12
        mock_settings.CHAT_MODEL = "gemini-1.5-flash"

        mock_genai.GenerativeModel.return_value.generate_content.return_value.text = (
            "O Relatório de Ação Docente consolida as atividades de ensino."
        )

        responder, _, _ = _make_responder(TRES_CHUNKS)
        resultado = responder.executar("o que é o rod")

        rod_cit = next(
            c for c in resultado["citacoes"] if c["documento_nome"] == "rod-graduacao-2023"
        )
        assert rod_cit["numero_pagina"] is None

    @patch("Backend.app.application.answer_question.settings")
    def test_sem_documentos_retorna_citacoes_vazia(self, mock_settings):
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.TOP_K = 3
        mock_settings.RERANK_FETCH_K = 12

        responder, _, _ = _make_responder([])   # repositório vazio
        resultado = responder.executar("qualquer pergunta")

        assert resultado["respondida"] is False
        assert resultado["citacoes"] == []
        assert resultado["fontes"] == []

    @patch("Backend.app.application.answer_question.settings")
    def test_sem_api_key_retorna_erro(self, mock_settings):
        mock_settings.GEMINI_API_KEY = ""   # sem chave

        responder, _, _ = _make_responder(TRES_CHUNKS)
        resultado = responder.executar("qualquer pergunta")

        assert resultado["respondida"] is False
        assert resultado["citacoes"] == []

    @patch("Backend.app.application.answer_question.genai")
    @patch("Backend.app.application.answer_question.settings")
    def test_modelo_sem_resposta_retorna_citacoes_vazia(self, mock_settings, mock_genai):
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.TOP_K = 3
        mock_settings.RERANK_FETCH_K = 12
        mock_settings.CHAT_MODEL = "gemini-1.5-flash"

        # Modelo retorna frase de "não encontrei"
        mock_genai.GenerativeModel.return_value.generate_content.return_value.text = (
            "Não encontrei a informação nos documentos disponíveis."
        )

        responder, _, _ = _make_responder(TRES_CHUNKS)
        resultado = responder.executar("informação inexistente")

        assert resultado["respondida"] is False
        assert resultado["citacoes"] == []

    @patch("Backend.app.application.answer_question.genai")
    @patch("Backend.app.application.answer_question.settings")
    def test_trecho_de_cada_citacao_nao_excede_limite(self, mock_settings, mock_genai):
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.TOP_K = 3
        mock_settings.RERANK_FETCH_K = 12
        mock_settings.CHAT_MODEL = "gemini-1.5-flash"

        mock_genai.GenerativeModel.return_value.generate_content.return_value.text = (
            "Resposta baseada nos documentos."
        )

        responder, _, _ = _make_responder(TRES_CHUNKS)
        resultado = responder.executar("documentos institucionais")

        for cit in resultado["citacoes"]:
            assert len(cit["trecho"]) <= 230, (
                f"Trecho da citação '{cit['documento_nome']}' excede limite"
            )
