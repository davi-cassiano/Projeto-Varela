"""
01_baixar_bases.py

Baixa e prepara as bases auxiliares que o projeto usa mas que não vêm
com os datasets principais:

  dados/municipios.csv  coordenadas dos municípios brasileiros, usadas
                        para geocodificar as agências pelo código IBGE
  dados/bairros.csv     coordenadas de bairros, para refinar a precisão
  dados/estados.json    contorno simplificado dos 27 estados, base
                        cartográfica do mapa do produto
  dados/cidades.json    cidades para rotular o mapa no zoom próximo

Uso:
    python pipeline/01_baixar_bases.py

Requer conexão com a internet apenas nesta etapa. Depois de executada,
todo o restante do pipeline e o produto final funcionam offline.
"""

import json
import os

import pandas as pd
import requests

DESTINO = "dados"

FONTES = {
    "municipios.csv":
        "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv",
    "bairros.csv":
        "https://raw.githubusercontent.com/alanwillms/geoinfo/master/latitude-longitude-bairros.csv",
    "uf.geojson":
        "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson",
}

UF_POR_CODIGO = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP", 41: "PR",
    42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def baixar():
    os.makedirs(DESTINO, exist_ok=True)
    for nome, url in FONTES.items():
        caminho = os.path.join(DESTINO, nome)
        if os.path.exists(caminho):
            print(f"  {nome} já existe, pulando")
            continue
        print(f"  baixando {nome}...")
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        with open(caminho, "wb") as f:
            f.write(r.content)
        print(f"  {nome}: {len(r.content) / 1024:.0f} KB")


def simplificar_estados():
    """
    O GeoJSON original tem 3,4 MB, inviável de embutir no HTML. A
    simplificação reduz para cerca de 60 KB, o que é mais que suficiente
    na escala em que o mapa é usado, e descarta ilhas minúsculas que só
    poluiriam a visualização.
    """
    from shapely.geometry import shape
    from shapely.ops import unary_union

    d = json.load(open(os.path.join(DESTINO, "uf.geojson"), encoding="utf-8"))
    saida = []

    for f in d["features"]:
        g = shape(f["geometry"])
        if g.geom_type == "MultiPolygon":
            partes = [p for p in g.geoms if p.area > 0.02]
            if not partes:
                partes = [max(g.geoms, key=lambda p: p.area)]
            g = unary_union(partes)

        s = g.simplify(0.035, preserve_topology=True)
        geoms = s.geoms if s.geom_type == "MultiPolygon" else [s]
        aneis = [
            [[round(x, 3), round(y, 3)] for x, y in p.exterior.coords]
            for p in geoms
        ]
        c = g.representative_point()
        saida.append({
            "uf": f["properties"]["sigla"],
            "nome": f["properties"]["name"],
            "aneis": aneis,
            "centro": [round(c.x, 3), round(c.y, 3)],
        })

    caminho = os.path.join(DESTINO, "estados.json")
    json.dump(saida, open(caminho, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    pontos = sum(len(a) for e in saida for a in e["aneis"])
    print(f"  estados.json: {len(saida)} estados, {pontos} pontos, "
          f"{os.path.getsize(caminho) / 1024:.0f} KB")


def preparar_cidades():
    """Lista compacta para rotular o mapa: nome, UF, latitude, longitude, capital."""
    m = pd.read_csv(os.path.join(DESTINO, "municipios.csv"))
    cidades = [
        [r.nome, UF_POR_CODIGO.get(r.codigo_uf, ""),
         round(r.latitude, 3), round(r.longitude, 3), int(r.capital)]
        for r in m.itertuples()
    ]
    caminho = os.path.join(DESTINO, "cidades.json")
    json.dump(cidades, open(caminho, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"  cidades.json: {len(cidades)} cidades, "
          f"{os.path.getsize(caminho) / 1024:.0f} KB")


if __name__ == "__main__":
    print("Baixando bases auxiliares")
    baixar()
    print("\nPreparando geometria")
    simplificar_estados()
    preparar_cidades()
    print("\nPronto. As próximas etapas do pipeline rodam offline.")
