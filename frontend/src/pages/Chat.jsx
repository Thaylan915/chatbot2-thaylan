import Sidebar from "../components/Sidebar";
import ChatArea from "../components/ChatArea";
import "./Chat.css";

export default function Chat() {
  // Estado de conversa selecionada vive na URL (?conversa=ID); a Sidebar lê
  // de location.search e a ChatArea lê via useLocation. Aqui a página apenas
  // monta os dois componentes lado a lado.
  return (
    <div className="layout">
      <Sidebar />
      <ChatArea />
    </div>
  );
}
