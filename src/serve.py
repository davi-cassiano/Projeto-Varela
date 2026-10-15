"""
serve.py — Serving: aplicar os modelos e entregar o resultado.

Responsabilidade única (SRP): recebe modelos ajustados e tabelas prontas
e produz o que o produto consome. Não treina e não lê fonte bruta.

Open/Closed: cada meio de transporte é uma classe com o mesmo contrato
(`Modal.estimar`). Incluir trem, por exemplo, é escrever uma classe nova
e passá-la a `comparar_modais`, sem alterar nada que já existe.

Liskov: qualquer `Modal` substitui outro em `comparar_modais`.

Dependency Inversion: o custo do carro depende de um `EstimadorPreco`
(abstração do train.py), não de um número fixo nem de um modelo
específico.

Stories atendidas: US03, US05, US06, US07 (cálculo por trecho) e US11
(preço de combustível por estado aplicado ao custo).
"""

from __future__ import annotations

import json
import math
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

import pandas as pd

from .features import distancia_km
from .train import EstimadorPreco, extensao_km

# ---------------------------------------------------------------------
# Parâmetros calibrados (origem: decisao_transporte.py, ANP, ANTT, ANAC)
# ---------------------------------------------------------------------

FATOR_SINUOSIDADE = 1.25
PRECO_GASOLINA_NACIONAL = 6.70     # R$/L, média ANP usada como referência


@dataclass
class Opcao:
    modal: str
    disponivel: bool
    custo: float
    horas: float
    distancia_km: float
    observacao: str = ""


class Modal(ABC):
    nome = "modal"

    @abstractmethod
    def estimar(self, distancia_reta_km: float, uf: str | None = None) -> Opcao:
        ...


class Carro(Modal):
    nome = "carro"

    def __init__(self, preco_por_uf: dict[str, float] | None = None,
                 preco_padrao: float = PRECO_GASOLINA_NACIONAL,
                 consumo_km_l: float = 12.0, pedagio_km: float = 0.05,
                 velocidade: float = 80.0, max_km_dia: float = 700.0):
        self.preco_por_uf = preco_por_uf or {}
        self.preco_padrao, self.consumo, self.pedagio = preco_padrao, consumo_km_l, pedagio_km
        self.velocidade, self.max_km_dia = velocidade, max_km_dia

    def estimar(self, distancia_reta_km, uf=None):
        d = distancia_reta_km * FATOR_SINUOSIDADE
        preco = self.preco_por_uf.get(uf, self.preco_padrao)
        obs = "Requer pernoite ou parada de descanso" if d > self.max_km_dia else ""
        return Opcao(self.nome, True, d * (preco / self.consumo + self.pedagio),
                     d / self.velocidade, d, obs)


class Onibus(Modal):
    nome = "onibus"
    A, B, C, VELOCIDADE = 1.43124328, 1.48070929, 0.74592568, 62.0

    def estimar(self, distancia_reta_km, uf=None):
        d = distancia_reta_km * FATOR_SINUOSIDADE
        obs = ("Linha direta pouco provável nessa distância" if d > 3000
               else "Linha longa, pode exigir conexão" if d > 1200 else "")
        return Opcao(self.nome, True, self.A + self.B * d ** self.C, d / self.VELOCIDADE, d, obs)


class Aviao(Modal):
    nome = "aviao"
    A, B, C = 174.52140223, 2.9577578, 0.68403605
    VELOCIDADE, TAXI_H, OVERHEAD_H, MINIMO_KM = 800.0, 0.4, 3.0, 150.0

    def estimar(self, distancia_reta_km, uf=None):
        if distancia_reta_km < self.MINIMO_KM:
            return Opcao(self.nome, False, 0.0, 0.0, distancia_reta_km,
                         "Distância curta demais para voo comercial")
        horas = distancia_reta_km / self.VELOCIDADE + self.TAXI_H + self.OVERHEAD_H
        obs = "" if distancia_reta_km <= 2500 else "Pode exigir conexão"
        return Opcao(self.nome, True, self.A + self.B * distancia_reta_km ** self.C,
                     horas, distancia_reta_km, obs)


