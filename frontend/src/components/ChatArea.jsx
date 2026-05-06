import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./ChatArea.css";
import enviarIcon from "../assets/images/enviar.svg";
import api from "../services/api";

export default function ChatArea({ conversaId, setConversaId, onConversaCriada }) {
  const [mensagens, setMensagens] = useState([]);
  const [input, setInput] = useState("");
  const [carregando, setCarregando] = useState(false);
  const fimRef = useRef(null);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens]);

  // Quando a conversa selecionada mudar, carrega o histórico (ou limpa).
  useEffect(() => {
    if (!conversaId) {
      setMensagens([]);
      return;
    }
    let ativo = true;
    api
      .get(`/api/chat/${conversaId}/historico/`)
      .then((res) => {
        if (!ativo) return;
        const msgs = (res.data?.mensagens || []).map((m) => ({
          id: m.id,
          role: m.role,
          texto: m.conteudo_original,
          feedback: m.feedback || null,
        }));
        setMensagens(msgs);
      })
      .catch(() => {
        if (ativo) setMensagens([]);
      });
    return () => {
      ativo = false;
    };
  }, [conversaId]);

  async function handleEnviar() {
    const texto = input.trim();
    if (!texto || carregando) return;

    setInput("");
    setMensagens((prev) => [...prev, { role: "user", texto }]);
    setCarregando(true);

    const eraNova = !conversaId;

    try {
      const res = await api.post("/api/chat/pergunta/", {
        conversa_id: conversaId,
        question: texto,
      });

      const novoId = res.data.conversa_id;
      if (eraNova) {
        setConversaId?.(novoId);
        onConversaCriada?.();
      }

      setMensagens((prev) => [
        ...prev,
        {
          id: res.data.answer_id,
          role: "assistant",
          texto: res.data.answer,
          feedback: null,
        },
      ]);
    } catch {
      setMensagens((prev) => [
        ...prev,
        { role: "assistant", texto: "Erro ao obter resposta. Tente novamente." },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  async function setFeedback(msgId, feedback) {
    if (!msgId) return;
    // toggle: se já tinha esse feedback, remove
    setMensagens((prev) =>
      prev.map((m) =>
        m.id === msgId
          ? { ...m, feedback: m.feedback === feedback ? null : feedback }
          : m
      )
    );
    const novoValor = (() => {
      const atual = mensagens.find((m) => m.id === msgId)?.feedback;
      return atual === feedback ? null : feedback;
    })();
    try {
      await api.post(`/api/chat/mensagens/${msgId}/feedback/`, {
        feedback: novoValor,
      });
    } catch {
      // rollback simples em caso de erro
    }
  }

  async function regenerar(msgId) {
    if (!msgId || carregando) return;
    setCarregando(true);
    try {
      const res = await api.post(`/api/chat/mensagens/${msgId}/regenerar/`);
      setMensagens((prev) => [
        ...prev,
        {
          id: res.data.id,
          role: "assistant",
          texto: res.data.answer,
          feedback: null,
        },
      ]);
    } catch {
      setMensagens((prev) => [
        ...prev,
        { role: "assistant", texto: "Erro ao regenerar resposta." },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleEnviar();
    }
  }

  return (
    <div className="chatArea">
      <div className="mensagens">
        {mensagens.length === 0 && (
          <div className="placeholder">
            <h2>Como posso ajudar?</h2>
          </div>
        )}

        {mensagens.map((m, i) => (
          <div key={m.id ?? i} className={`mensagem ${m.role}`}>
            {m.role === "assistant" ? (
              <>
                <ReactMarkdown>{m.texto}</ReactMarkdown>
                {m.id && (
                  <div className="acoesMsg">
                    <button
                      className={`btnAcao ${m.feedback === "positive" ? "ativo" : ""}`}
                      onClick={() => setFeedback(m.id, "positive")}
                      title="Resposta útil"
                    >
                      👍
                    </button>
                    <button
                      className={`btnAcao ${m.feedback === "negative" ? "ativo" : ""}`}
                      onClick={() => setFeedback(m.id, "negative")}
                      title="Resposta ruim"
                    >
                      👎
                    </button>
                    <button
                      className="btnAcao"
                      onClick={() => regenerar(m.id)}
                      title="Regenerar resposta"
                      disabled={carregando}
                    >
                      🔄
                    </button>
                  </div>
                )}
              </>
            ) : (
              <span>{m.texto}</span>
            )}
          </div>
        ))}

        {carregando && (
          <div className="mensagem assistant">
            <span>...</span>
          </div>
        )}

        <div ref={fimRef} />
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
          <button className="botaoEnviar" onClick={handleEnviar} disabled={carregando}>
            <img src={enviarIcon} alt="Enviar" />
          </button>
        </div>
      </div>
    </div>
  );
}
