import "./ConhecimentoArea.css";
import { useState } from "react";
import Documento from "./Documento";

import recarregar from "../assets/images/reload.svg";

export default function ConhecimentoArea() {
  const [modalOpen, setModalOpen] = useState(false);

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
          <h2>0</h2>
        </div>
        <div className="cardDados">
          <h2>Última Atualização</h2>
          <h2>21/02/2026</h2>
        </div>
        <div className="cardDados">
          <h2>Indexados</h2>
          <h2>0</h2>
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
            <button className="btnReindexar">
              <img src={recarregar} alt="Reindexar" />
              Reindexar todos
            </button>
          </div>

          {/*  */}
          <Documento
            titulo="Banco de dados"
            conteudo="teste teste teste"
            categoria="TI"
            dataCriacao="10/01/2026"
            ultimaAtualizacao="22/03/2026 10:00"
            status="pendente"
          />
          <Documento
            titulo="Banco de dados"
            conteudo="teste teste teste"
            categoria="TI"
            dataCriacao="10/01/2026"
            ultimaAtualizacao="22/03/2026 10:00"
            status="indexado"
          />
          {/*  */}
        </div>
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="overlay">
          <div className="modal">
            <h2>Novo Documento</h2>

            <label>
              Título
              <input type="text" placeholder="Digite o título" />
            </label>

            <label>
              Categoria
              <input type="text" placeholder="Digite a categoria" />
            </label>

            <label>
              Conteúdo
              <textarea placeholder="Digite o conteúdo..." />
            </label>

            <label>
              Origem
              <input type="text" placeholder="Digite a origem" />
            </label>

            <div className="modalActions">
              <button className="btnVoltar" onClick={() => setModalOpen(false)}>
                Voltar
              </button>

              <button className="btnSalvar">Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
