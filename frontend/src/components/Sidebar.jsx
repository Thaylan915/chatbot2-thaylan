import { useEffect, useState } from "react";
import "./Sidebar.css";
import logo from "../assets/images/logo_chatbot.svg";
import hideSidebar from "../assets/images/hide-sidebar.svg";
import novoChat from "../assets/images/novo_chat.svg";
import historico from "../assets/images/historico.svg";
import basedeconhec from "../assets/images/basedeconhecimento.svg";
import metricas from "../assets/images/metricas.svg";

import { useLocation } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { authService } from "../services/authService";
import api from "../services/api";

export default function Sidebar({ tipo }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [usuario, setUsuario] = useState(null);
  
  // Estado para guardar o histórico real
  const [conversasRecentes, setConversasRecentes] = useState([]);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      setUsuario(null);
      setConversasRecentes([]);
      return;
    }

    // Busca dados do usuário
    api.get("/api/users/me/")
      .then((res) => setUsuario(res.data))
      .catch(() => setUsuario(null));

    // Busca o histórico de conversas
    api.get("/api/chat/historico/periodo/")
      .then((res) => {
        if (res.data && res.data.conversas) {
          setConversasRecentes(res.data.conversas);
        }
      })
      .catch((err) => console.error("Erro ao buscar histórico:", err));
  }, []);

  function handleLogout() {
    authService.logout();
    navigate("/");
  }

  const nomeExibido = usuario?.username || "...";
  const inicial = nomeExibido[0]?.toUpperCase() || "?";

  // Formatar a data
  const formatarData = (dataString) => {
    const data = new Date(dataString);
    return data.toLocaleDateString("pt-BR", { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="sidebar">
      <div className="item header">
        <div className="esquerda">
          <img src={logo} className="icon" alt="Logo" />
          <span>ChatBOT</span>
        </div>
        <div className="direita">
          <img src={hideSidebar} className="icon" alt="Esconder Sidebar" />
        </div>
      </div>

      <div className="menuTop">
        <div className="item menu" onClick={() => navigate("/admin")}>
          <img src={novoChat} className="icon" alt="Novo Chat" />
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
        
        {/* Renderiza os chats reais */}
        {conversasRecentes.length > 0 ? (
          conversasRecentes.map((conv) => (
            <div 
              key={conv.id} 
              className="chatItem"
              onClick={() => navigate(`/admin?conversa=${conv.id}`)} 
              style={{
                backgroundColor:
                  location.pathname === "/admin" && new URLSearchParams(location.search).get("conversa") === String(conv.id)
                    ? "rgba(255, 255, 255, 0.06)"
                    : "transparent",
              }}
            >
              {conv.titulo || `Chat ${formatarData(conv.iniciada_em)}`}
            </div>
          ))
        ) : (
          <div className="chatItem" style={{ opacity: 0.6, cursor: "default" }}>
            Nenhuma conversa ainda
          </div>
        )}
      </div>

      <div className="perfil">
        <div className="perfilInfo">
          <div className="avatar">{inicial}</div>
          <div className="nome">{nomeExibido}</div>
        </div>
        <button onClick={handleLogout} className="btnLogout">
          Sair
        </button>
      </div>
    </div>
  );
}
