"""Gera notebooks/modelos.ipynb — versão executável no Google Colab dos dois
modelos do projeto. Rodar a partir da raiz do repositório."""

import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"name": "modelos.ipynb", "provenance": []},
}
C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))

md(r"""
# Sistema de Roteirização de Visitas às Agências — os dois modelos

**CCD610 · Projeto e Gestão de Dados · Checkpoint das Aulas 4, 5 e 6**
Davi Cassiano · Gabriel Felipe · Luca Juraski · Victor Meneguin

Este notebook reproduz, de ponta a ponta e sem depender de nada instalado, os dois modelos do pipeline:

| Parte | Modelo | Tipo | Story | Módulo no repositório |
| --- | --- | --- | --- | --- |
| 1 | **K-means** que forma as regionais a partir das coordenadas das agências | não supervisionado | US01 | `src/train.py` |
| 2 | **Regressão Ridge** do preço da gasolina por estado, com validação temporal | supervisionado | US11 | `src/features.py`, `src/train.py` |
| 3 | Os testes automatizados do repositório, rodando aqui | — | — | `tests/` |

O código é o mesmo de `src/`, copiado para as células para ser lido na ordem. A última parte clona o repositório e roda o `pytest`, para mostrar que o notebook e o pipeline dão o mesmo resultado.

**Para rodar no Colab:** *Ambiente de execução → Executar tudo* (Ctrl+F9). Leva menos de um minuto.

Repositório: https://github.com/davi-cassiano/Projeto-Varela
""")

code(r"""
import math, unicodedata, urllib.request, os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge

SEMENTE = 42
pd.set_option("display.width", 120)

# Os dois arquivos de entrada estão versionados em dados/colab/ (156 KB e 656 KB).
# Se o notebook estiver rodando dentro do repositório, usa a cópia local.
BASE = "https://raw.githubusercontent.com/davi-cassiano/Projeto-Varela/main/dados/colab/"

def carregar(nome, **kw):
    local = os.path.join("..", "dados", "colab", nome)
    return pd.read_csv(local if os.path.exists(local) else BASE + nome, **kw)

agencias = carregar("agencias_itau_geocodificadas.csv")
precos = carregar("precos_gasolina_comum_anp.csv", parse_dates=["data"])
print(f"{len(agencias)} agências · {len(precos)} semanas×estado de preço, de {precos.data.min():%m/%Y} a {precos.data.max():%m/%Y}")
""")

md(r"""
## Parte 1 · K-means: formar as regionais (não supervisionado, US01)

**O problema.** O cadastro do Banco Central tem 2.010 agências do Itaú Unibanco, mas não diz a qual regional cada uma pertence. O Rafael, gerente regional, precisa ver só as agências da regional dele. Então as regionais precisam ser *descobertas* a partir da posição geográfica — é um problema de agrupamento, sem rótulo, por isso aprendizado não supervisionado.

**Por que K-means.** Ele agrupa pontos por proximidade a um centro, e regionais de banco são exatamente isso: um polo e as agências em volta. Nenhuma regra geográfica é escrita à mão; as cidades-polo emergem dos grupos.

**Duas regras de produto por cima do algoritmo.** Uma regional com 300 agências não é gerenciável, e uma com 2 não justifica um gerente. Por isso:

- **Teto de 40 agências:** um grupo acima do teto é dividido de novo com K-means, recursivamente, até caber.
- **Piso de 4 agências:** um grupo abaixo do piso é absorvido pela regional vizinha mais próxima, desde que a soma não fure o teto.

O K-means padrão não tem noção de tamanho de grupo; a recursão e a absorção são o que transformam um agrupamento genérico numa divisão de regionais.
""")

