"""
Dashboard Streamlit — Assistente de Recall para Concessionárias Audi.

Conversa 100% guiada pelo chatbot (sem formulário):
1. O bot pergunta, em linguagem natural, o nome do cliente, o modelo e o ano.
   O LLM extrai esses campos das respostas (llm.extract_fields).
2. Com os três campos, valida a cobertura (vehicles.find_vehicle) por modelo+ano:
   - Não coberto → avisa que o veículo não faz parte do recall.
   - Coberto → abre o Q&A; o RAG responde só com o(s) boletim(ns) do veículo,
     e o bot oferece sugestões de perguntas comuns.

Barra lateral = "cheat sheet": documentos carregados e veículos atendidos.
"""

import streamlit as st

from embed import get_retriever, retrieve_context
from llm import PROMPT, extract_fields, get_llm
from vehicles import DOCUMENTS, find_vehicle, list_models

st.set_page_config(page_title="Assistente de Recall — Concessionárias", page_icon="🔧")

SUGESTOES = [
    "Qual o componente afetado?",
    "Qual é o procedimento de reparo?",
    "Quais peças são necessárias?",
    "Qual o risco para o cliente?",
]


# ---------------------------------------------------------------- recursos
@st.cache_resource(show_spinner="Carregando o índice de busca (FAISS + BGE-M3)...")
def boot():
    """Carrega LLM e retriever (índice já gravado) uma vez, cacheado."""
    return get_llm(), get_retriever()


def add(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def reset():
    st.session_state.clear()


# ---------------------------------------------------------------- estado inicial
if "stage" not in st.session_state:
    # stage: "coleta" -> "qa"
    st.session_state.stage = "coleta"
    st.session_state.dados = {"cliente": None, "modelo": None, "ano": None}
    st.session_state.info = None  # cobertura confirmada do veículo
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Olá! Sou o assistente de recall da concessionária. "
                "Vou registrar o atendimento. **Qual é o nome do cliente?**"
            ),
        }
    ]


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("📋 Cheat sheet")

    st.subheader("Documentos carregados")
    for arquivo, descricao in DOCUMENTS.items():
        st.markdown(f"- **{arquivo}**\n  \n  {descricao}")

    st.subheader("Veículos atendidos")
    st.caption("Modelos cobertos por algum boletim/recall:")
    for modelo in list_models():
        st.markdown(f"- {modelo}")

    st.divider()
    if st.button("🔄 Novo atendimento"):
        reset()
        st.rerun()


st.title("🔧 Assistente de Recall Audi")
st.caption("Ferramenta de apoio ao **concessionário** no atendimento de recalls.")

try:
    llm, retriever = boot()
except RuntimeError as e:
    st.error(str(e))
    st.info("No terminal, rode uma vez:  `python ingest.py`  e recarregue a página.")
    st.stop()


# ---------------------------------------------------------------- histórico
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


# ---------------------------------------------------------------- helpers de fluxo
def _proxima_pergunta_coleta() -> str:
    """Pergunta sobre o primeiro campo ainda em falta."""
    d = st.session_state.dados
    if not d["cliente"]:
        return "Certo. **Qual é o nome do cliente?**"
    if not d["modelo"]:
        return f"Obrigado. Qual é o **modelo do veículo** de {d['cliente']}?"
    return "E qual é o **ano** do veículo?"


def _tratar_coleta(texto: str):
    """Extrai campos da fala do concessionário e conduz a coleta."""
    achado = extract_fields(llm, texto)
    d = st.session_state.dados
    for campo in ("cliente", "modelo", "ano"):
        if not d[campo] and achado.get(campo):
            d[campo] = achado[campo]

    # Ainda falta algo? Pergunta o próximo.
    if not all(d.values()):
        add("assistant", _proxima_pergunta_coleta())
        return

    # Temos os três -> valida cobertura por modelo + ano.
    info = find_vehicle(d["modelo"], int(d["ano"]))
    if not info:
        add(
            "assistant",
            f"⚠️ O veículo **{d['modelo']} {d['ano']}** (cliente {d['cliente']}) "
            "**não faz parte de nenhum recall** cadastrado — modelo não coberto "
            "ou ano fora da faixa. Não há boletim aplicável.\n\n"
            "Use **🔄 Novo atendimento** na barra lateral para registrar outro.",
        )
        st.session_state.stage = "fim"
        return

    st.session_state.info = info
    st.session_state.stage = "qa"
    add(
        "assistant",
        f"✅ Atendimento de **{d['cliente']}** — **{info['modelo'].upper()}** "
        f"(anos {info['anos']}). Recall(s): {', '.join(info['docs'])}.\n\n"
        "Pode perguntar o que precisar sobre este recall — ou use uma das "
        "sugestões abaixo.",
    )


def _responder_qa(pergunta: str):
    """Responde uma pergunta do concessionário via RAG (só docs do veículo)."""
    info = st.session_state.info
    d = st.session_state.dados
    context = retrieve_context(retriever, pergunta, docs=info["docs"])
    chain = PROMPT | llm
    resposta = chain.invoke(
        {
            "question": pergunta,
            "context": context,
            "veiculo": f"{d['modelo']} {d['ano']}",
            "cliente": d["cliente"],
        }
    ).content
    add("assistant", resposta)


def processar(texto: str):
    """Roteia a mensagem do usuário conforme o estágio da conversa."""
    add("user", texto)
    if st.session_state.stage == "coleta":
        with st.spinner("Anotando..."):
            _tratar_coleta(texto)
    elif st.session_state.stage == "qa":
        with st.spinner("Consultando os boletins..."):
            _responder_qa(texto)
    st.rerun()


# ---------------------------------------------------------------- sugestões (Q&A)
if st.session_state.stage == "qa":
    st.write("**Sugestões:**")
    cols = st.columns(len(SUGESTOES))
    for col, sug in zip(cols, SUGESTOES, strict=True):
        if col.button(sug, use_container_width=True):
            processar(sug)


# ---------------------------------------------------------------- entrada de chat
placeholder = (
    "Digite aqui..." if st.session_state.stage != "fim"
    else "Inicie um novo atendimento na barra lateral."
)
if texto := st.chat_input(placeholder, disabled=st.session_state.stage == "fim"):
    processar(texto)
