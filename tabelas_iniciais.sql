-- Remover tabelas se existirem (em ordem correta para evitar conflitos de FK)
DROP TABLE IF EXISTS HistoricoManutencao CASCADE;
DROP TABLE IF EXISTS Aluguel CASCADE;
DROP TABLE IF EXISTS Manutencao CASCADE;
DROP TABLE IF EXISTS Veiculo CASCADE;
DROP TABLE IF EXISTS Cliente CASCADE;
DROP TABLE IF EXISTS Seguro CASCADE;

-- Remover tipo ENUM se existir
DROP TYPE IF EXISTS TierVeiculo CASCADE;

-- Criar tipo ENUM para Tier
CREATE TYPE TierVeiculo AS ENUM ('Básico', 'Avançado');

-- Criar tabelas com a nova estrutura
CREATE TABLE Cliente (
    ID SERIAL PRIMARY KEY,
    Nome VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Telefone VARCHAR(20),
    CNH VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE Veiculo (
    ID SERIAL PRIMARY KEY,
    Placa VARCHAR(10) UNIQUE NOT NULL,
    Modelo VARCHAR(50) NOT NULL,
    Ano INT NOT NULL,
    StatusDisponibilidade VARCHAR(20) DEFAULT 'Disponível',
    Tier TierVeiculo NOT NULL DEFAULT 'Básico'
);

CREATE TABLE Seguro (
    ID SERIAL PRIMARY KEY,
    Tipo VARCHAR(50) NOT NULL,
    Cobertura TEXT,
    ValorBasico DECIMAL(10, 2) NOT NULL,
    ValorAvancado DECIMAL(10, 2) NOT NULL
);

CREATE TABLE Manutencao (
    ID SERIAL PRIMARY KEY,
    Tipo VARCHAR(50) NOT NULL,
    DataInicio DATE NOT NULL,
    DataFim DATE,
    Custo DECIMAL(10, 2) NOT NULL,
    Descricao TEXT
);

CREATE TABLE Aluguel (
    ID SERIAL PRIMARY KEY,
    IDCliente INT NOT NULL,
    IDVeiculo INT NOT NULL,
    IDSeguro INT NOT NULL,
    DataInicio DATE NOT NULL,
    DataFim DATE NOT NULL,
    ValorTotal DECIMAL(10, 2) NOT NULL,
    Status VARCHAR(20) DEFAULT 'Ativo',
    FOREIGN KEY (IDCliente) REFERENCES Cliente(ID),
    FOREIGN KEY (IDVeiculo) REFERENCES Veiculo(ID),
    FOREIGN KEY (IDSeguro) REFERENCES Seguro(ID)
);

CREATE TABLE HistoricoManutencao (
    IDVeiculo INT,
    IDManutencao INT,
    DataRegistro DATE NOT NULL,
    PRIMARY KEY (IDVeiculo, IDManutencao),
    FOREIGN KEY (IDVeiculo) REFERENCES Veiculo(ID),
    FOREIGN KEY (IDManutencao) REFERENCES Manutencao(ID)
);
