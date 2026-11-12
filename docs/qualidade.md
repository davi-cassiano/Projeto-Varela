# Qualidade de dados

Entregável da Aula 9 · Governança de Dados e Qualidade

## 1. Governança: quem responde pelo quê

| Papel | Quem | Responsabilidade no projeto |
| --- | --- | --- |
| Dono dos dados de agências | Gabriel | Cadastro do Bacen, coordenadas, regra dos 30 km, riscos R1 e R7 |
| Dono dos dados de preços e do modelo | Luca | Série da ANP, atributos sem vazamento, métricas por sprint, riscos R2 e R4 |
| Dono do negócio e da rota | Victor | Prioridade e periodicidade simuladas, modais, riscos R3 e R5 |
| Guardião do repositório | Davi | Branches, revisão de PR, CI, prazo, risco R6 |

**Política de dados pessoais (LGPD, Lei Geral de Proteção de Dados).** O MVP só usa
bases públicas de pessoa jurídica. Agenda e histórico do gerente, que seriam
dados pessoais, ficam fora até haver base legal e acesso mínimo definidos
(risco R7, requisito RNF08).

## 2. Regras de qualidade

Seis regras, em `src/validate.py` (Python) e `sql/qualidade.sql` (SQL), cobrindo as
dimensões da aula. Cada regra tem limite explícito; o relatório é gerado por
`python -m src.validate` e gravado em `dados/saida/relatorio_qualidade.md`.

| # | Dimensão | Base | Regra | Limite |
| --- | --- | --- | --- | --- |
| 1 | Unicidade | agências | Um registro por código COMPE | 0 repetidos |
| 2 | Completude | agências | Colunas obrigatórias preenchidas | ≤ 1% de nulos por coluna |
| 3 | Validade | agências | UF nas 27 siglas, CEP com 8 dígitos, coordenadas dentro do Brasil | 0 inválidos |
| 4 | Consistência | agências | Código IBGE do município pertence à UF informada | 0 divergências |
| 5 | Consistência | agências, após preparação | Coordenada de bairro a no máximo 30 km do município | descartes ≤ 10% e cobertura de bairro ≥ 70% |
| 6 | Pontualidade | preços | Uma linha por semana×estado, preço plausível, semana mais recente há ≤ 90 dias | 0 duplicadas, 0 fora de R$ 0,50–15,00, ≤ 90 dias |

## 3. Resultado da execução de 12/11/2026

| # | Regra | Medido | Situação |
| --- | --- | --- | --- |
| 1 | Um registro por agência | 0 repetidos em 2.010 | ✅ Passou |
| 2 | Colunas obrigatórias preenchidas | pior coluna: `bairro`, 0,05% (1 agência) | ✅ Passou |
| 3 | UF, CEP e coordenadas válidos | 0 inválidos | ✅ Passou |
| 4 | Município pertence à UF | 0 divergências | ✅ Passou |
| 5 | Coordenada de bairro coerente com o município | **descartes 14,4% (290 de 2.010)** · cobertura 74,7% | ❌ Falhou |
| 6 | Série de preços única, válida e atual | 0 duplicadas · 0 fora da faixa · **última semana em 01/05/2021** | ❌ Falhou |

**4 de 6 regras passaram.** As duas falhas já estavam mapeadas como riscos (R1 e R2)
e como stories (US10 e US14); agora têm número, limite e dono.

## 4. SBAR da pior falha: a série de preços parou em maio de 2021

SBAR é um formato de quatro passos para comunicar um incidente: **S**ituação,
**B**ackground (contexto), **A**valiação e **R**ecomendação. Escolhemos a regra 6
como a pior falha porque ela afeta todo custo de carro que o produto calcula, enquanto
a regra 5 afeta a distância de 290 agências e tem correção já em andamento (Issue #16).

| | |
| --- | --- |
| **S · Situação** | A validação de 12/11/2026 reprovou a série de preços na pontualidade: a semana mais recente é de 01/05/2021, com 2.021 dias de idade, contra o limite de 90 dias. Unicidade e faixa de preço passaram. |
| **B · Contexto** | A série foi obtida em um arquivo público consolidado (2004–2021). O modelo de preço (US11) foi treinado e validado nela, com MAE de R$ 0,095/L. O produto não usa o nível de preço da série: aplica a **diferença de cada estado** sobre um preço nacional informado por parâmetro (`--preco-gasolina`), hoje R$ 6,70. O risco R2 já previa a defasagem. |
| **A · Avaliação** | Gravidade média. A premissa de que a diferença entre estados é estável não foi verificada com dados posteriores a 2021; se ela tiver mudado, o custo por estado fica enviesado sem que nenhum teste acuse. O preço nacional por parâmetro depende de alguém lembrar de atualizá-lo. |
| **R · Recomendação** | (1) Até a próxima sprint, Luca atualiza o preço nacional pela síntese semanal da ANP antes de cada geração do produto e registra o valor no `relatorio_execucao.json` — já implementado, falta a rotina. (2) Na Sprint 2, Luca baixa a série atual da ANP (2022 em diante), roda `python -m src.validate` e compara a diferença por estado recente com a prevista: se o MAE passar de R$ 0,25/L (RNF06), o modelo é retreinado. (3) Automatizar a ingestão da ANP é a US14, Onda 2. Indicador: regra 6 passando no relatório de qualidade. |

## 5. Monitoramento: o que repetir a cada carga

| O quê | Como | Limite | Responsável |
| --- | --- | --- | --- |
| Volume | Número de agências e de semanas×estado após a ingestão | ±10% em relação à carga anterior | Gabriel / Luca |
| Frescor | Regra 6 | 90 dias | Luca |
| Esquema | `exigir_colunas` no `ingest.py` quebra a carga se faltar coluna | 0 colunas ausentes | Gabriel |
| Distribuição | MAE do modelo por mês (`train.erro_por_mes`) | alerta acima de R$ 0,25/L (RNF06) | Luca |
| Regras de negócio | `python -m src.validate` no CI, a cada pull request, contra a linha de base `dados/colab/qualidade_linha_de_base.json` | falha conhecida não bloqueia; regra que regrediu bloqueia o merge | Davi |

O relatório de cada execução fica em `dados/saida/relatorio_qualidade.json`; guardar
o histórico permite ver a qualidade ao longo do tempo, como a aula recomenda.

## 6. Qualidade de código

- **Análise estática:** `ruff check src/ tests/` (configuração em `pyproject.toml`).
- **Testes:** `pytest --cov=src --cov-fail-under=70`. Pirâmide: testes unitários de
  features com casos de borda e parametrização; teste de fumaça do pipeline com uma
  amostra pequena e fixa (`tests/test_pipeline.py`); o critério da US11 como teste de modelo.
- **CI:** `.github/workflows/qualidade.yml` roda ruff, pytest com cobertura e a
  validação de dados em cada push e pull request.
- **Revisão de código:** lista da aula — correção e legibilidade, testes, dados e
  vazamento, segurança e privacidade, arquitetura (SOLID) — aplicada no PR #15
  (três comentários do Davi, resolvidos) e no PR desta entrega.
