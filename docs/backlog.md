# Backlog — Sistema de Roteirização de Visitas às Agências

Checkpoint das Aulas 4, 5 e 6 · Parte 1 — Engenharia de Requisitos

Persona central: **Rafael Menezes, gerente regional** (definida na Aula 3).
Toda story abaixo nasce de uma funcionalidade do Canvas MVP e é escrita do ponto
de vista do Rafael.

---

## 1. Épicos

Os épicos agrupam as funcionalidades da Onda 1 do Canvas MVP em blocos de valor.

| Épico | Valor de negócio | Funcionalidades do Canvas que agrupa |
| --- | --- | --- |
| **E1 · Montagem do planejamento** | O gerente descreve a viagem que precisa fazer, em vez de montá-la numa planilha | Selecionar agências · informar origem, período e restrições · definir objetivo |
| **E2 · Recomendação da rota** | O sistema propõe a ordem das visitas e o meio de transporte de cada trecho | Gerar sequência · recomendar modal por trecho · exibir distância, tempo e custo |
| **E3 · Avaliação do planejamento** | O gerente sabe quanto a viagem custa e quanto economiza antes de sair | Exibir totais e economia · comparar com cenário de referência · registrar o roteiro |
| **E4 · Dados e modelos** | As estimativas se apoiam em localização e preço confiáveis | Requisitos de dados que sustentam E1, E2 e E3 |

---

## 2. User stories

Formato: Como / Quero / Para, com critério de aceite em Dado / Quando / Então.
Prioridade na ordem do backlog (ver seção 5).

### Onda 1 — MVP

---

#### US01 · Selecionar as agências da minha regional
**Épico:** E1 · **Canvas:** Selecionar/informar agências a visitar

> **Como** Rafael, gerente regional,
> **quero** ver as agências da minha regional e selecionar quais visitar, filtrando por cidade, estado e prioridade,
> **para** montar a viagem só com as agências que precisam de visita.

**Critério de aceite**
- **Dado** a regional Goiânia carregada com suas 35 agências
- **Quando** Rafael filtra por prioridade alta
- **Então** a lista mostra apenas agências de prioridade alta da regional Goiânia, nenhuma de outra regional aparece, e ele consegue marcar várias de uma vez

---

#### US02 · Informar origem, período e restrições da viagem
**Épico:** E1 · **Canvas:** Informar origem, período e restrições de agenda

> **Como** Rafael,
> **quero** informar de onde saio, em que datas posso viajar, quantas visitas faço por dia e quais meios de transporte aceito,
> **para** que a rota recomendada caiba na minha agenda real.

**Critério de aceite**
- **Dado** um período de 5 dias e o limite de 2 visitas por dia
- **Quando** Rafael seleciona 12 agências e tenta avançar
- **Então** o sistema bloqueia o avanço e informa que cabem no máximo 10 visitas nesse período

---

#### US03 · Escolher o objetivo da rota
**Épico:** E1 · **Canvas:** Definir objetivo — menor custo, menor tempo ou combinação

> **Como** Rafael,
> **quero** escolher se a rota deve priorizar menor custo, menor tempo ou um equilíbrio ajustável entre os dois,
> **para** adaptar a viagem à urgência de cada ciclo de visitas.

**Critério de aceite**
- **Dado** o trecho mais longo da regional Araguaína, de 457 km, com carro, ônibus e avião liberados
- **Quando** Rafael define 100% de peso em custo
- **Então** o modal recomendado é o de menor custo do trecho
- **E quando** ele define 100% de peso em tempo, o modal recomendado é o de menor tempo

---

#### US04 · Receber a sequência de visitas
**Épico:** E2 · **Canvas:** Gerar sequência recomendada de visitas

> **Como** Rafael,
> **quero** receber a ordem em que devo visitar as agências selecionadas, distribuída nos dias da viagem,
> **para** não precisar decidir a ordem de cabeça.

**Critério de aceite**
- **Dado** 6 agências selecionadas, 2 delas com prazo de visita vencido, e a regra "priorizar prazos vencidos" ligada
- **Quando** Rafael gera o planejamento
- **Então** cada agência aparece exatamente uma vez, a rota começa e termina na origem, as 2 agências vencidas são visitadas antes das demais, e nenhum dia passa do limite de visitas por dia

> Nota de escopo: nesta onda a sequência usa uma regra de varredura geográfica.
> A otimização da ordem é a US12, na Onda 2.

---

