import Header from "../components/Header";
import "./Styles.css";
import { Link } from "react-router-dom";

export default function Cadastro() {
  return (
    <div className="pagina">
      <Header />

      <div className="conteudo">
        <div className="card">
          <h2>Cadastro</h2>

          <label>
            <span>Nome</span>
            <input type="text" placeholder="Digite seu nome" />
          </label>

          <label>
            <span>E-mail</span>
            <input type="email" placeholder="Digite seu e-mail" />
          </label>

          <label>
            <span>Senha</span>
            <input type="password" placeholder="Digite sua senha" />
          </label>

          <label>
            <span>Confirmar Senha</span>
            <input type="password" placeholder="Confirme sua senha" />
          </label>

          <button className="btnEntrar">Cadastrar</button>

          <Link to="/">Voltar para login</Link>
        </div>
      </div>
    </div>
  );
}
