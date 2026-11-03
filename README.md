Projeto desenvolvido em Python para consumo, tratamento e visualização de dados públicos por meio de APIs externas. O projeto foi baseado no desafio de criar aplicações utilizando dados reais, autenticação opcional, paginação, estruturas JSON e visualizações interativas.

## Funcionalidades
O projeto possui três aplicações principais:

### | Dashboard de Atividade Legislativa
Localizado em [`nivel4/nivel4_camara/camara_legislativo.py`](./nivel4/nivel4_camara/camara_legislativo.py).

Utiliza a API de Dados Abertos da Câmara dos Deputados para:
- Buscar proposições por tema e ano;
- Criar um ranking dos deputados que mais apresentaram proposições;
- Consultar votações do plenário;
- Analisar a participação dos partidos ao longo dos meses;
- Gerar gráficos de barras e heatmaps;
- Trabalhar com paginação e dados JSON aninhados;
- Utilizar cache local para reduzir requisições repetidas.

### | Rastreador de Voos em Tempo Real
Localizado em [`nivel4/nivel4_opensky/rastreador_voos.py`](./nivel4/nivel4_opensky/rastreador_voos.py).

Utiliza a OpenSky Network para:
- Consultar aeronaves sobrevoando o Brasil;
- Filtrar aeronaves por categoria;
- Exibir posições em um mapa interativo;
- Consultar a trajetória de uma aeronave pelo código ICAO24;
- Gerar mapas utilizando a biblioteca Folium;
- Utilizar autenticação opcional para a API.

### | Dashboard de Exploração Espacial
Localizado em [`nivel4/nivel4_nasa/painel_nasa.py`](./nivel4/nivel4_nasa/painel_nasa.py).

Utiliza APIs da NASA, da EONET e do Exoplanet Archive para:
- Consultar asteroides próximos da Terra;
- Comparar distância, velocidade e tamanho dos asteroides;
- Exibir a imagem astronômica do dia;
- Analisar exoplanetas por método de descoberta;
- Exibir eventos naturais recentes em um mapa;
- Gerar um dashboard HTML com abas interativas.

## Tecnologias utilizadas
- Python
- Requests
- Pandas
- Matplotlib
- Seaborn
- Plotly
- Folium
- Python-dotenv

## Como baixar & visualizar o projeto
Clone o repositório utilizando o Git:

```bash
git clone https://github.com/nanda-pereira/ed-ams1-apis-externas.git
cd ed-ams1-apis-externas
````

### Configurar o ambiente
Crie um ambiente virtual:

Windows
```
python -m venv venv
venv\Scripts\activate
```
Linux ou macOS
```
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências: 
```
pip install -r requirements.txt
```

### Configuração das APIs
Renomeie o arquivo .env.example para somente .env, removendo o ".example".
Edite o arquivo .env adicionando as suas chaves obtidas nos sites, substituindo os campos: 
````
NASA_API_KEY=sua_chave_da_nasa
OPENSKY_CLIENT_ID=seu_client_id_opcional
OPENSKY_CLIENT_SECRET=seu_client_secret_opcional
````
A API da NASA pode ser utilizada com uma chave gratuita obtida em: https://api.nasa.gov/
A OpenSky pode ser utilizada sem autenticação para consultas básicas. 
As credenciais são opcionais e permitem limites de acesso maiores.

## Como executar
## | Câmara dos Deputados
```
python nivel4/nivel4_camara/camara_legislativo.py
```
O programa solicitará:
- O tema da pesquisa;
- O ano desejado.
Ao final, os gráficos e arquivos gerados serão salvos em: nivel4/saidas/

## | Ratreador de Voos - OpenSky
```
python nivel4/nivel4_opensky/rastreador_voos.py
```
O programa permite escolher entre:
- Visualizar aeronaves sobrevoando o Brasil;
- Consultar a trajetória de uma aeronave utilizando o ICAO24.
Os mapas são gerados em formato HTML dentro da pasta: nivel4/saidas/

## | NASA
```
python nivel4/nivel4_nasa/painel_nasa.py
```
O programa permite escolher entre:
- Gerar um gráfico sobre asteroides próximos da Terra;
- Criar um dashboard com APOD, exoplanetas e eventos naturais.
Os resultados são salvos em: nivel4/saidas/

## Objetivos do projeto
Este projeto foi desenvolvido para praticar:
- Consumo de APIs REST;
- Autenticação opcional;
- Paginação de dados;
- Tratamento de JSON aninhado;
- Organização e análise de dados com Pandas;
- Criação de gráficos estatísticos;
- Criação de mapas interativos;
- Geração de dashboards em HTML;
- Uso de dados públicos reais para análise.

## Fontes dos dados
- [API de Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br/)
- [OpenSky Network](https://opensky-network.org/)
- [NASA Open APIs](https://api.nasa.gov/)
- [NASA EONET](https://eonet.gsfc.nasa.gov/)
- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/)

Desenvolvido por Fernanda & Maria Eduarda
