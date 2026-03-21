import "./ChatArea.css";
import enviarIcon from "../assets/images/enviar.svg";

export default function ChatArea() {
  return (
    <div className="chatArea">
      <div className="mensagens">
        <div className="placeholder">
          <h2>Como posso ajudar?</h2>
        </div>
      </div>
      <div className="partedebaixo">
        <div className="mensagemArea">
          <input type="text" placeholder="Envie uma mensagem..." />
          <button className="botaoEnviar">
            <img src={enviarIcon} alt="Enviar" />
          </button>
        </div>
      </div>
    </div>
  );
}
