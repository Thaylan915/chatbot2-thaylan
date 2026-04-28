import Sidebar from "../components/Sidebar";
import HistoricoArea from "../components/HistoricoArea";

export default function Historico() {
  return (
    <div className="layout">
      <Sidebar tipo={"admin"} />
      <HistoricoArea />
    </div>
  );
}
