import "./Documento.css";
import { useState } from "react";
import doc from "../assets/images/documento.svg";
import verificado from "../assets/images/verificado.svg";
import recarregar from "../assets/images/reload.svg";
import lixeira from "../assets/images/lixo.svg";
import pendente from "../assets/images/pendente.svg";

export default function Documento({
  titulo,
  conteudo,
  categoria,
  dataCriacao,
  ultimaAtualizacao,
  status,
  onDelete,
}) {
  const [confirmando, setConfirmando] = useState(false);
  const iconeStatus = status === "pendente" ? pendente : verificado;

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
            {titulo}: {conteudo}
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

          <div className="acao reindexar">
            <img src={recarregar} alt="Reindexar" />
          </div>

          <div className="acao excluir" onClick={() => setConfirmando(true)}>
            <img src={lixeira} alt="Excluir" />
          </div>
        </div>
      </div>

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
