import { useEffect, useState } from "react";
import "./Sidebar.css";
import logo        from "../assets/images/logo_chatbot.svg";
import hideSidebar from "../assets/images/hide-sidebar.svg";
import novoChat    from "../assets/images/novo_chat.svg";
import historico   from "../assets/images/historico.svg";
import basedeconhec from "../assets/images/basedeconhecimento.svg";
import metricas    from "../assets/images/metricas.svg";

import { useNavigate, useLocation } from "react-router-dom";
import { authService } from "../services/authService";
import api from "../services/api";

export default function Sidebar({
  conversaAtivaId,
  onNovoChat,
  onSelecionarConversa,
  refreshKey,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [usuario, setUsuario] = useState(null);
  const [conversas, setConversas] = useState([]);

  useEffect(() => {
    api.get("/api/users/me/")
      .then((res) => setUsuario(res.data))
      .catch(() => setUsuario(null));
  }, []);

  // Recarrega lista de conversas quando refreshKey muda
  useEffect(() => {
    api.get("/api/chat/conversas/")
      .then((res) => setConversas(res.data?.conversas || []))
      .catch(() => setConversas([]));
  }, [refreshKey]);

  function handleLogout() {
    authService.logout();
    navigate("/");
  }

  function handleNovoChat() {
    if (location.pathname !== "/admin") navigate("/admin");
    if (typeof onNovoChat === "function") onNovoChat();
  }

  function handleSelecionar(id) {
    if (location.pathname !== "/admin") navigate("/admin");
    if (typeof onSelecionarConversa === "function") onSelecionarConversa(id);
  }

  const nomeExibido = usuario?.username || "...";
  const inicial = nomeExibido[0]?.toUpperCase() || "?";
  const isAdmin = usuario?.role === "admin" || usuario?.is_staff === true;

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
        <div className="item menu" onClick={handleNovoChat}>
          <img src={novoChat} className="icon" />
          <span>Novo Chat</span>
        </div>

        {isAdmin && (
          <>
            <div className="item menu" onClick={() => navigate("/admin/base-de-conhecimento")}>
              <img src={basedeconhec} className="icon" />
              <span>Base de conhecimento</span>
            </div>

            <div className="item menu" onClick={() => navigate("/admin/metricas")}>
              <img src={metricas} className="icon" />
              <span>Métricas</span>
            </div>

            <div className="item menu" onClick={() => navigate("/admin/historico")}>
              <img src={historico} className="icon" />
              <span>Histórico</span>
            </div>
          </>
        )}
      </div>

      <div className="chats">
        <div className="miniTitulo">Seus chats</div>
        {conversas.length === 0 && (
          <div className="chatItem" style={{ opacity: 0.5 }}>
            Nenhuma conversa ainda
          </div>
        )}
        {conversas.map((c) => (
          <div
            key={c.id}
            className={`chatItem${c.id === conversaAtivaId ? " ativo" : ""}`}
            onClick={() => handleSelecionar(c.id)}
            title={c.titulo}
            style={{ cursor: "pointer" }}
          >
            {c.titulo || `Conversa #${c.id}`}
          </div>
        ))}
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
