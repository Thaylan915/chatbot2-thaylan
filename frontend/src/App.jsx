import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Cadastro from "./pages/Cadastro";
import Chat from "./pages/Chat";
import BaseDeConhecimento from "./pages/BaseDeConhecimento";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/admin" element={<Chat />} />
        <Route
          path="/admin/base-de-conhecimento"
          element={<BaseDeConhecimento />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
