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


def formatar(valor, sufixo=""):
    return "n/d" if pd.isna(valor) else f"{round(valor)}{sufixo}"


def desenhar_mapa(df, titulo, arquivo):
    mapa = folium.Map(location=[-14.2, -51.9], zoom_start=4, tiles="CartoDB positron")

    for _, a in df.iterrows():
        texto = (f"<b>{a['callsign'] or 'sem indicativo'}</b><br>"
                 f"ICAO24: {a['icao24']}<br>"
                 f"Altitude: {formatar(a['altitude_baro'], ' m')}<br>"
                 f"Velocidade: {formatar(a['velocidade'], ' m/s')}")
        folium.CircleMarker(
            location=[a["latitude"], a["longitude"]],   # folium: latitude primeiro
            radius=4,
            color=CORES.get(a["categoria"], "gray"),
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(texto, max_width=250),
        ).add_to(mapa)

    mapa.get_root().html.add_child(folium.Element(
        f"<h3 style='position:fixed;top:10px;left:60px;z-index:9999;"
        f"background:white;padding:6px 12px;border-radius:6px'>{titulo}</h3>"))
    mapa.save(arquivo)
    webbrowser.open(arquivo.as_uri())

def desafio_1(cabecalhos):
    print("\nFiltro de categoria:")
    for chave, (nome, _) in FILTROS.items():
        print(f"  {chave} - {nome}")
    escolha = input("Opção [4]: ").strip() or "4"
    nome, categorias = FILTROS.get(escolha, FILTROS["4"])

    df = buscar_aeronaves(cabecalhos)
    print(len(df), "aeronaves com posição no momento")
    if df.empty:
        return

    if categorias is not None:
        df = df[df["categoria"].isin(categorias)]
    print(len(df), "após o filtro:", nome)

    print(df[["icao24", "callsign", "categoria", "altitude_baro"]].head(10).to_string(index=False))
    desenhar_mapa(df, f"Aeronaves sobre o Brasil: {nome}", PASTA_SAIDAS / "mapa_brasil.html")

# ---------------------------------------------------------------------------
# desafio 2: trajetória de uma aeronave

def buscar_trajetoria(icao24, cabecalhos):
    """Endpoint experimental /tracks. Retorna lista de [lat, lon] ou None."""
    r = requests.get(f"{BASE_URL}/tracks",
                     params={"icao24": icao24.lower(), "time": 0},
                     headers=cabecalhos, timeout=30)
    if r.status_code != 200:
        print("/tracks indisponível:", r.status_code)
        return None

    caminho = r.json().get("path") or []
    # cada ponto: [tempo, latitude, longitude, altitude, rumo, no_solo]
    return [[p[1], p[2]] for p in caminho if p[1] is not None and p[2] is not None]


def coletar_trajetoria_manual(icao24, cabecalhos, amostras=12, intervalo=15):
    """Plano B: consulta a posição várias vezes e monta a trilha."""
    print(f"Coletando {amostras} posições a cada {intervalo}s...")
    pontos = []
    for _ in range(amostras):
        r = requests.get(f"{BASE_URL}/states/all", params={"icao24": icao24.lower()},
                         headers=cabecalhos, timeout=30)
        estados = (r.json().get("states") or []) if r.status_code == 200 else []
        if estados and estados[0][5] is not None:
            pontos.append([estados[0][6], estados[0][5]])   # [latitude, longitude]
        time.sleep(intervalo)
    return pontos


def desenhar_trajetoria(pontos, icao24):
    mapa = folium.Map(location=pontos[0], zoom_start=6, tiles="CartoDB positron")
    folium.PolyLine(pontos, color="#e76f51", weight=4, opacity=0.85).add_to(mapa)
    folium.Marker(pontos[0], tooltip="Início", icon=folium.Icon(color="green")).add_to(mapa)
    folium.Marker(pontos[-1], tooltip="Posição mais recente", icon=folium.Icon(color="red")).add_to(mapa)
    mapa.fit_bounds(pontos)

    arquivo = PASTA_SAIDAS / f"trajetoria_{icao24}.html"
    mapa.save(arquivo)
    webbrowser.open(arquivo.as_uri())


def desafio_2(cabecalhos):
    icao24 = input("ICAO24 da aeronave (veja na tabela do desafio 1): ").strip()
    if not icao24:
        return

    pontos = buscar_trajetoria(icao24, cabecalhos)
    if not pontos:
        pontos = coletar_trajetoria_manual(icao24, cabecalhos)

    if len(pontos) < 2:
        print("Pontos insuficientes. A aeronave precisa estar em voo.")
        return
    print(len(pontos), "pontos na trajetória")
    desenhar_trajetoria(pontos, icao24)


# ---------------------------------------------------------------------------

def main():
    cabecalhos = obter_cabecalhos()
    print("\n1 - Mapa das aeronaves sobre o Brasil")
    print("2 - Trajetória de uma aeronave (ICAO24)")
    opcao = input("Opção [1]: ").strip() or "1"

    if opcao == "2":
        desafio_2(cabecalhos)
    else:
        desafio_1(cabecalhos)


if __name__ == "__main__":
    main()