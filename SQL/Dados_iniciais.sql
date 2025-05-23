-- Script para criar as tabelas e inserir dados iniciais no banco de dados
-- Necessario para o funcionamento do sistema de aluguel de veículos
-- Este script deve ser executado no Supabase apos a criação das tabelas

INSERT INTO Seguro (Tipo, Cobertura, ValorBasico, ValorAvancado) VALUES
('Básico', 'Danos a terceiros', 80.00, 150.00),
('Completo', 'Cobertura total + assistência 24h', 200.00, 350.00);


INSERT INTO servico (nome, descricao, valorpadrao) VALUES
  ('GPS',               'Navegação GPS com mapas atualizados',         40.00),
  ('Assento Infantil',  'Cadeira de segurança para criança',           25.00),
  ('Wi-Fi',             'Internet a bordo até 5 GB por dia',           20.00),
  ('Proteção de Pneus', 'Cobertura contra danos em pneus',              15.00),
  ('Motorista Adicional','Habilita um segundo motorista no contrato', 100.00);
