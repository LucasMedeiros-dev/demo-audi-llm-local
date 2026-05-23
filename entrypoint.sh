#!/usr/bin/env bash
# Entrypoint do container do app:
#   1. aguarda o Ollama responder e garante os modelos (LLM + embeddings);
#   2. roda a ingestão se o índice FAISS ainda não existe;
#   3. inicia a API FastAPI.
#
# A espera/pull é feita em Python (wait_ollama.py) para não depender do `curl`,
# que não vem na imagem python:slim.
set -euo pipefail

# 1. Espera o Ollama e garante os modelos.
python wait_ollama.py

# 2. Ingestão: o próprio ingest.py decide se há trabalho a fazer (não recria
#    se o índice já existir). Idempotente — seguro chamar sempre.
python ingest.py

# 3. Sobe a API.
echo "==> Iniciando API em http://0.0.0.0:8000"
exec uvicorn api:app --host 0.0.0.0 --port 8000
