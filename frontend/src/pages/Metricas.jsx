import { useState, useEffect } from "react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

// ── Estilos compartilhados ──────────────────────────────────────────────────
const cardBase = {
  flex: "1 1 250px",
  backgroundColor: "#2c2f33",
  padding: "25px",
  borderRadius: "12px",
  textAlign: "center",
  border: "1px solid #444",
};

const cardLabel = {
  color: "#a0a0a0",
  margin: "0 0 15px 0",
  textTransform: "uppercase",
  fontSize: "0.9rem",
};

const cardValue = {
  fontSize: "3.5rem",
  margin: 0,
  fontWeight: "bold",
};

const cardSub = {
  marginTop: "8px",
  fontSize: "0.85rem",
  color: "#a0a0a0",
};

/**
 * Escolhe a cor da taxa em função do valor:
 *  - Sucesso/acurácia: verde alto, amarelo médio, vermelho baixo
 *  - Reformulação: invertido (alto reformulação = ruim)
 */
function corTaxa(valor, { invertida = false } = {}) {
  if (valor == null) return "#a0a0a0";
  const v = invertida ? 100 - valor : valor;
  if (v >= 75) return "#4caf50";
  if (v >= 40) return "#f0c87a";
  return "#ff6b6b";
}

/** Barrinha horizontal de progresso (0–100%) usada nos cards de taxa. */
function BarraProgresso({ valor, cor }) {
  const v = Math.max(0, Math.min(100, valor || 0));
  return (
    <div
      style={{
        marginTop: "10px",
        height: "6px",
        width: "100%",
        backgroundColor: "#1c1c1c",
        borderRadius: "3px",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${v}%`,
          backgroundColor: cor,
          transition: "width 0.4s ease",
        }}
      />
    </div>
  );
}

export default function Metricas() {
  const [data, setData]   = useState(null);
  const [admin, setAdmin] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.get("/api/chat/metricas/"),
      api.get("/api/admin/metrics/"),
    ]).then(([chatRes, adminRes]) => {
      if (chatRes.status === "fulfilled") setData(chatRes.value.data);
      if (adminRes.status === "fulfilled") setAdmin(adminRes.value.data);
      setLoading(false);
    });
  }, []);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        backgroundColor: "#1c1c1c",
        color: "#ffffff",
        overflow: "hidden",
      }}
    >
      <Sidebar />

      <div style={{ flex: 1, padding: "40px", overflowY: "auto" }}>
        <h1 style={{ borderBottom: "1px solid #333", paddingBottom: "15px", marginTop: 0 }}>
          📊 Métricas de Uso
        </h1>

        {loading ? (
          <p style={{ color: "#a0a0a0" }}>Carregando dados do servidor...</p>
        ) : !data && !admin ? (
          <p style={{ color: "#ff6b6b" }}>
            Erro ao carregar métricas. Verifique se o backend está rodando.
          </p>
        ) : (
          <>
            {admin && (
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 30 }}>
                <div
                  style={{
                    ...cardBase,
                    background: "linear-gradient(135deg, #00adb5 0%, #007a80 100%)",
                    color: "#fff",
                    border: "none",
                    flex: "1 1 320px",
                    maxWidth: 480,
                  }}
                >
                  <h3 style={{ ...cardLabel, color: "rgba(255,255,255,0.9)" }}>
                    Taxa de acurácia
                  </h3>
                  <p style={{ ...cardValue, color: "#fff" }}>
                    {admin.taxa_acuracia === null ? "—" : `${admin.taxa_acuracia}%`}
                  </p>
                  <div style={{ ...cardSub, color: "rgba(255,255,255,0.85)" }}>
                    {admin.feedback_avaliadas === 0
                      ? "Ainda não há respostas avaliadas pelos usuários."
                      : `${admin.feedback_positivos} positivas de ${admin.feedback_avaliadas} avaliadas`}
                  </div>
                </div>
              </div>
            )}

            {data && (
              <>
                <div style={{ display: "flex", gap: "20px", marginTop: "30px", flexWrap: "wrap" }}>
                  <div style={cardBase}>
                    <h3 style={cardLabel}>Total de Conversas</h3>
                    <p style={{ ...cardValue, color: "#4caf50" }}>{data.total_conversas}</p>
                  </div>

                  <div style={cardBase}>
                    <h3 style={cardLabel}>Total de Mensagens</h3>
                    <p style={{ ...cardValue, color: "#4caf50" }}>{data.total_mensagens}</p>
                  </div>

                  <div style={cardBase}>
                    <h3 style={cardLabel}>Média de Notas</h3>
                    <p style={{ ...cardValue, color: "#4caf50" }}>{data.media_notas}</p>
                  </div>
                </div>

                <h2
                  style={{
                    marginTop: "40px",
                    fontSize: "1.2rem",
                    color: "#a0a0a0",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Qualidade das respostas
                </h2>
                <div style={{ display: "flex", gap: "20px", marginTop: "15px", flexWrap: "wrap" }}>
                  <div style={cardBase}>
                    <h3 style={cardLabel}>✅ Taxa de sucesso</h3>
                    <p style={{ ...cardValue, color: corTaxa(data.taxa_sucesso) }}>
                      {data.taxa_sucesso ?? 0}%
                    </p>
                    <BarraProgresso valor={data.taxa_sucesso ?? 0} cor={corTaxa(data.taxa_sucesso)} />
                    <div style={cardSub}>
                      {data.respostas_ok ?? 0} de {data.respostas_total ?? 0} respostas com sucesso
                    </div>
                  </div>

                  <div style={cardBase}>
                    <h3 style={cardLabel}>🔁 Taxa de reformulação</h3>
                    <p style={{ ...cardValue, color: corTaxa(data.taxa_reformulacao, { invertida: true }) }}>
                      {data.taxa_reformulacao ?? 0}%
                    </p>
                    <BarraProgresso
                      valor={data.taxa_reformulacao ?? 0}
                      cor={corTaxa(data.taxa_reformulacao, { invertida: true })}
                    />
                    <div style={cardSub}>
                      {data.reformulacoes ?? 0} de {data.perguntas_total ?? 0} perguntas reformuladas
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    marginTop: "30px",
                    backgroundColor: "#2c2f33",
                    padding: "25px",
                    borderRadius: "12px",
                    maxWidth: "400px",
                    border: "1px solid #444",
                  }}
                >
                  <h2 style={{ marginTop: 0, marginBottom: "20px", fontSize: "1.2rem" }}>
                    Feedback dos Usuários
                  </h2>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: "1.2rem",
                      padding: "10px 0",
                      borderBottom: "1px solid #444",
                    }}
                  >
                    <span>👍 Positivos</span>
                    <strong style={{ color: "#4caf50" }}>{data.feedbacks_positivos}</strong>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: "1.2rem",
                      padding: "15px 0 0 0",
                    }}
                  >
                    <span>👎 Negativos</span>
                    <strong style={{ color: "#ff6b6b" }}>{data.feedbacks_negativos}</strong>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
