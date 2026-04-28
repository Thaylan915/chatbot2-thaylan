import "./HistoricoArea.css";

import exportar from "../assets/images/export.svg";

import Documento from "./Documento";
import CardHistorico from "./CardHistorico";

// Dados mockados — serão substituídos pela API futuramente
const historicos = [
  {
    tituloHistorico: "Estudo de caso",
    conteudoHistorico:
      "Análise detalhada sobre diferentes abordagens utilizadas no desenvolvimento de sistemas modernos e suas aplicações práticas.",
    data: "10/04/26",
    hora: "08:30",
    tituloDocumento: "Engenharia de Software",
  },
  {
    tituloHistorico: "Anotação pessoal",
    conteudoHistorico:
      "Reflexões sobre aprendizado contínuo na área de tecnologia e a importância de manter a prática constante no desenvolvimento.",
    data: "11/04/26",
    hora: "21:10",
    tituloDocumento: "Carreira em TI",
  },
  {
    tituloHistorico: "Resumo técnico",
    conteudoHistorico:
      "Descrição dos principais conceitos relacionados a bancos de dados, incluindo modelagem, normalização e consultas SQL.",
    data: "12/04/26",
    hora: "15:45",
    tituloDocumento: "Banco de Dados",
  },
  {
    tituloHistorico: "Pesquisa extensa",
    conteudoHistorico:
      "Este documento apresenta um estudo aprofundado sobre inteligência artificial, abordando desde conceitos básicos até aplicações avançadas em diferentes áreas como saúde, educação e indústria, destacando desafios e oportunidades futuras.",
    data: "13/04/26",
    hora: "10:20",
    tituloDocumento: "Inteligência Artificial",
  },
  {
    tituloHistorico: "Material de apoio",
    conteudoHistorico:
      "Conteúdo utilizado como base para estudos, contendo exemplos práticos e exercícios para fixação do aprendizado.",
    data: "14/04/26",
    hora: "17:00",
    tituloDocumento: "Algoritmos",
  },
];

// Alterar a função implementando o nome do usuário no PDF

async function exportarPDF(dados) {
  // Importa jsPDF dinamicamente (evita aumentar o bundle inicial)
  const { jsPDF } =
    await import("https://cdn.jsdelivr.net/npm/jspdf@2.5.1/+esm");

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const largura = doc.internal.pageSize.getWidth();
  const altura = doc.internal.pageSize.getHeight();
  const margemEsq = 15;
  const margemDir = largura - 15;
  const larguraUtil = margemDir - margemEsq;
  let y = 20;

  // ── Cabeçalho ──────────────────────────────────────────────
  doc.setFillColor(34, 40, 49); // #222831
  doc.rect(0, 0, largura, 28, "F");

  doc.setTextColor(238, 238, 238);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text("Histórico de Conversas", margemEsq, 17);

  const dataHoje = new Date().toLocaleDateString("pt-BR");
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(`Gerado em: ${dataHoje}`, margemDir, 17, { align: "right" });

  y = 38;

  // ── Cards ──────────────────────────────────────────────────
  dados.forEach((item) => {
    const linhasConteudo = doc.splitTextToSize(
      item.conteudoHistorico,
      larguraUtil - 6,
    );
    const alturaCard = 10 + 7 + linhasConteudo.length * 5 + 10;

    // Nova página se necessário
    if (y + alturaCard > altura - 15) {
      doc.addPage();
      y = 20;
    }

    // Fundo do card
    doc.setFillColor(57, 62, 70); // #393e46
    doc.roundedRect(margemEsq, y, larguraUtil, alturaCard, 3, 3, "F");

    // Título do histórico
    doc.setTextColor(238, 238, 238);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text(item.tituloHistorico, margemEsq + 4, y + 8);

    // Data e hora (alinhados à direita)
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(180, 180, 180);
    doc.text(`${item.data}  ${item.hora}`, margemDir - 4, y + 8, {
      align: "right",
    });

    // Conteúdo
    doc.setTextColor(220, 220, 220);
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    doc.text(linhasConteudo, margemEsq + 4, y + 16);

    // Rodapé do card — nome do documento
    const yRodape = y + alturaCard - 7;
    doc.setDrawColor(80, 85, 93);
    doc.line(margemEsq + 4, yRodape - 2, margemDir - 4, yRodape - 2);
    doc.setTextColor(150, 200, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text(item.tituloDocumento, margemEsq + 4, yRodape + 3);

    y += alturaCard + 6;
  });

  // ── Salva na pasta Downloads do navegador ─────────────────
  const nomeArquivo = `historico_${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(nomeArquivo);
}

export default function HistoricoArea() {
  return (
    <div className="histArea">
      <div className="topo">
        <h2>Histórico</h2>
        <button className="btnExportar" onClick={() => exportarPDF(historicos)}>
          <img src={exportar} alt="Exportar" />
          Exportar
        </button>
      </div>

      <div className="filtroHistorico">
        <div className="cardFiltro">
          <div className="espaco">
            <label for="filtroPeriodo">Periodo</label>
            <select name="filtroPeriodo" id="filtroPeriodo">
              <option value="hoje">Hoje</option>
              <option value="esta-semana">Esta Semana</option>
              <option value="este-mes">Este Mês</option>
              <option value="este-ano">Este Ano</option>
              <option value="todo-periodo">Todo o Periodo</option>
            </select>
          </div>

          <div className="espaco">
            <label for="filtroUsuario">Usuário</label>
            <select name="filtroUsuario" id="filtroUsuario">
              {/* listar usuarios no option */}
              <option value=""></option>
            </select>
          </div>

          <div className="espaco">
            <button className="btnFiltrar">Filtrar</button>
          </div>
        </div>
      </div>

      <div className="areaHistoricos">
        {/* fazer lógica de listagem dos historicos de chat do usuário filtrado */}

        <CardHistorico
          tituloHistorico="Estudo de caso"
          conteudoHistorico="Análise detalhada sobre diferentes abordagens utilizadas no desenvolvimento de sistemas modernos e suas aplicações práticas."
          data="10/04/26"
          hora="08:30"
          tituloDocumento="Engenharia de Software"
        />

        <CardHistorico
          tituloHistorico="Anotação pessoal"
          conteudoHistorico="Reflexões sobre aprendizado contínuo na área de tecnologia e a importância de manter a prática constante no desenvolvimento."
          data="11/04/26"
          hora="21:10"
          tituloDocumento="Carreira em TI"
        />

        <CardHistorico
          tituloHistorico="Resumo técnico"
          conteudoHistorico="Descrição dos principais conceitos relacionados a bancos de dados, incluindo modelagem, normalização e consultas SQL."
          data="12/04/26"
          hora="15:45"
          tituloDocumento="Banco de Dados"
        />

        <CardHistorico
          tituloHistorico="Pesquisa extensa"
          conteudoHistorico="Este documento apresenta um estudo aprofundado sobre inteligência artificial, abordando desde conceitos básicos até aplicações avançadas em diferentes áreas como saúde, educação e indústria, destacando desafios e oportunidades futuras."
          data="13/04/26"
          hora="10:20"
          tituloDocumento="Inteligência Artificial"
        />

        <CardHistorico
          tituloHistorico="Material de apoio"
          conteudoHistorico="Conteúdo utilizado como base para estudos, contendo exemplos práticos e exercícios para fixação do aprendizado."
          data="14/04/26"
          hora="17:00"
          tituloDocumento="Algoritmos"
        />
      </div>
    </div>
  );
}
