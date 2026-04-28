import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Cadastro from "./pages/Cadastro";
import Chat from "./pages/Chat";
import BaseDeConhecimento from "./pages/BaseDeConhecimento";
import Metricas from "./pages/Metricas";
import Historico from "./pages/Historico";
import { authService } from "./services/authService";

function RotaProtegida({ children }) {
  return authService.isAuthenticated() ? children : <Navigate to="/" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route
          path="/admin"
          element={
            <RotaProtegida>
              <Chat />
            </RotaProtegida>
          }
        />
        <Route
          path="/admin/base-de-conhecimento"
          element={
            <RotaProtegida>
              <BaseDeConhecimento />
            </RotaProtegida>
          }
        />
        <Route
          path="/admin/metricas"
          element={
            <RotaProtegida>
              <Metricas />
            </RotaProtegida>
          }
        />
        <Route
          path="/admin/historico"
          element={
            <RotaProtegida>
              <Historico />
            </RotaProtegida>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