#### US05 · Saber qual meio de transporte usar em cada trecho
**Épico:** E2 · **Canvas:** Recomendar modal por trecho (carro, ônibus, avião)

> **Como** Rafael,
> **quero** que cada trecho da viagem indique se devo ir de carro, ônibus ou avião,
> **para** não escolher o transporte só por hábito.

**Critério de aceite**
- **Dado** um trecho com menos de 150 km
- **Quando** o planejamento é gerado
- **Então** avião não é recomendado nem oferecido como alternativa
- **E dado** que Rafael desligou o ônibus nas restrições, nenhum trecho recomenda ônibus

---

#### US06 · Ver o detalhe de cada trecho
**Épico:** E2 · **Canvas:** Exibir distância, tempo e custo por trecho

> **Como** Rafael,
> **quero** abrir cada trecho e ver distância, tempo, custo, as alternativas descartadas e o motivo da escolha,
> **para** confiar na recomendação e poder justificá-la ao meu gestor.

**Critério de aceite**
- **Dado** um planejamento gerado
- **Quando** Rafael abre um trecho
- **Então** vê origem, destino, modal escolhido, distância, tempo, custo e os três modais lado a lado com o escolhido destacado
- **E quando** a diferença entre o escolhido e o segundo colocado for menor que 3%, o trecho avisa que houve empate técnico

---

#### US07 · Ver o custo total e a economia
**Épico:** E3 · **Canvas:** Exibir totais e economia estimada

> **Como** Rafael,
> **quero** ver no topo do resultado o custo total, o tempo de deslocamento, a distância e a economia estimada,
> **para** saber o tamanho da viagem antes de pedir aprovação.

**Critério de aceite**
- **Dado** um planejamento com trechos e pernoites
- **Quando** o resultado é exibido
- **Então** o custo total é exatamente a soma dos custos de cada trecho mais as diárias, sem diferença de centavos
- **E** uma diária só é cobrada quando o dia termina a mais de 80 km da origem

---

#### US08 · Comparar com o que eu faria sem o sistema
**Épico:** E3 · **Canvas:** Comparar cenário otimizado com cenário de referência

> **Como** Rafael,
> **quero** comparar a rota recomendada com a rota que eu faria sem o sistema,
> **para** enxergar de onde vem a economia.

**Critério de aceite**
- **Dado** um conjunto de agências selecionadas
- **Quando** o resultado é exibido
- **Então** o cenário de referência usa as mesmas agências, na ordem do cadastro, sempre de carro, com as mesmas regras de dias e pernoite
- **E** a tela mostra custo, tempo, distância e dias nos dois cenários, com a diferença destacada

---

#### US09 · Salvar e exportar o planejamento
**Épico:** E3 · **Canvas:** Registro básico do roteiro para análise posterior

> **Como** Rafael,
> **quero** salvar o planejamento e exportá-lo em um relatório imprimível,
> **para** anexar à solicitação de viagem e consultar depois.

**Critério de aceite**
- **Dado** um planejamento gerado
- **Quando** Rafael salva, fecha o sistema e o abre de novo
- **Então** o planejamento aparece na lista de salvos e reabre com os mesmos parâmetros
- **E quando** ele exporta, recebe uma folha A4 com parâmetros, itinerário, totais e comparação

---

#### US10 · Agências no lugar certo do mapa — *story de dados*
**Épico:** E4 · **Canvas:** sustenta US04, US05 e US06

> **Como** Rafael,
> **quero** que cada agência esteja na posição correta e que eu saiba quando a posição é aproximada,
> **para** confiar nas distâncias e nos custos calculados.

**Critério de aceite — métrica de dados**
- **Dado** as 2.010 agências do recorte, que na base do Banco Central não têm coordenada
- **Quando** o pipeline de ingestão e preparação roda
- **Então** 100% das agências recebem ao menos a coordenada do município
- **E** pelo menos 70% recebem coordenada de bairro
- **E** nenhuma coordenada de bairro fica a mais de 30 km do centro do próprio município
- **E** cada agência registra qual nível de precisão foi usado

> Resultado atual: 74,7% com coordenada de bairro, 290 coordenadas descartadas pela regra dos 30 km.
> Teste automático: `tests/test_features.py`.

---

#### US11 · Custo de carro com o preço do combustível do estado — *story de modelo*
**Épico:** E4 · **Canvas:** sustenta US05 e US07