code(r"""
TETO_AGENCIAS = 40   # acima disso a regional é subdividida
PISO_AGENCIAS = 4    # abaixo disso é absorvida pela vizinha


def _matriz_distancias(pontos: np.ndarray) -> np.ndarray:
    # Distância em linha reta (haversine) entre todos os pares, em km
    p = np.radians(pontos)
    la, lo = p[:, 0:1], p[:, 1:2]
    a = np.sin((la - la.T) / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _fatiar(ag, idx, teto):
    # Último recurso: grupo acima do teto com todas as agências na mesma coordenada
    # (uma capital com precisão de município). Sem eixo geográfico para cortar,
    # divide por código da agência, como um banco reparte uma praça densa por carteira.
    ordenado = list(ag.loc[idx].sort_values("cod_compe_ag").index)
    n = int(math.ceil(len(ordenado) / teto))
    return [pd.Index(f) for f in np.array_split(ordenado, n)]


def _dividir(ag, idx, teto):
    # K-means recursivo: divide até nenhum grupo passar do teto
    g = ag.loc[idx]
    if len(g) <= teto:
        return [idx]
    distintos = g[["lat", "lon"]].drop_duplicates().shape[0]
    if distintos < 2:
        return _fatiar(ag, idx, teto)

    k = min(int(math.ceil(len(g) / teto)), distintos)
    rotulos = KMeans(n_clusters=k, n_init=10, random_state=SEMENTE).fit_predict(g[["lat", "lon"]].values)

    saida = []
    for c in range(k):
        sub = g.index[rotulos == c]
        if len(sub) == len(g):
            return _fatiar(ag, idx, teto)
        saida += _dividir(ag, sub, teto)
    return saida


def _absorver_pequenas(ag, grupos, piso, teto):
    # Grupo abaixo do piso vai para a regional vizinha mais próxima que ainda caiba
    grupos = [list(g) for g in grupos]
    while True:
        tam = [len(g) for g in grupos]
        pequenas = [i for i, n in enumerate(tam) if n < piso]
        if not pequenas:
            break
        centros = np.array([ag.loc[g, ["lat", "lon"]].mean().values for g in grupos])
        dist = _matriz_distancias(centros)
        np.fill_diagonal(dist, np.inf)

        i = min(pequenas, key=lambda x: tam[x])
        candidatas = [j for j in np.argsort(dist[i]) if j != i and tam[j] + tam[i] <= teto]
        if not candidatas:
            break  # manter separada é melhor que furar o teto
        j = int(candidatas[0])
        grupos[j] = grupos[j] + grupos[i]
        grupos.pop(i)
    return grupos


def _nomear(ag, grupos):
    # Nome da regional = cidade com mais agências; desempata quando o polo se repete
    nomes = {i: ag.loc[g, "municipio_nome"].value_counts().index[0] for i, g in enumerate(grupos)}
    por_polo = {}
    for i, n in nomes.items():
        por_polo.setdefault(n, []).append(i)

    finais = dict(nomes)
    for polo, ids in por_polo.items():
        if len(ids) == 1:
            continue
        usados = set()
        for i in ids:
            g = ag.loc[grupos[i]]
            alternativas = list(g["municipio_nome"].value_counts().index[1:])
            alternativas += [str(b).title() for b in g["bairro"].value_counts().index[:5]]
            escolhido = next((a for a in alternativas if a and a != polo and a not in usados), None)
            if escolhido:
                usados.add(escolhido)
                finais[i] = f"{polo} / {escolhido}"

    contagem = {}
    for i in sorted(finais):
        contagem[finais[i]] = contagem.get(finais[i], 0) + 1
        if contagem[finais[i]] > 1:
            finais[i] = f"{finais[i]} {contagem[finais[i]]}"
    return finais


def treinar_regionais(agencias, teto=TETO_AGENCIAS, piso=PISO_AGENCIAS):
    # Atribui regional_id e regional a cada agência
    ag = agencias.reset_index(drop=True)
    grupos = _dividir(ag, ag.index, teto)
    grupos = _absorver_pequenas(ag, grupos, piso, teto)
    nomes = _nomear(ag, grupos)

    saida = ag.copy()
    saida["regional_id"] = -1
    for i, g in enumerate(grupos):
        saida.loc[g, "regional_id"] = i
    saida["regional"] = saida["regional_id"].map(nomes)
    return saida


def extensao_km(grupo):
    pts = grupo[["lat", "lon"]].drop_duplicates().values
    return 0.0 if len(pts) < 2 else float(_matriz_distancias(pts).max())
""")

