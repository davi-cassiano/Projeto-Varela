-- qualidade.sql — as mesmas regras de src/validate.py, em SQL (Aula 9).
-- Convenção da aula: consulta que retorna linhas é consulta que encontrou problema.
-- Tabelas: agencias (cadastro Bacen, recorte Itaú), agencias_prep (após a
-- preparação, com a coluna precisao) e precos (ANP, gasolina comum).
-- Rodar: python sql/rodar_qualidade.py  (carrega as tabelas em SQLite e executa cada bloco)

-- 1 · Unicidade: um registro por agência
SELECT cod_compe_ag, COUNT(*) AS n
FROM agencias
GROUP BY cod_compe_ag
HAVING COUNT(*) > 1;

-- 2 · Completude: até 1% de nulos por coluna obrigatória
SELECT coluna, pct_nulos
FROM (
  SELECT 'bairro' AS coluna, AVG(CASE WHEN bairro IS NULL OR bairro = '' THEN 1.0 ELSE 0 END) AS pct_nulos FROM agencias
  UNION ALL SELECT 'cep',        AVG(CASE WHEN cep IS NULL        THEN 1.0 ELSE 0 END) FROM agencias
  UNION ALL SELECT 'municipio',  AVG(CASE WHEN municipio IS NULL  THEN 1.0 ELSE 0 END) FROM agencias
  UNION ALL SELECT 'uf',         AVG(CASE WHEN uf IS NULL         THEN 1.0 ELSE 0 END) FROM agencias
  UNION ALL SELECT 'latitude',   AVG(CASE WHEN latitude IS NULL   THEN 1.0 ELSE 0 END) FROM agencias
  UNION ALL SELECT 'longitude',  AVG(CASE WHEN longitude IS NULL  THEN 1.0 ELSE 0 END) FROM agencias
)
WHERE pct_nulos > 0.01;

-- 3 · Validade: UF entre as 27 siglas, CEP com 8 dígitos, coordenadas dentro do Brasil
SELECT cod_compe_ag, uf, cep, latitude, longitude
FROM agencias
WHERE uf NOT IN ('AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE',
                 'PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO')
   OR LENGTH(REPLACE(cep, '-', '')) <> 8
   OR latitude  NOT BETWEEN -34.0 AND 5.5
   OR longitude NOT BETWEEN -74.0 AND -34.5;

-- 4 · Consistência: o código IBGE do município pertence à UF informada
SELECT a.cod_compe_ag, a.municipio, a.uf, u.uf AS uf_do_ibge
FROM agencias a
JOIN uf_ibge u ON u.codigo = a.municipio_ibge / 100000
WHERE u.uf <> a.uf;

-- 5 · Consistência geográfica (após a preparação): descartes da coordenada de bairro
--     por ficar a mais de 30 km do município devem ser ≤ 10%, e a cobertura ≥ 70%
SELECT
  SUM(CASE WHEN precisao = 'municipio' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS pct_sem_bairro,
  SUM(CASE WHEN precisao <> 'municipio' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS cobertura_bairro,
  (SELECT descartadas FROM resumo_prep) * 1.0 / COUNT(*) AS pct_descartes
FROM agencias_prep
HAVING pct_descartes > 0.10 OR cobertura_bairro < 0.70;

-- 6a · Unicidade da série: uma linha por semana e estado
SELECT data, estado, COUNT(*) AS n
FROM precos
GROUP BY data, estado
HAVING COUNT(*) > 1;

-- 6b · Validade: preço na faixa plausível
SELECT * FROM precos WHERE preco NOT BETWEEN 0.5 AND 15.0;

-- 6c · Pontualidade: a semana mais recente tem no máximo 90 dias
SELECT MAX(data) AS ultima_semana, JULIANDAY('now') - JULIANDAY(MAX(data)) AS idade_dias
FROM precos
HAVING idade_dias > 90;
