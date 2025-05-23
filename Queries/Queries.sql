-- Queries para o sistema de locadora de veículos
-- As queries foram escritas para serem executadas no Supabase 

-- Query 1: Listar todos os clientes com alugueis ativos
-- Query 2: Listar todos os alugueis de um cliente específico
-- Query 3: Listar a ultima manutenção de cada veículo
-- Query 4: Listar todos os veículos disponíveis para aluguel
-- Query 5: Listar todos os veículos em algum estado específico
-- Query 6: Servicos mais utilizados nos alugueis
-- Query 7: Listar os 10 clientes que mais gastaram
-- Query 8: Mostar todas as mautenções de um status específico, com horas de trabalho e mecanicos
-- Query 9: Mostrar quantidade de alugueis por modelo de veiculo
-- Query 10: Mostrar quantidade de alugueis e manutenções por modelo de veiculo
--------------------------------------------------------------------------------------------------------------------------
-- Query 1: Listar todos os clientes com alugueis ativos
SELECT 
  a.id,
  c.nome AS cliente,
  v.modelo AS veiculo,
  a.datainicio,
  a.datafim,
  a.valortotal
FROM aluguel a
JOIN cliente c ON a.idcliente = c.id
JOIN veiculo v ON a.idveiculo = v.id
WHERE a.status = 'Ativo';

-- Query 2: Listar todos os alugueis de um cliente específico
SELECT 
    a.id AS id_aluguel,
    a.datainicio,
    a.datafim,
    a.valortotal,
    a.status,
    c.nome AS nome_cliente,
    v.modelo AS modelo_veiculo,
    v.tier AS tier_veiculo,
    s.tipo AS nivel_seguro
FROM 
    public.aluguel a
JOIN 
    public.cliente c ON a.idcliente = c.id
JOIN 
    public.veiculo v ON a.idveiculo = v.id
JOIN 
    public.seguro s ON a.idseguro = s.id
WHERE 
    c.id = 2;

-- Query 3: Listar a ultima manutenção de cada veículo
SELECT 
  v.id,
  v.placa,
  v.modelo,
  MAX(m.datainicio) AS ultima_manutencao
FROM veiculo v
JOIN manutencao m ON v.id = m.idveiculo
GROUP BY v.placa, v.modelo, v.id
ORDER BY ultima_manutencao DESC;

-- Query 4: Listar todos os veículos disponíveis para aluguel
SELECT 
  v.id,
  v.modelo,
  v.placa,
  v.tier,
  v.status
FROM veiculo v
LEFT JOIN aluguel a ON v.id = a.idveiculo
WHERE a.id IS NULL OR a.status = 'Finalizado'
ORDER BY v.modelo;

-- Query 5: Listar todos os veículos em algum estado específico
-- Modificar o status desejado na cláusula WHERE
-- Possibilidades: 'Disponível', 'Alugado' ou 'Manutenção'
SELECT 
  v.id,
  v.modelo,
  v.placa,
  v.tier
FROM veiculo v
WHERE v.statusdisponibilidade = 'Disponível' -- Modificar para estatus desejado, seja 'Alugado' ou 'Manutenção'
ORDER BY v.modelo;

-- Query 6: Servicos mais utilizados nos alugueis
-- Esta consulta retorna os serviços mais utilizados nos alugueis, ordenados pelo total de uso

SELECT 
  s.nome,
  COUNT(asv.id_aluguel) AS total_uso
FROM servico s
JOIN aluguel_servico asv ON s.id = asv.id_servico
GROUP BY s.nome
ORDER BY total_uso DESC;

-- Query 7: Listar os 10 clientes que mais gastaram
SELECT 
  c.nome,
  SUM(a.valor + COALESCE(asv_total.total_servicos, 0)) AS total_gasto
FROM cliente c
JOIN aluguel a ON c.id = a.idcliente
LEFT JOIN (
  SELECT id_aluguel, SUM(preco * quantidade) AS total_servicos
  FROM aluguel_servico
  GROUP BY id_aluguel
) AS asv_total ON a.id = asv_total.id_aluguel
GROUP BY c.nome
ORDER BY total_gasto DESC
LIMIT 10;

-- Query 8: Mostar todas as mautenções de um status específico, com horas de trabalho e mecanicos

-- Modificar o status desejado na cláusula WHERE
-- Possibilidades: 'Ativo' ou 'Concluido' 
SELECT 
  m.id AS manutencao_id,
  m.idveiculo,
  STRING_AGG(mec.nome, ', ') AS mecanicos,
  SUM(mm.horas_trabalhadas) AS total_horas_trabalhadas
FROM manutencao m
JOIN manutencao_mecanico mm ON m.id = mm.id_manutencao
JOIN mecanico mec ON mm.id_mecanico = mec.id
WHERE m.status = 'Ativo'  -- Modificar para estatus desejado, seja 'Ativo' ou 'Concluido'
GROUP BY m.id, m.idveiculo
ORDER BY m.custo DESC;

-- Query 9: Mostrar quantidade de alugueis por modelo de veiculo
-- Esta consulta retorna a quantidade de alugueis por modelo de veiculo, ordenados pelo total de alugueis
SELECT 
  v.modelo,
  COUNT(a.id) AS total_alugueis
FROM veiculo v
LEFT JOIN aluguel a ON v.id = a.idveiculo
GROUP BY v.modelo
ORDER BY total_alugueis DESC;

-- Query 10: Mostrar quantidade de alugueis e manutenções por modelo de veiculo
-- Esta consulta retorna a quantidade de alugueis e manutenções por modelo de veiculo, ordenados pelo total de alugueis e manutenções
SELECT 
  v.modelo,
  COUNT(DISTINCT a.id) AS total_alugueis,
  COUNT(DISTINCT m.id) AS total_manutencoes
FROM veiculo v
LEFT JOIN aluguel a ON v.id = a.idveiculo
LEFT JOIN manutencao m ON v.id = m.idveiculo
GROUP BY v.modelo
ORDER BY total_alugueis DESC, total_manutencoes DESC;
