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

CREATE TABLE public.aluguel (
  id bigint primary key generated always as identity,
  idcliente integer NOT NULL,
  idveiculo integer NOT NULL,
  idseguro integer NOT NULL,
  datainicio timestamp with time zone NOT NULL,
  datafim timestamp with time zone NOT NULL,
  valortotal numeric(10,2) NOT NULL,
  status text NULL DEFAULT 'Ativo'
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

CREATE TABLE public.historicomanutencao (
  idveiculo integer NOT NULL,
  idmanutencao integer NOT NULL,
  dataregistro timestamp with time zone NOT NULL,
  CONSTRAINT historicomanutencao_pkey PRIMARY KEY (idveiculo, idmanutencao)
);

CREATE TABLE public.manutencao (
  id bigint primary key generated always as identity,
  tipo text NOT NULL,
  datainicio timestamp with time zone NOT NULL,
  datafim timestamp with time zone NULL,
  custo numeric(10,2) NOT NULL,
  descricao text NULL
);

CREATE TABLE public.seguro (
  id bigint primary key generated always as identity,
  tipo text NOT NULL,
  cobertura text NULL,
  valorbasico numeric(10,2) NOT NULL,
  valoravancado numeric(10,2) NOT NULL
);

CREATE TABLE public.veiculo (
  id bigint primary key generated always as identity,
  placa text NOT NULL,
  modelo text NOT NULL,
  ano integer NOT NULL,
  statusdisponibilidade text NULL DEFAULT 'Disponível',
  tier public.tierveiculo NOT NULL DEFAULT 'Básico',
  CONSTRAINT veiculo_placa_key UNIQUE (placa)
);