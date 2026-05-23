# syntax=docker/dockerfile:1

# ---------- Stage 1: build do frontend (React + Vite) ----------
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build          # gera /web/dist

# ---------- Stage 2: runtime Python (API + estáticos) ----------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências Python primeiro (melhor cache de camadas)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Código do backend, documentos e build do front
COPY *.py ./
COPY docs/ ./docs/
COPY --from=web /web/dist ./web/dist
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Healthcheck simples no catálogo (não depende do LLM)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/catalog')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
