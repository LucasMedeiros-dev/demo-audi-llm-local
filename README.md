# Assistente de Recall Audi — Q&A RAG com LLM local

Demo de um sistema simples de **Q&A com RAG** para apoiar **concessionários**
no atendimento de recalls. Roda 100% local com **Ollama**, **LangChain**,
embeddings **BGE-M3** + **FAISS** e interface em **Streamlit**.

## Como funciona

1. O **chatbot conduz a conversa** e pergunta, em linguagem natural, o **nome
   do cliente**, o **modelo** e o **ano**. O LLM extrai esses campos das
   respostas (não há formulário).
2. Com os três campos, o sistema verifica a cobertura por **modelo + ano**:
   - **Não coberto** (modelo ausente ou ano fora da faixa) → avisa que o
     veículo não faz parte do recall.
   - **Coberto** → abre o Q&A: responde com base nos boletins oficiais (PDFs em
     `docs/`), usando apenas o(s) documento(s) daquele veículo, e oferece
     **sugestões de perguntas** comuns em botões.
3. A barra lateral mostra o *cheat sheet*: documentos carregados e veículos atendidos.

**Match híbrido:** lista fixa (`vehicles.py`) decide rápido se o veículo está no
recall; o RAG (`embed.py` + `llm.py`) responde os detalhes técnicos.

## Estrutura

| Arquivo         | Responsabilidade                                            |
|-----------------|-------------------------------------------------------------|
| `llm.py`        | Setup do LLM local (Ollama) e prompt do assistente.         |
| `embed.py`      | Embeddings BGE-M3 + índice FAISS (build e busca).           |
| `ingest.py`     | Ingestão: embedda os PDFs e grava o FAISS (rodar 1x).       |
| `vehicles.py`   | Lista de veículos cobertos (extraída dos PDFs reais).        |
| `dashboard.py`  | Interface Streamlit (chat + sidebar).                       |
| `docs/`         | Boletins técnicos (PDFs reais).                             |

## Pré-requisitos

Instale o [Ollama](https://ollama.com) e baixe os modelos:

```bash
ollama pull gemma4:e4b       # LLM de chat
ollama pull bge-m3           # embeddings (multilíngue)
```

## Instalação e execução

```bash
pip install -r requirements.txt

# 1) Ingestão: embedda os PDFs e grava o índice FAISS (rode UMA vez)
python ingest.py

# 2) Suba o dashboard (apenas carrega o índice já pronto)
streamlit run dashboard.py
```

A ingestão embedda todos os documentos de uma vez e grava em `faiss_index/`.
O dashboard só carrega esse índice — por pergunta, embedda apenas a query.
Trocou os PDFs? Rode `python ingest.py --rebuild`.

## Configuração (variáveis de ambiente, opcional)

| Variável             | Padrão                   |
|----------------------|--------------------------|
| `OLLAMA_MODEL`       | `gemma4:e4b`             |
| `OLLAMA_EMBED_MODEL` | `bge-m3`                 |
| `OLLAMA_BASE_URL`    | `http://localhost:11434` |
| `DOCS_DIR`           | `docs`                   |
| `INDEX_DIR`          | `faiss_index`            |
