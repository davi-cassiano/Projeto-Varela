"""
monitor.py — Monitoramento do modelo de preço (US14).

Baixa a publicação semanal da ANP, reconstrói os atributos, reavalia o
modelo da US11 nas últimas semanas e emite alerta quando o erro passa do
limite do requisito RNF06 (R$ 0,25/L). É o que a ingestão programada
(.github/workflows/atualizar-precos.yml) roda toda semana.

    python -m src.monitor                 # baixa se o cache tiver mais de 7 dias
    python -m src.monitor --sem-download  # usa o cache local

Sai com código 1 quando há alerta, para o agendador avisar o dono (Luca).
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import date

import pandas as pd

from . import features, ingest, train

LIMITE_ALERTA = 0.25   # RNF06: MAE acima disso nas últimas semanas dispara alerta
SEMANAS_RECENTES = 4   # janela curta: choque de preço
SEMANAS_LONGAS = 12    # janela longa: deriva lenta (revisão do PR #29)


@dataclass
class Monitoramento:
    ultima_semana: str
    semanas_avaliadas: int
    mae_recente: float
    mae_baseline_recente: float
    preco_nacional_atual: float
    alerta: bool
    limite: float = LIMITE_ALERTA
    semanas_longas: int = SEMANAS_LONGAS
    mae_longo: float = 0.0
    alerta_longo: bool = False


def _mae_ultimas(atributos: pd.DataFrame, datas: list, semanas: int) -> tuple[float, float]:
    """Treina com tudo antes das últimas `semanas` e mede o erro nelas."""
    corte = datas[-semanas]
    treino, teste = atributos[atributos["data"] < corte], atributos[atributos["data"] >= corte]
    modelo = train.avaliar(train.RegressaoEstado().ajustar(treino), teste)
    baseline = train.avaliar(train.BaselineNacional().ajustar(treino), teste)
    return modelo.mae, baseline.mae


def avaliar_recente(atributos: pd.DataFrame, semanas: int = SEMANAS_RECENTES,
                    limite: float = LIMITE_ALERTA, semanas_longas: int = SEMANAS_LONGAS) -> Monitoramento:
    """Duas janelas: a curta pega um choque de preço; a longa, uma deriva
    lenta que semana a semana fica abaixo do limite. Qualquer uma acima do
    limite dispara o alerta (é o erro que o produto teria cometido se tivesse
    sido gerado antes dessas semanas, com o modelo da US11)."""
    datas = sorted(atributos["data"].unique())
    mae_curto, mae_base = _mae_ultimas(atributos, datas, semanas)
    mae_longo, _ = _mae_ultimas(atributos, datas, min(semanas_longas, len(datas) - 1))
    ultima = atributos[atributos["data"] == datas[-1]]
    return Monitoramento(
        ultima_semana=pd.Timestamp(datas[-1]).date().isoformat(),
        semanas_avaliadas=semanas,
        mae_recente=round(mae_curto, 3), mae_baseline_recente=round(mae_base, 3),
        preco_nacional_atual=round(float(ultima["nacional"].iloc[0]), 3),
        alerta=bool(mae_curto > limite or mae_longo > limite), limite=limite,
        semanas_longas=semanas_longas, mae_longo=round(mae_longo, 3), alerta_longo=bool(mae_longo > limite),
    )


def preco_nacional_atual(precos: pd.DataFrame) -> float:
    """Média dos estados na semana mais recente da série."""
    ultima = precos[precos["data"] == precos["data"].max()]
    return round(float(ultima["preco"].mean()), 3)


def relatorio_markdown(m: Monitoramento, gerado_em: date) -> str:
    situacao = "🚨 ALERTA: reavaliar e retreinar o modelo (RNF06)" if m.alerta else "✅ dentro do limite"
    return "\n".join([
        "# Monitoramento do modelo de preço", "",
        f"Gerado em {gerado_em:%d/%m/%Y} por `python -m src.monitor`.", "",
        "| Indicador | Valor |", "| --- | --- |",
        f"| Última semana publicada pela ANP | {m.ultima_semana} |",
        f"| Preço nacional atual (média dos estados) | R$ {m.preco_nacional_atual:.3f}/L |",
        f"| MAE do modelo nas últimas {m.semanas_avaliadas} semanas | R$ {m.mae_recente:.3f}/L |",
        f"| MAE do baseline nas mesmas semanas | R$ {m.mae_baseline_recente:.3f}/L |",
        f"| MAE do modelo nas últimas {m.semanas_longas} semanas (deriva lenta) | R$ {m.mae_longo:.3f}/L |",
        f"| Limite de alerta (RNF06) | R$ {m.limite:.2f}/L |",
        f"| Situação | {situacao} |", "",
    ])


def main() -> None:
    p = argparse.ArgumentParser(description="Monitoramento do modelo de preço (US14)")
    p.add_argument("--sem-download", action="store_true", help="usar o cache local da ANP")
    p.add_argument("--saida", default=os.path.join("dados", "saida"))
    args = p.parse_args()

    precos = ingest.carregar_precos(ingest.AnpSource(atualizar=not args.sem_download))
    m = avaliar_recente(features.atributos_preco(precos))
    os.makedirs(args.saida, exist_ok=True)
    hoje = date.today()
    with open(os.path.join(args.saida, "monitor_precos.json"), "w", encoding="utf-8") as f:
        json.dump({"gerado_em": hoje.isoformat(), **asdict(m)}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.saida, "monitor_precos.md"), "w", encoding="utf-8") as f:
        f.write(relatorio_markdown(m, hoje))
    print(relatorio_markdown(m, hoje))
    raise SystemExit(1 if m.alerta else 0)


if __name__ == "__main__":
    main()
