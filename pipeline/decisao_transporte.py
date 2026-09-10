"""
decisao_transporte.py

Modulo de estimativa de custo/tempo de deslocamento entre dois pontos
quaisquer no Brasil (lat/lon), para os modais Carro, Onibus e Aviao,
com recomendacao do melhor modal.

Todos os parametros sao ESTIMATIVAS calibradas com dados publicos reais
(ANP para combustivel, ANTT para onibus, ANAC para tarifa aerea media).
Nao substituem uma cotacao real - ver README/Notas do dataset para as
fontes e limitacoes de cada modelo.

Uso basico:
    from decisao_transporte import comparar_modais

    origem = (-23.5505, -46.6333)   # lat, lon de Sao Paulo
    destino = (-22.9068, -43.1729)  # lat, lon do Rio de Janeiro

    resultado = comparar_modais(origem, destino)
    print(resultado)
"""

import math
from dataclasses import dataclass, asdict


# ---------------------------------------------------------------------
# Parametros calibrados (ver Notas do dataset para as fontes)
# ---------------------------------------------------------------------

# --- Carro ---
PRECO_GASOLINA_RS_L = 6.70       # R$/L, media ANP 2026
CONSUMO_KM_L = 12.0              # km/l medio rodoviario
PEDAGIO_RS_KM = 0.05             # R$/km medio em rodovias federais pedagiadas
VEL_MEDIA_CARRO_KMH = 80.0       # velocidade de cruzeiro em rodovia
MAX_KM_DIA_SEGURO = 700.0        # limite recomendado de conducao segura/dia
FATOR_SINUOSIDADE = 1.25         # estrada real / linha reta

# --- Onibus (calibrado com faixas reais do Anuario Estatistico da ANTT) ---
_ONIBUS_A, _ONIBUS_B, _ONIBUS_C = 1.43124328, 1.48070929, 0.74592568
VEL_MEDIA_ONIBUS_KMH = 62.0       # velocidade media rodoviaria com paradas

# --- Aviao (calibrado com a tarifa media domestica real da ANAC) ---
_AVIAO_A, _AVIAO_B, _AVIAO_C = 174.52140223, 2.9577578, 0.68403605
VEL_CRUZEIRO_AVIAO_KMH = 800.0
TAXI_H_AVIAO = 0.4
OVERHEAD_AEROPORTO_H = 3.0        # check-in + deslocamento + espera + desembarque
DISTANCIA_MIN_AVIAO_KM = 150.0    # abaixo disso, nao ha rota aerea comercial pratica


def haversine_km(origem, destino):
    """Distancia em linha reta (km) entre dois pontos (lat, lon)."""
    lat1, lon1 = origem
    lat2, lon2 = destino
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@dataclass
class OpcaoModal:
    disponivel: bool
    custo_rs: float
    tempo_h: float
    observacao: str = ""


def estimar_carro(dist_linha_reta_km: float) -> OpcaoModal:
    dist_rodo = dist_linha_reta_km * FATOR_SINUOSIDADE
    custo = dist_rodo * (PRECO_GASOLINA_RS_L / CONSUMO_KM_L + PEDAGIO_RS_KM)
    tempo = dist_rodo / VEL_MEDIA_CARRO_KMH
    obs = "Requer pernoite/parada de descanso" if dist_rodo > MAX_KM_DIA_SEGURO else ""
    return OpcaoModal(True, round(custo, 2), round(tempo, 1), obs)


def estimar_onibus(dist_linha_reta_km: float) -> OpcaoModal:
    dist_rodo = dist_linha_reta_km * FATOR_SINUOSIDADE
    custo = _ONIBUS_A + _ONIBUS_B * (dist_rodo ** _ONIBUS_C)
    tempo = dist_rodo / VEL_MEDIA_ONIBUS_KMH
    if dist_rodo > 3000:
        obs = "Linha direta pouco provavel nessa distancia (estimativa teorica)"
    elif dist_rodo > 1200:
        obs = "Linha longa - pode exigir conexao"
    else:
        obs = ""
    return OpcaoModal(True, round(custo, 2), round(tempo, 1), obs)


def estimar_aviao(dist_linha_reta_km: float) -> OpcaoModal:
    if dist_linha_reta_km < DISTANCIA_MIN_AVIAO_KM:
        return OpcaoModal(False, 0.0, 0.0, "Distancia curta demais para voo comercial")
    custo = _AVIAO_A + _AVIAO_B * (dist_linha_reta_km ** _AVIAO_C)
    tempo_voo = dist_linha_reta_km / VEL_CRUZEIRO_AVIAO_KMH + TAXI_H_AVIAO
    tempo = tempo_voo + OVERHEAD_AEROPORTO_H
    obs = "" if dist_linha_reta_km <= 2500 else "Pode exigir conexao"
    return OpcaoModal(True, round(custo, 2), round(tempo, 1), obs)


def comparar_modais(origem, destino, peso_custo: float = 0.5):
    """
    Compara Carro, Onibus e Aviao entre dois pontos (lat, lon).

    peso_custo: entre 0 e 1. 1.0 = otimiza so custo, 0.0 = otimiza so tempo,
                0.5 = balanceado (padrao).

    Retorna um dict com a distancia, as opcoes por modal e as recomendacoes.
    """
    dist = haversine_km(origem, destino)

    opcoes = {
        "Carro": estimar_carro(dist),
        "Onibus": estimar_onibus(dist),
        "Aviao": estimar_aviao(dist),
    }
    disponiveis = {k: v for k, v in opcoes.items() if v.disponivel}

    melhor_custo = min(disponiveis, key=lambda k: disponiveis[k].custo_rs)
    melhor_tempo = min(disponiveis, key=lambda k: disponiveis[k].tempo_h)

    max_c = max(v.custo_rs for v in disponiveis.values())
    max_t = max(v.tempo_h for v in disponiveis.values())
    peso_tempo = 1 - peso_custo

    def score(v):
        c_norm = v.custo_rs / max_c if max_c else 0
        t_norm = v.tempo_h / max_t if max_t else 0
        return peso_custo * c_norm + peso_tempo * t_norm

    recomendado = min(disponiveis, key=lambda k: score(disponiveis[k]))

    return {
        "distancia_km": round(dist, 1),
        "opcoes": {k: asdict(v) for k, v in opcoes.items()},
        "melhor_custo": melhor_custo,
        "melhor_tempo": melhor_tempo,
        "recomendado": recomendado,
        "peso_custo_usado": peso_custo,
    }


if __name__ == "__main__":
    import json

    sao_paulo = (-23.5505, -46.6333)
    rio = (-22.9068, -43.1729)
    manaus = (-3.1190, -60.0217)

    print("=== Sao Paulo -> Rio de Janeiro ===")
    print(json.dumps(comparar_modais(sao_paulo, rio), indent=2, ensure_ascii=False))

    print("\n=== Sao Paulo -> Manaus (peso_custo=0.8, prioriza economia) ===")
    print(json.dumps(comparar_modais(sao_paulo, manaus, peso_custo=0.8), indent=2, ensure_ascii=False))
