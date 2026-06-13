import { useState, useEffect, useMemo } from "react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

// ── Helpers de cor ──────────────────────────────────────────────────────────
function corTaxa(valor, { invertida = false } = {}) {
  if (valor == null) return "#a0a0a0";
  const v = invertida ? 100 - valor : valor;
  if (v >= 75) return "#4caf50";
  if (v >= 40) return "#f0c87a";
  return "#ff6b6b";
}

function corClassificacao(c) {
  switch (c) {
    case "muito_constante":
      return "#4caf50";
    case "constante":
      return "#80c784";
    case "moderado":
      return "#f0c87a";
    case "instavel":
      return "#ff6b6b";
    default:
      return "#a0a0a0";
  }
}

function rotuloClassificacao(c) {
  switch (c) {
    case "muito_constante":
      return "Muito constante";
    case "constante":
      return "Constante";
    case "moderado":
      return "Moderado";
    case "instavel":
      return "Instável";
    default:
      return "Sem dados";
  }
}

function formatarDataHora(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return (
      d.toLocaleDateString("pt-BR") +
      " " +
      d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
    );
  } catch {
    return "—";
  }
}

// ── Barra de progresso ──────────────────────────────────────────────────────
function BarraProgresso({ valor, cor }) {
  const v = Math.max(0, Math.min(100, valor || 0));
  return (
    <div
      style={{
        marginTop: 10,
        height: 6,
        width: "100%",
        backgroundColor: "#393e46",
        borderRadius: 3,
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

// ── Export CSV ──────────────────────────────────────────────────────────────
function exportarCsvUsuarios(usuarios) {
  const headers = [
    "user_id",
    "username",
    "total_conversas",
    "total_perguntas",
    "total_respostas",
    "positivos",
    "negativos",
    "regeneradas",
    "taxa_acuracia_pct",
    "taxa_sucesso_pct",
    "ultima_atividade",
  ];
  const rows = usuarios.map((u) => [
    u.user_id,
    u.username,
    u.total_conversas,
    u.total_perguntas,
    u.total_respostas,
    u.positivos,
    u.negativos,
    u.regeneradas,
    u.taxa_acuracia ?? "",
    u.taxa_sucesso ?? "",
    u.ultima_atividade ?? "",
  ]);
  const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `metricas_usuarios_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Estilos compartilhados (padrão do projeto) ──────────────────────────────
const card = {
  flex: "1 1 220px",
  backgroundColor: "#222831",
  borderRadius: 22,
  padding: 20,
  display: "flex",
  flexDirection: "column",
  gap: 8,
};

const cardTitulo = {
  margin: 0,
  fontSize: "0.8rem",
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "rgba(255,255,255,0.5)",
};

const cardValor = {
  margin: 0,
  fontSize: "3rem",
  fontWeight: "bold",
  lineHeight: 1,
};

const cardSub = {
  fontSize: "0.82rem",
  color: "rgba(255,255,255,0.5)",
  marginTop: 2,
};

const secaoTitulo = {
  margin: "0 0 14px 0",
  fontSize: "0.8rem",
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.08em",
  color: "rgba(255,255,255,0.5)",
};

// ── Componente principal ────────────────────────────────────────────────────
export default function Metricas() {
  const [admin, setAdmin] = useState(null);
  const [chat, setChat] = useState(null);
  const [usuarios, setUsuarios] = useState(null);
  const [constancia, setConstancia] = useState(null);
  const [logs, setLogs] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.get("/api/admin/metrics/"),
      api.get("/api/chat/metricas/"),
      api.get("/api/admin/metrics/usuarios/"),
      api.get("/api/admin/metrics/constancia/?dias=14"),
      api.get("/api/admin-logs/"),
    ]).then(([a, c, u, k, l]) => {
      if (a.status === "fulfilled") setAdmin(a.value.data);
      if (c.status === "fulfilled") setChat(c.value.data);
      if (u.status === "fulfilled") setUsuarios(u.value.data?.usuarios || []);
      if (k.status === "fulfilled") setConstancia(k.value.data);
      if (l.status === "fulfilled") setLogs(l.value.data || []);
      setLoading(false);
    });
  }, []);

  const usuariosOrdenados = useMemo(() => {
    if (!usuarios) return [];
    return [...usuarios].sort(
      (a, b) => (b.total_perguntas || 0) - (a.total_perguntas || 0),
    );
  }, [usuarios]);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        backgroundColor: "#393e46",
        color: "#eeeeee",
        overflow: "hidden",
        fontFamily: '"Poppins", sans-serif',
      }}
    >
      <Sidebar />

      {/* ── Área principal ── */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        }}
      >
        {/* Cabeçalho */}
        <div
          style={{
            backgroundColor: "#222831",
            padding: "20px 40px",
            display: "flex",
            alignItems: "center",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            flexShrink: 0,
          }}
        >
          <h2 style={{ margin: 0, fontSize: 28, fontWeight: 700 }}>
            Métricas de Uso
          </h2>
        </div>

        {/* Conteúdo rolável */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px 40px 40px",
            display: "flex",
            flexDirection: "column",
            gap: 32,
          }}
        >
          {loading && (
            <p style={{ color: "rgba(255,255,255,0.4)", margin: 0 }}>
              Carregando dados do servidor...
            </p>
          )}

          {/* ── Taxa de acurácia ── */}
          {admin && (
            <section>
              <p style={secaoTitulo}>Acurácia</p>
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                <div
                  style={{
                    ...card,
                    flex: "1 1 320px",
                    maxWidth: 480,
                    background:
                      "linear-gradient(135deg,#00adb5 0%,#007a80 100%)",
                    border: "none",
                  }}
                >
                  <h3 style={{ ...cardTitulo, color: "rgba(255,255,255,0.8)" }}>
                    Taxa de acurácia
                  </h3>
                  <p style={{ ...cardValor, color: "#fff" }}>
                    {admin.taxa_acuracia === null
                      ? "—"
                      : `${admin.taxa_acuracia}%`}
                  </p>
                  <span style={{ ...cardSub, color: "rgba(255,255,255,0.7)" }}>
                    {admin.feedback_avaliadas === 0
                      ? "Ainda não há respostas avaliadas pelos usuários."
                      : `${admin.feedback_positivos} positivas de ${admin.feedback_avaliadas} avaliadas`}
                  </span>
                </div>
              </div>
            </section>
          )}

          {/* ── Totais e qualidade ── */}
          {chat && (
            <>
              <section>
                <p style={secaoTitulo}>Visão geral</p>
                <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                  <div style={card}>
                    <h3 style={cardTitulo}>Total de Conversas</h3>
                    <p style={{ ...cardValor, color: "#4caf50" }}>
                      {chat.total_conversas}
                    </p>
                  </div>
                  <div style={card}>
                    <h3 style={cardTitulo}>Total de Mensagens</h3>
                    <p style={{ ...cardValor, color: "#4caf50" }}>
                      {chat.total_mensagens}
                    </p>
                  </div>
                  <div style={card}>
                    <h3 style={cardTitulo}>Média de Notas</h3>
                    <p style={{ ...cardValor, color: "#4caf50" }}>
                      {chat.media_notas}
                    </p>
                  </div>
                </div>
              </section>

              <section>
                <p style={secaoTitulo}>Qualidade das respostas</p>
                <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                  <div style={card}>
                    <h3 style={cardTitulo}>✅ Taxa de sucesso</h3>
                    <p
                      style={{
                        ...cardValor,
                        color: corTaxa(chat.taxa_sucesso),
                      }}
                    >
                      {chat.taxa_sucesso ?? 0}%
                    </p>
                    <BarraProgresso
                      valor={chat.taxa_sucesso ?? 0}
                      cor={corTaxa(chat.taxa_sucesso)}
                    />
                    <span style={cardSub}>
                      {chat.respostas_ok ?? 0} de {chat.respostas_total ?? 0}{" "}
                      respostas com sucesso
                    </span>
                  </div>
                  <div style={card}>
                    <h3 style={cardTitulo}>🔁 Taxa de reformulação</h3>
                    <p
                      style={{
                        ...cardValor,
                        color: corTaxa(chat.taxa_reformulacao, {
                          invertida: true,
                        }),
                      }}
                    >
                      {chat.taxa_reformulacao ?? 0}%
                    </p>
                    <BarraProgresso
                      valor={chat.taxa_reformulacao ?? 0}
                      cor={corTaxa(chat.taxa_reformulacao, { invertida: true })}
                    />
                    <span style={cardSub}>
                      {chat.reformulacoes ?? 0} de {chat.perguntas_total ?? 0}{" "}
                      perguntas reformuladas
                    </span>
                  </div>
                </div>
              </section>
            </>
          )}

          {/* ── Constância ── */}
          {constancia && (
            <section>
              <p style={secaoTitulo}>
                Constância dos indicadores · últimos {constancia.dias} dias
              </p>
              <p style={{ ...cardSub, marginTop: -8, marginBottom: 14 }}>
                Mede a estabilidade dos indicadores via coeficiente de variação
                (CV). CV menor = indicador mais constante.
              </p>
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                <CardConstancia
                  titulo="Taxa de sucesso"
                  stats={constancia.estatisticas_sucesso}
                />
                <CardConstancia
                  titulo="Taxa de acurácia"
                  stats={constancia.estatisticas_acuracia}
                />
                <CardSerie
                  titulo="Taxa de sucesso por dia"
                  serie={constancia.serie_sucesso}
                  corTaxa={corTaxa}
                />
              </div>
            </section>
          )}

          {/* ── Tabela por usuário ── */}
          {usuarios && (
            <section>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 14,
                }}
              >
                <p style={{ ...secaoTitulo, margin: 0 }}>
                  Desempenho por usuário
                </p>
                <button
                  onClick={() => exportarCsvUsuarios(usuariosOrdenados)}
                  style={{
                    background: "#00adb5",
                    color: "#fff",
                    border: "none",
                    borderRadius: 20,
                    padding: "8px 18px",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    fontSize: 13,
                    fontWeight: 600,
                  }}
                >
                  ⬇ Exportar relatório (CSV)
                </button>
              </div>
              <div
                style={{
                  backgroundColor: "#222831",
                  borderRadius: 22,
                  overflow: "hidden",
                }}
              >
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: 14,
                  }}
                >
                  <thead>
                    <tr style={{ textAlign: "left" }}>
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
                      <tr
                        key={u.user_id}
                        style={{
                          borderTop: "1px solid rgba(255,255,255,0.06)",
                        }}
                      >
                        <td style={td}>{u.username}</td>
                        <td style={tdNum}>{u.total_conversas}</td>
                        <td style={tdNum}>{u.total_perguntas}</td>
                        <td style={tdNum}>{u.total_respostas}</td>
                        <td style={tdNum}>{u.positivos}</td>
                        <td style={tdNum}>{u.negativos}</td>
                        <td style={tdNum}>{u.regeneradas}</td>
                        <td
                          style={{ ...tdNum, color: corTaxa(u.taxa_acuracia) }}
                        >
                          {u.taxa_acuracia === null
                            ? "—"
                            : `${u.taxa_acuracia}%`}
                        </td>
                        <td
                          style={{ ...tdNum, color: corTaxa(u.taxa_sucesso) }}
                        >
                          {u.taxa_sucesso === null ? "—" : `${u.taxa_sucesso}%`}
                        </td>
                        <td
                          style={{
                            ...td,
                            color: "rgba(255,255,255,0.4)",
                            fontSize: 12,
                          }}
                        >
                          {formatarDataHora(u.ultima_atividade)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* ── Ações administrativas ── */}
          {logs && (
            <section>
              <p style={{ ...secaoTitulo, marginBottom: 14 }}>
                Ações administrativas · últimos {logs.length} registros
              </p>
              <div
                style={{
                  backgroundColor: "#222831",
                  borderRadius: 22,
                  overflow: "hidden",
                }}
              >
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: 14,
                  }}
                >
                  <thead>
                    <tr style={{ textAlign: "left" }}>
                      <th style={th}>Data/Hora</th>
                      <th style={th}>Usuário</th>
                      <th style={th}>Ação</th>
                      <th style={th}>Recurso</th>
                      <th style={th}>Nome</th>
                      <th style={th}>Detalhes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.length === 0 && (
                      <tr>
                        <td
                          colSpan={6}
                          style={{
                            ...td,
                            textAlign: "center",
                            color: "rgba(255,255,255,0.4)",
                            padding: 20,
                          }}
                        >
                          Nenhuma ação registrada ainda.
                        </td>
                      </tr>
                    )}
                    {logs.map((log) => (
                      <tr
                        key={log.id}
                        style={{
                          borderTop: "1px solid rgba(255,255,255,0.06)",
                        }}
                      >
                        <td
                          style={{
                            ...td,
                            fontSize: 12,
                            color: "rgba(255,255,255,0.4)",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {log.timestamp}
                        </td>
                        <td style={{ ...td, fontWeight: 600 }}>{log.user}</td>
                        <td style={td}>
                          <ChipAcao acao={log.action} />
                        </td>
                        <td style={{ ...td, color: "rgba(255,255,255,0.4)" }}>
                          {log.resource_type || "—"}
                        </td>
                        <td style={td}>
                          {log.resource_name?.length > 60
                            ? log.resource_name.slice(0, 57) + "…"
                            : log.resource_name || "—"}
                        </td>
                        <td
                          style={{
                            ...td,
                            color: "rgba(255,255,255,0.4)",
                            fontSize: 12,
                          }}
                        >
                          {log.details || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      </div>

      <style>{`
        div::-webkit-scrollbar {
          width: 6px;
        }
        div::-webkit-scrollbar-track {
          background: transparent;
        }
        div::-webkit-scrollbar-thumb {
          background: #00adb5;
          border-radius: 10px;
        }
        div::-webkit-scrollbar-thumb:hover {
          background: #00c8d2;
        }
      `}</style>
    </div>
  );
}

// ── Sub-componentes ─────────────────────────────────────────────────────────
const ACOES = {
  LOGIN: { label: "Login", cor: "#4a90e2", bg: "#4a90e222" },
  LOGOUT: { label: "Logout", cor: "#a0a0a0", bg: "#a0a0a022" },
  CREATE: { label: "Criação", cor: "#4caf50", bg: "#4caf5022" },
  UPDATE: { label: "Edição", cor: "#f0c87a", bg: "#f0c87a22" },
  DELETE: { label: "Exclusão", cor: "#ff6b6b", bg: "#ff6b6b22" },
  REINDEX: { label: "Reindexação", cor: "#00adb5", bg: "#00adb522" },
};

function ChipAcao({ acao }) {
  const info = ACOES[acao] || { label: acao, cor: "#a0a0a0", bg: "#a0a0a022" };
  return (
    <span
      style={{
        padding: "3px 12px",
        borderRadius: 20,
        fontSize: 12,
        fontWeight: 600,
        background: info.bg,
        color: info.cor,
        display: "inline-block",
      }}
    >
      {info.label}
    </span>
  );
}

function CardConstancia({ titulo, stats }) {
  const cor = corClassificacao(stats?.classificacao);
  const rotulo = rotuloClassificacao(stats?.classificacao);
  return (
    <div style={card}>
      <h3 style={cardTitulo}>{titulo}</h3>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontSize: "2.2rem", fontWeight: 700 }}>
          {stats?.media == null ? "—" : `${stats.media}%`}
        </span>
        <span style={{ fontSize: "0.82rem", color: "rgba(255,255,255,0.4)" }}>
          média
        </span>
      </div>
      <div
        style={{
          padding: "4px 12px",
          borderRadius: 20,
          display: "inline-block",
          alignSelf: "flex-start",
          background: cor + "22",
          color: cor,
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        {rotulo} · CV {stats?.cv == null ? "—" : `${stats.cv}%`}
      </div>
      <span style={cardSub}>
        σ = {stats?.desvio_padrao ?? "—"} · min {stats?.minimo ?? "—"} · max{" "}
        {stats?.maximo ?? "—"} · n={stats?.n ?? 0}
      </span>
    </div>
  );
}

function CardSerie({ titulo, serie, corTaxa }) {
  const max = 100;
  return (
    <div style={{ ...card, flex: "2 1 420px", maxWidth: 700 }}>
      <h3 style={cardTitulo}>{titulo}</h3>
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: 4,
          height: 100,
          marginTop: 8,
        }}
      >
        {serie.map((p, i) => {
          const v = p.valor ?? 0;
          const h = p.valor === null ? 4 : Math.max(4, (v / max) * 100);
          const cor = p.valor === null ? "rgba(255,255,255,0.1)" : corTaxa(v);
          return (
            <div
              key={i}
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              <div
                title={`${p.dia} — ${p.valor === null ? "sem dados" : v + "%"}`}
                style={{
                  width: "100%",
                  height: `${h}%`,
                  background: cor,
                  borderRadius: 3,
                }}
              />
            </div>
          );
        })}
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          color: "rgba(255,255,255,0.4)",
          fontSize: 10,
          marginTop: 6,
        }}
      >
        <span>{serie[0]?.dia.slice(5)}</span>
        <span>{serie[serie.length - 1]?.dia.slice(5)}</span>
      </div>
    </div>
  );
}

// ── Estilos de tabela ───────────────────────────────────────────────────────
const th = {
  padding: "12px 16px",
  fontWeight: 600,
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  color: "rgba(255,255,255,0.5)",
  borderBottom: "1px solid rgba(255,255,255,0.06)",
};
const thNum = { ...th, textAlign: "right" };
const td = { padding: "10px 16px" };
const tdNum = { ...td, textAlign: "right", fontVariantNumeric: "tabular-nums" };
