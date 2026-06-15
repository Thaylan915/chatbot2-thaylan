import "./DocumentoCategoria.css";
import { useState } from "react";
import PropTypes from "prop-types";
import api from "../services/api";

export default function DocumentoCategoria({
  id,
  nome,
  tipo,
  indexado_em,
  versao_ativa,
  total_versoes,
  corCategoria,
}) {
  const [modalMeta, setModalMeta] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [loadingMeta, setLoadingMeta] = useState(false);

  const [modalAcao, setModalAcao] = useState(false);
  const [acao, setAcao] = useState("REINDEX");
  const [detalhes, setDetalhes] = useState("");
  const [salvandoAcao, setSalvandoAcao] = useState(false);
  const [acaoFeita, setAcaoFeita] = useState(null);

  // ── Abre modal de metadados ───────────────────────────────────────────────
  async function abrirMetadata() {
    setModalMeta(true);
    setLoadingMeta(true);
    setMetadata(null);
    try {
      const res = await api.get(`/api/documents/${id}/metadata/`);
      setMetadata(res.data);
    } catch (e) {
      alert(e.response?.data?.error || "Erro ao carregar metadados.");
      setModalMeta(false);
    } finally {
      setLoadingMeta(false);
    }
  }

  // ── Registra ação administrativa ─────────────────────────────────────────
  async function handleRegistrarAcao() {
    setSalvandoAcao(true);
    try {
      await api.post(`/api/documents/${id}/admin-action/`, {
        action: acao,
        details: detalhes.trim(),
      });
      setAcaoFeita(acao);
      setDetalhes("");
      setTimeout(() => {
        setModalAcao(false);
        setAcaoFeita(null);
      }, 1800);
    } catch (e) {
      alert(e.response?.data?.error || "Erro ao registrar ação.");
    } finally {
      setSalvandoAcao(false);
    }
  }

  function fmtDataHora(iso) {
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

  return (
    <>
      <div className="docCat" style={{ "--cat-cor": corCategoria }}>
        <div className="docCatBar" />

        <div className="docCatInfo">
          <span className="docCatNome">{nome}</span>
          <span className="docCatMeta">
            {tipo.toUpperCase()} · Indexado em {indexado_em}
            {versao_ativa != null && (
              <>
                {" "}
                · v{versao_ativa} ativa
                {total_versoes > 1 ? ` (${total_versoes} versões)` : ""}
              </>
            )}
          </span>
        </div>

        <div className="docCatAcoes">
          <button
            className="docCatBtn docCatBtnMeta"
            onClick={abrirMetadata}
            title="Ver metadados"
          >
            Metadados
          </button>
          <button
            className="docCatBtn docCatBtnAdmin"
            onClick={() => setModalAcao(true)}
            title="Registrar ação administrativa"
          >
            Ação Admin
          </button>
        </div>
      </div>

      {/* ── Modal Metadados ── */}
      {modalMeta && (
        <div className="catOverlay">
          <div className="catModal">
            <h3 className="catModalTitulo">
              <span
                className="catModalTituloIco"
                style={{ background: corCategoria }}
              >
                M
              </span>
              Metadados
            </h3>

            {loadingMeta && <p style={{ opacity: 0.6 }}>Carregando...</p>}

            {metadata && (
              <div className="metaGrid">
                <MetaRow label="ID" value={metadata.id} />
                <MetaRow label="Nome" value={metadata.nome} />
                <MetaRow label="Tipo" value={metadata.tipo_display} />
                <MetaRow
                  label="Arquivo"
                  value={metadata.caminho_arquivo}
                  mono
                />
                <MetaRow
                  label="Indexado em"
                  value={fmtDataHora(metadata.indexado_em)}
                />
                <MetaRow
                  label="Atualizado em"
                  value={fmtDataHora(metadata.atualizado_em)}
                />

                <div className="metaDivider">Versões</div>
                <MetaRow
                  label="Total de versões"
                  value={metadata.versoes.total}
                />
                <MetaRow
                  label="Versão ativa"
                  value={metadata.versoes.versao_ativa ?? "—"}
                />
                <MetaRow
                  label="Arquivo ativo"
                  value={metadata.versoes.caminho_versao_ativa ?? "—"}
                  mono
                />

                <div className="metaDivider">Chunks</div>
                <MetaRow
                  label="Total de chunks"
                  value={metadata.chunks.total}
                />
                <MetaRow
                  label="Na versão ativa"
                  value={metadata.chunks.na_versao_ativa}
                />
              </div>
            )}

            <div className="catModalActions">
              <button
                className="catBtnFechar"
                onClick={() => setModalMeta(false)}
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal Ação Admin ── */}
      {modalAcao && (
        <div className="catOverlay">
          <div className="catModal">
            <h3 className="catModalTitulo">
              <span
                className="catModalTituloIco"
                style={{ background: "#7c6af7" }}
              >
                A
              </span>
              Ação Administrativa
            </h3>
            <p className="catModalDoc">
              Documento: <strong>{nome}</strong>
            </p>

            {acaoFeita ? (
              <div className="acaoSucesso">
                ✓ Ação <strong>{acaoFeita}</strong> registrada com sucesso!
              </div>
            ) : (
              <>
                <label className="catLabel">
                  Tipo de ação
                  <select
                    className="catSelect"
                    value={acao}
                    onChange={(e) => setAcao(e.target.value)}
                  >
                    <option value="CREATE">CREATE</option>
                    <option value="UPDATE">UPDATE</option>
                    <option value="DELETE">DELETE</option>
                    <option value="REINDEX">REINDEX</option>
                  </select>
                </label>

                <label className="catLabel">
                  Detalhes (opcional)
                  <textarea
                    className="catTextarea"
                    rows={3}
                    placeholder="Descreva o motivo ou contexto da ação..."
                    value={detalhes}
                    onChange={(e) => setDetalhes(e.target.value)}
                  />
                </label>

                <div className="catModalActions">
                  <button
                    className="catBtnFechar"
                    onClick={() => setModalAcao(false)}
                    disabled={salvandoAcao}
                  >
                    Cancelar
                  </button>
                  <button
                    className="catBtnRegistrar"
                    onClick={handleRegistrarAcao}
                    disabled={salvandoAcao}
                  >
                    {salvandoAcao ? "Registrando..." : "Registrar"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function MetaRow({ label, value, mono }) {
  return (
    <div className="metaRow">
      <span className="metaLabel">{label}</span>
      <span className={`metaValue${mono ? " metaMono" : ""}`}>
        {String(value)}
      </span>
    </div>
  );
}

DocumentoCategoria.propTypes = {
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  nome: PropTypes.string,
  tipo: PropTypes.string,
  indexado_em: PropTypes.string,
  versao_ativa: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  total_versoes: PropTypes.number,
  corCategoria: PropTypes.string,
};

MetaRow.propTypes = {
  label: PropTypes.string,
  value: PropTypes.any,
  mono: PropTypes.bool,
};
