import { useState, useEffect, useRef } from "react";
import "./ChatArea.css";
import enviarIcon from "../assets/images/enviar.svg";
import api from "../services/api.jsx";

export default function ChatArea() {
  const [mensagens, setMensagens] = useState([]);
  const [input, setInput] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [conversaId, setConversaId] = useState(null);
  const fimRef = useRef(null);

  useEffect(() => {
    api
      .post("/api/chat/iniciar/")
      .then((res) => setConversaId(res.data.conversa_id))
      .catch((err) => console.error("Erro ao iniciar conversa:", err));
  }, []);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens, carregando]);

  async function enviar() {
    const texto = input.trim();
    if (!texto || carregando) return;

    setInput("");
    setMensagens((prev) => [...prev, { role: "user", conteudo: texto }]);
    setCarregando(true);

    try {
      const res = await api.post("/api/chat/pergunta/", {
        conversa_id: conversaId,
        question: texto,
      });
      setMensagens((prev) => [
        ...prev,
        {
          role:       "assistant",
          conteudo:   res.data.answer,
          fontes:     res.data.fontes    ?? [],
          citacoes:   res.data.citacoes  ?? [],
          respondida: res.data.respondida,
        },
      ]);
    } catch {
      setMensagens((prev) => [
        ...prev,
        {
          role:       "assistant",
          conteudo:   "Não foi possível conectar ao servidor. Tente novamente.",
          fontes:     [],
          citacoes:   [],
          respondida: false,
        },
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

  return (
    <div className="chatArea">
      <div className="mensagens">
        {mensagens.length === 0 ? (
          <div className="placeholder">
            <h2>Como posso ajudar?</h2>
          </div>
        ) : (
          <div className="listaMensagens">
            {mensagens.map((msg, i) => {
              const semResposta =
                msg.role === "assistant" && msg.respondida === false;
              return (
                <div
                  key={i}
                  className={`bolha ${msg.role}${semResposta ? " sem-resposta" : ""}`}
                >
                  {semResposta && (
                    <div className="sem-resposta-header">
                      <span className="sem-resposta-icone">&#9888;</span>
                      <span className="sem-resposta-titulo">
                        Não foi possível responder
                      </span>
                    </div>
                  )}

                  <div className="textoBolha">{msg.conteudo}</div>

                  {msg.citacoes && msg.citacoes.length > 0 && (
                    <CitacoesArea citacoes={msg.citacoes} />
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
          <button
            className="botaoEnviar"
            onClick={enviar}
            disabled={carregando || !input.trim()}
          >
            <img src={enviarIcon} alt="Enviar" />
          </button>
        </div>
      </div>
    </div>
  );
}

function CitacoesArea({ citacoes }) {
  const [aberto, setAberto] = useState(false);

  return (
    <div className="citacoesArea">
      <button
        className="citacoesToggle"
        onClick={() => setAberto((v) => !v)}
        aria-expanded={aberto}
      >
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
                {c.numero_pagina && (
                  <span className="citacaoPagina">pág.&nbsp;{c.numero_pagina}</span>
                )}
              </div>
              <blockquote className="citacaoTrecho">"{c.trecho}"</blockquote>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
