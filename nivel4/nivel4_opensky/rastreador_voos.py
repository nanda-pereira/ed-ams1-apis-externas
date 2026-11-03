"""
rastreador de Voos - opensky network

desafio 1: mapa interativo das aeronaves sobre o Brasil, com filtro por categoria
desafio 2: trajetória de uma aeronave a partir do ICAO24
"""

import os
import time
import webbrowser
from pathlib import Path

import folium
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://opensky-network.org/api"
TOKEN_URL = ("https://auth.opensky-network.org/auth/realms/opensky-network"
             "/protocol/openid-connect/token")

# caixa geográfica aproximada do Brasil
BRASIL = {"lamin": -34.0, "lomin": -74.0, "lamax": 6.0, "lomax": -34.0}

COLUNAS = ["icao24", "callsign", "pais_origem", "tempo_posicao", "ultimo_contato",
           "longitude", "latitude", "altitude_baro", "no_solo", "velocidade",
           "rumo", "taxa_vertical", "sensores", "altitude_geo", "squawk",
           "spi", "fonte_posicao", "categoria"]

# opção do menu -> (nome, categorias aceitas; None = todas)
FILTROS = {
    "1": ("Helicópteros", {8}),
    "2": ("Comerciais (pequeno a pesado)", {3, 4, 5, 6}),
    "3": ("Aeronaves leves", {2}),
    "4": ("Todas", None),
}
CORES = {8: "red", 3: "blue", 4: "blue", 5: "blue", 6: "blue", 2: "green"}

PASTA_SAIDAS = Path(__file__).resolve().parent.parent / "saidas"
PASTA_SAIDAS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# autenticação (opcional)

def obter_cabecalhos():
    """Pega um token OAuth2 se houver credenciais no .env; senão, acesso anônimo."""
    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
    if not (client_id and client_secret):
        print("Sem credenciais: usando acesso anônimo (limite menor).")
        return {}

    resposta = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }, timeout=20)

    if resposta.status_code != 200:
        print("Falha ao obter token, seguindo como anônimo:", resposta.status_code)
        return {}
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


# ---------------------------------------------------------------------------
# desafio 1: aeronaves sobre o Brasil

def buscar_aeronaves(cabecalhos):
    params = {**BRASIL, "extended": 1}
    r = requests.get(f"{BASE_URL}/states/all", params=params,
                     headers=cabecalhos, timeout=30)
    if r.status_code != 200:
        print("Erro", r.status_code, r.text[:200])
        return pd.DataFrame(columns=COLUNAS)

    estados = r.json().get("states") or []
    df = pd.DataFrame(estados)
    if df.empty:
        return pd.DataFrame(columns=COLUNAS)

    df.columns = COLUNAS[:df.shape[1]]
    df["callsign"] = df["callsign"].str.strip()
    return df.dropna(subset=["latitude", "longitude"])
