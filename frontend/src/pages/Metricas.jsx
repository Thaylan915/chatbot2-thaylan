import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import api from "../services/api";

const cardStyle = {
  background: "#393e46",
  border: "1px solid #4a5060",
  borderRadius: 12,
  padding: "20px 24px",
  fontFamily: "Poppins",
  color: "#eee",
  minWidth: 220,
  flex: "1 1 220px",
};

const valorStyle = {
  fontSize: 38,
  fontWeight: 700,
  color: "#00adb5",
  marginTop: 8,
};

const labelStyle = {
  fontSize: 13,
  opacity: 0.7,
};

export default function Metricas() {
  const [m, setM] = useState(null);
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    api
      .get("/api/admin/metrics/")
      .then((res) => setM(res.data))
      .catch((e) =>
        setErro(e.response?.data?.error || "Erro ao carregar métricas")
      )
      .finally(() => setCarregando(false));
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh", backgroundColor: "#222831" }}>
      <Sidebar />
      <div style={{ flex: 1, padding: 30, overflowY: "auto" }}>
        <h2 style={{ color: "#00adb5", fontFamily: "Poppins", marginBottom: 24 }}>
          Métricas do Chatbot
        </h2>

        {carregando && <p style={{ color: "#eee", fontFamily: "Poppins" }}>Carregando...</p>}
        {erro && <p style={{ color: "#f55", fontFamily: "Poppins" }}>{erro}</p>}

        {m && (
          <>
            {/* Cards destacados — Taxa de acurácia e Taxa de sucesso */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
              <div
                style={{
                  ...cardStyle,
                  background: "linear-gradient(135deg, #00adb5 0%, #007a80 100%)",
                  color: "#fff",
                  flex: "1 1 320px",
                  maxWidth: 480,
                }}
              >
                <div style={{ ...labelStyle, color: "rgba(255,255,255,0.9)", fontSize: 14 }}>
                  Taxa de acurácia
                </div>
                <div style={{ ...valorStyle, color: "#fff", fontSize: 56 }}>
                  {m.taxa_acuracia === null ? "—" : `${m.taxa_acuracia}%`}
                </div>
                <div style={{ fontSize: 13, opacity: 0.9, marginTop: 4 }}>
                  {m.feedback_avaliadas === 0
                    ? "Ainda não há respostas avaliadas pelos usuários."
                    : `${m.feedback_positivos} positivas de ${m.feedback_avaliadas} avaliadas`}
                </div>
                <div style={{ fontSize: 11, opacity: 0.75, marginTop: 6, fontStyle: "italic" }}>
                  positivos ÷ (positivos + negativos)
                </div>
              </div>

              <div
                style={{
                  ...cardStyle,
                  background: "linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)",
                  color: "#fff",
                  flex: "1 1 320px",
                  maxWidth: 480,
                }}
              >
                <div style={{ ...labelStyle, color: "rgba(255,255,255,0.9)", fontSize: 14 }}>
                  Taxa de sucesso
                </div>
                <div style={{ ...valorStyle, color: "#fff", fontSize: 56 }}>
                  {m.taxa_sucesso === null ? "—" : `${m.taxa_sucesso}%`}
                </div>
                <div style={{ fontSize: 13, opacity: 0.9, marginTop: 4 }}>
                  {m.total_respostas === 0
                    ? "Nenhuma resposta gerada ainda."
                    : `${m.respostas_bem_sucedidas} aceitas de ${m.total_respostas} respostas`}
                </div>
                <div style={{ fontSize: 11, opacity: 0.75, marginTop: 6, fontStyle: "italic" }}>
                  respostas sem 👎 e sem regeneração ÷ total
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 32 }}>
              <div style={cardStyle}>
                <div style={labelStyle}>Quantidade de respostas</div>
                <div style={valorStyle}>{m.total_respostas}</div>
              </div>

              <div style={cardStyle}>
                <div style={labelStyle}>Avaliações positivas</div>
                <div style={valorStyle}>
                  {m.feedback_pct_positivo}%
                </div>
                <div style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>
                  {m.feedback_positivos} de {m.feedback_avaliadas} avaliadas
                </div>
              </div>

              <div style={cardStyle}>
                <div style={labelStyle}>Avaliações negativas</div>
                <div style={{ ...valorStyle, color: "#f08080" }}>
                  {m.feedback_pct_negativo}%
                </div>
                <div style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>
                  {m.feedback_negativos} de {m.feedback_avaliadas} avaliadas
                </div>
              </div>

              <div style={cardStyle}>
                <div style={labelStyle}>Refatorações</div>
                <div style={valorStyle}>{m.refatoracoes}</div>
                <div style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>
                  respostas regeneradas pelo usuário
                </div>
              </div>
            </div>

            <h3 style={{ color: "#00adb5", fontFamily: "Poppins", marginBottom: 12 }}>
              Outros números
            </h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 16 }}>
              <div style={cardStyle}>
                <div style={labelStyle}>Total de conversas</div>
                <div style={valorStyle}>{m.total_conversas}</div>
              </div>
              <div style={cardStyle}>
                <div style={labelStyle}>Total de perguntas feitas</div>
                <div style={valorStyle}>{m.total_perguntas}</div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
