"""
Espera o Ollama responder e garante que os modelos necessários existem.

Usado pelo entrypoint do container. Implementado em Python (stdlib) para não
depender do `curl`, que não vem na imagem python:slim.

    python wait_ollama.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/")
MODELS = [
    os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
    os.getenv("OLLAMA_EMBED_MODEL", "bge-m3"),
]


def wait_until_up(timeout: int = 600, interval: int = 3) -> None:
    """Bloqueia até /api/tags responder, ou aborta após `timeout` segundos."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/api/tags", timeout=5)
            print(f"==> Ollama disponível em {BASE_URL}")
            return
        except (urllib.error.URLError, OSError):
            print(f"    ...Ollama indisponível em {BASE_URL}, nova tentativa em {interval}s")
            time.sleep(interval)
    sys.exit(f"ERRO: Ollama não respondeu em {BASE_URL} após {timeout}s.")


def ensure_model(model: str) -> None:
    """Dispara o pull do modelo (no-op no Ollama se já estiver presente)."""
    print(f"==> Garantindo modelo: {model}")
    req = urllib.request.Request(
        f"{BASE_URL}/api/pull",
        data=json.dumps({"name": model}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        # O pull faz streaming do progresso; basta consumir até o fim.
        with urllib.request.urlopen(req, timeout=1800) as resp:
            for _ in resp:
                pass
    except (urllib.error.URLError, OSError) as e:
        print(f"    aviso: não foi possível puxar {model} automaticamente ({e}).")


if __name__ == "__main__":
    wait_until_up()
    for m in MODELS:
        ensure_model(m)
