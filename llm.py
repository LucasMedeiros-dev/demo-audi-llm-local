"""
Setup do LLM local (Ollama).

Mantém num só lugar a configuração do modelo de chat e o prompt usado no RAG.
Trocar de modelo é só mudar OLLAMA_MODEL (ou a variável de ambiente).
"""

import json
import os
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# Modelo de chat servido pelo Ollama. Rode antes:  ollama pull gemma3:4b
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Prompt do assistente. O público é o CONCESSIONÁRIO, não o cliente final.
SYSTEM_PROMPT = """Você é um assistente técnico que apoia CONCESSIONÁRIOS \
autorizados Audi no atendimento de recalls e boletins técnicos (TSB).

Regras:
- Responda SEMPRE em português do Brasil, de forma objetiva e técnica.
- Use APENAS as informações do CONTEXTO abaixo (trechos dos boletins oficiais).
- Se a resposta não estiver no contexto, diga que não há essa informação no \
boletim e oriente o concessionário a consultar a montadora.
- Cite o procedimento, peças e códigos quando estiverem disponíveis.
- O atendimento é referente ao veículo: {veiculo} (cliente: {cliente}).

CONTEXTO:
{context}
"""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)


def get_llm(temperature: float = 0.1) -> ChatOllama:
    """Instancia o modelo de chat local via Ollama."""
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
    )


# ----------------------------------------------------- extração da coleta guiada
_EXTRACT_PROMPT = ChatPromptTemplate.from_template(
    """Extraia os dados do atendimento da mensagem do concessionário.

Campos:
- cliente: nome do cliente (string) ou null
- modelo: modelo do veículo, ex.: "A4", "RS5 Sportback" (string) ou null
- ano: ano do veículo (inteiro de 4 dígitos) ou null

Preencha apenas o que estiver claramente presente. Não invente.
Responda SOMENTE com um objeto JSON, sem texto ao redor.

Mensagem: {texto}
"""
)


def extract_fields(llm: ChatOllama, texto: str) -> dict:
    """
    Usa o LLM para extrair {cliente, modelo, ano} de uma frase em linguagem
    natural. Sempre retorna as três chaves (com None quando ausente).
    """
    vazio = {"cliente": None, "modelo": None, "ano": None}
    try:
        raw = (_EXTRACT_PROMPT | llm).invoke({"texto": texto}).content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return vazio
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError, ValueError):
        return vazio

    cliente = data.get("cliente") or None
    modelo = data.get("modelo") or None
    ano = data.get("ano")
    try:
        ano = int(ano) if ano is not None else None
    except (TypeError, ValueError):
        ano = None
    return {"cliente": cliente, "modelo": modelo, "ano": ano}
