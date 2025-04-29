-- Inserir clientes
INSERT INTO Cliente (Nome, Email, Telefone, CNH) VALUES
('Lucas Oliveira', 'lucas@email.com', '(11) 97777-1111', 'CNH-111111'),
('Julia Santos', 'julia@email.com', '(21) 98888-2222', 'CNH-222222'),
('Rafael Costa', 'rafael@email.com', '(31) 99999-3333', 'CNH-333333');

-- Inserir veículos com tier
INSERT INTO Veiculo (Placa, Modelo, Ano, StatusDisponibilidade, Tier) VALUES
('BRA-2F22', 'Sedan Comfort', 2023, 'Disponível', 'Básico'),
('SPO-5G55', 'SUV Elite', 2024, 'Disponível', 'Avançado'),
('RIO-8H88', 'Hatch City', 2022, 'Alugado', 'Básico'),
('BHZ-3I33', 'Pickup Work', 2021, 'Manutenção', 'Avançado');

-- Inserir seguros (ValorBasico = custo para tier Básico, ValorAvancado = custo para tier Avançado)
INSERT INTO Seguro (Tipo, Cobertura, ValorBasico, ValorAvancado) VALUES
('Básico', 'Danos a terceiros', 80.00, 150.00),
('Completo', 'Cobertura total + assistência 24h', 200.00, 350.00);

-- Inserir aluguéis (IDSeguro independe do tier do veículo)
INSERT INTO Aluguel (IDCliente, IDVeiculo, IDSeguro, DataInicio, DataFim, ValorTotal, Status) VALUES
(1, 2, 1, '2024-06-01', '2024-06-05', 1850.00, 'Ativo'),      -- SUV Avançado com Seguro Básico (ValorAvancado = 150)
(2, 3, 2, '2024-05-25', '2024-05-30', 1350.00, 'Concluído'),  -- Hatch Básico com Seguro Completo (ValorBasico = 200)
(3, 1, 2, '2024-06-02', '2024-06-04', 1000.00, 'Ativo');      -- Sedan Básico com Seguro Completo (ValorBasico = 200)

-- Inserir manutenções
INSERT INTO Manutencao (Tipo, DataInicio, DataFim, Custo, Descricao) VALUES
('Preventiva', '2024-05-20', '2024-05-22', 500.00, 'Revisão de rotina'),
('Corretiva', '2024-06-01', NULL, 1200.00, 'Reparo no motor');

-- Registrar histórico de manutenções
INSERT INTO HistoricoManutencao (IDVeiculo, IDManutencao, DataRegistro) VALUES
(4, 1, '2024-05-20'),  -- Pickup Work em manutenção
(4, 2, '2024-06-01');