code(r"""
com_regional = treinar_regionais(agencias)

tamanhos = com_regional.groupby("regional_id").size()
extensoes = com_regional.groupby("regional_id").apply(extensao_km, include_groups=False)
print(f"Regionais: {com_regional.regional_id.nunique()}")
print(f"Agências por regional — mediana {tamanhos.median():.0f} · mín {tamanhos.min()} · máx {tamanhos.max()}")
print(f"Extensão (maior distância entre duas agências) — mediana {extensoes.median():.0f} km · "
      f"{(extensoes > 150).sum()} regionais acima de 150 km")
assert tamanhos.max() <= TETO_AGENCIAS and tamanhos.min() >= PISO_AGENCIAS  # critério da US01

resumo = (com_regional.groupby("regional")
          .agg(agencias=("cod_compe_ag", "size"), municipios=("municipio_nome", "nunique"),
               ufs=("uf", lambda s: ", ".join(sorted(s.unique()))))
          .sort_values("agencias", ascending=False))
resumo.head(12)
""")

code(r"""
# Mapa: cada cor é uma regional. Nenhuma fronteira foi desenhada à mão.
fig, ax = plt.subplots(figsize=(7, 7))
rng = np.random.default_rng(SEMENTE)
cores = rng.permutation(com_regional.regional_id.nunique())
ax.scatter(com_regional.lon, com_regional.lat, c=cores[com_regional.regional_id], cmap="tab20", s=6, alpha=0.8)
ax.set_aspect("equal"); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
ax.set_title(f"{len(com_regional)} agências em {com_regional.regional_id.nunique()} regionais (k-means com teto 40 e piso 4)")
for lado in ("top", "right"): ax.spines[lado].set_visible(False)
plt.show()
""")

md(r"""
**O que olhar no resultado.** Nenhuma regional fura o teto de 40 nem o piso de 4 — é o critério de aceite da US01, e está no teste `test_nenhuma_regional_fura_teto_nem_piso`. As regionais grandes em extensão (acima de 150 km) ficam no interior do Norte e do Centro-Oeste, onde as agências são esparsas; é o comportamento esperado, e o risco R5 (rotas com ida e volta) é maior nelas.

**Limitação conhecida.** O K-means agrupa por distância em linha reta. Duas agências separadas por um rio sem ponte, ou por uma serra, ficam na mesma regional. Para o MVP isso é aceitável porque a regional é um recorte de gestão, não uma rota; a rota é calculada depois, trecho a trecho.
""")

md(r"""
## Parte 2 · Regressão Ridge: o preço da gasolina por estado (supervisionado, US11)

**O problema.** O custo de carro de um trecho depende do preço da gasolina. O produto usava um único preço para o Brasil inteiro. Mas o preço varia muito por estado — no Acre é um dos mais caros, no Amapá um dos mais baratos. A US11 pede que o custo use o preço do estado.

**Por que é supervisionado.** Temos a série semanal da ANP: para cada semana e estado, o preço médio real. Esse preço é o *rótulo*; o modelo aprende a relação entre atributos conhecidos (estado, diferença histórica, mês) e o preço, e é avaliado comparando a previsão com o preço real de semanas que ele não viu.

**O que o modelo prevê.** Não o preço em si, mas a **diferença do estado para a média nacional** (*spread*). A diferença é muito mais estável que o nível do preço: o Acre é sempre mais caro que a média, pouco importa se a gasolina está a R$ 3 ou a R$ 7. Depois, preço do estado = preço nacional + diferença prevista.

**Os atributos**, calculados só com o passado para não vazar informação do futuro:

| Atributo | O que é |
| --- | --- |
| `uf` | o estado (vira uma coluna 0/1 por estado) |
| `spread_52` | a diferença média do estado nas 52 semanas **anteriores** |
| `mes` | o mês, para capturar sazonalidade |

**Validação temporal.** Treino até dezembro de 2019 e teste de janeiro de 2020 a maio de 2021. Nunca embaralhar as semanas: se o modelo visse uma semana de 2020 no treino, saberia o futuro ao prever a semana vizinha, e o erro ficaria artificialmente baixo. O corte em 2020 deixa o choque de preços da pandemia inteiro no teste — o cenário mais difícil.

**O critério de aceite da US11.** Erro absoluto médio (MAE) de no máximo R$ 0,15/L e pelo menos 25% abaixo do baseline. O baseline é o que o produto fazia antes: o preço nacional para todos os estados.
""")

