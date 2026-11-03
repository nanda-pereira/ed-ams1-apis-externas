"""
dashboard de atividade legislativa - câmara dos deputados

desafio 1: ranking dos deputados que mais apresentaram proposições sobre um tema
desafio 2: heatmap de participação em votações por partido ao longo dos meses
"""

import json
import time
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import requests
import seaborn as sns

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}

PASTA_SAIDAS = Path(__file__).resolve().parent.parent / "saidas"
PASTA_SAIDAS.mkdir(exist_ok=True)
CACHE_AUTORES = PASTA_SAIDAS / "cache_autores.json"


# ---------------------------------------------------------------------------
# acesso à api da câmara dos deputados

def requisitar(endpoint, params=None, tentativas=4):
    """GET na API; tenta de novo em caso de limite de taxa (429) ou erro de servidor."""
    for tentativa in range(tentativas):
        try:
            r = requests.get(f"{BASE_URL}/{endpoint}", params=params,
                             headers=HEADERS, timeout=30)
        except requests.RequestException as erro:
            print("Erro de conexão:", erro)
            time.sleep(2 ** tentativa)
            continue

        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** tentativa)  # espera 1s, 2s, 4s, 8s
            continue

        print(f"Erro {r.status_code} em {endpoint}: {r.text[:150]}")
        return None
    return None


def buscar_todas_paginas(endpoint, params=None, max_paginas=3, itens=100):
    """Percorre a paginação até acabar o link 'next' ou atingir max_paginas."""
    params = dict(params or {})
    params["itens"] = itens
    resultados = []

    for pagina in range(1, max_paginas + 1):
        params["pagina"] = pagina
        corpo = requisitar(endpoint, params)
        if not corpo:
            break
        resultados += corpo["dados"]

        tem_proxima = any(l["rel"] == "next" for l in corpo.get("links", []))
        if not tem_proxima:
            break
        time.sleep(0.3)
    return resultados

# ---------------------------------------------------------------------------
# desafio 1: ranking de deputados por tema

def proposicoes_por_tema(tema, ano, tipo="PL", max_paginas=3):
    return buscar_todas_paginas("proposicoes", {
        "keywords": tema,
        "ano": ano,
        "siglaTipo": tipo,
        "ordem": "DESC",
        "ordenarPor": "id",
    }, max_paginas)


def ranking_deputados(proposicoes):
    """Conta em quantas proposições cada deputado aparece como autor."""
    cache = {}
    if CACHE_AUTORES.exists():
        cache = json.loads(CACHE_AUTORES.read_text(encoding="utf-8"))

    contagem = Counter()
    for i, prop in enumerate(proposicoes, 1):
        chave = str(prop["id"])
        if chave not in cache:
            corpo = requisitar(f"proposicoes/{chave}/autores")
            cache[chave] = corpo["dados"] if corpo else []
            time.sleep(0.2)

        for autor in cache[chave]:
            # autores também podem ser comissões, o Executivo, etc.
            if "/deputados/" in (autor.get("uri") or ""):
                contagem[autor["nome"]] += 1

        if i % 25 == 0:
            print(f"  {i}/{len(proposicoes)} proposições processadas")

    CACHE_AUTORES.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    df = pd.DataFrame(contagem.items(), columns=["deputado", "proposicoes"])
    return df.sort_values("proposicoes", ascending=False).reset_index(drop=True)


def grafico_ranking(df, tema, ano, top=10):
    topo = df.head(top)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=topo, y="deputado", x="proposicoes", orient="h", color="#2a9d8f")
    plt.title(f"Deputados com mais proposições sobre '{tema}' em {ano}")
    plt.xlabel("Proposições apresentadas")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(PASTA_SAIDAS / f"ranking_{tema}_{ano}.png", dpi=200)
    plt.show()