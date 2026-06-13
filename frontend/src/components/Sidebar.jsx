import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./Sidebar.css";
import logo from "../assets/images/logo_chatbot.svg";
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
  const [menuAberto, setMenuAberto] = useState(false);
  const isAtivo = (path) => location.pathname === path;

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
      </div>

      <div className="menuTop">
        <div className="item menu" onClick={handleNovoChat}>
          <img src={novoChat} className="icon" alt="Novo Chat" />
          <span>Novo Chat</span>
        </div>

        {isAdmin && (
          <>
            <div
              className={`item menu ${isAtivo("/admin/base-de-conhecimento") ? "ativo" : ""}`}
              onClick={() => navigate("/admin/base-de-conhecimento")}
            >
              <img src={basedeconhec} className="icon" />
              <span>Base de conhecimento</span>
            </div>

            <div
              className={`item menu ${isAtivo("/admin/categorias") ? "ativo" : ""}`}
              onClick={() => navigate("/admin/categorias")}
            >
              <img src={basedeconhec} className="icon" />
              <span>Categorias</span>
            </div>

            <div
              className={`item menu ${isAtivo("/admin/metricas") ? "ativo" : ""}`}
              onClick={() => navigate("/admin/metricas")}
            >
              <img src={metricas} className="icon" />
              <span>Métricas</span>
            </div>

            <div
              className={`item menu ${isAtivo("/admin/historico") ? "ativo" : ""}`}
              onClick={() => navigate("/admin/historico")}
            >
              <img src={historico} className="icon" />
              <span>Histórico</span>
            </div>
          </>
        )}
      </div>

      <div className="chatsContainer">
        <div className="miniTitulo">Seus chats</div>

        <div className="chats">
          {conversas.length === 0 && (
            <div className="chatItem">Nenhuma conversa ainda</div>
          )}

          {conversas.map((c) => {
            const ativo = c.id === conversaAtivaId;
            return (
              <div
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
              </div>
            );
          })}
        </div>
      </div>

      <div className="perfil">
        <div className="perfilInfo" onClick={() => setMenuAberto(!menuAberto)}>
          <div className="avatar">{inicial}</div>
          <div className="nome">{nomeExibido}</div>
        </div>
        {menuAberto && (
          <button onClick={handleLogout} className="btnLogout">
            Sair
          </button>
        )}
      </div>
    </div>
  );
}
