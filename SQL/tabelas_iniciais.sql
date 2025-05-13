-- Remover tabelas se existirem (em ordem correta para evitar conflitos de FK)
DROP TABLE IF EXISTS Aluguel CASCADE;
DROP TABLE IF EXISTS Manutencao CASCADE;
DROP TABLE IF EXISTS Veiculo CASCADE;
DROP TABLE IF EXISTS Cliente CASCADE;
DROP TABLE IF EXISTS Seguro CASCADE;
DROP TABLE IF EXISTS Servico CASCADE;
DROP TABLE IF EXISTS Aluguel_Servico CASCADE;
DROP TABLE IF EXISTS Mecanico CASCADE;
DROP TABLE IF EXISTS Manutencao_Mecanico CASCADE;

-- Remover tipo ENUM se existir
DROP TYPE IF EXISTS TierVeiculo CASCADE;

-- Criar tipo ENUM para Tier
CREATE TYPE TierVeiculo AS ENUM ('Básico', 'Avançado');

CREATE TABLE public.veiculo (
  id bigint primary key generated always as identity,
  placa text NOT NULL,
  modelo text NOT NULL,
  ano integer NOT NULL,
  statusdisponibilidade text NULL DEFAULT 'Disponível',
  tier public.tierveiculo NOT NULL DEFAULT 'Básico',
  CONSTRAINT veiculo_placa_key UNIQUE (placa)
);



CREATE TABLE public.seguro (
  id bigint primary key generated always as identity,
  tipo text NOT NULL,
  cobertura text NULL,
  valorbasico numeric(10,2) NOT NULL,
  valoravancado numeric(10,2) NOT NULL
);

CREATE TABLE public.cliente (
  id bigint primary key generated always as identity,
  nome text NOT NULL,
  email text NULL,
  telefone text NULL,
  cnh text NOT NULL,
  CONSTRAINT cliente_cnh_key UNIQUE (cnh),
  CONSTRAINT cliente_email_key UNIQUE (email)
);

CREATE TABLE public.aluguel (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  idcliente integer NOT NULL,
  idveiculo integer NOT NULL,
  idseguro  integer NOT NULL,
  datainicio date NOT NULL,
  datafim    date NOT NULL,
  valortotal numeric(10,2) NOT NULL,
  status     text DEFAULT 'Ativo',
  -- chaves estrangeiras
  CONSTRAINT fk_aluguel_cliente FOREIGN KEY (idcliente)
    REFERENCES public.cliente (id),
  CONSTRAINT fk_aluguel_veiculo FOREIGN KEY (idveiculo)
    REFERENCES public.veiculo (id),
  CONSTRAINT fk_aluguel_seguro FOREIGN KEY (idseguro)
    REFERENCES public.seguro (id)
);



CREATE TABLE public.manutencao (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  idveiculo integer NOT NULL,
  tipo       text    NOT NULL,
  datainicio date    NOT NULL,
  datafim    date,
  status     text    DEFAULT 'Pendente',
  custo      numeric(10,2) NOT NULL,
  descricao  text,
  -- chave estrangeira
  CONSTRAINT fk_manutencao_veiculo FOREIGN KEY (idveiculo)
    REFERENCES public.veiculo (id)
);



-- 6) Tabela de serviços
CREATE TABLE public.servico (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  nome text       NOT NULL,
  descricao text  NULL,
  valorpadrao numeric(10,2) NOT NULL
);

-- Junção N:M aluguel ↔ serviço (com atributos preço e quantidade)
CREATE TABLE public.aluguel_servico (
  id_aluguel bigint NOT NULL,
  id_servico bigint NOT NULL,
  preco      numeric(10,2) NOT NULL,
  CONSTRAINT pk_aluguel_servico PRIMARY KEY (id_aluguel, id_servico),
  CONSTRAINT fk_as_aluguel FOREIGN KEY (id_aluguel)
    REFERENCES public.aluguel(id),
  CONSTRAINT fk_as_servico FOREIGN KEY (id_servico)
    REFERENCES public.servico(id)
);

-- 7) Tabela de mecânicos
CREATE TABLE public.mecanico (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  nome text          NOT NULL,
  especialidade text NULL
);

-- Junção N:M manutenção ↔ mecânico (com atributo horas_trabalhadas)
CREATE TABLE public.manutencao_mecanico (
  id_manutencao     bigint NOT NULL,
  id_mecanico       bigint NOT NULL,
  horas_trabalhadas numeric(5,2) NOT NULL,
  CONSTRAINT pk_manutencao_mecanico PRIMARY KEY (id_manutencao, id_mecanico),
  CONSTRAINT fk_mm_manutencao FOREIGN KEY (id_manutencao)
    REFERENCES public.manutencao(id),
  CONSTRAINT fk_mm_mecanico FOREIGN KEY (id_mecanico)
    REFERENCES public.mecanico(id)
);

