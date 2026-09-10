"""
Monta o pacote de dados que vai embutido no HTML do prototipo.

Fronteira explicita entre dado e interface: tudo o que a tela consome sai
daqui. Trocar o mock por API depois significa reproduzir este formato, sem
tocar nas telas.

Campos REAIS (Bacen 11/2024 + geocodificacao + k-means):
    codigo, nome, endereco, bairro, municipio, uf, lat, lon, precisao,
    regional

Campos SIMULADOS (nao existem em base publica, sao de planejamento):
    prioridade, data_limite, ultima_visita

Os simulados sao derivados de forma deterministica do codigo da agencia,
para que o prototipo mostre sempre os mesmos dados a cada abertura.
"""

import hashlib
import json
import re
from datetime import date, timedelta

import numpy as np
import pandas as pd

HOJE = date(2026, 9, 10)
SAIDA = "dados/dados_prototipo.json"


def semente(codigo):
    """Numero estavel entre 0 e 1, derivado do codigo da agencia."""
    h = hashlib.md5(str(codigo).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def limpar(texto):
    t = str(texto or "").strip()
    return "" if t.lower() in ("nan", "none") else t


def titulo(texto):
    """MAIUSCULAS do Bacen viram Capitalizado, preservando siglas curtas."""
    t = limpar(texto).title()
    for sigla in (" Do ", " Da ", " De ", " Dos ", " Das ", " E "):
        t = t.replace(sigla, sigla.lower())
    return t


ag = pd.read_csv("dados/agencias_com_regional.csv")

# A base do Bacen grava municipio em maiusculas e sem acento ("SAO PAULO").
# O codigo IBGE ja esta la, entao da para recuperar a grafia correta.
# A etapa de regionais ja resolve isso; aqui e so uma rede de seguranca.
if "municipio_nome" not in ag.columns:
    mun = pd.read_csv("dados/municipios.csv")[["codigo_ibge", "nome"]]
    mun = mun.rename(columns={"nome": "municipio_nome"})
    ag = ag.merge(mun, left_on="municipio_ibge", right_on="codigo_ibge", how="left")
ag["municipio_nome"] = ag["municipio_nome"].fillna(ag["municipio"].map(titulo))

GENERICOS = {"MATRIZ", "SEDE", "FILIAL", "", "NAN", "NONE"}


def nome_agencia(bruto, bairro, municipio):
    """
    Limpa o nome vindo do Bacen. Ele costuma repetir a UF no fim
    ('AGUAI-SP', 'BARAO DE COCAIS - MG.'), o que e ruido na tela, porque
    cidade e UF ja aparecem em coluna propria.
    """
    t = limpar(bruto).upper()
    t = re.sub(r"\s*[-/]\s*[A-Z]{2}\.?\s*$", "", t)
    t = t.strip(" .-/")

    if t in GENERICOS:
        return titulo(bairro) or municipio

    return titulo(t)

# ---------------------------------------------------------------------
# Agencias
# ---------------------------------------------------------------------

agencias = []
for a in ag.itertuples():
    s = semente(f"{a.regional_id}-{a.cod_compe_ag}-{a.Index}")

    # Prioridade: uma minoria e alta, a maioria media, o resto baixa.
    prioridade = "alta" if s < 0.22 else ("media" if s < 0.68 else "baixa")

    # Data limite: agencias de prioridade alta vencem antes.
    janela = {"alta": 45, "media": 110, "baixa": 200}[prioridade]
    dias = int(7 + s * janela)
    data_limite = HOJE + timedelta(days=dias)

    # Ultima visita: entre 1 e 11 meses atras.
    ultima = HOJE - timedelta(days=int(30 + s * 300))

    agencias.append(
        {
            "id": f"{a.regional_id}-{int(a.cod_compe_ag)}-{a.Index}",
            "codigo": int(a.cod_compe_ag),
            "nome": nome_agencia(a.nome_agencia, a.bairro, a.municipio_nome),
            "endereco": titulo(a.endereco),
            "bairro": titulo(a.bairro),
            "municipio": a.municipio_nome,
            "uf": a.uf,
            "cep": limpar(a.cep),
            "lat": round(float(a.lat), 5),
            "lon": round(float(a.lon), 5),
            "precisao": a.precisao,
            "regional": int(a.regional_id),
            "prioridade": prioridade,
            "dataLimite": data_limite.isoformat(),
            "ultimaVisita": ultima.isoformat(),
        }
    )

# ---------------------------------------------------------------------
# Regionais
# ---------------------------------------------------------------------

R = 6371.0


def extensao(g):
    pts = g[["lat", "lon"]].drop_duplicates().values
    if len(pts) < 2:
        return 0.0
    P = np.radians(pts)
    la, lo = P[:, 0:1], P[:, 1:2]
    x = (
        np.sin((la - la.T) / 2) ** 2
        + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2
    )
    return float((2 * R * np.arcsin(np.sqrt(np.clip(x, 0, 1)))).max())


regionais = []
for rid, g in ag.groupby("regional_id"):
    # A sede e a cidade com mais agencias, que da nome a regional.
    sede_mun = g["municipio_nome"].value_counts().index[0]
    sede = g[g["municipio_nome"] == sede_mun].iloc[0]

    regionais.append(
        {
            "id": int(rid),
            "nome": g["regional"].iloc[0],
            "sede": {
                "municipio": sede_mun,
                "uf": sede["uf"],
                "lat": round(float(sede["lat"]), 5),
                "lon": round(float(sede["lon"]), 5),
            },
            "agencias": int(len(g)),
            "municipios": int(g["municipio_nome"].nunique()),
            "ufs": sorted(g["uf"].unique().tolist()),
            "extensaoKm": round(extensao(g)),
        }
    )

regionais.sort(key=lambda r: r["nome"])

# ---------------------------------------------------------------------
# Aeroportos
# ---------------------------------------------------------------------

aero = pd.read_excel(
    "dados/brutos/base_consolidada_roteirizacao.xlsx", sheet_name="Aeroportos"
)
aeroportos = [
    {
        "iata": r["IATA"],
        "nome": limpar(r["Nome do Aeroporto"]),
        "municipio": titulo(r["Cidade"]),
        "uf": r["UF"],
        "lat": round(float(r["Latitude"]), 5),
        "lon": round(float(r["Longitude"]), 5),
    }
    for _, r in aero.iterrows()
]

# ---------------------------------------------------------------------
# Parametros do modelo de transporte
# Espelham decisao_transporte.py. Alterar aqui muda o calculo na tela.
# ---------------------------------------------------------------------

parametros = {
    "carro": {
        "precoGasolinaLitro": 6.70,
        "consumoKmLitro": 12.0,
        "pedagioPorKm": 0.05,
        "velocidadeKmh": 80.0,
        "maxKmDia": 700.0,
    },
    "onibus": {"a": 1.43124328, "b": 1.48070929, "c": 0.74592568, "velocidadeKmh": 62.0},
    "aviao": {
        "a": 174.52140223,
        "b": 2.9577578,
        "c": 0.68403605,
        "velocidadeKmh": 800.0,
        "taxiHoras": 0.4,
        "overheadAeroportoHoras": 3.0,
        "distanciaMinimaKm": 150.0,
    },
    "fatorSinuosidade": 1.25,
    "fontes": {
        "agencias": "Bacen, agências em funcionamento, posição 29/11/2024",
        "combustivel": "ANP, síntese semanal de preços",
        "onibus": "ANTT, Anuário Estatístico do Transporte Rodoviário",
        "aviao": "ANAC, tarifa média doméstica",
    },
}

# ---------------------------------------------------------------------

# contorno dos estados, para a base cartografica do mapa
estados = json.load(open("dados/estados.json", encoding="utf-8"))
# cidades: contexto geografico no zoom proximo [nome, uf, lat, lon, capital]
cidades = json.load(open("dados/cidades.json", encoding="utf-8"))

pacote = {
    "geradoEm": HOJE.isoformat(),
    "estados": estados,
    "cidades": cidades,
    "instituicao": "Itaú Unibanco",
    "parametros": parametros,
    "regionais": regionais,
    "agencias": agencias,
    "aeroportos": aeroportos,
}

with open(SAIDA, "w", encoding="utf-8") as f:
    json.dump(pacote, f, ensure_ascii=False, separators=(",", ":"))

import os

print(f"{SAIDA}: {os.path.getsize(SAIDA) / 1024:.0f} KB")
print(f"  {len(regionais)} regionais")
print(f"  {len(agencias)} agencias")
print(f"  {len(aeroportos)} aeroportos")
print(f"  {len(estados)} estados no contorno")
print(f"  {len(cidades)} cidades de contexto")
print()
print("distribuicao de prioridade:")
p = pd.Series([a["prioridade"] for a in agencias]).value_counts()
print(p.to_string())
print()
print("amostra:")
for a in agencias[:3]:
    print(" ", {k: a[k] for k in ("nome", "municipio", "uf", "prioridade", "dataLimite")})
