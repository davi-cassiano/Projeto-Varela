# Plano de melhoria

Entregável da Aula 8 · três ações, escolhidas pelas notas mais baixas da
[autoavaliação de maturidade](autoavaliacao-maturidade.md) e pelo impacto no produto.
Registradas no quadro como as Issues #25, #26 e #27 e revisitadas na próxima retrospectiva.

| # | Ação | Área e nota | Responsável | Prazo | Indicador de sucesso | Situação |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Validar os dados a cada carga e ligar ruff, pytest com cobertura e a validação ao CI.** Seis regras com limite explícito em `src/validate.py` e `sql/qualidade.sql`; relatório gerado pelo pipeline; workflow do GitHub Actions bloqueando merge quando lint ou teste falham. | Qualidade · P | Luca (validação e testes) · Davi (CI) | Esta entrega (12/11) | Relatório de qualidade em `dados/saida/relatorio_qualidade.md`; workflow verde no PR; cobertura ≥ 70% | ✅ Concluída em 12/11: 79 testes, 88% de cobertura, 6 regras (4 passam), SBAR da pior falha em `qualidade.md` |
| 2 | **Registrar as medições por ciclo** — velocidade, número de testes, cobertura, MAE do modelo, regras de qualidade e revisão de riscos — numa tabela única, atualizada ao fim de cada sprint. | Medição · P | Victor | Aula 10 | Tabela em `planejamento.md` §6 com uma linha por ciclo, começando pela Sprint 1 | ✅ Concluída em 12/11, com duas linhas (Sprint 1 e ciclo de qualidade) |
| 3 | **Fechar o ciclo de planejamento.** Registrar as sprints não executadas e o risco R6 materializado, revisar a matriz com data, e executar a Issue #16 (limite de desvio proporcional ao tamanho do município), que é a causa da regra 5 reprovada. | Planejamento · P e Riscos · P | Davi (replanejamento e riscos) · Gabriel (#16) | Próxima sprint, até a Aula 10 | Matriz com data de revisão e R6 atualizado; #16 fechada com as 10 agências do Rio mantendo coordenada de bairro, cobertura ≥ 74,7% e Mirandópolis ainda descartado; regra 5 passando | 🔶 Em andamento: matriz revisada, sprints não executadas registradas e sprint final entregue em 12/11; #16 fica para depois do curso |

## Por que estas três, e não outras

- **Impacto no produto antes de impacto na nota.** Uma base que muda sem aviso invalida
  distâncias e custos em silêncio; por isso a validação de dados veio primeiro.
- **Esforço viável.** As ações 1 e 2 cabiam num dia de trabalho e saíram no mesmo dia.
  A ação 3 tem uma parte de registro (feita) e uma de código (#16), que precisa de teste
  de sensibilidade e ficou para a próxima sprint.
- **Deixadas de fora, de propósito:** proteger a `main` e criar tags de versão do modelo
  (Configuração em L, impacto menor); verificar por teste os critérios das stories de
  interface (depende da validação com um gerente, que é a próxima sprint).

## Como será revisitado

Na próxima retrospectiva o grupo repete o checklist da autoavaliação. A ação só conta
como concluída se a nota da área subiu com evidência, não se a tarefa foi feita.
