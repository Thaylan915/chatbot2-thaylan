import "./Sidebar.css";
import logo from "../assets/images/logo_chatbot.svg";
import hideSidebar from "../assets/images/hide-sidebar.svg";
import novoChat from "../assets/images/novo_chat.svg";
import historico from "../assets/images/historico.svg";
import basedeconhec from "../assets/images/basedeconhecimento.svg";
import metricas from "../assets/images/metricas.svg";

import { useNavigate } from "react-router-dom";

export default function Sidebar({ tipo }) {
  const navigate = useNavigate();

  function irBaseConhecimento() {
    navigate("/admin/base-de-conhecimento");
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
        <div className="item menu">
          <img src={novoChat} className="icon" />
          <span>Novo Chat</span>
        </div>

        {tipo === "admin" && (
          <>
            <div className="item menu" onClick={irBaseConhecimento}>
              <img src={basedeconhec} className="icon" />
              <span>Base de conhecimento</span>
            </div>

            <div className="item menu">
              <img src={metricas} className="icon" />
              <span>Métricas</span>
            </div>

            <div className="item menu">
              <img src={historico} className="icon" />
              <span>Histórico</span>
            </div>
          </>
        )}
      </div>

      <div className="chats">
        <div className="miniTitulo">Seus chats</div>
        {/* Criar uma classe para chat */}
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
      </div>
    </div>
  );
}
