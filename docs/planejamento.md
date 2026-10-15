# Planejamento e Riscos

Checkpoint das Aulas 4, 5 e 6 · Parte 3 — Planejamento e Riscos

**Regra de rastreabilidade:** cada pacote de trabalho da WBS aponta para uma
user story do backlog (`docs/backlog.md` e Issues #1 a #14), e cada story aponta
para uma funcionalidade do Canvas MVP.

---

## 1. WBS — Estrutura Analítica do Projeto

WBS (*Work Breakdown Structure*) é a decomposição do projeto em pacotes de
trabalho pequenos o bastante para estimar e atribuir. Quatro níveis, como na
Aula 6: projeto → fases (as do CRISP-DM, mais gestão) → entregáveis → pacotes.

**Nível 1 — Sistema de Roteirização de Visitas às Agências**

| Nível 2 · Fase | Nível 3 · Entregável | Nível 4 · Pacote de trabalho | Story | Situação |
| --- | --- | --- | --- | --- |
| **1. Entendimento do negócio** | Canvas MVP e backlog | 1.1 Definir persona, hipótese e métricas de validação | US07, US08 | Concluído |
| | | 1.2 Redigir, revisar (INVEST) e priorizar as user stories | US01–US14 | Concluído |
| **2. Entendimento dos dados** | Relatório de qualidade | 2.1 Avaliar completude e consistência da base do Bacen | US10 | Concluído |
| | | 2.2 Avaliar cobertura e lacunas da série da ANP | US11 | Concluído |
| **3. Preparação dos dados** | `ingest.py` e `features.py` com testes | 3.1 Implementar a ingestão com a abstração `DataSource` | US10, US11 | Sprint 1 |
| | | 3.2 Implementar a escada de precisão das coordenadas | US10 | Sprint 1 |
| | | 3.3 Validar o desvio de 30 km e corrigir abreviações | US10 | Sprint 1 |
| | | 3.4 Gerar atributos do modelo sem vazamento temporal | US11 | Sprint 1 |
| **4. Modelagem** | `train.py` e `serve.py` com testes | 4.1 Treinar o k-means das regionais com teto e piso | US01 | Sprint 1 |
| | | 4.2 Treinar e comparar os modelos de preço por estado | US11 | Sprint 1 |
| | | 4.3 Implementar os modais e a comparação por trecho | US03, US05 | Sprint 1 |
| | | 4.4 Implementar a sequência provisória de visitas | US04 | Protótipo |
| | | 4.5 Otimizar a sequência de visitas | US12 | Onda 2 |
| **5. Avaliação** | Critérios de aceite verificados | 5.1 Validar o modelo de preço contra o baseline | US11 | Sprint 1 |
| | | 5.2 Calcular o cenário de referência | US08 | Protótipo |
| | | 5.3 Calcular totais, diárias e economia | US07 | Protótipo |
| **6. Entrega** | Protótipo navegável | 6.1 Construir seleção de agências e restrições | US01, US02 | Protótipo |
| | | 6.2 Construir escolha de objetivo com prévia | US03 | Protótipo |
| | | 6.3 Construir resultado, mapa e detalhe do trecho | US05, US06 | Protótipo |
| | | 6.4 Salvar e exportar o planejamento | US09 | Protótipo |
| | | 6.5 Construir o painel consolidado da regional | US13 | Onda 2 |
| | | 6.6 Automatizar a atualização de preços | US14 | Onda 2 |
| **7. Gestão** | Plano e controle | 7.1 Estimar o backlog em Planning Poker | US01–US14 | Sprint 1 |
| | | 7.2 Revisar e integrar o pull request | US10, US11 | Sprint 1 |
| | | 7.3 Revisar a matriz de riscos a cada sprint | transversal | Contínuo |

"Protótipo" indica que a story já está navegável no protótipo de interface
entregue no checkpoint anterior.

### Conferência da regra dos 100%

Toda story aparece em pelo menos um pacote, e nenhum pacote existe sem story
(exceto 7.3, que é transversal).

| Story | Pacotes | | Story | Pacotes |
| --- | --- | --- | --- | --- |
| US01 | 1.2, 4.1, 6.1 | | US08 | 1.1, 5.2 |
| US02 | 1.2, 6.1 | | US09 | 1.2, 6.4 |
| US03 | 1.2, 4.3, 6.2 | | US10 | 2.1, 3.1, 3.2, 3.3, 7.2 |
| US04 | 1.2, 4.4 | | US11 | 2.2, 3.1, 3.4, 4.2, 5.1, 7.2 |
| US05 | 1.2, 4.3, 6.3 | | US12 | 1.2, 4.5 |
| US06 | 1.2, 6.3 | | US13 | 1.2, 6.5 |
| US07 | 1.1, 5.3 | | US14 | 1.2, 6.6 |

---

## 2. Estimativas

### Escala e referência

Story points na escala de Fibonacci: 1, 2, 3, 5, 8, 13. A **US01** é a story de
referência, com **3 pontos**; as demais são estimadas por comparação com ela.
Qualquer story com 13 pontos ou mais é dividida.

### Pontos por story

Valores finais, fechados no Planning Poker (registro na seção seguinte).

| Story | Pontos | Justificativa da comparação com a US01 |
| --- | --- | --- |
| US01 · Selecionar agências | 3 | Referência |
| US02 · Origem, período e restrições | 3 | Mesmo porte; a trava de viabilidade compensa a lista mais simples |
| US03 · Escolher o objetivo | 2 | Menor: a lógica de peso já existe no modelo de transporte |
| US04 · Sequência de visitas | 5 | Maior: distribui em dias respeitando teto e janela |
| US05 · Modal por trecho | 3 | Mesmo porte: três classes com o mesmo contrato |
| US06 · Detalhe do trecho | 3 | Mesmo porte: exibição, mais a regra de empate técnico |
| US07 · Totais e economia | 2 | Menor: soma, mais a regra de diária |
| US08 · Cenário de referência | 3 | Mesmo porte: reaproveita o cálculo da US07 |
| US09 · Salvar e exportar | 5 | Maior: salvar, reabrir e exportar em formato legível fora do sistema (revisto no Poker, de 3 para 5) |
| US10 · Coordenadas das agências | 5 | Maior: três níveis, validação de desvio e correção de abreviações |
| US11 · Preço de combustível por estado | 8 | Bem maior: modelo, validação temporal, baseline e integração |
| US12 · Sequência otimizada | 8 | Bem maior e incerta; escopo limitado no Poker a vizinho mais próximo + 2-opt para caber em 8 |
| US13 · Painel da regional | 3 | Mesmo porte |
| US14 · Preços automáticos | 5 | Maior e dependente de fonte externa |

**Total:** Onda 1 com 42 pontos · Onda 2 com 16 pontos · backlog com 58 pontos.

### Registro do Planning Poker

Votação simultânea em cartas de Fibonacci. Votos vizinhos (como 2 e 3) foram
resolvidos com uma conversa rápida; votos distantes (como 3 e 8) levaram a uma
segunda rodada, depois de quem votou o menor e quem votou o maior explicarem o
motivo. A US01 não foi votada: é a referência, com 3 pontos.

| Story | 1ª rodada (Davi · Gabriel · Luca · Victor) | 2ª rodada | Final |
| --- | --- | --- | --- |
| US02 | 3 · 3 · 3 · 3 | — | **3** |
| US03 | 2 · 2 · 3 · 2 | — | **2** |
| US04 | 3 · 5 · 8 · 5 | 5 · 5 · 5 · 5 | **5** |
| US05 | 3 · 3 · 3 · 3 | — | **3** |
| US06 | 2 · 3 · 3 · 3 | — | **3** |
| US07 | 2 · 2 · 2 · 2 | — | **2** |
| US08 | 3 · 2 · 3 · 3 | — | **3** |
| US09 | 3 · 3 · 5 · 8 | 5 · 5 · 5 · 5 | **5** |
| US10 | 5 · 5 · 8 · 5 | — | **5** |
| US11 | 5 · 8 · 13 · 8 | 8 · 8 · 8 · 8 | **8** |
| US12 | 8 · 13 · 8 · 13 | 8 · 8 · 8 · 8 | **8** |
| US13 | 3 · 3 · 2 · 3 | — | **3** |
| US14 | 5 · 8 · 5 · 5 | — | **5** |

**Divergências que mudaram a conversa:**

- **US04 (3 a 8).** O 3 considerava só ordenar as agências por ângulo. O 8
  lembrou que a sequência precisa ser quebrada em dias respeitando o teto de
  horas e a janela de atendimento. Ficou 5: a regra de dias é mais trabalho que
  a US01, mas a lógica de ordenação já existe.
- **US09 (3 a 8).** O 3 pensava só em "salvar". O 8 incluiu reabrir um
  planejamento antigo quando a base de agências mudou. Ficou 5, com a decisão de
  que reabrir mostra um aviso se alguma agência saiu da base, sem tentar
  reconciliar.
- **US11 (5 a 13).** O 13 refletia a incerteza de um modelo ainda não testado.
  O argumento que fechou em 8: o baseline já tinha sido medido (MAE de
  R$ 0,20/L), então a meta era conhecida. Um 13 obrigaria a dividir a story.
- **US12 (8 e 13).** Empate. O grupo preferiu reduzir o escopo a dividir:
  vizinho mais próximo seguido de 2-opt (troca de pares de trechos que se
  cruzam). Algoritmos mais sofisticados viram story nova, se a métrica de
  economia pedir.

**Efeito no plano:** a US09 subiu de 3 para 5. O backlog passou de 56 para 58
pontos, a Sprint 3 de 14 para 16 e a previsão continua em 4 sprints.

### Capacidade

| Item | Valor |
| --- | --- |
| Pessoas | 4 |
| Duração da sprint | 2 semanas |
| Velocidade assumida na Sprint 1 | **20 pontos** |
| Premissa | Cada integrante concilia o projeto com outras disciplinas e provas; a velocidade é hipótese e será recalibrada ao fim da Sprint 1 |
| Previsão | 58 pontos ÷ 20 por sprint = 2,9, ou seja, **pelo menos 3 sprints**; encaixando as stories inteiras, 4 (seção 5) |

---

## 3. Matriz de riscos

Probabilidade e impacto em baixa (1), média (2) e alta (3). Exposição =
probabilidade × impacto. Resposta: evitar, mitigar, transferir ou aceitar.

| ID | Risco | Tipo | Prob. | Impacto | Exposição | Resposta | Ação | Responsável |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **R1** | Coordenadas de agências erradas por colisão de nomes de bairro | Dados | Média | Alto | **6** | Mitigar | Descartar bairro a mais de 30 km do município; marcar precisão na interface; teste automático | Gabriel |
| **R2** | Série da ANP termina em 2021, sem preços recentes | Dados | Alta | Médio | **6** | Mitigar | Modelar a diferença entre estados, mais estável que o nível de preço; automatizar a ingestão na US14 | Luca |
| **R3** | Prioridade e periodicidade de visita não existem em base pública | Dados | Alta | Alto | **9** | Transferir | A área de negócio fornece o dado no piloto; até lá, campos simulados e declarados como tal | Victor |
| **R4** | Modelo de preço perde precisão num choque de mercado (drift) | Modelo | Média | Médio | **4** | Mitigar | Reavaliar a cada atualização da série; alerta acima de R$ 0,25/L | Luca |
| **R5** | Sequência por varredura gera rotas com ida e volta | Modelo | Alta | Médio | **6** | Aceitar | Declarado na interface e no backlog; otimização na US12 | Victor |
| **R6** | Sprint 1 cheia demais para o grupo, que concilia provas | Prazo | Média | Médio | **4** | Mitigar | Sprint 1 com 19 dos 20 pontos; story maior (US11) puxada primeiro | Davi |
| **R7** | Agenda e histórico do gerente seriam dados pessoais em produção | Privacidade | Baixa | Alto | **3** | Evitar | MVP sem dados pessoais; base legal e acesso mínimo antes da implantação | Gabriel |

Riscos de dados: R1, R2 e R3. Riscos de modelo: R4 e R5.

### Posição na matriz

| Probabilidade ↓ · Impacto → | Baixo | Médio | Alto |
| --- | --- | --- | --- |
| **Alta** | | R2, R5 | **R3** |
| **Média** | | R4, R6 | R1 |
| **Baixa** | | | R7 |

Vermelho (exposição 6 ou mais): R1, R2, R3 e R5 — tratados antes ou durante a
Sprint 1. Amarelo (3 a 4): R4, R6 e R7 — com resposta e dono definidos.

**Divisão de responsabilidades:** cada integrante é dono dos riscos da frente
que conduz — Gabriel na base de agências (R1, R7), Luca no modelo de preço
(R2, R4), Victor no negócio e na rota (R3, R5) e Davi na gestão do repositório
e do prazo (R6).

---

## 4. Plano da Sprint 1

**Meta da sprint:** transformar a base de agências e o custo de deslocamento num
pipeline modular e testado, com o preço de combustível por estado validado
contra o baseline.

| Item | Pontos | Pacotes da WBS | Responsável |
| --- | --- | --- | --- |
| US10 · Agências no lugar certo do mapa | 5 | 3.1, 3.2, 3.3 | Gabriel |
| US11 · Preço de combustível por estado | 8 | 3.4, 4.2, 5.1 | Luca |
| US05 · Modal por trecho | 3 | 4.3 | Victor |
| Testes automatizados e pull request revisado | 3 | 7.1, 7.2 | Davi |
| **Total** | **19** | | |

**Capacidade:** 20 pontos. **Selecionado:** 19 pontos.

### Por que estas stories

As stories de interface da Onda 1 já estão navegáveis no protótipo. A Sprint 1
ataca o que sustenta os números exibidos: a localização das agências (R1), o
preço do combustível (R2 e R4) e o cálculo por modal. São também as stories com
critério de métrica de dados e de modelo.

### Definição de pronto

Uma story está pronta quando:

1. O critério de aceite Dado/Quando/Então foi verificado, de preferência por um
   teste automático em `tests/`
2. O código está no módulo da sua responsabilidade (`ingest`, `features`,
   `train` ou `serve`)
3. O pull request foi revisado por outro integrante, com os comentários resolvidos
4. O pipeline roda de ponta a ponta com `python -m src.pipeline`

### Riscos monitorados nesta sprint

R1, R2, R4 e R6.

### Resultado da Sprint 1

| Item | Situação |
| --- | --- |
| US10 | Entregue — 74,7% com coordenada de bairro (meta: 70%) |
| US11 | Entregue — MAE R$ 0,095/L (meta: até R$ 0,15/L e 25% abaixo do baseline) |
| US05 | Entregue — avião indisponível abaixo de 150 km e modal desligado nunca recomendado |
| Testes e PR | 23 testes passando; pull request #15 revisado pelo Davi, três comentários resolvidos e merge feito |

---

## 5. Próximas sprints

As stories de interface da Onda 1 já existem no protótipo; nas próximas
sprints elas passam a ter o critério de aceite validado com um gerente real.

| Sprint | Stories | Pontos |
| --- | --- | --- |
| Sprint 2 | US01, US02, US03, US04, US07, US08 — montagem, sequência e avaliação | 18 |
| Sprint 3 | US06, US09, US12 — detalhe, registro e sequência otimizada | 16 |
| Sprint 4 | US13, US14 — painel e atualização automática de preços | 8 |

Total de 58 pontos em 4 sprints. A velocidade real medida na Sprint 1 recalibra
esta previsão.
