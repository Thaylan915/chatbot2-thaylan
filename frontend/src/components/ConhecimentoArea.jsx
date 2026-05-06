import "./ConhecimentoArea.css";
import { useState, useEffect, useCallback } from "react";
import Documento from "./Documento";
import api from "../services/api";

import recarregar from "../assets/images/reload.svg";

const TIPO_LABEL = {
  portaria: "Portaria",
  resolucao: "Resolução",
  rod: "ROD",
};

function formatarData(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("pt-BR");
  } catch {
    return "—";
  }
}

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

export default function ConhecimentoArea() {
  const [modalOpen, setModalOpen] = useState(false);
  const [documentos, setDocumentos] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);

  // Form state
  const [novoNome, setNovoNome] = useState("");
  const [novoTipo, setNovoTipo] = useState("portaria");
  const [novoArquivo, setNovoArquivo] = useState(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const res = await api.get("/api/documents/");
      setDocumentos(res.data?.documentos || []);
    } catch (e) {
      setErro(
        e.response?.data?.error ||
          e.response?.statusText ||
          "Erro ao carregar documentos"
      );
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  async function handleSalvar() {
    if (!novoNome.trim() || !novoArquivo) {
      alert("Informe o nome e selecione um PDF.");
      return;
    }
    setSalvando(true);
    try {
      const fd = new FormData();
      fd.append("nome", novoNome.trim());
      fd.append("tipo", novoTipo);
      fd.append("arquivo", novoArquivo);
      await api.post("/api/documents/", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setModalOpen(false);
      setNovoNome("");
      setNovoTipo("portaria");
      setNovoArquivo(null);
      carregar();
    } catch (e) {
      alert(
        e.response?.data?.error ||
          e.response?.statusText ||
          "Erro ao salvar documento"
      );
    } finally {
      setSalvando(false);
    }
  }

  async function handleEditar(id, { nome, tipo, arquivo }) {
    try {
      const fd = new FormData();
      if (nome) fd.append("nome", nome);
      if (tipo) fd.append("tipo", tipo);
      if (arquivo) fd.append("arquivo", arquivo);
      await api.patch(`/api/documents/${id}/`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      carregar();
    } catch (e) {
      alert(
        e.response?.data?.error ||
          e.response?.statusText ||
          "Erro ao editar documento"
      );
      throw e;
    }
  }

  async function handleExcluir(id) {
    try {
      // Passo 1: solicita exclusão e recebe token
      const resSolicitar = await api.delete(`/api/documents/${id}/`);
      const token = resSolicitar.data?.token;
      if (!token) {
        throw new Error("Token de confirmação não recebido.");
      }
      // Passo 2: confirma exclusão com o token
      await api.post(`/api/documents/${id}/confirm/`, { token });
      carregar();
    } catch (e) {
      alert(
        e.response?.data?.error ||
          e.response?.statusText ||
          e.message ||
          "Erro ao excluir documento"
      );
    }
  }

  const total = documentos.length;
  const ultima = documentos.reduce((max, d) => {
    if (!d.indexado_em) return max;
    return !max || new Date(d.indexado_em) > new Date(max) ? d.indexado_em : max;
  }, null);

  return (
    <div className="conhecArea">
      <div className="topo">
        <h2>Base de Conhecimento</h2>
        <button className="btnAdd" onClick={() => setModalOpen(true)}>
          + Adicionar documento
        </button>
      </div>

      <div className="dadosDoc">
        <div className="cardDados">
          <h2>Total de Documentos</h2>
          <h2>{total}</h2>
        </div>
        <div className="cardDados">
          <h2>Última Atualização</h2>
          <h2>{formatarData(ultima)}</h2>
        </div>
        <div className="cardDados">
          <h2>Indexados</h2>
          <h2>{total}</h2>
        </div>
        <div className="cardDados">
          <h2>Pendentes</h2>
          <h2>0</h2>
        </div>
      </div>

      <div className="areaDocumentos">
        <div className="listaDocumentos">
          <div className="headerDoc">
            <h2>Documentos</h2>
            <button className="btnReindexar" onClick={carregar}>
              <img src={recarregar} alt="Reindexar" />
              Recarregar
            </button>
          </div>

          <div className="listaScroll">
            {carregando && <p style={{ padding: 16 }}>Carregando...</p>}
            {erro && (
              <p style={{ padding: 16, color: "#c33" }}>Erro: {erro}</p>
            )}
            {!carregando && !erro && documentos.length === 0 && (
              <p style={{ padding: 16 }}>Nenhum documento cadastrado.</p>
            )}
            {documentos.map((d) => (
              <Documento
                key={d.id}
                id={d.id}
                titulo={d.nome}
                conteudo=""
                categoria={TIPO_LABEL[d.tipo] || d.tipo}
                dataCriacao={formatarData(d.indexado_em)}
                ultimaAtualizacao={formatarDataHora(d.indexado_em)}
                status="indexado"
                tipoAtual={d.tipo}
                onDelete={() => handleExcluir(d.id)}
                onEdit={(payload) => handleEditar(d.id, payload)}
                onVersoesChange={carregar}
              />
            ))}
          </div>
        </div>
      </div>

      {/* MODAL */}
      {modalOpen && (
        <div className="overlay">
          <div className="modal">
            <h2>Novo Documento</h2>

            <label>
              Nome
              <input
                type="text"
                placeholder="Digite o nome"
                value={novoNome}
                onChange={(e) => setNovoNome(e.target.value)}
              />
            </label>

            <label>
              Tipo
              <select
                value={novoTipo}
                onChange={(e) => setNovoTipo(e.target.value)}
              >
                <option value="portaria">Portaria</option>
                <option value="resolucao">Resolução</option>
                <option value="rod">ROD</option>
              </select>
            </label>

            <label>
              Arquivo PDF
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setNovoArquivo(e.target.files?.[0] || null)}
              />
            </label>

            <div className="modalActions">
              <button
                className="btnVoltar"
                onClick={() => setModalOpen(false)}
                disabled={salvando}
              >
                Voltar
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
    </div>
  );
}