> **Como** Rafael,
> **quero** que o custo dos trechos de carro use o preço do combustível do estado onde estou viajando,
> **para** que a estimativa de custo reflita a região, e não uma média do país.

**Critério de aceite — métrica do modelo**
- **Dado** a série semanal de preços de gasolina comum da ANP por estado, com o modelo treinado até dezembro de 2019
- **Quando** o modelo é avaliado no período de 2020 a 2021, que ele não viu no treino
- **Então** o erro absoluto médio (MAE) é de no máximo R$ 0,15 por litro
- **E** fica pelo menos 25% abaixo do baseline atual, que usa o mesmo preço nacional para todos os estados (MAE de R$ 0,20 por litro)

> Resultado atual: MAE de R$ 0,095 por litro, 52% abaixo do baseline.
> Teste automático: `tests/test_train.py::test_criterio_de_aceite_us11`.

---

### Onda 2 — evolução

---

#### US12 · Sequência otimizada de visitas
**Épico:** E2 · **Canvas:** Reotimização dinâmica dos cronogramas

> **Como** Rafael,
> **quero** que a ordem das visitas minimize o deslocamento total,
> **para** não fazer trechos de ida e volta desnecessários.

**Critério de aceite**
- **Dado** 20 seleções de teste com 5 a 15 agências
- **Quando** a sequência otimizada é comparada à varredura geográfica atual
- **Então** a distância total nunca é maior, e é menor em pelo menos 10% na média

---

#### US13 · Painel consolidado da regional
**Épico:** E3 · **Canvas:** Dashboard gerencial

> **Como** Rafael,
> **quero** ver o percentual de agências dentro da periodicidade e o custo acumulado dos meus planejamentos,
> **para** acompanhar a regional ao longo do mês.

**Critério de aceite**
- **Dado** uma regional com planejamentos salvos
- **Quando** Rafael abre o painel
- **Então** vê o percentual de agências dentro do prazo, comparado à meta de 90%, e o custo acumulado dos planejamentos salvos

---

#### US14 · Preços atualizados automaticamente
**Épico:** E4 · **Canvas:** Atualização automática de preços e rotas

> **Como** Rafael,
> **quero** que os preços de combustível e passagens sejam atualizados sem intervenção manual,
> **para** que o custo estimado não envelheça.

**Critério de aceite**
- **Dado** uma nova publicação semanal da ANP
- **Quando** a ingestão programada roda
- **Então** a série é atualizada, o modelo da US11 é reavaliado, e um alerta é emitido se o MAE da última semana passar de R$ 0,25 por litro

---

## 3. Revisão INVEST

INVEST: **I**ndependent (independente), **N**egotiable (negociável), **V**aluable
(gera valor), **E**stimable (estimável), **S**mall (cabe numa sprint),
**T**estable (testável).

| Story | I | N | V | E | S | T | Observação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US03 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US04 | ⚠ | ✓ | ✓ | ✓ | ✓ | ✓ | Precisa de uma seleção de agências como entrada; testável de forma isolada com uma lista fixa |
| US05 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US06 | ⚠ | ✓ | ✓ | ✓ | ✓ | ✓ | Exibe o que a US05 calcula; a dependência é de dado, não de entrega |
| US07 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US08 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US09 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US10 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US11 | ✓ | ✓ | ✓ | ⚠ | ✓ | ✓ | Estimativa incerta: modelo é experimento; baseline medido antes reduz o risco |
| US12 | ✓ | ✓ | ✓ | ⚠ | ⚠ | ✓ | Pode não caber numa sprint; se passar de 8 pontos, dividir em heurística e refinamento |
| US13 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| US14 | ⚠ | ✓ | ✓ | ⚠ | ⚠ | ✓ | Depende de fonte com publicação automatizada; avaliar antes de estimar |

Nenhuma story precisou ser reescrita. As marcadas com ⚠ têm a ressalva registrada
e serão revistas no Planning Poker.

---

## 4. Requisitos

### 4.1 Requisitos funcionais

