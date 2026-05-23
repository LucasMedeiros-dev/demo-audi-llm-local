import { useState } from "react";
import ChatWidget from "./ChatWidget.jsx";
import { FEATURED } from "./vehicles.js";

function Rings() {
  return (
    <span className="rings" aria-hidden>
      <span /><span /><span /><span />
    </span>
  );
}

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const abrirChat = () => setChatOpen(true);

  return (
    <>
      {/* ---------- Navbar ---------- */}
      <nav className="nav">
        <div className="container">
          <div className="brand">
            <Rings /> Recall Audi
          </div>
          <div>
            <a href="#veiculos">Veículos</a>
            <a href="#como-funciona">Como funciona</a>
            <a href="#atendimento" onClick={abrirChat}>
              Atendimento
            </a>
          </div>
        </div>
      </nav>

      {/* ---------- Hero ---------- */}
      <header className="hero">
        <div className="container hero-content">
          <span className="tag">Central para concessionárias</span>
          <h1>Recalls Audi resolvidos com precisão e agilidade.</h1>
          <p>
            Verifique em segundos se o veículo do cliente faz parte de um recall
            e consulte os boletins técnicos oficiais com nosso assistente
            inteligente — tudo em um só lugar.
          </p>
          <button className="btn btn-primary" onClick={abrirChat}>
            Iniciar atendimento ➤
          </button>
        </div>
      </header>

      {/* ---------- Veículos ---------- */}
      <section id="veiculos" className="vehicles">
        <div className="container">
          <div className="section-head">
            <span>Linha atendida</span>
            <h2>Modelos cobertos por recall</h2>
            <p>
              Confira alguns dos modelos Audi contemplados pelos boletins
              técnicos vigentes. A cobertura exata depende do modelo e do ano.
            </p>
          </div>
          <div className="grid">
            {FEATURED.map((v) => (
              <article className="card" key={v.nome}>
                <img src={v.img} alt={`${v.nome} — recall`} loading="lazy" />
                <div className="card-body">
                  <h3>{v.nome}</h3>
                  <p>
                    <strong>{v.anos}</strong>
                    <br />
                    {v.desc}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Como funciona ---------- */}
      <section id="como-funciona">
        <div className="container">
          <div className="section-head">
            <span>Simples e guiado</span>
            <h2>Como funciona o atendimento</h2>
            <p>
              O assistente conduz a conversa e, ao final, responde dúvidas
              técnicas com base nos boletins oficiais.
            </p>
          </div>
          <div className="steps">
            <div className="step">
              <div className="num">1</div>
              <h3>Identifique o cliente</h3>
              <p>Informe o nome, o modelo e o ano do veículo no chat.</p>
            </div>
            <div className="step">
              <div className="num">2</div>
              <h3>Verifique o recall</h3>
              <p>
                O sistema confirma na hora se o veículo faz parte de algum
                boletim técnico.
              </p>
            </div>
            <div className="step">
              <div className="num">3</div>
              <h3>Consulte os detalhes</h3>
              <p>
                Pergunte sobre componente afetado, procedimento, peças e riscos —
                respostas direto dos documentos.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- CTA ---------- */}
      <section id="atendimento" className="cta">
        <div className="container">
          <h2>Pronto para atender seu cliente?</h2>
          <p>Abra o assistente e inicie o atendimento agora mesmo.</p>
          <button className="btn btn-primary" onClick={abrirChat}>
            Abrir assistente de recall ➤
          </button>
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer>
        <div className="container">
          Central de Recall Audi — Ferramenta de apoio às concessionárias
          autorizadas. Demonstração não oficial.
        </div>
      </footer>

      {/* ---------- Chat ---------- */}
      {!chatOpen && (
        <button
          className="chat-launcher"
          onClick={abrirChat}
          aria-label="Abrir assistente de recall"
        >
          💬
        </button>
      )}
      <ChatWidget open={chatOpen} onClose={() => setChatOpen(false)} />
    </>
  );
}
