"""
validate.py — Regras de qualidade de dados (Aula 9).

Seis regras, cobrindo as quatro dimensões da aula: completude, unicidade,
validade e consistência, mais pontualidade para a série de preços. Cada
regra tem um limite explícito e devolve o que foi medido, para o relatório
registrar a falha com número, não com impressão.

Responsabilidade única: este módulo só mede. Não corrige, não filtra e não
decide o que fazer com a falha — isso é da ingestão (que descarta) ou do
SBAR (que recomenda). Recebe tabelas já carregadas pelo ingest.py, então
não sabe se o dado veio de Excel, CSV ou memória (DIP).

Uso, a partir da raiz do repositório:

    python -m src.validate                # relatório em dados/saida/relatorio_qualidade.{json,md}
    python -m src.validate --sem-download

As mesmas regras, em SQL, estão em sql/qualidade.sql.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import date

import pandas as pd

from . import features, ingest

UFS = set(features.UF_POR_CODIGO.values())
LAT_BRASIL = (-34.0, 5.5)
LON_BRASIL = (-74.0, -34.5)

# Limites: decisão do time, registrados aqui para a falha ser objetiva
MAX_NULOS = 0.01            # até 1% de nulos por coluna obrigatória
# Até 10% das agências perdendo a coordenada de bairro. Definido antes da medição
# (revisão do PR #28): uma em dez agências com distância menos precisa é o máximo
# que aceitamos num produto de deslocamento. O teste de sensibilidade do PR #15
# mostrou que nenhum limite único atinge 10% (100 km ainda descarta 10,7%); a
# regra é uma meta que só o limite proporcional ao município (Issue #16) cumpre.
MAX_DESCARTE_BAIRRO = 0.10
MIN_COBERTURA_BAIRRO = 0.70 # critério da US10
MAX_IDADE_PRECOS_DIAS = 90  # série de preços com no máximo um trimestre de atraso
FAIXA_PRECO = (0.5, 15.0)

COLUNAS_OBRIGATORIAS = ["cod_compe_ag", "nome_agencia", "bairro", "cep",
                        "municipio", "uf", "municipio_ibge", "latitude", "longitude"]


@dataclass
class Resultado:
    regra: str
    dimensao: str
    base: str
    limite: str
    medido: str
    passou: bool
    detalhe: str = ""


# ---------------------------------------------------------------------
# Agências (cadastro do Banco Central, recorte Itaú Unibanco)
# ---------------------------------------------------------------------

def unicidade_agencias(ag: pd.DataFrame) -> Resultado:
    dup = ag["cod_compe_ag"].duplicated(keep=False)
    return Resultado(
        "Um registro por agência", "Unicidade", "agências",
        "0 códigos COMPE repetidos", f"{int(dup.sum())} repetidos", not dup.any(),
        ", ".join(map(str, ag.loc[dup, "cod_compe_ag"].unique()[:10])),
    )


def completude_agencias(ag: pd.DataFrame) -> Resultado:
    nulos = {c: float(ag[c].isna().mean()) for c in COLUNAS_OBRIGATORIAS if c in ag}
    pior = max(nulos, key=nulos.get)
    return Resultado(
        "Colunas obrigatórias preenchidas", "Completude", "agências",
        f"até {MAX_NULOS:.0%} de nulos por coluna",
        f"pior coluna: {pior} com {nulos[pior]:.2%}",
        max(nulos.values()) <= MAX_NULOS,
        "; ".join(f"{c} {v:.2%}" for c, v in nulos.items() if v > 0),
    )


def validade_agencias(ag: pd.DataFrame) -> Resultado:
    uf_ok = ag["uf"].isin(UFS)
    cep_ok = ag["cep"].astype(str).str.replace(r"\D", "", regex=True).str.len() == 8
    lat_ok = ag["latitude"].between(*LAT_BRASIL)
    lon_ok = ag["longitude"].between(*LON_BRASIL)
    invalidos = int((~(uf_ok & cep_ok & lat_ok & lon_ok)).sum())
    return Resultado(
        "UF, CEP e coordenadas em faixas válidas", "Validade", "agências",
        "0 registros fora da faixa", f"{invalidos} inválidos", invalidos == 0,
        f"uf {int((~uf_ok).sum())} · cep {int((~cep_ok).sum())} · "
        f"lat {int((~lat_ok).sum())} · lon {int((~lon_ok).sum())}",
    )


def consistencia_municipio_uf(ag: pd.DataFrame) -> Resultado:
    uf_do_ibge = (ag["municipio_ibge"] // 100000).map(features.UF_POR_CODIGO)
    divergentes = ag[uf_do_ibge != ag["uf"]]
    return Resultado(
        "Município (código IBGE) pertence à UF informada", "Consistência", "agências",
        "0 divergências", f"{len(divergentes)} divergentes", divergentes.empty,
        ", ".join(f"{r.municipio}/{r.uf}≠{u}" for r, u in
                  zip(divergentes.head(5).itertuples(), uf_do_ibge[divergentes.index].head(5), strict=True)),
    )


def consistencia_coordenadas(ag_enriquecidas: pd.DataFrame) -> Resultado:
    """Depois da preparação: quantas coordenadas de bairro foram descartadas por
    ficarem a mais de 30 km do centro do município, e quanto sobrou de cobertura."""
    n = len(ag_enriquecidas)
    descartadas = int(ag_enriquecidas.attrs.get("descartadas_por_desvio", 0))
    cobertura = float((ag_enriquecidas["precisao"] != "municipio").mean())
    passou = descartadas / n <= MAX_DESCARTE_BAIRRO and cobertura >= MIN_COBERTURA_BAIRRO
    return Resultado(
        "Coordenada de bairro coerente com o município (≤ 30 km)", "Consistência",
        "agências (após preparação)",
        f"descartes ≤ {MAX_DESCARTE_BAIRRO:.0%} e cobertura de bairro ≥ {MIN_COBERTURA_BAIRRO:.0%}",
        f"descartes {descartadas / n:.1%} ({descartadas} de {n}) · cobertura {cobertura:.1%}",
        passou,
        "colisão de nome de bairro entre municípios; limite único prejudica municípios extensos (Issue #16)",
    )


# ---------------------------------------------------------------------
# Preços (série semanal da ANP, gasolina comum)
# ---------------------------------------------------------------------

def integridade_precos(precos: pd.DataFrame, hoje: date | None = None) -> Resultado:
    hoje = hoje or date.today()
    dup = int(precos.duplicated(["data", "estado"]).sum())
    fora = int((~precos["preco"].between(*FAIXA_PRECO)).sum())
    ultima = pd.Timestamp(precos["data"].max()).date()
    idade = (hoje - ultima).days
    passou = dup == 0 and fora == 0 and idade <= MAX_IDADE_PRECOS_DIAS
    return Resultado(
        "Série de preços única, válida e atual", "Pontualidade", "preços",
        f"1 linha por semana×estado · preço em R$ {FAIXA_PRECO[0]}–{FAIXA_PRECO[1]} · "
        f"última semana há ≤ {MAX_IDADE_PRECOS_DIAS} dias",
        f"{dup} duplicadas · {fora} fora da faixa · última semana {ultima:%d/%m/%Y}, há {idade} dias",
        passou,
        "série pública termina em maio/2021; o produto aplica a diferença por estado sobre o preço "
        "nacional informado por parâmetro (--preco-gasolina). Automatizar é a US14",
    )


# ---------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------

def validar(agencias: pd.DataFrame, agencias_enriquecidas: pd.DataFrame,
            precos: pd.DataFrame, hoje: date | None = None) -> list[Resultado]:
    return [
        unicidade_agencias(agencias),
        completude_agencias(agencias),
        validade_agencias(agencias),
        consistencia_municipio_uf(agencias),
        consistencia_coordenadas(agencias_enriquecidas),
        integridade_precos(precos, hoje),
    ]


def relatorio_markdown(resultados: list[Resultado], gerado_em: date) -> str:
    linhas = [
        "# Relatório de qualidade de dados", "",
        f"Gerado em {gerado_em:%d/%m/%Y} por `python -m src.validate`. "
        "Regras em `src/validate.py` e `sql/qualidade.sql`.", "",
        "| # | Dimensão | Base | Regra | Limite | Medido | Situação |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for i, r in enumerate(resultados, 1):
        linhas.append(f"| {i} | {r.dimensao} | {r.base} | {r.regra} | {r.limite} | {r.medido} | "
                      f"{'✅ Passou' if r.passou else '❌ Falhou'} |")
    falhas = [r for r in resultados if not r.passou]
    linhas += ["", f"**{len(resultados) - len(falhas)} de {len(resultados)} regras passaram.**", ""]
    for r in falhas:
        linhas += [f"- **Falhou — {r.regra}:** {r.medido}. {r.detalhe}."]
    return "\n".join(linhas) + "\n"


def gravar(resultados: list[Resultado], pasta: str, gerado_em: date) -> None:
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "relatorio_qualidade.json"), "w", encoding="utf-8") as f:
        json.dump({"gerado_em": gerado_em.isoformat(), "regras": [asdict(r) for r in resultados]},
                  f, ensure_ascii=False, indent=2)
    with open(os.path.join(pasta, "relatorio_qualidade.md"), "w", encoding="utf-8") as f:
        f.write(relatorio_markdown(resultados, gerado_em))


def _carregar_amostra(pasta: str):
    """Recorte versionado em dados/colab/: o mesmo que o notebook usa. Serve para
    o CI, onde as bases brutas não estão disponíveis."""
    agencias = pd.read_csv(os.path.join(pasta, "agencias_itau_geocodificadas.csv"), dtype={"cep": str})
    with open(os.path.join(pasta, "resumo_preparacao.json"), encoding="utf-8") as f:
        agencias.attrs["descartadas_por_desvio"] = json.load(f)["descartadas_por_desvio"]
    precos = pd.read_csv(os.path.join(pasta, "precos_gasolina_comum_anp.csv"), parse_dates=["data"])
    return agencias, agencias, precos


def _carregar_bases(dados: str, brutos: str):
    consolidada = os.path.join(brutos, "base_consolidada_roteirizacao.xlsx")
    agencias = ingest.carregar_agencias(ingest.ExcelSource(consolidada, "Agencias_Geocodificadas"))
    fonte_bairros = ingest.CsvSource(os.path.join(dados, "bairros.csv"), sep=";", quotechar='"')
    bairros = ingest.carregar_bairros(fonte_bairros)
    precos = ingest.carregar_precos(ingest.TsvSource(os.path.join(brutos, "2004-2021.tsv")))
    return agencias, features.enriquecer_coordenadas(agencias, bairros), precos


def regressoes(resultados: list[Resultado], linha_de_base: str) -> list[str]:
    """Regras que passavam na linha de base e agora falham (revisão do PR #28).

    Uma falha já conhecida é um achado registrado; uma regra que regrediu é
    um defeito novo e deve bloquear o merge. A linha de base é o JSON com as
    regras que passavam na última execução aceita pelo time."""
    with open(linha_de_base, encoding="utf-8") as f:
        passavam = set(json.load(f)["regras_que_passam"])
    return [r.regra for r in resultados if r.regra in passavam and not r.passou]


def main() -> None:
    p = argparse.ArgumentParser(description="Regras de qualidade de dados")
    p.add_argument("--linha-de-base", default=None,
                   help="JSON com as regras que passavam; sai com erro só se alguma delas regredir")
    p.add_argument("--sem-download", action="store_true", help="não baixar bases auxiliares")
    p.add_argument("--amostra", action="store_true",
                   help="validar o recorte versionado em dados/colab/ (sem as bases brutas)")
    p.add_argument("--atualizar-precos", action="store_true",
                   help="US14: validar a série atual da ANP em vez do arquivo 2004-2021")
    args = p.parse_args()

    dados, brutos = "dados", os.path.join("dados", "brutos")
    if args.amostra:
        agencias, enriquecidas, precos = _carregar_amostra(os.path.join(dados, "colab"))
    else:
        if not args.sem_download:
            ingest.baixar_bases_auxiliares(dados)
        agencias, enriquecidas, precos = _carregar_bases(dados, brutos)
        if args.atualizar_precos:
            precos = ingest.carregar_precos(ingest.AnpSource(atualizar=not args.sem_download))

    resultados = validar(agencias, enriquecidas, precos)
    hoje = date.today()
    gravar(resultados, os.path.join(dados, "saida"), hoje)
    print(relatorio_markdown(resultados, hoje))
    if args.linha_de_base:
        reg = regressoes(resultados, args.linha_de_base)
        for r in reg:
            print(f"REGRESSÃO: '{r}' passava na linha de base e agora falha")
        raise SystemExit(1 if reg else 0)
    raise SystemExit(0 if all(r.passou for r in resultados) else 1)


if __name__ == "__main__":
    main()
