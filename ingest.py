"""
Ingestão dos documentos — execute UMA vez antes de subir a API.

    python ingest.py            # cria o índice se não existir
    python ingest.py --rebuild  # recria do zero (use ao trocar os PDFs)

Lê os PDFs de ./docs, gera os embeddings (BGE-M3) e grava o índice FAISS em
./faiss_index. A API apenas CARREGA esse índice — nunca o constrói.
Assim os documentos são embeddados de uma vez aqui, e não a cada pergunta.
"""

import argparse
import os

from embed import DOCS_DIR, INDEX_DIR, build_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestão de PDFs no índice FAISS.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Recria o índice mesmo que já exista.",
    )
    args = parser.parse_args()

    # O índice só "existe" se o arquivo do FAISS estiver presente — não basta
    # o diretório existir (ex.: volume Docker montado mas ainda vazio).
    index_file = os.path.join(INDEX_DIR, "index.faiss")
    if os.path.isfile(index_file) and not args.rebuild:
        print(
            f"Índice já existe em '{INDEX_DIR}/'. "
            "Use --rebuild para recriá-lo. Nada a fazer."
        )
        return

    print(f"Lendo PDFs de '{DOCS_DIR}/' e gerando embeddings (BGE-M3)...")
    vectorstore = build_index()
    n = vectorstore.index.ntotal
    print(f"Pronto: {n} chunks indexados em '{INDEX_DIR}/'.")


if __name__ == "__main__":
    main()
