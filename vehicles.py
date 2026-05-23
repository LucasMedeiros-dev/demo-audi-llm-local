"""
Lista de veículos cobertos pelos boletins técnicos (recalls) em ./docs.

Fonte da verdade para a checagem rápida "o veículo está no recall?".
Extraída diretamente dos PDFs reais da pasta docs/. O match é por
**modelo + ano**: o mesmo modelo pode aparecer em anos/boletins diferentes,
então o ano define se há (e qual) boletim aplicável.

Match híbrido: esta lista decide o sim/não imediato; o RAG (embed.py)
responde os detalhes técnicos a partir do conteúdo dos PDFs.
"""

# Documento -> descrição curta (mostrado no "cheat sheet" da barra lateral)
DOCUMENTS = {
    "MC-10124507-9999.pdf": (
        "Audi RS5 (2013) — Ruído/chiado no freio dianteiro (TSB 46 Brake noise)"
    ),
    "MC-10245688-0001.pdf": (
        "Audi pre sense / frenagem automática (MLB) — "
        "diversos modelos 2017–2025 (TSB 90)"
    ),
}

# Cada entrada: modelo -> lista de coberturas
# {"anos": [(ini, fim), ...], "doc": arquivo}
# "anos" são faixas inclusivas. Modelos normalizados em minúsculas.
_PRESENSE = "MC-10245688-0001.pdf"
_BRAKE = "MC-10124507-9999.pdf"

VEHICLES = {
    # --- MC-10124507-9999.pdf : ruído de freio (2013) ---
    #     RS5 também aparece no boletim de pre sense (anos diferentes).
    "rs5": [
        {"anos": [(2013, 2013)], "doc": _BRAKE},
        {"anos": [(2018, 2019), (2021, 2025)], "doc": _PRESENSE},
    ],
    "rs5 cabriolet": [{"anos": [(2013, 2013)], "doc": _BRAKE}],

    # --- MC-10245688-0001.pdf : Audi pre sense / frenagem ---
    "a4": [{"anos": [(2017, 2025)], "doc": _PRESENSE}],
    "a4 allroad": [{"anos": [(2017, 2025)], "doc": _PRESENSE}],
    "q7": [{"anos": [(2017, 2025)], "doc": _PRESENSE}],
    "s4": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "a5": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "a5 cabriolet": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "a5 sportback": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "s5": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "s5 cabriolet": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "s5 sportback": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "q5": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "sq5": [{"anos": [(2018, 2025)], "doc": _PRESENSE}],
    "a6": [{"anos": [(2019, 2025)], "doc": _PRESENSE}],
    "a7": [{"anos": [(2019, 2025)], "doc": _PRESENSE}],
    "a8": [{"anos": [(2019, 2025)], "doc": _PRESENSE}],
    "q8": [{"anos": [(2019, 2025)], "doc": _PRESENSE}],
    "rs5 sportback": [{"anos": [(2019, 2019), (2021, 2025)], "doc": _PRESENSE}],
    "e-tron quattro": [{"anos": [(2019, 2019), (2021, 2025)], "doc": _PRESENSE}],
    "s6": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "a6 allroad": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "s7": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "s8": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "e-tron sportback quattro": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "q5 e quattro": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "sq7": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "sq8": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "rs q8": [{"anos": [(2020, 2025)], "doc": _PRESENSE}],
    "a8 e quattro": [{"anos": [(2020, 2021)], "doc": _PRESENSE}],
    "rs6 avant": [{"anos": [(2021, 2025)], "doc": _PRESENSE}],
    "rs7": [{"anos": [(2021, 2025)], "doc": _PRESENSE}],
    "q5 sportback": [{"anos": [(2021, 2025)], "doc": _PRESENSE}],
    "sq5 sportback": [{"anos": [(2021, 2025)], "doc": _PRESENSE}],
    "a7 e quattro": [{"anos": [(2021, 2022)], "doc": _PRESENSE}],
    "e-tron s": [{"anos": [(2022, 2025)], "doc": _PRESENSE}],
    "e-tron gt": [{"anos": [(2022, 2025)], "doc": _PRESENSE}],
    "rs e-tron gt": [{"anos": [(2022, 2025)], "doc": _PRESENSE}],
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _anos_str(faixas) -> str:
    """Formata faixas de anos como '2018-2019, 2021-2025' (ou '2013')."""
    return ", ".join(
        f"{a}" if a == b else f"{a}-{b}" for a, b in faixas
    )


def match_model(modelo: str):
    """
    Resolve o nome do modelo digitado para uma chave de VEHICLES.

    Prioriza match exato; depois, entre os modelos cujo nome é substring da
    entrada (ex.: 'audi rs5 sportback'), escolhe o NOME MAIS LONGO — o mais
    específico. Não usa 'entrada in modelo' para evitar que 'rs5' case com
    'rs5 sportback' ou 'q5 sportback' com 'sq5 sportback'.
    """
    m = _normalize(modelo)
    if not m:
        return None
    if m in VEHICLES:
        return m

    candidatos = [k for k in VEHICLES if k in m]
    if not candidatos:
        return None
    return max(candidatos, key=len)


def find_vehicle(modelo: str, ano: int):
    """
    Verifica se (modelo, ano) está coberto por algum recall.

    Retorna dict com {modelo, anos, docs} se coberto; caso contrário None.
    Se o modelo existe mas o ano está fora de todas as faixas, retorna None
    (modelo certo, ano fora da faixa = sem boletim aplicável).
    """
    chave = match_model(modelo)
    if chave is None:
        return None

    docs, faixas = [], []
    for cobertura in VEHICLES[chave]:
        if any(ini <= ano <= fim for ini, fim in cobertura["anos"]):
            docs.append(cobertura["doc"])
            faixas.extend(cobertura["anos"])

    if not docs:
        return None
    return {"modelo": chave, "anos": _anos_str(sorted(set(faixas))), "docs": docs}


def list_models():
    """Lista legível de 'MODELO (anos)' para exibir na barra lateral."""
    linhas = []
    for modelo, coberturas in VEHICLES.items():
        todas = [f for c in coberturas for f in c["anos"]]
        linhas.append(f"{modelo.upper()} ({_anos_str(sorted(set(todas)))})")
    return linhas
