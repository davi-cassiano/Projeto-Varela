# Autoavaliação de maturidade

Entregável da Aula 8 · CMMI, MPS-BR e Maturidade

**Data da avaliação:** 12/11/2026 · **Avaliadores:** Davi, Gabriel, Luca e Victor

## 1. Método

Seguimos os quatro passos da aula: escolher as áreas, levantar evidências, pontuar e
priorizar melhorias. Seis áreas de processo, duas ou três perguntas objetivas por área,
cada resposta sustentada por um artefato do repositório ou do quadro. A nota usa a escala
da ISO/IEC 33020, a mesma das avaliações do MPS-BR (Melhoria de Processo do Software
Brasileiro):

| Nota | Significado | Faixa |
| --- | --- | --- |
| **N** | Não praticado — não há evidência | 0 a 15% |
| **P** | Parcialmente praticado — há evidência, mas inconsistente ou incompleta | 15 a 50% |
| **L** | Largamente praticado — realizado na maior parte dos casos, com pequenas lacunas | 50 a 85% |
| **F** | Totalmente praticado — consistente e com evidência clara | 85 a 100% |

A regra que adotamos para não cair na "nota sem evidência": **se a pergunta não tem um link,
a resposta é "não"**. A avaliação retrata o estado do projeto no início de 12/11/2026, antes
das ações desta entrega, para que o plano de melhoria tenha contra o que ser medido.

## 2. Checklist com evidências

### Requisitos — nota **L**

