import Sidebar from "../components/Sidebar";
import ChatArea from "../components/ChatArea";
import "./Chat.css";

export default function Chat() {
  return (
    <div className="layout">
      <Sidebar tipo={"admin"} />
      <ChatArea />
    </div>
  );
}
