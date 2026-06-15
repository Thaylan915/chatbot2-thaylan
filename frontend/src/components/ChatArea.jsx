import { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { useLocation } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import "./ChatArea.css";
import enviarIcon from "../assets/images/enviar.svg";
import api from "../services/api.jsx";
import { authService } from "../services/authService";

export default function ChatArea() {
  const [mensagens, setMensagens]   = useState([]);
  const [input, setInput]           = useState("");
  const [erroCarregamento, setErroCarregamento] = useState("");
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
          id:                 res.data.answer_id ?? res.data.mensagem_id,
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

    setMensagens((prev) => [
      ...prev,
      { role: "user", conteudo: `Consultar em: ${documentoNome}` },
    ]);

    await enviarPergunta(texto, {
      documentoIdFiltro: documentoId,
      ecoarUsuario:      false,
    });
  }

  async function regenerar(msgId) {
    if (!msgId || carregando) return;
    setCarregando(true);
    try {
      const res = await api.post(`/api/chat/mensagens/${msgId}/regenerar/`);
      setMensagens((prev) => [
        ...prev,
        {
          role: "assistant",
          id: res.data.id,
          conteudo: res.data.answer,
          fontes: [],
          citacoes: [],
          respondida: true,
          intencao: "rag",
          opcoesClarificacao: [],
          avaliada: false,
        },
      ]);
    } catch {
      setMensagens((prev) => [
        ...prev,
        { role: "assistant", conteudo: "Erro ao regenerar resposta." },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  }

  function perguntaAnteriorA(index) {
    for (let j = index - 1; j >= 0; j--) {
      if (mensagens[j].role === "user") return mensagens[j].conteudo || "";
    }
    return "";
  }

  function baixarBlob(blob, nomeArquivo) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = nomeArquivo;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function exportarRespostaTxt(index, msg) {
    const pergunta = perguntaAnteriorA(index);
    const data = new Date().toLocaleString("pt-BR");
    const fontes = (msg.fontes || []).map((f) => `- ${f.nome}`).join("\n");
    const citacoes = (msg.citacoes || [])
      .map(
        (c) =>
          `[${c.ordem}] ${c.documento_nome}${
            c.numero_pagina ? ` (pág. ${c.numero_pagina})` : ""
          }\n    "${c.trecho}"`
      )
      .join("\n");

    const conteudo =
      `Relatório de resposta — Chatbot IFES\n` +
      `Gerado em: ${data}\n\n` +
      `Pergunta:\n${pergunta}\n\n` +
      `Resposta:\n${msg.conteudo || ""}\n\n` +
      (fontes ? `Fontes:\n${fontes}\n\n` : "") +
      (citacoes ? `Citações:\n${citacoes}\n` : "");

    const nome = `resposta_${msg.id || "chat"}_${new Date()
      .toISOString()
      .slice(0, 10)}.txt`;
    baixarBlob(new Blob([conteudo], { type: "text/plain;charset=utf-8" }), nome);
  }

  async function exportarRespostaPdf(index, msg) {
    const { jsPDF } = await import(
      "https://cdn.jsdelivr.net/npm/jspdf@2.5.1/+esm"
    );

    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const largura = doc.internal.pageSize.getWidth();
    const altura = doc.internal.pageSize.getHeight();
    const margemEsq = 15;
    const margemDir = largura - 15;
    const larguraUtil = margemDir - margemEsq;
    let y = 20;

    // Cabeçalho
    doc.setFillColor(34, 40, 49);
    doc.rect(0, 0, largura, 28, "F");
    doc.setTextColor(238, 238, 238);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(16);
    doc.text("Relatório de Resposta — Chatbot IFES", margemEsq, 17);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.text(
      `Gerado em: ${new Date().toLocaleString("pt-BR")}`,
      margemDir,
      17,
      { align: "right" }
    );
    y = 38;

    const escreverBloco = (titulo, texto, corTitulo = [0, 173, 181]) => {
      if (!texto) return;
      const linhas = doc.splitTextToSize(texto, larguraUtil);
      const espacoNecessario = 8 + linhas.length * 5 + 4;
      if (y + espacoNecessario > altura - 15) {
        doc.addPage();
        y = 20;
      }
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(...corTitulo);
      doc.text(titulo, margemEsq, y);
      y += 6;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      doc.setTextColor(40, 40, 40);
      doc.text(linhas, margemEsq, y);
      y += linhas.length * 5 + 4;
    };

    escreverBloco("Pergunta", perguntaAnteriorA(index));
    escreverBloco("Resposta", msg.conteudo || "");

    if (msg.fontes?.length) {
      const lista = msg.fontes.map((f) => `• ${f.nome}`).join("\n");
      escreverBloco("Fontes consultadas", lista);
    }

    if (msg.citacoes?.length) {
      const lista = msg.citacoes
        .map(
          (c) =>
            `[${c.ordem}] ${c.documento_nome}${
              c.numero_pagina ? ` (pág. ${c.numero_pagina})` : ""
            }\n    "${c.trecho}"`
        )
        .join("\n\n");
      escreverBloco("Citações", lista);
    }

    doc.save(
      `resposta_${msg.id || "chat"}_${new Date().toISOString().slice(0, 10)}.pdf`
    );
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

              let classeExtra = "";
              if (ehClarificacao) classeExtra = " clarificacao";
              else if (semResposta) classeExtra = " sem-resposta";

              const chave = msg.id ?? msg._tempId ?? `msg-${i}`;
              return (
                <div key={chave} className={`bolha ${msg.role}${classeExtra}`}>
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

                  {/* Botões de avaliação */}
                  {msg.role === "assistant" && msg.id && !semResposta && !msg.avaliada && (
                    <div className="feedbackArea">
                      <span className="feedbackPergunta">A resposta foi útil?</span>
                      <button onClick={() => enviarFeedback(i, msg.id, 1)} title="Sim">👍</button>
                      <button onClick={() => enviarFeedback(i, msg.id, -1)} title="Não">👎</button>
                      <button
                        onClick={() => regenerar(msg.id)}
                        title="Reformular resposta"
                        disabled={carregando}
                        style={{ marginLeft: 8 }}
                      >
                        🔄 Reformular
                      </button>
                      <button
                        onClick={() => exportarRespostaPdf(i, msg)}
                        title="Exportar resposta como PDF"
                        style={{ marginLeft: 8 }}
                      >
                        📄 PDF
                      </button>
                      <button
                        onClick={() => exportarRespostaTxt(i, msg)}
                        title="Exportar resposta como texto"
                        style={{ marginLeft: 4 }}
                      >
                        📝 TXT
                      </button>
                    </div>
                  )}
                  {msg.avaliada && msg.role === "assistant" && msg.id && !semResposta && (
                    <div className="feedbackArea">
                      <span className="feedbackObrigado">Obrigado pelo feedback! ✓</span>
                      <button
                        onClick={() => regenerar(msg.id)}
                        title="Reformular resposta"
                        disabled={carregando}
                        style={{ marginLeft: 8 }}
                      >
                        🔄 Reformular
                      </button>
                      <button
                        onClick={() => exportarRespostaPdf(i, msg)}
                        title="Exportar resposta como PDF"
                        style={{ marginLeft: 8 }}
                      >
                        📄 PDF
                      </button>
                      <button
                        onClick={() => exportarRespostaTxt(i, msg)}
                        title="Exportar resposta como texto"
                        style={{ marginLeft: 4 }}
                      >
                        📝 TXT
                      </button>
                    </div>
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

OpcoesClarificacao.propTypes = {
  opcoes: PropTypes.array,
  onEscolher: PropTypes.func,
  desabilitado: PropTypes.bool,
};

function CitacoesArea({ citacoes }) {
  const [aberto, setAberto] = useState(false);
  return (
    <div className="citacoesArea">
      <button className="citacoesToggle" onClick={() => setAberto((v) => !v)} aria-expanded={aberto}>
        <span className="citacoesIcone">&#128196;</span>
        <span>{citacoes.length} fonte{citacoes.length === 1 ? "" : "s"} consultada{citacoes.length === 1 ? "" : "s"}</span>
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

CitacoesArea.propTypes = {
  citacoes: PropTypes.array,
};