def comparar_modais(origem: tuple[float, float], destino: tuple[float, float],
                    peso_custo: float = 0.5, modais: list[Modal] | None = None,
                    uf: str | None = None) -> dict:
    """Compara os modais num trecho e recomenda um, pelo peso entre custo e tempo.

    Custo e tempo são normalizados pelo maior valor do trecho, para que
    reais e horas entrem na mesma escala.
    """
    modais = modais or [Carro(), Onibus(), Aviao()]
    dist = distancia_km(*origem, *destino)
    opcoes = [m.estimar(dist, uf) for m in modais]
    validas = [o for o in opcoes if o.disponivel]

    max_c = max(o.custo for o in validas) or 1
    max_h = max(o.horas for o in validas) or 1

    def nota(o):
        return peso_custo * o.custo / max_c + (1 - peso_custo) * o.horas / max_h

    return {
        "distancia_km": dist,
        "opcoes": {o.modal: asdict(o) for o in opcoes},
        "melhor_custo": min(validas, key=lambda o: o.custo).modal,
        "melhor_tempo": min(validas, key=lambda o: o.horas).modal,
        "recomendado": min(validas, key=nota).modal,
        "peso_custo": peso_custo,
    }


# ---------------------------------------------------------------------
# Preço de combustível por estado (US11)
# ---------------------------------------------------------------------

def precos_por_uf(estimador: EstimadorPreco, atributos: pd.DataFrame,
                  preco_nacional: float = PRECO_GASOLINA_NACIONAL) -> dict[str, float]:
    """Preço estimado por estado, dado o preço nacional de referência.

    Usa a diferença recente de cada estado (última semana da série) como
    entrada do modelo, aplicada ao preço nacional atual.
    """
    ultima = atributos.sort_values("data").groupby("uf").tail(1).copy()
    ultima["nacional"] = preco_nacional
    previsto = estimador.prever(ultima)
    return {uf: round(float(p), 3) for uf, p in zip(ultima["uf"], previsto)}


# ---------------------------------------------------------------------
# Pacote de dados do produto
# ---------------------------------------------------------------------

def _limpar(v) -> str:
    t = str(v if v is not None else "").strip()
    return "" if t.lower() in ("nan", "none") else t


def _titulo(v) -> str:
    t = _limpar(v).title()
    for p in (" Do ", " Da ", " De ", " Dos ", " Das ", " E "):
        t = t.replace(p, p.lower())
    return t


_GENERICOS = {"MATRIZ", "SEDE", "FILIAL", "", "NAN", "NONE"}


def _nome_agencia(bruto, bairro, municipio) -> str:
    """Remove a UF repetida no fim ("AGUAI-SP") e troca nomes genéricos
    como "MATRIZ" pelo bairro."""
    t = re.sub(r"\s*[-/]\s*[A-Z]{2}\.?\s*$", "", _limpar(bruto).upper()).strip(" .-/")
    return (_titulo(bairro) or municipio) if t in _GENERICOS else _titulo(t)


