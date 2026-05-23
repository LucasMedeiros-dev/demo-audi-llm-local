"""
Backend FastAPI — API do assistente de recall.

Expõe endpoints pequenos e SEM estado; o frontend (React) orquestra o fluxo
guiado (coleta -> validação -> Q&A):

    POST /api/extract   {"texto": "..."}                  -> {cliente, modelo, ano}
    POST /api/validate  {"modelo": "...", "ano": 2020}    -> cobertura do recall
    POST /api/ask       {"pergunta", "modelo", "ano", "cliente", "docs"} -> resposta
    GET  /api/catalog                                     -> docs + veículos atendidos

Reaproveita llm.py, embed.py e vehicles.py. O índice FAISS deve existir
(rode `python ingest.py` uma vez); o LLM e o retriever são carregados no startup.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from embed import get_retriever, retrieve_context
from llm import PROMPT, extract_fields, get_llm
from vehicles import DOCUMENTS, find_vehicle, list_models

# Recursos carregados uma vez no startup (LLM + retriever do índice já gravado).
resources: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    resources["llm"] = get_llm()
    resources["retriever"] = get_retriever()
    yield
    resources.clear()


app = FastAPI(title="Assistente de Recall Audi", lifespan=lifespan)

# Front roda em outra porta no dev (Vite); libera CORS para chamadas locais.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------- modelos (I/O)
class ExtractIn(BaseModel):
    texto: str


class ExtractOut(BaseModel):
    cliente: str | None = None
    modelo: str | None = None
    ano: int | None = None


class ValidateIn(BaseModel):
    modelo: str
    ano: int


class ValidateOut(BaseModel):
    coberto: bool
    modelo: str | None = None
    anos: str | None = None
    docs: list[str] = []


class AskIn(BaseModel):
    pergunta: str
    modelo: str
    ano: int
    cliente: str
    docs: list[str] = []


class AskOut(BaseModel):
    resposta: str


# --------------------------------------------------------------- endpoints
@app.post("/api/extract", response_model=ExtractOut)
def extract(body: ExtractIn):
    """Extrai {cliente, modelo, ano} de uma frase em linguagem natural."""
    return extract_fields(resources["llm"], body.texto)


@app.post("/api/validate", response_model=ValidateOut)
def validate(body: ValidateIn):
    """Verifica se (modelo, ano) está coberto por algum recall."""
    info = find_vehicle(body.modelo, body.ano)
    if not info:
        return ValidateOut(coberto=False)
    return ValidateOut(coberto=True, **info)


@app.post("/api/ask", response_model=AskOut)
def ask(body: AskIn):
    """Responde a pergunta via RAG, restrita aos boletins do veículo."""
    if not body.pergunta.strip():
        raise HTTPException(status_code=400, detail="Pergunta vazia.")

    context = retrieve_context(
        resources["retriever"], body.pergunta, docs=body.docs or None
    )
    chain = PROMPT | resources["llm"]
    resposta = chain.invoke(
        {
            "question": body.pergunta,
            "context": context,
            "veiculo": f"{body.modelo} {body.ano}",
            "cliente": body.cliente,
        }
    ).content
    return AskOut(resposta=resposta)


@app.get("/api/catalog")
def catalog():
    """Documentos carregados e veículos atendidos (para o cheat sheet)."""
    return {
        "documentos": [{"arquivo": k, "descricao": v} for k, v in DOCUMENTS.items()],
        "veiculos": list_models(),
    }


# --------------------------------------------------------------- site estático
# Em produção, serve o build do front (web/dist) na raiz. Em dev, use o Vite
# (npm run dev) com proxy para esta API — então o dist pode não existir ainda.
_DIST = os.path.join(os.path.dirname(__file__), "web", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="site")
