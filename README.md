<div align="center">

# 🔧 Central de Recall Audi

### Sistema de Q&A com RAG e LLM local para concessionárias

Um site institucional **SEO-otimizado** com um **assistente de chat** que verifica
recalls por modelo + ano e responde dúvidas técnicas direto dos boletins oficiais —
tudo rodando **100% local** via Ollama. Sem nuvem, sem custo por token, sem vazar dados.

<br/>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local-000000?logo=ollama&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-vector%20store-0467DF)
![BGE--M3](https://img.shields.io/badge/Embeddings-BGE--M3-FF6F00)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

## ✨ Destaques

- 🌐 **Hero site SEO** — landing com tema Audi, fotos dos veículos, meta tags,
  Open Graph, Twitter Card e dados estruturados (Schema.org).
- 💬 **Chat widget flutuante** — atendimento guiado sem sair da página.
- 🧭 **Fluxo conversacional** — o assistente pergunta cliente → modelo → ano; o
  **LLM interpreta** linguagem natural (`"é o A4 2020 do João"`).
- ✅ **Match híbrido** — checagem determinística de recall por **modelo + ano**;
  RAG para os detalhes técnicos.
- 🔍 **RAG com BGE-M3 + FAISS** — embeddings multilíngues (PT/EN), com o prefixo de
  instrução de query recomendado pelo BGE para melhor recall.
- 🔒 **100% local** — LLM e embeddings via Ollama; nenhum dado sai da máquina.
- 🐳 **Production-ready** — Docker multi-stage, healthcheck, ingestão automática.

---

## 🏗️ Arquitetura

```
┌──────────────────────────┐         ┌──────────────────────────────┐
│  Frontend (React + Vite) │         │  Backend (FastAPI)           │
│                          │  /api   │                              │
│  • Hero site SEO         │ ──────► │  POST /api/extract  (LLM)    │
│  • Chat widget flutuante │         │  POST /api/validate (recall) │
│  • Orquestra o fluxo     │ ◄────── │  POST /api/ask      (RAG)    │
└──────────────────────────┘         │  GET  /api/catalog           │
                                      └───────────────┬──────────────┘
                                                      │
                          ┌───────────────────────────┼───────────────────────┐
                          ▼                            ▼                       ▼
                  llm.py (ChatOllama)      embed.py (BGE-M3 + FAISS)   vehicles.py (match)
                          │                            │
                          └──────────► Ollama (local) ◄┘
```

| Arquivo / pasta | Responsabilidade |
|---|---|
| `api.py`        | Backend FastAPI: endpoints `/extract`, `/validate`, `/ask`, `/catalog` + serve o site. |
| `llm.py`        | Setup do LLM (Ollama), prompt do assistente e extração de campos. |
| `embed.py`      | Embeddings **BGE-M3** + índice **FAISS** (build e busca). |
| `vehicles.py`   | Lista de veículos cobertos (extraída dos PDFs); match por modelo + ano. |
| `ingest.py`     | Ingestão: embedda os PDFs e grava o FAISS (rodar uma vez). |
| `docs/`         | Boletins técnicos oficiais (PDFs). |
| `web/`          | Frontend React/Vite (hero site + chat widget). |

---

## 🚀 Início rápido

### Pré-requisitos

- [Ollama](https://ollama.com) rodando localmente
- Python 3.12+ e Node 22+ (apenas para execução sem Docker)

```bash
ollama pull gemma4:e4b   # LLM de chat
ollama pull bge-m3       # embeddings multilíngues
```

### Opção A — Docker (recomendado) 🐳

Requer o **Ollama rodando no host**. O container conecta via
`host.docker.internal`, puxa os modelos e roda a ingestão automaticamente.

```bash
docker compose up --build
```

➡️ Acesse **http://localhost:8000** — site + chat.

### Opção B — Local (dev)

```bash
# 1. Backend
pip install -r requirements.txt
python ingest.py                       # embedda os PDFs (uma vez)
uvicorn api:app --reload --port 8000

# 2. Frontend (outro terminal)
cd web
npm install
npm run dev                            # http://localhost:5173 (proxy p/ :8000)
```

Em produção sem Docker: `cd web && npm run build` e suba só o `uvicorn` — o
FastAPI passa a servir o `web/dist` na raiz.

---

## 🧠 Como funciona o assistente

1. **Coleta guiada** — o bot pergunta nome, modelo e ano; o `/api/extract` usa o
   LLM para extrair os campos de frases em linguagem natural.
2. **Validação** — com os três campos, `/api/validate` confirma a cobertura por
   **modelo + ano**. Modelo ausente ou ano fora da faixa → "não faz parte do recall".
3. **Q&A (RAG)** — `/api/ask` recupera trechos dos boletins **daquele veículo**
   (FAISS + BGE-M3) e o LLM responde citando procedimento, peças e códigos.
   Botões de sugestão aceleram as perguntas comuns.

> **Por que "embeddar uma vez"?** Os documentos são vetorizados na ingestão
> (`ingest.py`) e gravados no FAISS. Por pergunta, embeddamos apenas a *query* —
> intrínseco ao RAG e barato (uma frase).

---

## ⚙️ Configuração (variáveis de ambiente)

| Variável             | Padrão                            | Descrição                  |
|----------------------|-----------------------------------|----------------------------|
| `OLLAMA_MODEL`       | `gemma4:e4b`                      | Modelo de chat             |
| `OLLAMA_EMBED_MODEL` | `bge-m3`                          | Modelo de embeddings       |
| `OLLAMA_BASE_URL`    | `http://localhost:11434`          | Endpoint do Ollama         |
| `DOCS_DIR`           | `docs`                            | Pasta dos PDFs             |
| `INDEX_DIR`          | `faiss_index`                     | Pasta do índice FAISS      |

No Docker, `OLLAMA_BASE_URL` aponta para `http://host.docker.internal:11434`.

---

## 🧪 Qualidade

```bash
ruff check --select F,E,W,I,UP,B *.py   # lint do backend
cd web && npm run build                 # type/compile check do front
```

---

## 📄 Licença

MIT. Demonstração não oficial — "Audi" e modelos são marcas de seus respectivos
detentores; uso apenas ilustrativo.