| Pergunta | Resposta | Evidência |
| --- | --- | --- |
| As stories têm critério de aceite verificável e estão ligadas à persona e ao Canvas? | Sim, as 14 | [`docs/backlog.md`](backlog.md), [Issues #1 a #14](https://github.com/davi-cassiano/Projeto-Varela/issues) |
| Requisitos não funcionais e de dados estão escritos e ligados às stories? | Sim | [`docs/backlog.md` §3 e §4](backlog.md) |
| Mudanças de requisito são registradas e rastreadas até o código? | Parcialmente: a Issue #16 nasceu de uma revisão de PR e está ligada à US10, mas as stories de interface (US01 a US09) não têm o critério de aceite verificado por teste | [Issue #16](https://github.com/davi-cassiano/Projeto-Varela/issues/16), [`docs/arquitetura.md` §2](arquitetura.md) |

**Justificativa:** rastreabilidade Canvas → story → módulo → teste existe para as stories de dados e modelo; para as de interface, para no protótipo.

### Planejamento — nota **P**

| Pergunta | Resposta | Evidência |
| --- | --- | --- |
| Existe WBS com a story de origem de cada pacote e a regra dos 100% conferida? | Sim | [`docs/planejamento.md` §1](planejamento.md) |
| As estimativas foram feitas pelo time e a capacidade registrada? | Sim, Planning Poker com registro das divergências | [`docs/planejamento.md` §2](planejamento.md) |
| O plano é acompanhado e replanejado quando a realidade muda? | **Não.** O plano previa Sprints 2 a 4 a partir de 15/10; nenhuma foi executada nem replanejada até esta avaliação | [`docs/planejamento.md` §5](planejamento.md), histórico de commits (nenhum entre 15/10 e 12/11) |

**Justificativa:** planejar está F; acompanhar e corrigir, que é o que a Gerência de Projetos do nível G do MPS-BR exige, está N. A média honesta é P.

### Gerência de configuração — nota **L**

| Pergunta | Resposta | Evidência |
| --- | --- | --- |
| Código versionado, com mudanças por branch e pull request? | Sim, 24 PRs, commits pequenos | [Pull requests](https://github.com/davi-cassiano/Projeto-Varela/pulls?q=is%3Apr) |
| Dados e ambiente controlados para reproduzir qualquer resultado? | Sim: bases brutas fora do Git com instruções de obtenção, recortes pequenos versionados, sementes fixas, `requirements.txt` | [`dados/brutos/LEIA-ME.md`](../dados/brutos/LEIA-ME.md), [`dados/colab/`](../dados/colab), [`src/train.py`](../src/train.py) `SEMENTE = 42` |
| Baselines e versões do modelo são identificados? | Parcialmente: o modelo é regenerado pelo pipeline e as métricas ficam no `relatorio_execucao.json`, mas não há tag nem registro de versão; `main` não está protegida; 9 branches já integradas continuam abertas | [Branches](https://github.com/davi-cassiano/Projeto-Varela/branches) |

### Garantia da qualidade — nota **P**

| Pergunta | Resposta | Evidência |
| --- | --- | --- |
| Há testes automatizados ligados aos critérios de aceite? | Sim, 23 testes | [`tests/`](../tests) |
| Os dados são validados a cada carga, com regras e limites? | **Não.** A ingestão descarta valores fora de faixa, mas não existe relatório de qualidade nem regra com limite explícito | [`src/ingest.py`](../src/ingest.py) `carregar_precos` |
| Análise estática, cobertura e CI rodam a cada mudança? | **Não.** Nenhum linter configurado, cobertura nunca medida, nenhum workflow | — |

**Justificativa:** o que existe é bom (testes com critério de aceite, PR revisado com três comentários resolvidos), mas é metade da prática: nada roda sozinho e os dados não são verificados.

### Medição — nota **P**

| Pergunta | Resposta | Evidência |
| --- | --- | --- |
| A velocidade do time é registrada? | Sim, uma vez: 19 de 20 pontos na Sprint 1 | [`docs/planejamento.md` §4](planejamento.md) |
| As métricas do modelo são acompanhadas entre ciclos? | Não: MAE e RMSE foram medidos uma vez, no PR #15, e não há tabela por ciclo | [`docs/arquitetura.md` §6](arquitetura.md) |
| Há indicador de qualidade de dados acompanhado? | Não | — |

### Gerência de riscos — nota **P**

| Pergunta | Resposta | Evidência |
| --- | --- | --- |
| Existe matriz com probabilidade, impacto, resposta e dono? | Sim, 7 riscos | [`docs/planejamento.md` §3](planejamento.md) |
| A matriz é revisada a cada sprint, como o pacote 7.3 da WBS prevê? | **Não.** Nenhuma revisão desde 15/10. O risco R6 (prazo) se materializou e não foi registrado | [`docs/planejamento.md` §3](planejamento.md) |

## 3. Resumo

| Área | Nota | Lacuna principal |
| --- | --- | --- |
| Requisitos | **L** | Critérios das stories de interface não verificados por teste |
| Planejamento | **P** | Plano não acompanhado nem replanejado |
| Configuração | **L** | Sem proteção da `main`, sem versão do modelo, branches antigas abertas |
| Qualidade | **P** | Sem validação de dados, sem linter, sem cobertura, sem CI |
| Medição | **P** | Métricas medidas uma vez, não acompanhadas |
| Riscos | **P** | Matriz não revisada; R6 materializado sem registro |

Em termos de MPS-BR: o projeto pratica o nível G (gerenciar projeto e requisitos) de forma
largamente consistente e começou o nível F (medição, qualidade, configuração) de forma parcial.
O nível não é a meta; a lacuna que mais causa retrabalho é a de qualidade, porque uma base de
dados que muda sem aviso invalida o modelo e as distâncias em silêncio.

## 4. Plano de melhoria

Três ações, escolhidas pelas notas mais baixas e pelo impacto no produto. O plano está
também em [`docs/plano-melhoria.md`](plano-melhoria.md), e cada ação é uma Issue no quadro (#25, #26 e #27).

| # | Ação | Por quê | Responsável e prazo | Como saberemos | Situação em 12/11 |
| --- | --- | --- | --- | --- | --- |
| 1 | Validar os dados a cada carga e ligar ruff, pytest com cobertura e a validação ao CI | Qualidade em P; riscos R1 e R2 sem medição | Luca (validação) e Davi (CI) · esta entrega | Relatório de qualidade gerado pelo pipeline; workflow verde no PR | **Concluída** nesta entrega (Aula 9): 6 regras, 4 passam, 2 falhas documentadas com SBAR; 79 testes, 88% de cobertura, CI em `.github/workflows/qualidade.yml` |
| 2 | Registrar as medições por ciclo: velocidade, MAE do modelo, cobertura e regras de qualidade numa tabela única | Medição em P | Victor · Aula 10 | Tabela em `docs/planejamento.md` com uma linha por ciclo | **Concluída:** §6 do `planejamento.md`, com as linhas da Sprint 1 e desta entrega |
| 3 | Fechar o ciclo de planejamento: registrar as sprints não executadas, revisar a matriz de riscos com data, e executar a Issue #16 (limite de desvio por município) | Planejamento e Riscos em P; R6 materializado; regra 5 de qualidade reprovada | Davi (replanejamento e riscos) e Gabriel (#16) · próxima sprint, até a Aula 10 | Matriz com data de revisão e R6 atualizado; Issue #16 fechada com as 10 agências do Rio mantendo coordenada de bairro e cobertura ≥ 74,7% | **Em andamento:** matriz revisada em 12/11 (§3 do `planejamento.md`); #16 aberta |

## 5. O que esta avaliação ensinou

- Ter os documentos não é ter o processo. WBS, Poker e matriz de riscos estavam corretos e
  pararam no dia da entrega. A prática que faltou foi a mais barata: olhar o plano de novo.
- Nota alta sem evidência é a armadilha que a aula descreve. Requisitos quase foi F até
  perguntarmos "onde está o teste do critério da US04?".
- A próxima autoavaliação deve ser feita no fim da próxima sprint, com este mesmo checklist,
  para saber se as três ações mudaram as notas.

## 6. Reavaliação ao fim do ciclo (12/11/2026, depois das ações)

O mesmo checklist, aplicado depois do ciclo de qualidade e da sprint final, para
saber se as ações mudaram as notas. Nota F exige consistência ao longo de vários
ciclos; com um ciclo só, o máximo honesto é L.

| Área | Antes | Depois | O que mudou | O que ainda falta para F |
| --- | --- | --- | --- | --- |
| Requisitos | L | **L** | 14 de 14 stories com critério verificado (US12 e US14 por teste automático) | Validação das stories de interface com um gerente real |
| Planejamento | P | **L** | Sprints não executadas registradas; replanejamento; sprint final com meta, pontos e resultado; tabela de medições | Mais de um ciclo acompanhado |
| Configuração | L | **L** | CI em cada PR; produto regenerado pelo pipeline | `main` protegida, tags de versão, branches antigas apagadas |
| Qualidade | P | **L** | 6 regras de dados com relatório e SBAR; 96 testes, 88% de cobertura; ruff; CI; PRs revisados com bloqueia/sugestão | Validação de dados bloqueando o merge quando uma regra nova falhar; mais ciclos |
| Medição | P | **L** | Tabela por ciclo com velocidade, testes, cobertura, MAE e regras; monitor semanal do modelo | Histórico de vários ciclos |
| Riscos | P | **L** | Matriz revisada com data; R6 registrado como ocorrido; R1 e R2 medidos por regra de qualidade | Revisão em toda retrospectiva, não só nesta |
