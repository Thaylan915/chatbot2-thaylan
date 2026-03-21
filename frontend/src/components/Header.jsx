import "../pages/Styles.css";
import { useNavigate } from "react-router-dom";

export default function Header() {
  const navigate = useNavigate();

  function irTelaAdm() {
    navigate("/admin");
  }

  return (
    <div className="header">
      <div className="titulo">
        <h1>ChatBOT</h1>
        <p>Transformando perguntas em soluções</p>
      </div>

      <div className="entrarAdm">
        <button className="btnAdm" onClick={irTelaAdm}>
          Entrar como administrador
        </button>
      </div>
    </div>
  );
}