code(r"""
UF_POR_ESTADO = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "BAHIA": "BA",
    "CEARA": "CE", "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES", "GOIAS": "GO",
    "MARANHAO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG", "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR",
    "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ",
    "RIO GRANDE DO NORTE": "RN", "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO",
    "RORAIMA": "RR", "SANTA CATARINA": "SC", "SAO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c)).upper().strip()


def atributos_preco(precos):
    # Uma linha por semana e estado, com os atributos do modelo (features.py)
    df = precos.copy()
    df["uf"] = df["estado"].map(sem_acento).map(UF_POR_ESTADO)
    assert not df["uf"].isna().any(), "estado sem sigla"

    df["nacional"] = df.groupby("data")["preco"].transform("mean")   # média dos estados na semana
    df["spread"] = df["preco"] - df["nacional"]                       # alvo: diferença do estado
    df = df.sort_values(["uf", "data"])
    df["spread_52"] = (                                               # só o passado: shift(1)
        df.groupby("uf")["spread"]
        .transform(lambda s: s.shift(1).rolling(52, min_periods=12).mean())
    )
    df["mes"] = df["data"].dt.month
    return df.dropna(subset=["spread_52"]).reset_index(drop=True)


atributos = atributos_preco(precos)
atributos.tail(3)
""")

code(r"""
class EstimadorPreco(ABC):
    # Interface comum dos candidatos: aprende com a série, prevê o preço dado o nacional.
    # Interface pequena de propósito (ISP); qualquer estimador substitui outro (LSP).
    nome = "estimador"

    @abstractmethod
    def ajustar(self, treino): ...

    @abstractmethod
    def prever(self, tabela): ...


class BaselineNacional(EstimadorPreco):
    # O que o produto fazia: o mesmo preço para todos os estados
    nome = "Baseline: preço nacional para todos"

    def ajustar(self, treino):
        return self

    def prever(self, tabela):
        return tabela["nacional"].to_numpy()


class EfeitoMedioEstado(EstimadorPreco):
    # Preço nacional + diferença média do estado nos últimos anos do treino
    nome = "Nacional + efeito médio do estado"

    def __init__(self, anos=2):
        self.anos = anos

    def ajustar(self, treino):
        corte = treino["data"].max() - pd.DateOffset(years=self.anos)
        self.efeito_ = treino[treino["data"] > corte].groupby("uf")["spread"].mean()
        return self

    def prever(self, tabela):
        return (tabela["nacional"] + tabela["uf"].map(self.efeito_).fillna(0)).to_numpy()


class RegressaoEstado(EstimadorPreco):
    # Regressão linear regularizada (Ridge) da diferença do estado, a partir
    # da diferença recente, do estado e do mês
    nome = "Regressão Ridge da diferença do estado"

    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def _matriz(self, tabela):
        x = pd.get_dummies(tabela[["uf"]].astype(str), prefix="uf")
        x = x.reindex(columns=getattr(self, "colunas_", x.columns), fill_value=0)
        x["spread_52"] = tabela["spread_52"].to_numpy()
        for m in range(2, 13):
            x[f"mes_{m}"] = (tabela["mes"].to_numpy() == m).astype(float)
        return x.astype(float)

    def ajustar(self, treino):
        self.colunas_ = pd.get_dummies(treino[["uf"]].astype(str), prefix="uf").columns
        self.modelo_ = Ridge(alpha=self.alpha).fit(self._matriz(treino), treino["spread"])
        return self

    def prever(self, tabela):
        return tabela["nacional"].to_numpy() + self.modelo_.predict(self._matriz(tabela))


CORTE_TEMPORAL = "2020-01-01"


@dataclass
class Avaliacao:
    nome: str
    mae: float
    rmse: float


def separar_no_tempo(atributos, corte=CORTE_TEMPORAL):
    # Treino antes do corte, teste depois. Nunca embaralhar.
    return atributos[atributos["data"] < corte], atributos[atributos["data"] >= corte]


def avaliar(estimador, teste):
    erro = teste["preco"].to_numpy() - estimador.prever(teste)
    return Avaliacao(estimador.nome, float(np.mean(np.abs(erro))), float(np.sqrt(np.mean(erro ** 2))))


def treinar_modelo_preco(atributos, corte=CORTE_TEMPORAL):
    # Ajusta os candidatos, avalia no teste, escolhe o de menor MAE e o reajusta com toda a série
    treino, teste = separar_no_tempo(atributos, corte)
    candidatos = [BaselineNacional(), EfeitoMedioEstado(), RegressaoEstado()]
    avaliacoes = [avaliar(c.ajustar(treino), teste) for c in candidatos]
    melhor = min(range(len(candidatos)), key=lambda i: avaliacoes[i].mae)
    vencedor = type(candidatos[melhor])().ajustar(atributos)
    return vencedor, avaliacoes


def erro_por_mes(estimador, teste):
    # MAE mês a mês no teste, para enxergar drift
    t = teste.copy()
    t["erro_abs"] = np.abs(t["preco"].to_numpy() - estimador.prever(t))
    return t.groupby(t["data"].dt.to_period("M"))["erro_abs"].mean()
""")

