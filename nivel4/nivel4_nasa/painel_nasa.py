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

def grafico_asteroides(df, inicio, fim):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x="distancia_km", y="velocidade_km_s",
                    size="diametro_m", hue="perigoso",
                    sizes=(20, 300), alpha=0.7)
    plt.xscale("log")
    plt.xlabel("Distância da Terra (km, escala log)")
    plt.ylabel("Velocidade relativa (km/s)")
    plt.title(f"Asteroides próximos: {inicio} a {fim}")
    plt.tight_layout()
    plt.savefig(PASTA_SAIDAS / "asteroides.png", dpi=200)
    plt.show()

    print("Correlação distância x velocidade:")
    print(df[["distancia_km", "velocidade_km_s"]].corr().round(3))


def desafio_1():
    padrao_fim = date.today()
    padrao_inicio = padrao_fim - timedelta(days=6)
    entrada_ini = input(f"Data inicial AAAA-MM-DD [{padrao_inicio}]: ").strip()
    entrada_fim = input(f"Data final AAAA-MM-DD [{padrao_fim}]: ").strip()

    inicio = date.fromisoformat(entrada_ini) if entrada_ini else padrao_inicio
    fim = date.fromisoformat(entrada_fim) if entrada_fim else padrao_fim

    df = buscar_asteroides(inicio, fim)
    print(len(df), "aproximações encontradas")
    if not df.empty:
        grafico_asteroides(df, inicio, fim)

# ---------------------------------------------------------------------------
# desafio 2: dashboard com abas

def buscar_apod():
    r = requests.get("https://api.nasa.gov/planetary/apod",
                     params={"api_key": API_KEY}, timeout=30)
    return r.json() if r.status_code == 200 else None


def buscar_metodos_exoplanetas():
    """Exoplanet Archive usa TAP: a consulta SQL vai no parâmetro 'query'."""
    consulta = ("select discoverymethod, count(*) as total "
                "from pscomppars group by discoverymethod order by total desc")
    r = requests.get("https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
                     params={"query": consulta, "format": "json"}, timeout=60)
    return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()


def buscar_eventos(dias=2):
    r = requests.get("https://eonet.gsfc.nasa.gov/api/v3/events",
                     params={"days": dias, "status": "all"}, timeout=30)
    if r.status_code != 200:
        return pd.DataFrame()

    linhas = []
    for evento in r.json().get("events", []):
        geo = evento["geometry"][-1]          # posição mais recente
        if geo["type"] != "Point":
            continue
        lon, lat = geo["coordinates"]         # EONET: longitude primeiro
        linhas.append({
            "titulo": evento["title"],
            "categoria": evento["categories"][0]["title"],
            "data": geo["date"],
            "lat": lat,
            "lon": lon,
        })
    return pd.DataFrame(linhas)


def bloco_apod(apod):
    if not apod:
        return "<p>APOD indisponível no momento.</p>"
    if apod.get("media_type") == "image":
        midia = f'<img src="{apod["url"]}" alt="APOD" style="max-width:100%;border-radius:8px">'
    else:
        midia = f'<p><a href="{apod["url"]}" target="_blank">Abrir vídeo do dia</a></p>'
    return (f"<h2>{html.escape(apod.get('title', ''))}</h2>"
            f"<p><i>{apod.get('date', '')}</i></p>{midia}"
            f"<p>{html.escape(apod.get('explanation', ''))}</p>")


def montar_dashboard(apod, df_exo, df_eventos, arquivo):
    figuras = {}

    if not df_exo.empty:
        fig = px.bar(df_exo, x="total", y="discoverymethod", orientation="h",
                     labels={"total": "Exoplanetas confirmados",
                             "discoverymethod": "Método de descoberta"},
                     title="Exoplanetas por método de descoberta")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        figuras["Exoplanetas"] = fig

    if not df_eventos.empty:
        figuras["Eventos naturais"] = px.scatter_geo(
            df_eventos, lat="lat", lon="lon", color="categoria",
            hover_name="titulo", hover_data=["data"],
            projection="natural earth",
            title="Eventos naturais das últimas 48 horas (EONET)")

    abas = {"APOD": bloco_apod(apod)}
    for i, (nome, fig) in enumerate(figuras.items()):
        abas[nome] = fig.to_html(full_html=False,
                                 include_plotlyjs="cdn" if i == 0 else False)

    botoes = "".join(f'<button onclick="mostrar({i})">{nome}</button>'
                     for i, nome in enumerate(abas))
    paineis = "".join(f'<section class="aba">{conteudo}</section>'
                      for conteudo in abas.values())

    pagina = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Exploração Espacial</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 1000px; margin: 0 auto; padding: 24px; }}
  nav button {{ padding: 10px 18px; margin-right: 6px; border: 1px solid #ccc;
                background: #fff; border-radius: 8px; cursor: pointer; }}
  nav button.ativo {{ background: #111; color: #fff; }}
  .aba {{ display: none; padding-top: 16px; }}
</style></head>
<body>
  <h1>Exploração Espacial</h1>
  <nav>{botoes}</nav>
  {paineis}
<script>
  function mostrar(i) {{
    document.querySelectorAll('.aba').forEach((a, j) => a.style.display = i === j ? 'block' : 'none');
    document.querySelectorAll('nav button').forEach((b, j) => b.classList.toggle('ativo', i === j));
    window.dispatchEvent(new Event('resize'));
  }}
  mostrar(0);
</script></body></html>"""

    arquivo.write_text(pagina, encoding="utf-8")
    webbrowser.open(arquivo.as_uri())


def desafio_2():
    print("Buscando APOD, exoplanetas e eventos naturais...")
    montar_dashboard(buscar_apod(), buscar_metodos_exoplanetas(),
                     buscar_eventos(2), PASTA_SAIDAS / "dashboard_nasa.html")


# ---------------------------------------------------------------------------

def main():
    print("1 - Asteroides: distância x velocidade")
    print("2 - Dashboard com abas")
    opcao = input("Opção [1]: ").strip() or "1"
    if opcao == "2":
        desafio_2()
    else:
        desafio_1()


if __name__ == "__main__":
    main()