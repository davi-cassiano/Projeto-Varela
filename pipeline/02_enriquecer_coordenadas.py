"""
02_enriquecer_coordenadas.py

A base do Banco Central traz endereço, bairro, CEP e código IBGE do
município, mas nenhuma coordenada. Este script resolve isso em três
níveis de precisão, do mais fino para o mais grosso:

    bairro         cruzamento de município + bairro com a base pública
    bairro_aprox   mesmo cruzamento, com correspondência aproximada para
                   absorver as abreviações do cadastro do Bacen
    municipio      centróide do município pelo código IBGE, com cobertura
                   garantida

A coluna 'precisao' registra qual nível foi usado em cada agência, e o
produto exibe isso na interface em vez de fingir precisão uniforme.

VALIDAÇÃO DE SANIDADE
A base pública de bairros tem colisão de nomes: o bairro Mirandópolis,
na capital paulista, recebe as coordenadas da CIDADE de Mirandópolis, a
530 km de distância. Qualquer coordenada de bairro que caia a mais de
DESVIO_MAX_KM do centróide do próprio município é descartada.

Uso:
    python pipeline/02_enriquecer_coordenadas.py

Entrada:  dados/brutos/base_consolidada_roteirizacao.xlsx
Saída:    dados/agencias_enriquecidas.csv
"""

import difflib
import math
import re
import unicodedata

import pandas as pd

INSTITUICAO = "ITA"      # casa com ITAU e ITAÚ
DESVIO_MAX_KM = 30.0
ENTRADA = "dados/brutos/base_consolidada_roteirizacao.xlsx"
SAIDA = "dados/agencias_enriquecidas.csv"

ABREVIACOES = [
    (r"^S\.?\s*", "SAO "),
    (r"^STA\.?\s+", "SANTA "),
    (r"^STO\.?\s+", "SANTO "),
    (r"^V\.?\s*", "VILA "),
    (r"^JD\.?\s*", "JARDIM "),
    (r"^PQ\.?\s*", "PARQUE "),
    (r"^PQE\.?\s*", "PARQUE "),
    (r"^CH\.?\s*", "CHACARA "),
    (r"^CID\.?\s*", "CIDADE "),
    (r"^CJ\.?\s*", "CONJUNTO "),
    (r"^PR\.?\s*", "PRAIA "),
    (r"^B\.?\s+VISTA", "BOA VISTA"),
    (r"^N\.?\s*SRA\.?\s*", "NOSSA SENHORA "),
    (r"^PRES\.?\s*", "PRESIDENTE "),
    (r"^ENG\.?\s*", "ENGENHEIRO "),
    (r"^PROF\.?\s*", "PROFESSOR "),
    (r"^DR\.?\s+", "DOUTOR "),
    (r"^AL\.?\s+", "ALAMEDA "),
]


def norm(texto):
    t = str(texto or "").strip().upper()
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Z0-9\s\.]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for padrao, troca in ABREVIACOES:
        t = re.sub(padrao, troca, t)
    return re.sub(r"\s+", " ", t.replace(".", " ")).strip()


def dist_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def main():
    df = pd.read_excel(ENTRADA, sheet_name="Agencias_Geocodificadas")
    ag = df[df["nome_instituicao"].str.contains(INSTITUICAO, na=False)]
    ag = ag.copy().reset_index(drop=True)

    bai = pd.read_csv("dados/bairros.csv", sep=";", quotechar='"')
    bai["mun_n"] = bai["municipio"].map(norm)
    bai["bai_n"] = bai["bairro"].map(norm)
    bai = bai.drop_duplicates(subset=["uf", "mun_n", "bai_n"])

    indice = {(r.uf, r.mun_n, r.bai_n): (r.latitude, r.longitude) for r in bai.itertuples()}
    por_municipio = {}
    for r in bai.itertuples():
        por_municipio.setdefault((r.uf, r.mun_n), []).append(r.bai_n)

    lats, lons, precisoes = [], [], []
    descartadas = 0

    for a in ag.itertuples():
        chave = (a.uf, norm(a.municipio))
        bairro = norm(a.bairro)

        coord = indice.get((a.uf, chave[1], bairro))
        precisao = "bairro"

        if coord is None and bairro and chave in por_municipio:
            perto = difflib.get_close_matches(bairro, por_municipio[chave], n=1, cutoff=0.82)
            if perto:
                coord = indice.get((a.uf, chave[1], perto[0]))
                precisao = "bairro_aprox"

        if coord is not None:
            if dist_km(a.latitude, a.longitude, coord[0], coord[1]) > DESVIO_MAX_KM:
                coord = None
                descartadas += 1

        if coord is None:
            coord = (a.latitude, a.longitude)
            precisao = "municipio"

        lats.append(coord[0])
        lons.append(coord[1])
        precisoes.append(precisao)

    ag["lat"], ag["lon"], ag["precisao"] = lats, lons, precisoes
    ag.to_csv(SAIDA, index=False)

    print(f"{len(ag)} agências processadas\n")
    print("Cobertura por nível de precisão:")
    for nivel, qtd in ag["precisao"].value_counts().items():
        print(f"  {nivel:14s} {qtd:5d}  ({qtd / len(ag) * 100:5.1f}%)")
    print(f"\nCoordenadas descartadas por desvio acima de {DESVIO_MAX_KM:.0f} km: {descartadas}")
    print(f"Pontos distintos no mapa: {ag[['lat', 'lon']].drop_duplicates().shape[0]}"
          f"  (antes: {ag['municipio'].nunique()})")
    print(f"\nGravado: {SAIDA}")


if __name__ == "__main__":
    main()
