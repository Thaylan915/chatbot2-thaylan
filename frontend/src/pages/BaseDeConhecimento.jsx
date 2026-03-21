import Sidebar from "../components/Sidebar";
import ConhecimentoArea from "../components/ConhecimentoArea";

export default function BaseDeConhecimento() {
  return (
    <div className="layout">
      <Sidebar tipo={"admin"} />
      <ConhecimentoArea />
    </div>
  );
}
