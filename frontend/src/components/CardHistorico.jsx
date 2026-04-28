import "./CardHistorico.css";

export default function CardHistorico({
  tituloHistorico,
  conteudoHistorico,
  data,
  hora,
  tituloDocumento,
}) {
  return (
    <div className="card">
      <div className="superior">
        <div className="conteudo">
          <h2>{tituloHistorico}</h2>
          <p>{conteudoHistorico}</p>
        </div>

        <div className="informacao">
          <p>{data}</p>
          <p>{hora}</p>
        </div>
      </div>

      <div className="inferior">
        <h2>{tituloDocumento}</h2>
        <h2>Ver Detalhes ➔</h2>
      </div>
    </div>
  );
}
