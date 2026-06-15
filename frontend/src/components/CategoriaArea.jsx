import "./CategoriaArea.css";
import { useState, useEffect, useCallback } from "react";
import DocumentoCategoria from "./DocumentoCategoria";
import api from "../services/api";

const CATEGORIAS_META = {
  portaria: { label: "Portaria", cor: "#00adb5", sigla: "P" },
  resolucao: { label: "Resolução", cor: "#e0a020", sigla: "R" },
  rod: { label: "ROD", cor: "#7c6af7", sigla: "D" },
};

function formatarData(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("pt-BR");
  } catch {
    return "—";
  }
}

export default function CategoriaArea() {
  const [categorias, setCategorias] = useState([]);
  const [carregandoCats, setCarregandoCats] = useState(true);
  const [categoriaSelecionada, setCategoriaSelecionada] = useState(null); // tipo string
  const [documentos, setDocumentos] = useState([]);
  const [carregandoDocs, setCarregandoDocs] = useState(false);
  const [filtroInicio, setFiltroInicio] = useState("");
  const [filtroFim, setFiltroFim] = useState("");
  const [totalCat, setTotalCat] = useState(0);

  // Carrega cards de categorias
  useEffect(() => {
    api
      .get("/api/categories/")
      .then((res) => setCategorias(res.data?.categorias || []))
      .catch(() => setCategorias([]))
      .finally(() => setCarregandoCats(false));
  }, []);

  // Carrega documentos da categoria selecionada
  const carregarDocumentos = useCallback(
    async (tipo, inicio = "", fim = "") => {
      if (!tipo) return;
      setCarregandoDocs(true);
      try {
        const params = {};
        if (inicio) params.data_inicio = inicio;
        if (fim) params.data_fim = fim;
        const res = await api.get(`/api/categories/${tipo}/`, { params });
        setDocumentos(res.data?.documentos || []);
        setTotalCat(res.data?.total || 0);
      } catch {
        setDocumentos([]);
      } finally {
        setCarregandoDocs(false);
      }
    },
    [],
  );

  function handleSelecionarCategoria(tipo) {
    setCategoriaSelecionada(tipo);
    setFiltroInicio("");
    setFiltroFim("");
    carregarDocumentos(tipo);
  }

  function handleFiltrar() {
    carregarDocumentos(categoriaSelecionada, filtroInicio, filtroFim);
  }

  function handleVoltar() {
    setCategoriaSelecionada(null);
    setDocumentos([]);
    setFiltroInicio("");
    setFiltroFim("");
  }

  const meta = categoriaSelecionada
    ? CATEGORIAS_META[categoriaSelecionada]
    : null;

  // ── Tela de listagem de categorias ───────────────────────────────────────
  if (!categoriaSelecionada) {
    return (
      <div className="catArea">
        <div className="catTopo">
          <h2>Categorias</h2>
          <p className="catSubtitulo">
            Selecione uma categoria para visualizar seus documentos
          </p>
        </div>

        <div className="catGrid">
          {carregandoCats && (
            <p style={{ padding: 24, opacity: 0.6 }}>Carregando...</p>
          )}
          {!carregandoCats &&
            categorias.map((cat) => {
              const m = CATEGORIAS_META[cat.tipo] || {
                label: cat.label,
                cor: "#aaa",
                sigla: cat.tipo[0].toUpperCase(),
              };
              return (
                <button
                  key={cat.tipo}
                  className="catCard"
                  style={{ "--cat-cor": m.cor }}
                  onClick={() => handleSelecionarCategoria(cat.tipo)}
                >
                  <div className="catCardSigla">{m.sigla}</div>
                  <div className="catCardInfo">
                    <span className="catCardLabel">{m.label}</span>
                    <span className="catCardTotal">
                      {cat.total_documentos}
                      <small>
                        {" "}
                        documento{cat.total_documentos === 1 ? "" : "s"}
                      </small>
                    </span>
                  </div>
                  <div className="catCardArrow">→</div>
                </button>
              );
            })}
        </div>
      </div>
    );
  }

  // ── Tela de documentos da categoria ──────────────────────────────────────
  return (
    <div className="catArea">
      <div className="catTopo">
        <div className="catTopoLeft">
          <button className="catBtnVoltar" onClick={handleVoltar}>
            ← Categorias
          </button>
          <div className="catBadge" style={{ backgroundColor: meta.cor }}>
            {meta.sigla}
          </div>
          <div>
            <h2 style={{ margin: 0 }}>{meta.label}</h2>
            <span className="catSubtitulo">
              {totalCat} documento{totalCat === 1 ? "" : "s"}
            </span>
          </div>
        </div>
      </div>

      {/* Filtro de período */}
      <div className="catFiltros">
        <span className="catFiltroLabel">Filtrar por período:</span>
        <input
          type="date"
          value={filtroInicio}
          onChange={(e) => setFiltroInicio(e.target.value)}
          className="catFiltroData"
        />
        <span style={{ color: "#aaa" }}>até</span>
        <input
          type="date"
          value={filtroFim}
          onChange={(e) => setFiltroFim(e.target.value)}
          className="catFiltroData"
        />
        <button className="catBtnFiltrar" onClick={handleFiltrar}>
          Filtrar
        </button>
        {(filtroInicio || filtroFim) && (
          <button
            className="catBtnLimpar"
            onClick={() => {
              setFiltroInicio("");
              setFiltroFim("");
              carregarDocumentos(categoriaSelecionada);
            }}
          >
            ✕ Limpar
          </button>
        )}
      </div>

      {/* Lista de documentos */}
      <div className="catListaWrap">
        {carregandoDocs && (
          <p style={{ padding: 24, opacity: 0.6 }}>Carregando documentos...</p>
        )}
        {!carregandoDocs && documentos.length === 0 && (
          <p style={{ padding: 24, opacity: 0.6 }}>
            Nenhum documento encontrado nessa categoria.
          </p>
        )}
        {!carregandoDocs &&
          documentos.map((doc) => (
            <DocumentoCategoria
              key={doc.id}
              id={doc.id}
              nome={doc.nome}
              tipo={doc.tipo}
              indexado_em={formatarData(doc.indexado_em)}
              versao_ativa={doc.versao_ativa}
              total_versoes={doc.total_versoes}
              corCategoria={meta.cor}
            />
          ))}
      </div>
    </div>
  );
}
