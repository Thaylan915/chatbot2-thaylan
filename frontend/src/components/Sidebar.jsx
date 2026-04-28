import "./Sidebar.css";
import logo from "../assets/images/logo_chatbot.svg";
import hideSidebar from "../assets/images/hide-sidebar.svg";
import novoChat from "../assets/images/novo_chat.svg";
import historico from "../assets/images/historico.svg";
import basedeconhec from "../assets/images/basedeconhecimento.svg";
import metricas from "../assets/images/metricas.svg";

import { useNavigate } from "react-router-dom";
import { authService } from "../services/authService";

export default function Sidebar({ tipo }) {
  const navigate = useNavigate();

  function handleLogout() {
    authService.logout();
    navigate("/");
  }

  return (
    <div className="sidebar">
      <div className="item header">
        <div className="esquerda">
          <img src={logo} className="icon" />
          <span>ChatBOT</span>
        </div>
        <div className="direita">
          <img src={hideSidebar} className="icon" />
        </div>
      </div>

      <div className="menuTop">
        <div className="item menu" onClick={() => navigate("/admin")}>
          <img src={novoChat} className="icon" />
          <span>Novo Chat</span>
        </div>

        {tipo === "admin" && (
          <>
            <div
              className="item menu"
              onClick={() => navigate("/admin/base-de-conhecimento")}
            >
              <img src={basedeconhec} className="icon" />
              <span>Base de conhecimento</span>
            </div>

            <div
              className="item menu"
              onClick={() => navigate("/admin/metricas")}
            >
              <img src={metricas} className="icon" />
              <span>Métricas</span>
            </div>

            <div
              className="item menu"
              onClick={() => navigate("/admin/historico")}
            >
              <img src={historico} className="icon" />
              <span>Histórico</span>
            </div>
          </>
        )}
      </div>

      <div className="chats">
        <div className="miniTitulo">Seus chats</div>
        <div className="chatItem">Chat sobre IA</div>
        <div className="chatItem">Banco de dados</div>
        <div className="chatItem">Projeto TCC</div>
        <div className="chatItem">Teste</div>
        <div className="chatItem">Teste 123</div>
      </div>

      <div className="perfil">
        <div className="perfilInfo">
          <div className="avatar">K</div>
          <div className="nome">Kenzo Annichini de Oliveira</div>
        </div>
        <button onClick={handleLogout} className="btnLogout">
          Sair
        </button>
      </div>
    </div>
  );
}
