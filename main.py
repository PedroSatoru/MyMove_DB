import os
from dotenv import load_dotenv
from supabase import create_client, Client
import random
from faker import Faker
from datetime import datetime, timedelta

# Carregar variáveis de ambiente
load_dotenv()

# Obter e normalizar as chaves do Supabase
_raw_url = os.getenv("SUPABASE_URL", "")
_raw_key = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = _raw_url.strip().strip('"')
SUPABASE_KEY = _raw_key.strip().strip('"')

# Verificar se as variáveis foram carregadas corretamente
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("As variáveis SUPABASE_URL e SUPABASE_KEY não foram carregadas corretamente.")

# Criar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gerar nomes e frases em português
fake = Faker('pt_BR')
fake.seed_instance(42)

def gerar_clientes(qtd: int = 3):
    """Gera clientes com dados brasileiros, evitando duplicatas de email e cnh."""
    # Buscar existentes
    resp = supabase.table('cliente').select('email, cnh').execute()
    existentes = resp.data or []
    emails_existentes = {c['email'] for c in existentes if c.get('email')}
    cnhs_existentes   = {c['cnh']   for c in existentes if c.get('cnh')}

    novos = []
    while len(novos) < qtd:
        nome     = fake.name()
        email    = fake.email()
        telefone = fake.phone_number()
        cnh      = fake.numerify(text='###########')
        # pular duplicados
        if email in emails_existentes or any(c['email']==email for c in novos):
            continue
        if cnh in cnhs_existentes or any(c['cnh']==cnh for c in novos):
            continue
        novos.append({
            'nome': nome,
            'email': email,
            'telefone': telefone,
            'cnh': cnh
        })

    supabase.table('cliente').insert(novos).execute()

def gerar_veiculos(qtd: int = 2):
    """Gera veículos com status e tier consolidados"""
    modelos = ['sedan', 'hatch', 'suv', 'pickup']
    veiculos = [{
        'placa': fake.unique.license_plate(),
        'modelo': random.choice(modelos),
        'ano': random.randint(2018, 2024),
        # Usar valores que batem com a enum TierVeiculo e sem erros de digitação
        'statusdisponibilidade': random.choice(['Disponível', 'Manutenção']),
        'tier': random.choice(['Básico', 'Avançado'])
    } for _ in range(qtd)]
    
    supabase.table('veiculo').insert(veiculos).execute()

def gerar_alugueis(qtd: int = 2):
    """Gera aluguéis vinculando entidades existentes"""
    clientes = supabase.table('cliente').select('id').execute().data
    veiculos = supabase.table('veiculo').select('id, statusdisponibilidade').execute().data
    seguros  = supabase.table('seguro').select('id').execute().data
    
    alugueis = []
    for _ in range(qtd):
        disponiveis = [v for v in veiculos if v['statusdisponibilidade'] == 'Disponível']
        if not disponiveis:
            print("Nenhum veículo disponível para aluguel.")
            break
        veiculo = random.choice(disponiveis)
        cliente = random.choice(clientes)
        seguro  = random.choice(seguros)
        
        data_inicio = fake.date_between(start_date='-30d', end_date='today')
        data_fim    = data_inicio + timedelta(days=random.randint(1, 14))
        
        alugueis.append({
            'idcliente':   cliente['id'],
            'idveiculo':   veiculo['id'],
            'idseguro':    seguro['id'],
            'datainicio':  data_inicio.isoformat(),
            'datafim':     data_fim.isoformat(),
            'valortotal':  round(random.uniform(200, 2000), 2),
            'status':      random.choice(['Ativo', 'Concluído'])
        })
        
        # Atualiza veículo para "Alugado"
        supabase.table('veiculo') \
            .update({'statusdisponibilidade': 'Alugado'}) \
            .eq('id', veiculo['id']) \
            .execute()
    
    supabase.table('aluguel').insert(alugueis).execute()

def gerar_manutencoes(qtd: int = 1):
    """Gera registros de manutenção"""
    # Selecionar veículos (pode-se optar por filtrar somente os disponíveis, se desejar)
    veiculos = supabase.table('veiculo').select('id').execute().data
    
    # Lista auxiliar para relacionar veículo e dados da manutenção
    manutencoes_data = []   # armazenará apenas os dados para inserir na tabela manutencao
    relacionamentos = []    # armazenará tuplas (idveiculo, data_inicio) para o histórico
    
    for _ in range(qtd):
        # Escolhe veículo aleatoriamente
        veiculo = random.choice(veiculos)
        # Marca o veículo como em manutenção
        supabase.table('veiculo') \
            .update({'statusdisponibilidade': 'Manutenção'}) \
            .eq('id', veiculo['id']) \
            .execute()

        data_inicio = fake.date_between(start_date='-60d', end_date='today')
        data_fim    = data_inicio + timedelta(days=random.randint(1, 3))
        
        # Prepara dados para manutenção, sem incluir idveiculo (pois a coluna não existe)
        manutencao = {
            'tipo':       random.choice(['preventiva', 'corretiva']),
            'datainicio': data_inicio.isoformat(),
            'datafim':    data_fim.isoformat(),
            'custo':      round(random.uniform(300, 5000), 2),
            'descricao':  fake.sentence()
        }
        manutencoes_data.append(manutencao)
        # Armazena o id do veículo para vincular posteriormente com a manutenção inserida
        relacionamentos.append({
            'idveiculo': veiculo['id'],
            'data_inicio': data_inicio.isoformat()  # usaremos essa data no histórico
        })
    
    if not manutencoes_data:
        return
    
    result = supabase.table('manutencao').insert(manutencoes_data).execute()
    
    # Considera que a ordem dos registros inseridos corresponde à dos itens em "relacionamentos"
    for idx, m in enumerate(result.data):
        rel = relacionamentos[idx]
        # Registra no histórico de manutenção vinculando o veículo à manutenção inserida
        supabase.table('historicomanutencao').insert({
            'idveiculo':    rel['idveiculo'],
            'idmanutencao': m['id'],
            'dataregistro': m['datainicio']
        }).execute()
        # Após a manutenção, libera o veículo
        supabase.table('veiculo') \
            .update({'statusdisponibilidade': 'Disponível'}) \
            .eq('id', rel['idveiculo']) \
            .execute()

if __name__ == "__main__":
    gerar_clientes(random.randint(1, 20))
    gerar_veiculos(random.randint(1, 20))
    gerar_manutencoes(random.randint(0, 10))
    gerar_alugueis(random.randint(1, 20))
    
    print("Dados inseridos com sucesso!")