code(r"""
treino, teste = separar_no_tempo(atributos)
print(f"Treino: {len(treino)} linhas até {treino.data.max():%d/%m/%Y} · Teste: {len(teste)} linhas de {teste.data.min():%d/%m/%Y} a {teste.data.max():%d/%m/%Y}")

vencedor, avaliacoes = treinar_modelo_preco(atributos)
tabela = pd.DataFrame([a.__dict__ for a in avaliacoes]).set_index("nome").round(3)
tabela.columns = ["MAE (R$/L)", "RMSE (R$/L)"]
display(tabela)

baseline, ridge = avaliacoes[0].mae, avaliacoes[2].mae
print(f"Vencedor: {vencedor.nome}")
print(f"Ridge tem {100 * (1 - ridge / baseline):.0f}% menos erro que o baseline")

# Critério de aceite da US11 (o mesmo de tests/test_train.py)
assert ridge <= 0.15, "MAE acima de R$ 0,15/L"
assert ridge <= 0.75 * baseline, "menos de 25% abaixo do baseline"
print("Critério de aceite da US11: atendido")
""")

code(r"""
# Drift: o erro mês a mês no período de teste
modelo_teste = RegressaoEstado().ajustar(treino)
mensal = pd.DataFrame({"Baseline": erro_por_mes(BaselineNacional(), teste),
                       "Ridge": erro_por_mes(modelo_teste, teste)})

fig, ax = plt.subplots(figsize=(9, 4))
x = mensal.index.to_timestamp()
ax.plot(x, mensal["Baseline"], marker="o", ms=3, color="#C26A1E", label="Baseline (preço nacional único)")
ax.plot(x, mensal["Ridge"], marker="o", ms=3, color="#1F6FB2", label="Regressão Ridge por estado")
ax.axhline(0.15, ls="--", color="#5A7185", lw=1); ax.text(x[0], 0.153, "critério da US11: até R$ 0,15/L", fontsize=8, color="#5A7185")
pico = mensal["Ridge"].idxmax()
ax.annotate(f"maior erro: {pico.strftime('%m/%Y')}", (pico.to_timestamp(), mensal["Ridge"].max()), xytext=(0, 16), textcoords="offset points", ha="center", fontsize=8)
ax.set_ylim(0, 0.3); ax.set_ylabel("MAE (R$/L)"); ax.legend(frameon=False, fontsize=9)
ax.set_title("Erro mensal no período de teste (jan/2020 a mai/2021)")
for lado in ("top", "right"): ax.spines[lado].set_visible(False)
plt.show()
""")