| ID | Requisito | Stories |
| --- | --- | --- |
| RF01 | Listar e filtrar as agências da regional por cidade, estado e prioridade | US01 |
| RF02 | Receber origem, período, janela de visita, limite diário e modais permitidos | US02 |
| RF03 | Bloquear a geração quando a agenda não comporta a seleção | US02 |
| RF04 | Aceitar objetivo de menor custo, menor tempo ou peso ajustável entre os dois | US03 |
| RF05 | Gerar a sequência de visitas, distribuída em dias, saindo e voltando à origem | US04, US12 |
| RF06 | Recomendar um modal por trecho entre carro, ônibus e avião | US05 |
| RF07 | Exibir distância, tempo, custo e alternativas de cada trecho | US06 |
| RF08 | Calcular custo total, tempo, distância, diárias e economia estimada | US07 |
| RF09 | Calcular o cenário de referência com as mesmas regras do recomendado | US08 |
| RF10 | Salvar, reabrir e exportar planejamentos | US09 |

### 4.2 Requisitos não funcionais

| ID | Categoria | Requisito | Stories |
| --- | --- | --- | --- |
| RNF01 | Desempenho | Gerar um planejamento de até 40 agências em no máximo 2 segundos num notebook comum | US04, US05 |
| RNF02 | Disponibilidade | Funcionar sem internet e sem servidor | Todas |
| RNF03 | Explicabilidade | Toda recomendação de modal mostra o motivo e as alternativas descartadas | US05, US06 |
| RNF04 | Transparência | Todo dado estimado ou simulado aparece identificado como tal na interface | US07, US10 |
| RNF05 | Desempenho do modelo | MAE do preço de combustível de no máximo R$ 0,15/L no período de teste | US11 |
| RNF06 | Robustez a drift | O modelo é reavaliado a cada atualização da série, com alerta acima de R$ 0,25/L | US11, US14 |
| RNF07 | Reprodutibilidade | O pipeline roda ponta a ponta e produz a mesma saída para a mesma entrada (sementes fixas) | US10, US11 |
| RNF08 | Privacidade | Nenhum dado pessoal é tratado no MVP (ver 4.3) | Todas |

### 4.3 Requisitos de dados

| Aspecto | Requisito |
| --- | --- |
| **Fontes** | Cadastro de agências do Banco Central (posição 29/11/2024); série semanal de preços de combustível da ANP (2004–2021); bases públicas de coordenadas de municípios e bairros; base consolidada do grupo com aeroportos e preços estimados de ônibus e avião |
| **Volume** | 16.552 agências no país, 2.010 no recorte Itaú Unibanco; 23.570 registros de gasolina comum em 27 estados |
| **Qualidade** | Coordenada obrigatória para 100% das agências; coordenada de bairro validada contra o centro do município (máximo 30 km); texto padronizado (espaços, acentos, abreviações do Bacen); preço sem valores nulos no produto usado |
| **Atualização** | Cadastro de agências: a cada publicação do Bacen. Preços: semanal na fonte, mas a série disponível encerra em maio/2021 — limitação declarada e tratada pela US11 e pela US14 |
| **Restrições e LGPD** | As bases são públicas e tratam de pessoa jurídica (agências), não de pessoas físicas. Prioridade, prazo e última visita são simulados porque não existem em base pública. Numa implantação real, a agenda do gerente e o histórico de visitas seriam dados pessoais e exigiriam base legal, acesso mínimo e descarte definido |

---

## 5. Critério de priorização

O backlog foi ordenado pelo **valor para a hipótese central do MVP**, conforme o
Canvas: *uma recomendação automatizada de roteiro ajuda o gerente a planejar com
menor esforço, custo e tempo*.

1. **Primeiro, o que permite testar a hipótese de ponta a ponta** (US01 a US08).
   Sem a jornada completa — selecionar, restringir, escolher objetivo, receber a
   rota e comparar — não há como medir economia, que é a métrica de validação
   principal do Canvas.
2. **Depois, o que dá confiança ao resultado** (US10, US11). Dados e modelo vêm
   antes na construção, porque as distâncias e custos dependem deles, mas depois
   na ordem de valor: sozinhos, não entregam nada ao Rafael.
3. **Por último, o que torna o uso recorrente** (US09).
4. **A Onda 2** (US12 a US14) melhora uma hipótese que ainda precisa ser
   validada; antecipá-la seria crescer escopo antes de aprender.

A facilidade técnica não foi critério, como pede a Aula 4. Dependência técnica só
desempata.

---

## 6. Organização no GitHub Issues

Etiquetas: `onda-1`, `onda-2`, `E1-montagem`, `E2-recomendacao`, `E3-avaliacao`,
`E4-dados-modelos`, `story-de-dados`, `story-de-modelo`.

Colunas do quadro (GitHub Projects): **Backlog · Onda 1 (MVP) · Onda 2 ·
Concluído**, como pede a Aula 4.
