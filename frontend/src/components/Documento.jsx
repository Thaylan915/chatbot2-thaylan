import "./Documento.css";
import { useState } from "react";
import doc from "../assets/images/documento.svg";
import verificado from "../assets/images/verificado.svg";
import recarregar from "../assets/images/reload.svg";
import lixeira from "../assets/images/lixo.svg";
import pendente from "../assets/images/pendente.svg";
import historico from "../assets/images/historico.svg";
import api from "../services/api";

const TIPOS = [
  { valor: "portaria", label: "Portaria" },
  { valor: "resolucao", label: "Resolução" },
  { valor: "rod", label: "ROD" },
];

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

export default function Documento({
  id,
  titulo,
  conteudo,
  categoria,
  dataCriacao,
  ultimaAtualizacao,
  status,
  tipoAtual,
  onDelete,
  onEdit,
  onVersoesChange,
}) {
  const [confirmando, setConfirmando] = useState(false);
  const [editando, setEditando]       = useState(false);
  const [verVersoes, setVerVersoes]   = useState(false);
  const [versoes, setVersoes]         = useState([]);
  const [loadingVersoes, setLoadingVersoes] = useState(false);

  const [nomeEdit, setNomeEdit]       = useState(titulo || "");
  const [tipoEdit, setTipoEdit]       = useState(tipoAtual || "portaria");
  const [arquivoEdit, setArquivoEdit] = useState(null);
  const [salvando, setSalvando]       = useState(false);

  const iconeStatus = status === "pendente" ? pendente : verificado;

  function abrirEdicao() {
    setNomeEdit(titulo || "");
    setTipoEdit(tipoAtual || "portaria");
    setArquivoEdit(null);
    setEditando(true);
  }

  async function abrirVersoes() {
    setVerVersoes(true);
    setLoadingVersoes(true);
    try {
      const res = await api.get(`/api/documents/${id}/versoes/`);
      setVersoes(res.data?.versoes || []);
    } catch (e) {
      alert(
        e.response?.data?.error ||
          e.response?.statusText ||
          "Erro ao carregar versões"
      );
    } finally {
      setLoadingVersoes(false);
    }
  }

  async function ativarVersao(numero) {
    try {
      await api.post(`/api/documents/${id}/versoes/${numero}/ativar/`);
      const res = await api.get(`/api/documents/${id}/versoes/`);
      setVersoes(res.data?.versoes || []);
      onVersoesChange?.();
    } catch (e) {
      alert(
        e.response?.data?.error ||
          e.response?.statusText ||
          "Erro ao ativar versão"
      );
    }
  }

  async function handleSalvar() {
    if (!nomeEdit.trim()) {
      alert("O nome não pode ficar vazio.");
      return;
    }
    setSalvando(true);
    try {
      await onEdit?.({
        nome: nomeEdit.trim(),
        tipo: tipoEdit,
        arquivo: arquivoEdit,
      });
      setEditando(false);
    } finally {
      setSalvando(false);
    }
  }

  function handleConfirmar() {
    setConfirmando(false);
    if (onDelete) onDelete();
  }

  return (
    <>
      <div className="documento">
        <div className="docIcon">
          <img src={doc} alt="Documento" />
        </div>

        <div className="informacoes">
          <h4>
            {titulo}
            {conteudo ? `: ${conteudo}` : ""}
          </h4>

          <div className="inferior">
            <span>
              {categoria} • {dataCriacao}
            </span>
            <span>Atualizado: {ultimaAtualizacao}</span>
          </div>
        </div>

        <div className="interativo">
          <div
            className={`estado
            ${status === "indexado" ? "indexado" : ""}
            ${status === "pendente" ? "pendente" : ""}`}
          >
            <span>{status === "pendente" ? "Pendente" : "Indexado"}</span>
            <img src={iconeStatus} alt="Status" />
          </div>

          <div className="acao versoes" onClick={abrirVersoes} title="Versões">
            <img src={historico} alt="Versões" />
          </div>

          <div className="acao editar" onClick={abrirEdicao} title="Editar">
            <img src={recarregar} alt="Editar" />
          </div>

          <div className="acao excluir" onClick={() => setConfirmando(true)} title="Excluir">
            <img src={lixeira} alt="Excluir" />
          </div>
        </div>
      </div>

      {/* Modal de edição */}
      {editando && (
        <div className="overlay">
          <div className="modal">
            <h2>Editar Documento</h2>

            <label>
              Nome
              <input
                type="text"
                value={nomeEdit}
                onChange={(e) => setNomeEdit(e.target.value)}
              />
            </label>

            <label>
              Tipo
              <select
                value={tipoEdit}
                onChange={(e) => setTipoEdit(e.target.value)}
              >
                {TIPOS.map((t) => (
                  <option key={t.valor} value={t.valor}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Substituir arquivo PDF (opcional)
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setArquivoEdit(e.target.files?.[0] || null)}
              />
            </label>
            <p style={{ fontSize: 12, opacity: 0.7, margin: "4px 0 0 0" }}>
              Enviar um novo PDF cria uma nova versão automaticamente.
            </p>

            <div className="modalActions">
              <button
                className="btnVoltar"
                onClick={() => setEditando(false)}
                disabled={salvando}
              >
                Cancelar
              </button>
              <button
                className="btnSalvar"
                onClick={handleSalvar}
                disabled={salvando}
              >
                {salvando ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de versões */}
      {verVersoes && (
        <div className="overlay">
          <div className="modal" style={{ maxWidth: 640 }}>
            <h2>Versões — {titulo}</h2>

            {loadingVersoes && <p>Carregando...</p>}

            {!loadingVersoes && versoes.length === 0 && (
              <p>Nenhuma versão registrada.</p>
            )}

            {!loadingVersoes && versoes.length > 0 && (
              <div style={{ maxHeight: 400, overflowY: "auto" }}>
                {versoes.map((v) => (
                  <div
                    key={v.numero}
                    style={{
                      padding: "12px 14px",
                      borderRadius: 8,
                      marginBottom: 8,
                      background: v.ativa ? "rgba(0, 173, 181, 0.15)" : "#393e46",
                      border: v.ativa ? "1px solid #00adb5" : "1px solid transparent",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600 }}>
                          v{v.numero}
                          {v.ativa && (
                            <span style={{ color: "#00adb5", marginLeft: 8, fontSize: 12 }}>
                              ● ATIVA
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>
                          {v.nome}
                        </div>
                        <div style={{ fontSize: 11, opacity: 0.6, marginTop: 4 }}>
                          {fmtDataHora(v.criada_em)} · {v.qtd_chunks} chunks · {v.tipo}
                        </div>
                      </div>
                      {!v.ativa && (
                        <button
                          className="btnSalvar"
                          style={{ padding: "6px 12px", fontSize: 13 }}
                          onClick={() => ativarVersao(v.numero)}
                        >
                          Ativar
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="modalActions">
              <button className="btnVoltar" onClick={() => setVerVersoes(false)}>
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de confirmação de exclusão */}
      {confirmando && (
        <div className="overlay">
          <div className="modal modalConfirmacao">
            <h2>Confirmar exclusão</h2>
            <p>
              Tem certeza que deseja excluir o documento{" "}
              <strong>{titulo}</strong>? Esta ação não pode ser desfeita.
            </p>
            <div className="modalActions">
              <button className="btnVoltar" onClick={() => setConfirmando(false)}>
                Cancelar
              </button>
              <button className="btnExcluirConfirmar" onClick={handleConfirmar}>
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