def montar_pacote(agencias: pd.DataFrame, aeroportos: pd.DataFrame,
                  estados: list, cidades: list, precos_uf: dict[str, float],
                  avaliacoes: list, gerado_em: str) -> dict:
    """Estrutura única consumida pela interface. Trocar este pacote por uma
    API com o mesmo formato não exige mudança nas telas."""
    lista_ag = [{
        "id": f"{int(a.regional_id)}-{int(a.cod_compe_ag)}-{i}",
        "codigo": int(a.cod_compe_ag),
        "nome": _nome_agencia(a.nome_agencia, a.bairro, a.municipio_nome),
        "endereco": _titulo(a.endereco), "bairro": _titulo(a.bairro),
        "municipio": a.municipio_nome, "uf": a.uf, "cep": _limpar(a.cep),
        "lat": round(float(a.lat), 5), "lon": round(float(a.lon), 5),
        "precisao": a.precisao, "regional": int(a.regional_id),
        "prioridade": a.prioridade, "dataLimite": a.data_limite, "ultimaVisita": a.ultima_visita,
    } for i, a in enumerate(agencias.itertuples())]

    regionais = []
    for rid, g in agencias.groupby("regional_id"):
        sede_mun = g["municipio_nome"].value_counts().index[0]
        sede = g[g["municipio_nome"] == sede_mun].iloc[0]
        regionais.append({
            "id": int(rid), "nome": g["regional"].iloc[0],
            "sede": {"municipio": sede_mun, "uf": sede["uf"],
                     "lat": round(float(sede["lat"]), 5), "lon": round(float(sede["lon"]), 5)},
            "agencias": int(len(g)), "municipios": int(g["municipio_nome"].nunique()),
            "ufs": sorted(g["uf"].unique().tolist()), "extensaoKm": round(extensao_km(g)),
        })
    regionais.sort(key=lambda r: r["nome"])

    lista_aero = [{
        "iata": r["IATA"], "nome": _limpar(r["Nome do Aeroporto"]),
        "municipio": _titulo(r["Cidade"]), "uf": r["UF"],
        "lat": round(float(r["Latitude"]), 5), "lon": round(float(r["Longitude"]), 5),
    } for _, r in aeroportos.iterrows()]

    return {
        "geradoEm": gerado_em,
        "instituicao": "Itaú Unibanco",
        "estados": estados,
        "cidades": cidades,
        "parametros": {
            "carro": {"precoGasolinaLitro": PRECO_GASOLINA_NACIONAL, "consumoKmLitro": 12.0,
                      "pedagioPorKm": 0.05, "velocidadeKmh": 80.0, "maxKmDia": 700.0},
            "onibus": {"a": Onibus.A, "b": Onibus.B, "c": Onibus.C, "velocidadeKmh": Onibus.VELOCIDADE},
            "aviao": {"a": Aviao.A, "b": Aviao.B, "c": Aviao.C, "velocidadeKmh": Aviao.VELOCIDADE,
                      "taxiHoras": Aviao.TAXI_H, "overheadAeroportoHoras": Aviao.OVERHEAD_H,
                      "distanciaMinimaKm": Aviao.MINIMO_KM},
            "fatorSinuosidade": FATOR_SINUOSIDADE,
            "precoGasolinaPorUf": precos_uf,
            "modeloPreco": [asdict(a) for a in avaliacoes],
            "fontes": {
                "agencias": "Bacen, agências em funcionamento, posição 29/11/2024",
                "combustivel": "ANP, síntese semanal de preços",
                "onibus": "ANTT, Anuário Estatístico do Transporte Rodoviário",
                "aviao": "ANAC, tarifa média doméstica",
            },
        },
        "regionais": regionais,
        "agencias": lista_ag,
        "aeroportos": lista_aero,
    }


def gravar_pacote(pacote: dict, caminho: str) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(pacote, f, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------
# Montagem do produto
# ---------------------------------------------------------------------

def montar_produto(pacote_json: str, pasta_fonte: str, destino: str) -> int:
    """Injeta o pacote e os módulos JavaScript no template do protótipo e
    grava um HTML único, autocontido. Devolve o tamanho em bytes."""
    import os

    def ler(nome):
        with open(os.path.join(pasta_fonte, nome), encoding="utf-8") as f:
            return f.read()

    motor = ler("motor.js").split('if (typeof module !== "undefined")')[0].rstrip()
    html = (ler("app.template.html")
            .replace("__DADOS__", pacote_json)
            .replace("__MOTOR__", motor)
            .replace("__CSS_RESULTADO__", ler("resultado.css"))
            .replace("__ROTEIRO__", ler("roteiro.js"))
            .replace("__MAPA__", ler("mapa.js"))
            .replace("__TELAS__", ler("telas_resultado.js"))
            .replace("__EXTRAS__", ler("telas_extras.js")))
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.getsize(destino)
