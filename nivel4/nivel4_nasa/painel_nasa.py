"""
dashboard de Exploração Espacial - NASA Open APIs

desafio 1: dispersão distância da Terra x velocidade relativa de asteroides
desafio 2: dashboard com abas (APOD, exoplanetas por método, eventos EONET)
"""

import html
import os
import webbrowser
from datetime import date, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import requests
import seaborn as sns
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

PASTA_SAIDAS = Path(__file__).resolve().parent.parent / "saidas"
PASTA_SAIDAS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# desafio 1: asteroides próximos (NeoWs)


def buscar_asteroides(inicio, fim):
    """O NeoWs aceita no máximo 7 dias por chamada: divide em janelas."""
    registros = []
    atual = inicio

    while atual <= fim:
        janela_fim = min(atual + timedelta(days=6), fim)
        r = requests.get("https://api.nasa.gov/neo/rest/v1/feed", params={
            "start_date": atual.isoformat(),
            "end_date": janela_fim.isoformat(),
            "api_key": API_KEY,
        }, timeout=30)

        if r.status_code != 200:
            print("Erro NeoWs:", r.status_code, r.text[:150])
            break

        for dia, lista in r.json()["near_earth_objects"].items():
            for neo in lista:
                aproximacao = neo["close_approach_data"][0]
                registros.append({
                    "nome": neo["name"],
                    "data": dia,
                    "diametro_m": neo["estimated_diameter"]["meters"]["estimated_diameter_max"],
                    "distancia_km": float(aproximacao["miss_distance"]["kilometers"]),
                    "velocidade_km_s": float(aproximacao["relative_velocity"]["kilometers_per_second"]),
                    "perigoso": neo["is_potentially_hazardous_asteroid"],
                })
        atual = janela_fim + timedelta(days=1)

    return pd.DataFrame(registros)

