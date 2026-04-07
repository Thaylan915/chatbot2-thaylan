import { useState, useRef, useEffect } from "react";
import "./ChatArea.css";
import enviarIcon from "../assets/images/enviar.svg";
import api from "../services/api";

export default function ChatArea() {
  const [mensagens, setMensagens] = useState([]);
  const [input, setInput] = useState("");
  const [conversaId, setConversaId] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const fimRef = useRef(null);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens]);

  async function handleEnviar() {
    const texto = input.trim();
    if (!texto || carregando) return;

    setInput("");
    setMensagens((prev) => [...prev, { role: "user", texto }]);
    setCarregando(true);

    try {
      const res = await api.post("/api/chat/pergunta/", {
        conversa_id: conversaId,
        question: texto,
      });

      if (!conversaId) setConversaId(res.data.conversa_id);

      setMensagens((prev) => [
        ...prev,
        { role: "assistant", texto: res.data.answer },
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
          <div key={i} className={`mensagem ${m.role}`}>
            <span>{m.texto}</span>
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
