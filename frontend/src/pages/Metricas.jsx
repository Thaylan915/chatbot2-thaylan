import { useState, useEffect, useMemo } from "react";
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

function corTaxa(valor, { invertida = false } = {}) {
  if (valor == null) return "#a0a0a0";
  const v = invertida ? 100 - valor : valor;
  if (v >= 75) return "#4caf50";
  if (v >= 40) return "#f0c87a";
  return "#ff6b6b";
}

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

function corClassificacao(c) {
  switch (c) {
    case "muito_constante": return "#4caf50";
    case "constante":       return "#80c784";
    case "moderado":        return "#f0c87a";
    case "instavel":        return "#ff6b6b";
    default:                return "#a0a0a0";
  }
}

function rotuloClassificacao(c) {
  switch (c) {
    case "muito_constante": return "Muito constante";
    case "constante":       return "Constante";
    case "moderado":        return "Moderado";
    case "instavel":        return "Instável";
    default:                return "Sem dados";
  }
}

function formatarDataHora(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("pt-BR") + " " + d.toLocaleTimeString("pt-BR", {
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function exportarCsvUsuarios(usuarios) {
  const headers = [
    "user_id", "username", "total_conversas", "total_perguntas",
    "total_respostas", "positivos", "negativos", "regeneradas",
    "taxa_acuracia_pct", "taxa_sucesso_pct", "ultima_atividade",
  ];
  const rows = usuarios.map((u) => [
    u.user_id, u.username, u.total_conversas, u.total_perguntas,
    u.total_respostas, u.positivos, u.negativos, u.regeneradas,
    u.taxa_acuracia ?? "", u.taxa_sucesso ?? "",
    u.ultima_atividade ?? "",
  ]);
  const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url;
  a.download = `metricas_usuarios_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function Metricas() {
  const [admin, setAdmin]           = useState(null);
  const [chat,  setChat]            = useState(null);
  const [usuarios, setUsuarios]     = useState(null);
  const [constancia, setConstancia] = useState(null);
  const [loading, setLoading]       = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.get("/api/admin/metrics/"),
      api.get("/api/chat/metricas/"),
      api.get("/api/admin/metrics/usuarios/"),
      api.get("/api/admin/metrics/constancia/?dias=14"),
    ]).then(([a, c, u, k]) => {
      if (a.status === "fulfilled") setAdmin(a.value.data);
      if (c.status === "fulfilled") setChat(c.value.data);
      if (u.status === "fulfilled") setUsuarios(u.value.data?.usuarios || []);
      if (k.status === "fulfilled") setConstancia(k.value.data);
      setLoading(false);
    });
  }, []);

  const usuariosOrdenados = useMemo(() => {
    if (!usuarios) return [];
    return [...usuarios].sort((a, b) => (b.total_perguntas || 0) - (a.total_perguntas || 0));
  }, [usuarios]);

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw", backgroundColor: "#1c1c1c", color: "#fff", overflow: "hidden" }}>
      <Sidebar />

      <div style={{ flex: 1, padding: 40, overflowY: "auto" }}>
        <h1 style={{ borderBottom: "1px solid #333", paddingBottom: 15, marginTop: 0 }}>
          📊 Métricas de Uso
        </h1>

        {loading && <p style={{ color: "#a0a0a0" }}>Carregando dados do servidor...</p>}

        {admin && (
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 30 }}>
            <div style={{ ...cardBase, background: "linear-gradient(135deg,#00adb5 0%,#007a80 100%)", color: "#fff", border: "none", flex: "1 1 320px", maxWidth: 480 }}>
              <h3 style={{ ...cardLabel, color: "rgba(255,255,255,0.9)" }}>Taxa de acurácia</h3>
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

        {chat && (
          <>
            <div style={{ display: "flex", gap: 20, marginTop: 30, flexWrap: "wrap" }}>
              <div style={cardBase}><h3 style={cardLabel}>Total de Conversas</h3><p style={{ ...cardValue, color: "#4caf50" }}>{chat.total_conversas}</p></div>
              <div style={cardBase}><h3 style={cardLabel}>Total de Mensagens</h3><p style={{ ...cardValue, color: "#4caf50" }}>{chat.total_mensagens}</p></div>
              <div style={cardBase}><h3 style={cardLabel}>Média de Notas</h3><p style={{ ...cardValue, color: "#4caf50" }}>{chat.media_notas}</p></div>
            </div>

            <h2 style={{ marginTop: 40, fontSize: "1.2rem", color: "#a0a0a0", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Qualidade das respostas
            </h2>
            <div style={{ display: "flex", gap: 20, marginTop: 15, flexWrap: "wrap" }}>
              <div style={cardBase}>
                <h3 style={cardLabel}>✅ Taxa de sucesso</h3>
                <p style={{ ...cardValue, color: corTaxa(chat.taxa_sucesso) }}>{chat.taxa_sucesso ?? 0}%</p>
                <BarraProgresso valor={chat.taxa_sucesso ?? 0} cor={corTaxa(chat.taxa_sucesso)} />
                <div style={cardSub}>{chat.respostas_ok ?? 0} de {chat.respostas_total ?? 0} respostas com sucesso</div>
              </div>
              <div style={cardBase}>
                <h3 style={cardLabel}>🔁 Taxa de reformulação</h3>
                <p style={{ ...cardValue, color: corTaxa(chat.taxa_reformulacao, { invertida: true }) }}>{chat.taxa_reformulacao ?? 0}%</p>
                <BarraProgresso valor={chat.taxa_reformulacao ?? 0} cor={corTaxa(chat.taxa_reformulacao, { invertida: true })} />
                <div style={cardSub}>{chat.reformulacoes ?? 0} de {chat.perguntas_total ?? 0} perguntas reformuladas</div>
              </div>
            </div>
          </>
        )}

        {/* ── Constância dos indicadores ─────────────────────────────────── */}
        {constancia && (
          <>
            <h2 style={{ marginTop: 40, fontSize: "1.2rem", color: "#a0a0a0", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Constância dos indicadores · últimos {constancia.dias} dias
            </h2>
            <p style={{ color: "#a0a0a0", fontSize: 13, marginTop: -6 }}>
              Mede a estabilidade dos indicadores ao longo do tempo via coeficiente de variação (CV).
              CV menor = indicador mais constante.
            </p>
            <div style={{ display: "flex", gap: 20, marginTop: 15, flexWrap: "wrap" }}>
              <CardConstancia titulo="Taxa de sucesso" stats={constancia.estatisticas_sucesso} />
              <CardConstancia titulo="Taxa de acurácia" stats={constancia.estatisticas_acuracia} />
              <CardSerie titulo="Taxa de sucesso por dia" serie={constancia.serie_sucesso} corTaxa={corTaxa} />
            </div>
          </>
        )}

        {/* ── Tabela por usuário ─────────────────────────────────────────── */}
        {usuarios && (
          <>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 40, marginBottom: 10 }}>
              <h2 style={{ fontSize: "1.2rem", color: "#a0a0a0", textTransform: "uppercase", letterSpacing: "0.05em", margin: 0 }}>
                Desempenho por usuário
              </h2>
              <button
                onClick={() => exportarCsvUsuarios(usuariosOrdenados)}
                style={{
                  background: "#00adb5",
                  color: "#fff",
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 14px",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontSize: 13,
                }}
              >
                ⬇ Exportar relatório (CSV)
              </button>
            </div>
            <div style={{ background: "#2c2f33", border: "1px solid #444", borderRadius: 12, overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                  <tr style={{ background: "#1c1c1c", textAlign: "left" }}>
                    <th style={th}>Usuário</th>
                    <th style={thNum}>Conversas</th>
                    <th style={thNum}>Perguntas</th>
                    <th style={thNum}>Respostas</th>
                    <th style={thNum}>👍</th>
                    <th style={thNum}>👎</th>
                    <th style={thNum}>🔄</th>
                    <th style={thNum}>Acurácia</th>
                    <th style={thNum}>Sucesso</th>
                    <th style={th}>Última atividade</th>
                  </tr>
                </thead>
                <tbody>
                  {usuariosOrdenados.map((u) => (
                    <tr key={u.user_id} style={{ borderTop: "1px solid #444" }}>
                      <td style={td}>{u.username}</td>
                      <td style={tdNum}>{u.total_conversas}</td>
                      <td style={tdNum}>{u.total_perguntas}</td>
                      <td style={tdNum}>{u.total_respostas}</td>
                      <td style={tdNum}>{u.positivos}</td>
                      <td style={tdNum}>{u.negativos}</td>
                      <td style={tdNum}>{u.regeneradas}</td>
                      <td style={{ ...tdNum, color: corTaxa(u.taxa_acuracia) }}>
                        {u.taxa_acuracia === null ? "—" : `${u.taxa_acuracia}%`}
                      </td>
                      <td style={{ ...tdNum, color: corTaxa(u.taxa_sucesso) }}>
                        {u.taxa_sucesso === null ? "—" : `${u.taxa_sucesso}%`}
                      </td>
                      <td style={{ ...td, color: "#a0a0a0", fontSize: 12 }}>
                        {formatarDataHora(u.ultima_atividade)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function CardConstancia({ titulo, stats }) {
  const cor = corClassificacao(stats?.classificacao);
  const rotulo = rotuloClassificacao(stats?.classificacao);
  return (
    <div style={cardBase}>
      <h3 style={cardLabel}>{titulo}</h3>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, justifyContent: "center" }}>
        <span style={{ fontSize: "2.2rem", fontWeight: 700 }}>
          {stats?.media == null ? "—" : `${stats.media}%`}
        </span>
        <span style={{ fontSize: "0.85rem", color: "#a0a0a0" }}>média</span>
      </div>
      <div style={{ marginTop: 10, padding: "4px 10px", borderRadius: 16, display: "inline-block",
                    background: cor + "22", color: cor, fontSize: 12, fontWeight: 600 }}>
        {rotulo} · CV {stats?.cv == null ? "—" : `${stats.cv}%`}
      </div>
      <div style={cardSub}>
        σ = {stats?.desvio_padrao ?? "—"} ·
        min {stats?.minimo ?? "—"} · max {stats?.maximo ?? "—"} · n={stats?.n ?? 0}
      </div>
    </div>
  );
}

function CardSerie({ titulo, serie, corTaxa }) {
  const max = 100;
  return (
    <div style={{ ...cardBase, textAlign: "left", flex: "2 1 420px", maxWidth: 700 }}>
      <h3 style={cardLabel}>{titulo}</h3>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 100, marginTop: 12 }}>
        {serie.map((p, i) => {
          const v = p.valor ?? 0;
          const h = p.valor === null ? 4 : Math.max(4, (v / max) * 100);
          const cor = p.valor === null ? "#444" : corTaxa(v);
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <div
                title={`${p.dia} — ${p.valor === null ? "sem dados" : v + "%"}`}
                style={{ width: "100%", height: `${h}%`, background: cor, borderRadius: 3 }}
              />
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", color: "#a0a0a0", fontSize: 10, marginTop: 6 }}>
        <span>{serie[0]?.dia.slice(5)}</span>
        <span>{serie[serie.length - 1]?.dia.slice(5)}</span>
      </div>
    </div>
  );
}

const th    = { padding: "10px 12px", fontWeight: 600, color: "#a0a0a0", borderBottom: "1px solid #444" };
const thNum = { ...th, textAlign: "right" };
const td    = { padding: "9px 12px" };
const tdNum = { ...td, textAlign: "right", fontVariantNumeric: "tabular-nums" };
