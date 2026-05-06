import { useState } from "react";
import Sidebar from "../components/Sidebar";
import ChatArea from "../components/ChatArea";
import "./Chat.css";

export default function Chat() {
  const [conversaId, setConversaId] = useState(null);
  // Incrementado quando a lista de conversas precisa ser recarregada
  const [refreshConversas, setRefreshConversas] = useState(0);

  function novoChat() {
    setConversaId(null);
  }

  function selecionarConversa(id) {
    setConversaId(id);
  }

  function aoCriarConversa() {
    // Quando ChatArea cria uma nova conversa, atualiza a lista do sidebar
    setRefreshConversas((n) => n + 1);
  }

  return (
    <div className="layout">
      <Sidebar
        conversaAtivaId={conversaId}
        onNovoChat={novoChat}
        onSelecionarConversa={selecionarConversa}
        refreshKey={refreshConversas}
      />
      <ChatArea
        conversaId={conversaId}
        setConversaId={setConversaId}
        onConversaCriada={aoCriarConversa}
      />
    </div>
  );
}
