import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import api from "../services/api";

function formatarDataHora(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return `${d.toLocaleDateString("pt-BR")} ${d.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  } catch {
    return "—";
  }
}

export default function Historico() {
  const [conversas, setConversas] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);
  const [selecionada, setSelecionada] = useState(null);
  const [mensagens, setMensagens] = useState([]);
  const [carregandoMsgs, setCarregandoMsgs] = useState(false);

  useEffect(() => {
    api
      .get("/api/admin/conversas/")
      .then((res) => setConversas(res.data?.conversas || []))
      .catch((e) =>
        setErro(e.response?.data?.error || "Erro ao carregar conversas")
      )
      .finally(() => setCarregando(false));
  }, []);

  function abrirConversa(c) {
    setSelecionada(c);
    setMensagens([]);
    setCarregandoMsgs(true);
    api
      .get(`/api/chat/${c.id}/historico/`)
      .then((res) => setMensagens(res.data?.mensagens || []))
      .catch(() => setMensagens([]))
      .finally(() => setCarregandoMsgs(false));
  }

  return (
    <div style={{ display: "flex", height: "100vh", backgroundColor: "#222831" }}>
      <Sidebar />
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Lista de conversas */}
        <div
          style={{
            width: 360,
            borderRight: "1px solid #393e46",
            overflowY: "auto",
            padding: 16,
          }}
        >
          <h2 style={{ color: "#00adb5", fontFamily: "Poppins", marginBottom: 16 }}>
            Todas as conversas
          </h2>
          {carregando && <p style={{ color: "#eee" }}>Carregando...</p>}
          {erro && <p style={{ color: "#f55" }}>{erro}</p>}
          {!carregando && !erro && conversas.length === 0 && (
            <p style={{ color: "#eee", opacity: 0.6 }}>Nenhuma conversa.</p>
          )}
          {conversas.map((c) => (
            <div
              key={c.id}
              onClick={() => abrirConversa(c)}
              style={{
                padding: "12px 14px",
                marginBottom: 8,
                background:
                  selecionada?.id === c.id ? "#00adb5" : "#393e46",
                color: selecionada?.id === c.id ? "#fff" : "#eee",
                borderRadius: 8,
                cursor: "pointer",
                fontFamily: "Poppins",
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                {c.titulo || `Conversa #${c.id}`}
              </div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>
                👤 {c.usuario} • {formatarDataHora(c.iniciada_em)}
              </div>
              <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>
                {c.qtd_mensagens} mensagem(ns)
              </div>
            </div>
          ))}
        </div>

        {/* Detalhes da conversa selecionada */}
        <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
          {!selecionada && (
            <p style={{ color: "#eee", opacity: 0.6, fontFamily: "Poppins" }}>
              Selecione uma conversa à esquerda para visualizar.
            </p>
          )}
          {selecionada && (
            <>
              <h2 style={{ color: "#00adb5", fontFamily: "Poppins" }}>
                {selecionada.titulo}
              </h2>
              <p style={{ color: "#eee", fontFamily: "Poppins", opacity: 0.7 }}>
                Usuário: <strong>{selecionada.usuario}</strong> ·{" "}
                {formatarDataHora(selecionada.iniciada_em)}
              </p>
              <hr style={{ borderColor: "#393e46", margin: "16px 0" }} />
              {carregandoMsgs && <p style={{ color: "#eee" }}>Carregando mensagens...</p>}
              {!carregandoMsgs &&
                mensagens.map((m) => (
                  <div
                    key={m.id}
                    style={{
                      maxWidth: 700,
                      margin: m.role === "user" ? "8px 0 8px auto" : "8px auto 8px 0",
                      background: m.role === "user" ? "#00adb5" : "#4a5060",
                      color: "#fff",
                      padding: "10px 14px",
                      borderRadius: 12,
                      fontFamily: "Poppins",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                    }}
                  >
                    {m.conteudo_original}
                    {m.role === "assistant" && m.feedback && (
                      <div style={{ fontSize: 11, opacity: 0.8, marginTop: 4 }}>
                        Feedback: {m.feedback === "positive" ? "👍 positivo" : "👎 negativo"}
                        {m.foi_reformulada && " · regenerada"}
                      </div>
                    )}
                  </div>
                ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
