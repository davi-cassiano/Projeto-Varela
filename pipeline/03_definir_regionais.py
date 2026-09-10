"""
Define as regionais a partir das coordenadas das agencias.

Duas regras, nesta ordem:

  1. TETO   - proximidade geografica (k-means), subdividindo recursivamente
              qualquer grupo que passe do numero maximo de agencias.
  2. PISO   - grupos pequenos demais para serem uma regional sao absorvidos
              pela regional vizinha mais proxima que ainda tenha espaco.

O k-means sozinho nao sabe quantas agencias cabem numa agenda de visitas.
Por isso o teto e o piso sao parametros de produto, ajustaveis aqui.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

MAX_AGENCIAS = 40   # teto: acima disso a regional e subdividida
MIN_AGENCIAS = 4    # piso: abaixo disso a regional e absorvida pela vizinha

R_TERRA = 6371.0


def dist_matriz(pontos):
    P = np.radians(pontos)
    la, lo = P[:, 0:1], P[:, 1:2]
    a = (
        np.sin((la - la.T) / 2) ** 2
        + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2
    )
    return 2 * R_TERRA * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def extensao_km(g):
    pts = g[["lat", "lon"]].drop_duplicates().values
    return 0.0 if len(pts) < 2 else float(dist_matriz(pts).max())


def fatiar(ag, idx):
    """
    Ultimo recurso: o grupo passa do teto mas todas as agencias estao na
    mesma coordenada, entao nao ha eixo geografico para cortar. Divide em
    fatias de tamanho igual por codigo da agencia. E o que um banco faz na
    pratica numa praca densa: reparte por carteira, nao por geografia.
    """
    ordenado = list(ag.loc[idx].sort_values("cod_compe_ag").index)
    n = int(np.ceil(len(ordenado) / MAX_AGENCIAS))
    return [pd.Index(fatia) for fatia in np.array_split(ordenado, n)]


def dividir(ag, idx):
    """Subdivide recursivamente ate ninguem passar do teto."""
    g = ag.loc[idx]
    pontos_distintos = g[["lat", "lon"]].drop_duplicates().shape[0]

    if len(g) <= MAX_AGENCIAS:
        return [idx]

    # Cidades onde todas as agencias tem a mesma coordenada nao podem ser
    # separadas no espaco.
    if pontos_distintos < 2:
        return fatiar(ag, idx)

    k = min(int(np.ceil(len(g) / MAX_AGENCIAS)), pontos_distintos)
    rotulos = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(
        g[["lat", "lon"]].values
    )

    saida = []
    for c in range(k):
        sub = g.index[rotulos == c]
        if len(sub) == len(g):          # k-means nao separou nada
            return fatiar(ag, idx)
        saida += dividir(ag, sub)
    return saida


def absorver_pequenas(ag, grupos):
    """Funde grupos abaixo do piso na regional vizinha mais proxima."""
    grupos = [list(g) for g in grupos]

    while True:
        tamanhos = [len(g) for g in grupos]
        pequenas = [i for i, n in enumerate(tamanhos) if n < MIN_AGENCIAS]
        if not pequenas:
            break

        centros = np.array(
            [ag.loc[g, ["lat", "lon"]].mean().values for g in grupos]
        )
        dists = dist_matriz(centros)
        np.fill_diagonal(dists, np.inf)

        # comeca pela menor de todas, para as fusoes ficarem estaveis
        i = min(pequenas, key=lambda x: tamanhos[x])

        candidatos = [
            j
            for j in np.argsort(dists[i])
            if j != i and tamanhos[j] + tamanhos[i] <= MAX_AGENCIAS
        ]
        if not candidatos:
            # Nenhuma vizinha com espaco: manter separada e melhor do que
            # furar o teto que acabamos de estabelecer.
            break

        j = int(candidatos[0])
        grupos[j] = grupos[j] + grupos[i]
        grupos.pop(i)

    return grupos


def nomear(ag, grupo):
    """A regional herda o nome da cidade com mais agencias no grupo."""
    g = ag.loc[grupo]
    polo = g["municipio_nome"].value_counts().index[0]
    ufs = g["uf"].value_counts()
    return polo, list(ufs.index)


def desambiguar(ag, grupos, nomes):
    """
    Varias regionais podem cair na mesma cidade-polo: a capital sozinha
    gera oito. Como o nome vira um seletor na interface, precisa ser unico.

    Tenta, em ordem: a segunda cidade do grupo ('Sao Paulo / Osasco'), o
    bairro predominante ('Sao Paulo / Itaim Bibi') e, por fim, um numero.
    """
    por_polo = {}
    for i, nome in nomes.items():
        por_polo.setdefault(nome, []).append(i)

    finais = dict(nomes)

    for polo, ids in por_polo.items():
        if len(ids) == 1:
            continue

        usados = set()
        for i in ids:
            g = ag.loc[grupos[i]]

            alternativas = list(g["municipio_nome"].value_counts().index[1:])
            alternativas += [
                str(b).title() for b in g["bairro"].value_counts().index[:5]
            ]

            escolhido = next(
                (a for a in alternativas if a and a != polo and a not in usados), None
            )
            if escolhido:
                usados.add(escolhido)
                finais[i] = f"{polo} / {escolhido}"

    # rede de seguranca: se ainda houver empate, numera
    contagem = {}
    for i in sorted(finais):
        nome = finais[i]
        contagem[nome] = contagem.get(nome, 0) + 1
        if contagem[nome] > 1:
            finais[i] = f"{nome} {contagem[nome]}"

    return finais


def main():
    ag = pd.read_csv("dados/agencias_enriquecidas.csv").reset_index(drop=True)

    # grafia correta do municipio (a base do Bacen e maiuscula e sem acento)
    mun = pd.read_csv("dados/municipios.csv")[["codigo_ibge", "nome"]]
    ag = ag.merge(
        mun.rename(columns={"nome": "municipio_nome"}),
        left_on="municipio_ibge",
        right_on="codigo_ibge",
        how="left",
    )
    ag["municipio_nome"] = ag["municipio_nome"].fillna(ag["municipio"].str.title())

    grupos = dividir(ag, ag.index)
    grupos = absorver_pequenas(ag, grupos)

    ag["regional_id"] = -1
    nomes = {}
    for i, g in enumerate(grupos):
        ag.loc[g, "regional_id"] = i
        polo, ufs = nomear(ag, g)
        nomes[i] = polo

    nomes = desambiguar(ag, grupos, nomes)
    ag["regional"] = ag["regional_id"].map(nomes)

    tam = np.array([len(g) for g in grupos])
    ext = np.array([extensao_km(ag.loc[g]) for g in grupos])
    ufs = np.array([ag.loc[g, "uf"].nunique() for g in grupos])

    print(f"Regionais: {len(grupos)}  (teto {MAX_AGENCIAS}, piso {MIN_AGENCIAS})\n")
    print(f"Agencias por regional")
    print(f"  mediana {np.median(tam):.0f} | min {tam.min()} | max {tam.max()}")
    print(f"  abaixo do piso: {(tam < MIN_AGENCIAS).sum()}")
    print(f"  acima do teto:  {(tam > MAX_AGENCIAS).sum()}")
    print()
    print("Extensao interna")
    print(f"  mediana {np.median(ext):.0f} km | maxima {ext.max():.0f} km")
    print(f"  acima de 150 km (aviao entra no modelo): {(ext > 150).sum()}")
    print(f"  acima de 400 km: {(ext > 400).sum()}")
    print()
    print(f"Regionais cobrindo mais de um estado: {(ufs > 1).sum()}")

    # nomes repetidos quebram o seletor da interface
    repetidos = pd.Series(list(nomes.values())).value_counts()
    repetidos = repetidos[repetidos > 1]
    if len(repetidos):
        print(f"\nNomes de polo repetidos: {len(repetidos)}")
        print(repetidos.head(8).to_string())

    ag.to_csv("dados/agencias_com_regional.csv", index=False)
    print("\nGravado: dados/agencias_com_regional.csv")


if __name__ == "__main__":
    main()
