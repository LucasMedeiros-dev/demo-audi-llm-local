import { useEffect, useRef, useState } from "react";

// Sugestões de perguntas mostradas na fase de Q&A.
const SUGESTOES = [
  "Qual o componente afetado?",
  "Qual é o procedimento de reparo?",
  "Quais peças são necessárias?",
  "Qual o risco para o cliente?",
];

const SAUDACAO = {
  from: "bot",
  text:
    "Olá! Sou o assistente de recall da concessionária. Vou registrar o " +
    "atendimento. Qual é o nome do cliente?",
};

// O fluxo guiado é orquestrado AQUI no front; o backend só expõe
// /extract (LLM), /validate (recall por modelo+ano) e /ask (RAG).
export default function ChatWidget({ open, onClose }) {
  const [messages, setMessages] = useState([SAUDACAO]);
  const [stage, setStage] = useState("coleta"); // coleta -> qa -> fim
  const [dados, setDados] = useState({ cliente: null, modelo: null, ano: null });
  const [info, setInfo] = useState(null); // cobertura confirmada
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages, busy]);

  const push = (from, text) => setMessages((m) => [...m, { from, text }]);

  function proximaPergunta(d) {
    if (!d.cliente) return "Certo. Qual é o nome do cliente?";
    if (!d.modelo) return `Obrigado. Qual é o modelo do veículo de ${d.cliente}?`;
    return "E qual é o ano do veículo?";
  }

  async function api(path, payload) {
    const res = await fetch(`/api/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Falha na requisição (${res.status})`);
    return res.json();
  }

  async function tratarColeta(texto) {
    const achado = await api("extract", { texto });
    const d = { ...dados };
    for (const campo of ["cliente", "modelo", "ano"]) {
      if (!d[campo] && achado[campo]) d[campo] = achado[campo];
    }
    setDados(d);

    if (!d.cliente || !d.modelo || !d.ano) {
      push("bot", proximaPergunta(d));
      return;
    }

    // Temos os três -> valida cobertura por modelo + ano.
    const v = await api("validate", { modelo: d.modelo, ano: d.ano });
    if (!v.coberto) {
      push(
        "alert",
        `⚠️ O veículo ${d.modelo} ${d.ano} (cliente ${d.cliente}) não faz ` +
          "parte de nenhum recall cadastrado — modelo não coberto ou ano fora " +
          "da faixa. Não há boletim aplicável."
      );
      setStage("fim");
      return;
    }

    setInfo(v);
    setStage("qa");
    push(
      "bot",
      `✅ Atendimento de ${d.cliente} — ${v.modelo.toUpperCase()} ` +
        `(anos ${v.anos}). Recall(s): ${v.docs.join(", ")}.\n\n` +
        "Pode perguntar o que precisar sobre este recall, ou usar uma das sugestões."
    );
  }

  async function responderQA(pergunta) {
    const r = await api("ask", {
      pergunta,
      modelo: dados.modelo,
      ano: dados.ano,
      cliente: dados.cliente,
      docs: info?.docs ?? [],
    });
    push("bot", r.resposta);
  }

  async function enviar(texto) {
    const t = texto.trim();
    if (!t || busy || stage === "fim") return;
    push("user", t);
    setInput("");
    setBusy(true);
    try {
      if (stage === "coleta") await tratarColeta(t);
      else if (stage === "qa") await responderQA(t);
    } catch (e) {
      push("alert", `Não consegui responder agora. ${e.message}`);
    } finally {
      setBusy(false);
    }
  }

  if (!open) return null;

  return (
    <div className="chat-panel" role="dialog" aria-label="Assistente de recall">
      <div className="chat-header">
        <div className="title">
          <span aria-hidden>🔧</span> Assistente de Recall
        </div>
        <button onClick={onClose} aria-label="Fechar chat">
          ×
        </button>
      </div>

      <div className="chat-body" ref={bodyRef}>
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.from}`}>
            {m.text}
          </div>
        ))}
        {busy && <div className="typing">digitando…</div>}
      </div>

      {stage === "qa" && (
        <div className="suggestions">
          {SUGESTOES.map((s) => (
            <button key={s} onClick={() => enviar(s)} disabled={busy}>
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          enviar(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            stage === "fim" ? "Atendimento encerrado" : "Digite aqui…"
          }
          disabled={busy || stage === "fim"}
          aria-label="Mensagem"
        />
        <button type="submit" disabled={busy || stage === "fim"} aria-label="Enviar">
          ➤
        </button>
      </form>
    </div>
  );
}
