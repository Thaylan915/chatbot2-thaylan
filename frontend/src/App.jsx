import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Cadastro from "./pages/Cadastro";
import Chat from "./pages/Chat";
import BaseDeConhecimento from "./pages/BaseDeConhecimento";
import Metricas from "./pages/Metricas";
import Historico from "./pages/Historico";
import { authService } from "./services/authService";
import api from "./services/api";

function RotaProtegida({ children }) {
  return authService.isAuthenticated() ? children : <Navigate to="/" replace />;
}

function RotaAdmin({ children }) {
  const [estado, setEstado] = useState("loading"); // loading | admin | nao-admin | nao-auth

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      setEstado("nao-auth");
      return;
    }
    api.get("/api/users/me/")
      .then((res) => {
        const isAdmin = res.data?.role === "admin" || res.data?.is_staff === true;
        setEstado(isAdmin ? "admin" : "nao-admin");
      })
      .catch(() => setEstado("nao-auth"));
  }, []);

  if (estado === "loading") return null;
  if (estado === "nao-auth") return <Navigate to="/" replace />;
  if (estado === "nao-admin") return <Navigate to="/admin" replace />;
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/admin" element={<RotaProtegida><Chat /></RotaProtegida>} />
        <Route path="/admin/base-de-conhecimento" element={<RotaAdmin><BaseDeConhecimento /></RotaAdmin>} />
        <Route path="/admin/metricas" element={<RotaAdmin><Metricas /></RotaAdmin>} />
        <Route path="/admin/historico" element={<RotaAdmin><Historico /></RotaAdmin>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
