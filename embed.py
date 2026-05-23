"""
Criação do embedding e do índice FAISS.

Usa o modelo de embeddings **BGE-M3** (BAAI General Embedding) servido pelo
Ollama. O BGE-M3 é multilíngue — importante aqui, porque os boletins estão em
inglês e o atendimento ao concessionário é em português.

"Truque" do BGE: para *recuperação*, a query (pergunta) deve receber um
prefixo de instrução; os documentos NÃO. Isso melhora bastante o recall.
Aplicamos isso de forma transparente em `embed_query`.

O índice é persistido em ./faiss_index para não reprocessar a cada execução.
"""

import os

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS_DIR = os.getenv("DOCS_DIR", "docs")
INDEX_DIR = os.getenv("INDEX_DIR", "faiss_index")

# Embeddings BGE-M3 local. Rode antes:  ollama pull bge-m3
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Instrução recomendada pelo BGE para a query de busca (lado da pergunta).
BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class BGEEmbeddings(OllamaEmbeddings):
    """
    OllamaEmbeddings com o detalhe do BGE: prefixa a instrução só nas queries.

    Documentos vão sem prefixo (embed_documents herdado); apenas embed_query
    recebe o BGE_QUERY_INSTRUCTION antes de gerar o vetor.
    """

    def embed_query(self, text: str) -> list[float]:
        return super().embed_query(BGE_QUERY_INSTRUCTION + text)


def get_embeddings() -> BGEEmbeddings:
    return BGEEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)


def build_index() -> FAISS:
    """
    Lê os PDFs, divide em chunks, gera os embeddings e grava o índice FAISS.

    Etapa de INGESTÃO — chamada pelo ingest.py, não pelo dashboard. É aqui que
    os documentos são embeddados (uma vez), não a cada pergunta.
    """
    loader = PyPDFDirectoryLoader(DOCS_DIR)
    documents = loader.load()
    if not documents:
        raise RuntimeError(
            f"Nenhum PDF encontrado em '{DOCS_DIR}/'. Coloque os boletins lá."
        )

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(chunks, get_embeddings())
    vectorstore.save_local(INDEX_DIR)
    return vectorstore


def load_vectorstore() -> FAISS:
    """
    Carrega o índice FAISS já gravado em disco.

    NÃO constrói o índice: se ele não existir, orienta a rodar a ingestão.
    A construção é responsabilidade do ingest.py.
    """
    if not os.path.isdir(INDEX_DIR):
        raise RuntimeError(
            f"Índice FAISS não encontrado em '{INDEX_DIR}/'. "
            "Rode a ingestão uma vez antes:  python ingest.py"
        )

    return FAISS.load_local(
        INDEX_DIR,
        get_embeddings(),
        allow_dangerous_deserialization=True,  # índice gerado localmente por nós
    )


def get_retriever(k: int = 4):
    """Retorna um retriever pronto para o RAG, a partir do índice já gravado."""
    vectorstore = load_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})


def retrieve_context(retriever, question: str, docs: list[str] | None = None) -> str:
    """
    Busca trechos relevantes e devolve o texto concatenado (com a fonte).

    Se `docs` for informado, mantém apenas trechos vindos desses arquivos —
    é assim que filtramos pelo recall do veículo específico do cliente.
    """
    found = retriever.invoke(question)

    if docs:
        wanted = {d.lower() for d in docs}
        filtered = [
            d for d in found
            if os.path.basename(d.metadata.get("source", "")).lower() in wanted
        ]
        found = filtered or found  # fallback: se filtro zerar, usa o que achou

    blocks = []
    for d in found:
        src = os.path.basename(d.metadata.get("source", "documento"))
        page = d.metadata.get("page")
        ref = f"{src}, pág. {page + 1}" if isinstance(page, int) else src
        blocks.append(f"[Fonte: {ref}]\n{d.page_content}")
    return "\n\n".join(blocks)
