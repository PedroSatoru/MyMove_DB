# MyMove_DB

Banco de dados e gerador de dados para uma locadora de veículos utilizando Supabase e Faker.

---

## Sumário

- [Descrição](#descrição)
- [Entidades e Relacionamentos](#entidades-e-relacionamentos)
  - [MER (Diagrama)](#mer-diagrama)
  - [Modelo Relacional (3FN)](#modelo-relacional-3fn)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Queries SQL](#queries-sql)
- [Equipe](#equipe)
- [Observações](#observações)

---

## Descrição

Este projeto tem como objetivo criar o esquema de um banco de dados para uma locadora de veículos e gerar dados fictícios para as tabelas.  
O sistema armazena informações de:

- **Clientes**  
- **Veículos**  
- **Seguros**  
- **Manutenções** (incluindo relação com mecânicos)  
- **Aluguéis** (com controle de períodos para evitar sobreposição e vínculo com serviços)  
- **Serviços** associados aos aluguéis  
- **Junções N:M** com atributos para os relacionamentos:  
  - `aluguel_servico` (atributos: preço e quantidade)  
  - `manutencao_mecanico` (atributo: horas_trabalhadas)

---

## Entidades e Relacionamentos

### MER (Diagrama)

```mermaid
erDiagram
    CLIENTE {
      bigint id PK
      text nome
      text email
      text telefone
      text cnh
    }
    VEICULO {
      bigint id PK
      text placa
      text modelo
      int ano
      text statusdisponibilidade
      TierVeiculo tier
    }
    SEGURO {
      bigint id PK
      text tipo
      text cobertura
      numeric valorbasico
      numeric valoravancado
    }
    MANUTENCAO {
      bigint id PK
      bigint idveiculo FK
      text tipo
      date datainicio
      date datafim
      text status
      numeric custo
      text descricao
    }
    ALUGUEL {
      bigint id PK
      bigint idcliente FK
      bigint idveiculo FK
      bigint idseguro FK
      date datainicio
      date datafim
      numeric valortotal
      text status
    }
    SERVICO {
      bigint id PK
      text nome
      text descricao
      numeric valorpadrao
    }
    MECANICO {
      bigint id PK
      text nome
      text especialidade
    }
    ALUGUEL_SERVICO {
      bigint id_aluguel FK
      bigint id_servico FK
      numeric preco
      integer quantidade
    }
    MANUTENCAO_MECANICO {
      bigint id_manutencao FK
      bigint id_mecanico FK
      numeric horas_trabalhadas
    }

    CLIENTE ||--o{ ALUGUEL : "faz"
    VEICULO ||--o{ ALUGUEL : "é alugado em"
    SEGURO  ||--o{ ALUGUEL : "cobre"
    ALUGUEL ||--o{ ALUGUEL_SERVICO : "inclui"
    SERVICO ||--o{ ALUGUEL_SERVICO : "é fornecido em"
    VEICULO ||--o{ MANUTENCAO : "passa por"
    MANUTENCAO ||--o{ MANUTENCAO_MECANICO : "envolve"
    MECANICO ||--o{ MANUTENCAO_MECANICO : "executa"

```

### modelo-relacional-3FN

![Diagrama MER](Diagrama/3FN.svg)
