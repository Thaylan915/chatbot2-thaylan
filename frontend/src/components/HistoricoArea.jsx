import "./HistoricoArea.css";
import { useEffect, useState } from "react";
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

export default function HistoricoArea() {
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
        setErro(e.response?.data?.error || "Erro ao carregar conversas"),
      )
      .finally(() => setCarregando(false));
  }, []);

  function abrirConversa(c) {
    const id = Number(c?.id);
    if (!Number.isInteger(id) || id <= 0) return;
    setSelecionada(c);
    setMensagens([]);
    setCarregandoMsgs(true);

    api
      .get(`/api/chat/${id}/historico/`)
      .then((res) => setMensagens(res.data?.mensagens || []))
      .catch(() => setMensagens([]))
      .finally(() => setCarregandoMsgs(false));
  }

  const isAtiva = (id) => selecionada?.id === id;

  return (
    <div className="histArea">
      {/* LISTA DE CONVERSAS */}
      <div className="histLista">
        <h2 className="histTitulo">Todas as conversas</h2>

        {carregando && <p className="histMsg">Carregando...</p>}
        {erro && <p className="histMsgErro">{erro}</p>}
        {!carregando && !erro && conversas.length === 0 && (
          <p className="histMsgVazio">Nenhuma conversa.</p>
        )}

        {conversas.map((c) => (
          <button
            type="button"
            key={c.id}
            onClick={() => abrirConversa(c)}
            className={`histConversa${isAtiva(c.id) ? " ativa" : ""}`}
          >
            <div className="histConversaTitulo">
              {c.titulo || `Conversa #${c.id}`}
            </div>
            <div className="histConversaMeta">
              {c.usuario} • {formatarDataHora(c.iniciada_em)}
            </div>
            <div className="histConversaQtd">
              {c.qtd_mensagens} mensagem(ns)
            </div>
          </button>
        ))}
      </div>

      {/* DETALHES */}
      <div className="histDetalhes">
        {!selecionada && (
          <p className="histPlaceholder">
            Selecione uma conversa à esquerda para visualizar.
          </p>
        )}

        {selecionada && (
          <>
            <h2 className="histDetalhesTitulo">{selecionada.titulo}</h2>

            <p className="histDetalhesMeta">
              Usuário: <strong>{selecionada.usuario}</strong> ·{" "}
              {formatarDataHora(selecionada.iniciada_em)}
            </p>

            <hr className="histDivisor" />

            {carregandoMsgs && <p className="histMsg">Carregando mensagens...</p>}

            {!carregandoMsgs &&
              mensagens.map((m) => (
                <div key={m.id} className={`histBolha ${m.role}`}>
                  {m.conteudo_original}

                  {m.role === "assistant" && m.feedback && (
                    <div className="histFeedback">
                      Feedback:{" "}
                      {m.feedback === "positive" ? "👍 positivo" : "👎 negativo"}
                      {m.foi_reformulada && " · regenerada"}
                    </div>
                  )}
                </div>
              ))}
          </>
        )}
      </div>
    </div>
  );
}
