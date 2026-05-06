import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import ReactMarkdown from "react-markdown"; // <-- IMPORTAÇÃO DO MARKDOWN (Issue 2)
import "./ChatArea.css";
import enviarIcon from "../assets/images/enviar.svg";
import api from "../services/api.jsx";
import { authService } from "../services/authService";

export default function ChatArea() {
  const [mensagens, setMensagens]   = useState([]);
  const [input, setInput]           = useState("");
  const [carregando, setCarregando] = useState(false);
  const [conversaId, setConversaId] = useState(null);
  const ultimaPerguntaRef           = useRef("");   // usada para reenviar após clarificação
  const fimRef                      = useRef(null);
  const location                    = useLocation();

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      setMensagens([]);
      setConversaId(null);
      setErroCarregamento("");
      return;
    }

    const conversaSelecionada = new URLSearchParams(location.search).get("conversa");

    if (conversaSelecionada) {
      setCarregando(true);
      setErroCarregamento("");
      api
        .get(`/api/chat/${conversaSelecionada}/historico/`)
        .then((res) => {
          const mensagensHistorico = (res.data.mensagens || []).map((m) => ({
            role: m.role,
            conteudo: m.conteudo_original,
            fontes: m.fontes ?? [],
            citacoes: [],
            documentoPrincipal: null,
            respondida: true,
            avaliada: false,
          }));

          setConversaId(Number(conversaSelecionada));
          setMensagens(mensagensHistorico);
        })
        .catch((err) => {
          console.error("Erro ao carregar histórico da conversa:", err);
          setErroCarregamento(
            err.response?.status === 401
              ? "Sua sessão expirou. Faça login novamente para acessar o chat."
              : "Não foi possível carregar esta conversa agora."
          );
          setMensagens([]);
        })
        .finally(() => setCarregando(false));
      return;
    }

    setMensagens([]);
    setConversaId(null);
    setErroCarregamento("");
  }, [location.search]);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens, carregando]);

  /**
   * Envia a pergunta para o backend.
   *
   * @param {string}  texto              — pergunta do usuário
   * @param {object}  [opts]
   * @param {number}  [opts.documentoIdFiltro] — ID do documento escolhido após
   *                                              clarificação (omitir no 1º envio)
   * @param {boolean} [opts.ecoarUsuario=true]  — se deve acrescentar a pergunta
   *                                              como bolha do usuário (desligado
   *                                              quando o usuário clica uma opção
   *                                              de clarificação — a pergunta já
   *                                              está no histórico)
   */
  async function enviarPergunta(texto, { documentoIdFiltro, ecoarUsuario = true } = {}) {
    if (!texto || carregando) return;

    ultimaPerguntaRef.current = texto;

    if (ecoarUsuario) {
      setMensagens((prev) => [...prev, { role: "user", conteudo: texto }]);
    }
    setCarregando(true);

    try {
      const payload = { question: texto };
      if (conversaId) {
        payload.conversa_id = conversaId;
      }
      if (documentoIdFiltro != null) {
        payload.documento_id_filtro = documentoIdFiltro;
      }

      const res = await api.post("/api/chat/pergunta/", payload);

      if (!conversaId && res.data?.conversa_id) {
        setConversaId(res.data.conversa_id);
      }

      setMensagens((prev) => [
        ...prev,
        {
          role:               "assistant",
          id:                 res.data.mensagem_id,             // necessário para feedback
          conteudo:           res.data.answer,
          fontes:             res.data.fontes              ?? [],
          citacoes:           res.data.citacoes            ?? [],
          respondida:         res.data.respondida,
          intencao:           res.data.intencao            ?? "rag",
          opcoesClarificacao: res.data.opcoes_clarificacao ?? [],
          avaliada:           false,
        },
      ]);
    } catch (error) {
      console.error("Erro na requisição da pergunta:", error);
      setErroCarregamento(
        error.response?.status === 401
          ? "Sua sessão expirou. Faça login novamente para continuar."
          : "Não foi possível conectar ao servidor. Tente novamente."
      );
      setMensagens((prev) => [
        ...prev,
        {
          role:               "assistant",
          conteudo:           "Não foi possível conectar ao servidor. Tente novamente.",
          fontes:             [],
          citacoes:           [],
          respondida:         false,
          intencao:           "rag",
          opcoesClarificacao: [],
        },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  async function enviar() {
    const texto = input.trim();
    if (texto.length < 2) {
      alert("Por favor, digite uma pergunta válida com mais detalhes.");
      return;
    }
    setInput("");
    await enviarPergunta(texto);
  }

  /**
   * Usuário clicou numa opção de clarificação — reenvia a última pergunta
   * restringindo a busca ao documento escolhido.
   */
  async function escolherContexto(documentoId, documentoNome) {
    const texto = ultimaPerguntaRef.current;
    if (!texto) return;

    // Marca a escolha como uma bolha do usuário, para deixar claro no histórico
    setMensagens((prev) => [
      ...prev,
      { role: "user", conteudo: `Consultar em: ${documentoNome}` },
    ]);

    await enviarPergunta(texto, {
      documentoIdFiltro: documentoId,
      ecoarUsuario:      false,
    });
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  }

  // ISSUE 4: FUNÇÃO PARA ENVIAR FEEDBACK DA RESPOSTA
  async function enviarFeedback(index, mensagemId, nota) {
    if (!mensagemId) return;
    try {
      await api.patch(`/api/chat/mensagem/${mensagemId}/feedback/`, { nota });
      setMensagens(prev => {
        const novas = [...prev];
        novas[index].avaliada = true;
        return novas;
      });
    } catch (err) {
      console.error("Erro ao enviar feedback", err);
      alert("Erro ao salvar feedback.");
    }
  }

  return (
    <div className="chatArea">
      <div className="mensagens">
        {mensagens.length === 0 ? (
          <div className="placeholder">
            <h2>Como posso ajudar?</h2>
            {erroCarregamento && <p className="placeholderErro">{erroCarregamento}</p>}
          </div>
        ) : (
          <div className="listaMensagens">
            {mensagens.map((msg, i) => {
              const ehClarificacao =
                msg.role === "assistant" && msg.intencao === "clarificacao";
              const semResposta =
                msg.role === "assistant" &&
                msg.respondida === false &&
                !ehClarificacao;

              const classeExtra = ehClarificacao
                ? " clarificacao"
                : semResposta
                ? " sem-resposta"
                : "";

              return (
                <div key={i} className={`bolha ${msg.role}${classeExtra}`}>
                  {semResposta && (
                    <div className="sem-resposta-header">
                      <span className="sem-resposta-icone">&#9888;</span>
                      <span className="sem-resposta-titulo">Não foi possível responder</span>
                    </div>
                  )}

                  {ehClarificacao && (
                    <div className="clarificacao-header">
                      <span className="clarificacao-icone">&#10068;</span>
                      <span className="clarificacao-titulo">
                        Pergunta ambígua — confirme o contexto
                      </span>
                    </div>
                  )}

                  <div className="textoBolha">
                    {msg.role === "assistant" ? (
                      <div className="markdownResposta">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <p className="markdownParagrafo">{children}</p>,
                            ul: ({ children }) => <ul className="markdownLista">{children}</ul>,
                            ol: ({ children }) => <ol className="markdownLista">{children}</ol>,
                            li: ({ children }) => <li className="markdownItem">{children}</li>,
                            strong: ({ children }) => <strong className="markdownNegrito">{children}</strong>,
                            blockquote: ({ children }) => <blockquote className="markdownCitacao">{children}</blockquote>,
                          }}
                        >
                          {msg.conteudo || ""}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      msg.conteudo
                    )}
                  </div>

                  {ehClarificacao && msg.opcoesClarificacao?.length > 0 && (
                    <OpcoesClarificacao
                      opcoes={msg.opcoesClarificacao}
                      onEscolher={escolherContexto}
                      desabilitado={carregando}
                    />
                  )}

                  {msg.citacoes && msg.citacoes.length > 0 && (
                    <CitacoesArea citacoes={msg.citacoes} />
                  )}

                  {msg.role === "assistant" && msg.documentoPrincipal && (
                    <div className="documentoPrincipalArea">
                      <span className="documentoPrincipalLabel">Documento principal</span>
                      <span className="documentoPrincipalValor">
                        {msg.documentoPrincipal.nome} ({String(msg.documentoPrincipal.tipo || "desconhecido").toUpperCase()})
                      </span>
                    </div>
                  )}

                  {/* ISSUE 4: BOTÕES DE AVALIAÇÃO */}
                  {msg.role === "assistant" && msg.id && !semResposta && !msg.avaliada && (
                    <div className="feedbackArea">
                      <span className="feedbackPergunta">A resposta foi útil?</span>
                      <button onClick={() => enviarFeedback(i, msg.id, 1)} title="Sim">👍</button>
                      <button onClick={() => enviarFeedback(i, msg.id, -1)} title="Não">👎</button>
                    </div>
                  )}
                  {msg.avaliada && (
                     <div className="feedbackArea"><span className="feedbackObrigado">Obrigado pelo feedback! ✓</span></div>
                  )}
                </div>
              );
            })}

            {carregando && (
              <div className="bolha assistant">
                <div className="digitando">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={fimRef} />
          </div>
        )}
      </div>

      <div className="partedebaixo">
        <div className="mensagemArea">
          <input
            type="text"
            placeholder="Envie uma mensagem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={carregando}
          />
          <button className="botaoEnviar" onClick={enviar} disabled={carregando || input.trim().length < 2}>
            <img src={enviarIcon} alt="Enviar" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Opções de clarificação (renderizadas quando a pergunta é ambígua) ──
function OpcoesClarificacao({ opcoes, onEscolher, desabilitado }) {
  return (
    <ul className="opcoesClarificacao">
      {opcoes.map((op) => (
        <li key={op.documento_id}>
          <button
            className="opcaoClarificacao"
            onClick={() => onEscolher(op.documento_id, op.documento_nome)}
            disabled={desabilitado}
          >
            <div className="opcaoHeader">
              <span className="opcaoDoc">{op.documento_nome}</span>
              {op.numero_pagina && (
                <span className="opcaoPagina">pág.&nbsp;{op.numero_pagina}</span>
              )}
            </div>
            <div className="opcaoTrecho">"{op.trecho}"</div>
          </button>
        </li>
      ))}
    </ul>
  );
}

function CitacoesArea({ citacoes }) {
  const [aberto, setAberto] = useState(false);
  return (
    <div className="citacoesArea">
      <button className="citacoesToggle" onClick={() => setAberto((v) => !v)} aria-expanded={aberto}>
        <span className="citacoesIcone">&#128196;</span>
        <span>{citacoes.length} fonte{citacoes.length !== 1 ? "s" : ""} consultada{citacoes.length !== 1 ? "s" : ""}</span>
        <span className="citacoesChevron">{aberto ? "▲" : "▼"}</span>
      </button>
      {aberto && (
        <ul className="citacoesList">
          {citacoes.map((c) => (
            <li key={c.ordem} className="citacaoCard">
              <div className="citacaoHeader">
                <span className="citacaoOrdem">{c.ordem}</span>
                <span className="citacaoDoc">{c.documento_nome}</span>
                {c.numero_pagina && <span className="citacaoPagina">pág.&nbsp;{c.numero_pagina}</span>}
              </div>
              <blockquote className="citacaoTrecho">{c.trecho}</blockquote>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}