md(r"""
**O que o gráfico mostra.** O modelo fica abaixo do critério de R$ 0,15/L em todos os meses. O erro sobe no choque de preços da pandemia (abril e maio de 2020) e tem o pico em outubro de 2020: o modelo foi ajustado num regime de preços e avaliado em outro. É o **drift** descrito na Aula 4 — e o motivo do requisito RNF06, que manda reavaliar o modelo a cada atualização da série e alertar se o MAE passar de R$ 0,25/L. (Setembro de 2020 não existe na série da ANP.)

**Sensibilidade ao ponto de corte** (pergunta da revisão do PR #15): a conclusão não depende de onde o treino termina.
""")

code(r"""
linhas = []
for corte in ["2019-01-01", "2020-01-01", "2020-07-01"]:
    _, av = treinar_modelo_preco(atributos, corte)
    linhas.append({"corte": corte, "baseline": round(av[0].mae, 3), "ridge": round(av[2].mae, 3),
                   "redução": f"{100 * (1 - av[2].mae / av[0].mae):.0f}%"})
pd.DataFrame(linhas).set_index("corte")
""")

md(r"""
### Como o produto usa o modelo (serving)

O protótipo precisa de um preço por estado *hoje*, mas a série termina em 2021. O serving aplica a diferença prevista de cada estado sobre o **preço nacional atual**, informado por parâmetro (`python -m src.pipeline --preco-gasolina 6.45`). A premissa, declarada no risco R2, é que a diferença entre estados é mais estável que o nível do preço.
""")

code(r"""
def precos_por_uf(estimador, atributos, preco_nacional):
    # Última semana de cada estado como entrada, aplicada ao preço nacional atual (serve.py)
    ultima = atributos.sort_values("data").groupby("uf").tail(1).copy()
    ultima["nacional"] = preco_nacional
    return pd.Series(estimador.prever(ultima), index=ultima["uf"].values).round(3).sort_values()

por_uf = precos_por_uf(vencedor, atributos, preco_nacional=6.70)
print("Com o preço nacional a R$ 6,70/L:")
print(f"  mais baratos: {', '.join(f'{uf} {v:.2f}' for uf, v in por_uf.head(3).items())}")
print(f"  mais caros:   {', '.join(f'{uf} {v:.2f}' for uf, v in por_uf.tail(3).items())}")
print(f"  SP {por_uf['SP']:.2f} · RJ {por_uf['RJ']:.2f} · diferença de R$ {por_uf['RJ'] - por_uf['SP']:.2f}/L no mesmo trecho")
""")

md(r"""
## Parte 3 · O mesmo resultado no repositório

As células acima copiam o código de `src/`. Para mostrar que o notebook e o pipeline são a mesma coisa, esta parte clona o repositório e roda os 23 testes automatizados — entre eles o critério de aceite da US11 e a regra de teto e piso da US01.
""")

code(r"""
%%bash
if [ ! -d Projeto-Varela ]; then git clone -q https://github.com/davi-cassiano/Projeto-Varela.git; fi
cd Projeto-Varela
pip install -q -r requirements.txt 2>/dev/null
python -m pytest tests -q 2>&1 | tail -3
""")

md(r"""
---

**Rastreabilidade.** Parte 1 é a US01 (Issue #1), pacote 4.1 da WBS. Parte 2 é a US11 (Issue #11), pacotes 3.4, 4.2 e 5.1, entregue na Sprint 1 pelo PR #15. Os documentos completos estão em `docs/backlog.md`, `docs/arquitetura.md` e `docs/planejamento.md`.
""")

nb.cells = C
nbf.write(nb, "notebooks/modelos.ipynb")
print("notebooks/modelos.ipynb:", len(C), "células")
