import { useState } from "react";
import Header from "../components/Header";
import "./Styles.css";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

export default function Cadastro() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ nome: "", email: "", senha: "", confirmarSenha: "" });
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");

    if (form.senha !== form.confirmarSenha) {
      setErro("As senhas não coincidem.");
      return;
    }

    setCarregando(true);
    try {
      await api.post("/api/users/register/", {
        username: form.nome,
        email: form.email,
        password: form.senha,
        password2: form.confirmarSenha,
      });
      navigate("/");
    } catch (err) {
      setErro(err.response?.data?.error || "Erro ao cadastrar. Tente novamente.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="pagina">
      <Header />

      <div className="conteudo">
        <div className="card">
          <h2>Cadastro</h2>

          <form onSubmit={handleSubmit}>
            <label>
              <span>Nome</span>
              <input
                type="text"
                name="nome"
                placeholder="Digite seu nome"
                value={form.nome}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>E-mail</span>
              <input
                type="email"
                name="email"
                placeholder="Digite seu e-mail"
                value={form.email}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>Senha</span>
              <input
                type="password"
                name="senha"
                placeholder="Digite sua senha"
                value={form.senha}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>Confirmar Senha</span>
              <input
                type="password"
                name="confirmarSenha"
                placeholder="Confirme sua senha"
                value={form.confirmarSenha}
                onChange={handleChange}
                required
              />
            </label>

            {erro && <p style={{ color: "red", marginBottom: "8px" }}>{erro}</p>}

            <button className="btnEntrar" type="submit" disabled={carregando}>
              {carregando ? "Cadastrando..." : "Cadastrar"}
            </button>
          </form>

          <Link to="/">Voltar para login</Link>
        </div>
      </div>
    </div>
  );
}
