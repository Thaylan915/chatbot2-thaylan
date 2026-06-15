import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { useLocation, useNavigate } from "react-router-dom";
import "./Sidebar.css";
import logo from "../assets/images/logo_chatbot.svg";
import hideSidebar from "../assets/images/hide-sidebar.svg";
import novoChat from "../assets/images/novo_chat.svg";
import historico from "../assets/images/historico.svg";
import basedeconhec from "../assets/images/basedeconhecimento.svg";
import metricas from "../assets/images/metricas.svg";

import { authService } from "../services/authService";
import api from "../services/api";

export default function Sidebar({ refreshKey } = {}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [usuario, setUsuario] = useState(null);
  const [conversas, setConversas] = useState([]);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      setUsuario(null);
      setConversas([]);
      return;
    }
    api
      .get("/api/users/me/")
      .then((res) => setUsuario(res.data))
      .catch(() => setUsuario(null));
  }, []);

  useEffect(() => {
    if (!authService.isAuthenticated()) return;
    api
      .get("/api/chat/conversas/")
      .then((res) => setConversas(res.data?.conversas || []))
      .catch(() => setConversas([]));
  }, [refreshKey]);

  function handleLogout() {
    authService.logout();
    navigate("/");
  }
  function handleNovoChat() {
    navigate(`/admin?_novo=${Date.now()}`);
  }
  function handleSelecionar(id) {
    navigate(`/admin?conversa=${id}`);
  }

  const nomeExibido = usuario?.username || "...";
  const inicial = nomeExibido[0]?.toUpperCase() || "?";
  const isAdmin = usuario?.role === "admin" || usuario?.is_staff === true;

  const conversaAtivaId = (() => {
    if (location.pathname !== "/admin") return null;
    const id = new URLSearchParams(location.search).get("conversa");
    return id ? Number(id) : null;
  })();

  const formatarData = (iso) => {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
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
        <button type="button" className="item menu" onClick={handleNovoChat}>
          <img src={novoChat} className="icon" alt="Novo Chat" />
          <span>Novo Chat</span>
        </button>

        {isAdmin && (
          <>
            <button
              type="button"
              className="item menu"
              onClick={() => navigate("/admin/base-de-conhecimento")}
            >
              <img src={basedeconhec} className="icon" alt="" />
              <span>Base de conhecimento</span>
            </button>

            {/* ── NOVO: link para Categorias ── */}
            <button
              type="button"
              className="item menu"
              onClick={() => navigate("/admin/categorias")}
            >
              <img src={basedeconhec} className="icon" alt="" />
              <span>Categorias</span>
            </button>

            <button
              type="button"
              className="item menu"
              onClick={() => navigate("/admin/metricas")}
            >
              <img src={metricas} className="icon" alt="" />
              <span>Métricas</span>
            </button>

            <button
              type="button"
              className="item menu"
              onClick={() => navigate("/admin/historico")}
            >
              <img src={historico} className="icon" alt="" />
              <span>Histórico</span>
            </button>
          </>
        )}
      </div>

      <div className="chats">
        <div className="miniTitulo">Seus chats</div>
        {conversas.length === 0 && (
          <div className="chatItem" style={{ opacity: 0.6, cursor: "default" }}>
            Nenhuma conversa ainda
          </div>
        )}
        {conversas.map((c) => {
          const ativo = c.id === conversaAtivaId;
          return (
            <button
              type="button"
              key={c.id}
              className={`chatItem${ativo ? " ativo" : ""}`}
              onClick={() => handleSelecionar(c.id)}
              title={c.titulo}
              style={{
                cursor: "pointer",
                backgroundColor: ativo
                  ? "rgba(255,255,255,0.06)"
                  : "transparent",
              }}
            >
              {c.titulo || `Chat ${formatarData(c.iniciada_em)}`}
            </button>
          );
        })}
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

Sidebar.propTypes = {
  refreshKey: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
};
