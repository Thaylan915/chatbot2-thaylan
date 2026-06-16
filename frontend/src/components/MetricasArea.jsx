import "./MetricasArea.css";
import { useState, useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import api from "../services/api";

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
    <div className="barraProgresso">
      <div
        className="barraProgressoFill"
        style={{ width: `${v}%`, backgroundColor: cor }}
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
  a.remove();
  URL.revokeObjectURL(url);
}

// ── Componente principal ────────────────────────────────────────────────────
export default function MetricasArea() {
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
    <div className="metricasArea">
      <div className="metricasHeader">
        <h2>Métricas de Uso</h2>
      </div>

      <div className="metricasConteudo">
        {loading && (
          <p className="metricasLoading">Carregando dados do servidor...</p>
        )}

        {/* ── Taxa de acurácia ── */}
        {admin && (
          <section>
            <p className="secaoTitulo">Acurácia</p>
            <div className="cardRow">
              <div className="metricasCard cardDestaque">
                <h3 className="cardTitulo claro">Taxa de acurácia</h3>
                <p className="cardValor" style={{ color: "#fff" }}>
                  {admin.taxa_acuracia === null
                    ? "—"
                    : `${admin.taxa_acuracia}%`}
                </p>
                <span className="cardSub claro">
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
              <p className="secaoTitulo">Visão geral</p>
              <div className="cardRow">
                <div className="metricasCard">
                  <h3 className="cardTitulo">Total de Conversas</h3>
                  <p className="cardValor" style={{ color: "#4caf50" }}>
                    {chat.total_conversas}
                  </p>
                </div>
                <div className="metricasCard">
                  <h3 className="cardTitulo">Total de Mensagens</h3>
                  <p className="cardValor" style={{ color: "#4caf50" }}>
                    {chat.total_mensagens}
                  </p>
                </div>
                <div className="metricasCard">
                  <h3 className="cardTitulo">Média de Notas</h3>
                  <p className="cardValor" style={{ color: "#4caf50" }}>
                    {chat.media_notas}
                  </p>
                </div>
              </div>
            </section>

            <section>
              <p className="secaoTitulo">Qualidade das respostas</p>
              <div className="cardRow">
                <div className="metricasCard">
                  <h3 className="cardTitulo">✅ Taxa de sucesso</h3>
                  <p
                    className="cardValor"
                    style={{ color: corTaxa(chat.taxa_sucesso) }}
                  >
                    {chat.taxa_sucesso ?? 0}%
                  </p>
                  <BarraProgresso
                    valor={chat.taxa_sucesso ?? 0}
                    cor={corTaxa(chat.taxa_sucesso)}
                  />
                  <span className="cardSub">
                    {chat.respostas_ok ?? 0} de {chat.respostas_total ?? 0}{" "}
                    respostas com sucesso
                  </span>
                </div>
                <div className="metricasCard">
                  <h3 className="cardTitulo">🔁 Taxa de reformulação</h3>
                  <p
                    className="cardValor"
                    style={{
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
                  <span className="cardSub">
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
            <p className="secaoTitulo">
              Constância dos indicadores · últimos {constancia.dias} dias
            </p>
            <p className="secaoSub">
              Mede a estabilidade dos indicadores via coeficiente de variação
              (CV). CV menor = indicador mais constante.
            </p>
            <div className="cardRow">
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
                corBarra={corTaxa}
              />
            </div>
          </section>
        )}

        {/* ── Tabela por usuário ── */}
        {usuarios && (
          <section>
            <div className="secaoHeader">
              <p className="secaoTitulo semMargem">Desempenho por usuário</p>
              <button
                className="btnExportarCsv"
                onClick={() => exportarCsvUsuarios(usuariosOrdenados)}
              >
                ⬇ Exportar relatório (CSV)
              </button>
            </div>
            <div className="metricasTabelaWrap">
              <table className="metricasTabela">
                <thead>
                  <tr>
                    <th>Usuário</th>
                    <th className="num">Conversas</th>
                    <th className="num">Perguntas</th>
                    <th className="num">Respostas</th>
                    <th className="num">👍</th>
                    <th className="num">👎</th>
                    <th className="num">🔄</th>
                    <th className="num">Acurácia</th>
                    <th className="num">Sucesso</th>
                    <th>Última atividade</th>
                  </tr>
                </thead>
                <tbody>
                  {usuariosOrdenados.map((u) => (
                    <tr key={u.user_id}>
                      <td>{u.username}</td>
                      <td className="num">{u.total_conversas}</td>
                      <td className="num">{u.total_perguntas}</td>
                      <td className="num">{u.total_respostas}</td>
                      <td className="num">{u.positivos}</td>
                      <td className="num">{u.negativos}</td>
                      <td className="num">{u.regeneradas}</td>
                      <td
                        className="num"
                        style={{ color: corTaxa(u.taxa_acuracia) }}
                      >
                        {u.taxa_acuracia === null ? "—" : `${u.taxa_acuracia}%`}
                      </td>
                      <td
                        className="num"
                        style={{ color: corTaxa(u.taxa_sucesso) }}
                      >
                        {u.taxa_sucesso === null ? "—" : `${u.taxa_sucesso}%`}
                      </td>
                      <td className="tdMuted">
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
            <p className="secaoTitulo">
              Ações administrativas · últimos {logs.length} registros
            </p>
            <div className="metricasTabelaWrap">
              <table className="metricasTabela">
                <thead>
                  <tr>
                    <th>Data/Hora</th>
                    <th>Usuário</th>
                    <th>Ação</th>
                    <th>Recurso</th>
                    <th>Nome</th>
                    <th>Detalhes</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan={6} className="tdVazio">
                        Nenhuma ação registrada ainda.
                      </td>
                    </tr>
                  )}
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td className="tdMuted tdNowrap">{log.timestamp}</td>
                      <td className="tdForte">{log.user}</td>
                      <td>
                        <ChipAcao acao={log.action} />
                      </td>
                      <td className="tdMuted">{log.resource_type || "—"}</td>
                      <td>
                        {log.resource_name?.length > 60
                          ? log.resource_name.slice(0, 57) + "…"
                          : log.resource_name || "—"}
                      </td>
                      <td className="tdMuted">{log.details || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
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
    <span className="chipAcao" style={{ background: info.bg, color: info.cor }}>
      {info.label}
    </span>
  );
}

function CardConstancia({ titulo, stats }) {
  const cor = corClassificacao(stats?.classificacao);
  const rotulo = rotuloClassificacao(stats?.classificacao);
  return (
    <div className="metricasCard">
      <h3 className="cardTitulo">{titulo}</h3>
      <div className="cardConstanciaValor">
        <span className="cardConstanciaMedia">
          {stats?.media == null ? "—" : `${stats.media}%`}
        </span>
        <span className="cardConstanciaMediaLabel">média</span>
      </div>
      <div
        className="cardConstanciaBadge"
        style={{ background: cor + "22", color: cor }}
      >
        {rotulo} · CV {stats?.cv == null ? "—" : `${stats.cv}%`}
      </div>
      <span className="cardSub">
        σ = {stats?.desvio_padrao ?? "—"} · min {stats?.minimo ?? "—"} · max{" "}
        {stats?.maximo ?? "—"} · n={stats?.n ?? 0}
      </span>
    </div>
  );
}

function CardSerie({ titulo, serie, corBarra }) {
  const max = 100;
  return (
    <div className="metricasCard cardSerie">
      <h3 className="cardTitulo">{titulo}</h3>
      <div className="cardSerieGrafico">
        {serie.map((p) => {
          const v = p.valor ?? 0;
          const h = p.valor === null ? 4 : Math.max(4, (v / max) * 100);
          const cor = p.valor === null ? "rgba(255,255,255,0.1)" : corBarra(v);
          return (
            <div key={p.dia} className="cardSerieColuna">
              <div
                className="cardSerieBarra"
                title={`${p.dia} — ${p.valor === null ? "sem dados" : v + "%"}`}
                style={{ height: `${h}%`, background: cor }}
              />
            </div>
          );
        })}
      </div>
      <div className="cardSerieEixo">
        <span>{serie[0]?.dia.slice(5)}</span>
        <span>{serie[serie.length - 1]?.dia.slice(5)}</span>
      </div>
    </div>
  );
}

BarraProgresso.propTypes = {
  valor: PropTypes.number,
  cor: PropTypes.string,
};

ChipAcao.propTypes = {
  acao: PropTypes.string,
};

CardConstancia.propTypes = {
  titulo: PropTypes.string,
  stats: PropTypes.object,
};

CardSerie.propTypes = {
  titulo: PropTypes.string,
  serie: PropTypes.array,
  corBarra: PropTypes.func,
};
