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

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("As variáveis SUPABASE_URL e SUPABASE_KEY não foram carregadas corretamente.")

# Criar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gerar nomes e frases em português
fake = Faker('pt_BR')
fake.seed_instance(42)

def gerar_clientes(qtd: int = 3):
    """Gera clientes com dados brasileiros, evitando duplicatas de email e cnh."""
    # Busca os registros atuais
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

    if novos:
        supabase.table('cliente').insert(novos).execute()
    else:
        print("Nenhum novo cliente para inserir.")

def gerar_veiculos(qtd: int = 2):
    """Gera veículos garantindo a unicidade da placa e definindo seu status."""
    modelos = ['sedan', 'hatch', 'suv', 'pickup']
    # Para evitar duplicidade, usamos fake.unique
    veiculos = [{
        'placa': fake.unique.license_plate(),
        'modelo': random.choice(modelos),
        'ano': random.randint(2018, 2024),
        # Define o status inicial como Disponível
        'statusdisponibilidade': 'Disponível',
        'tier': random.choice(['Básico', 'Avançado'])
    } for _ in range(qtd)]
    
    if veiculos:
        supabase.table('veiculo').insert(veiculos).execute()
    else:
        print("Nenhum veículo gerado.")

def garantir_seguros(min_qtd: int = 1):
    """Garante que haja pelo menos `min_qtd` registros na tabela seguro."""
    resp = supabase.table('seguro').select('id, valorbasico, valoravancado').execute().data or []
    faltam = max(0, min_qtd - len(resp))
    if faltam:
        novos = []
        for _ in range(faltam):
            novos.append({
                'nome': fake.word().capitalize(),
                'valorbasico': random.randint(50, 100),
                'valoravancado': random.randint(100, 200)
            })
        supabase.table('seguro').insert(novos).execute()

def gerar_alugueis(qtd: int = 2):
    """Gera aluguéis apenas para veículos disponíveis e atualiza seu status conforme o aluguel."""
    # garante ao menos 1 seguro
    garantir_seguros(1)

    clientes = supabase.table('cliente').select('id').execute().data
    veiculos = supabase.table('veiculo').select('id, statusdisponibilidade, tier').execute().data
    seguros  = supabase.table('seguro').select('*').execute().data

    if not clientes or not veiculos:
        print("Verifique se há clientes e veículos suficientes para gerar aluguéis.")
        return
    # (agora seguros nunca estará vazio)

    alugueis = []
    hoje = datetime.now().date()  # usando date para compatibilidade
    inicio_min = hoje - timedelta(days=90)  # 3 meses atrás
    fim_max = hoje + timedelta(days=60)       # 2 meses à frente

    for _ in range(qtd):
        veiculos = supabase.table('veiculo') \
            .select('id, statusdisponibilidade, tier') \
            .execute().data
        disponiveis = [v for v in veiculos if v['statusdisponibilidade'] == 'Disponível']
        if not disponiveis:
            print("Nenhum veículo disponível para aluguel.")
            break

        veiculo = random.choice(disponiveis)
        cliente = random.choice(clientes)
        seguro = random.choice(seguros)

        # data_inicio entre inicio_min e hoje (nunca depois de hoje)
        data_inicio = fake.date_between_dates(date_start=inicio_min, date_end=hoje)

        # Define status aleatório
        status_aluguel = random.choice(['Ativo', 'Concluído'])
        # Para registros Concluídos, a data de fim deve ser anterior a hoje e maior que data_inicio
        if status_aluguel == 'Concluído':
            if data_inicio >= hoje:
                status_aluguel = 'Ativo'
            else:
                fim_limite = hoje - timedelta(days=1)
                min_fim = data_inicio + timedelta(days=1)
                if min_fim > fim_limite:
                    status_aluguel = 'Ativo'
                else:
                    dias_range = (fim_limite - min_fim).days
                    duracao = random.randint(1, dias_range if dias_range > 0 else 1)
                    data_fim = min_fim + timedelta(days=duracao)
        if status_aluguel == 'Ativo':
            min_fim = max(hoje, data_inicio + timedelta(days=1))
            dias_range = (fim_max - min_fim).days
            duracao = random.randint(1, dias_range if dias_range > 0 else 1)
            data_fim = min_fim + timedelta(days=duracao)

        if veiculo['tier'] == 'Básico':
            valor_dia = 80
            seguro_valor = seguro.get('valorbasico', 0)
        else:
            valor_dia = 140
            seguro_valor = seguro.get('valoravancado', 0)

        valortotal = (valor_dia * (data_fim - data_inicio).days) + seguro_valor

        alugueis.append({
            'idcliente': cliente['id'],
            'idveiculo': veiculo['id'],
            'idseguro': seguro['id'],
            'datainicio': data_inicio.isoformat(),
            'datafim': data_fim.isoformat(),
            'valortotal': valortotal,
            'status': status_aluguel
        })

        if status_aluguel == 'Ativo':
            status_update = 'Alugado'
        else:
            status_update = 'Disponível'
        supabase.table('veiculo') \
            .update({'statusdisponibilidade': status_update}) \
            .eq('id', veiculo['id']) \
            .execute()

    if alugueis:
        supabase.table('aluguel').insert(alugueis).execute()
    else:
        print("Nenhum aluguel gerado.")

def gerar_manutencoes(qtd: int = 1):
    """
    Gera registros de manutenção para veículos disponíveis e garante o histórico,
    usando datas onde o início ocorre entre hoje – 90 e hoje.
    Para manutenção:
      - Se o status for 'Concluído', a data de fim deverá ser anterior a hoje.
      - Se for 'Ativo', a data de fim ficará posterior ou igual a hoje.
    O campo 'status' na manutenção utilizará a mesma lógica de aluguel.
    OBS: A coluna datafim será armazenada apenas com a data (YYYY-MM-DD).
    """
    veiculos = supabase.table('veiculo').select('id, statusdisponibilidade').execute().data
    disponiveis = [v for v in veiculos if v['statusdisponibilidade'] == 'Disponível']
    if not disponiveis:
        print("Nenhum veículo disponível para manutenção.")
        return

    manutencoes_data = []
    relacionamentos = []
    hoje = datetime.now().date()  # utilizando date para consistência
    inicio_min = hoje - timedelta(days=90)
    fim_max = hoje + timedelta(days=60)

    # Define status aleatório para manutenção
    status_manutencao = random.choice(['Ativo', 'Concluído'])
    
    for _ in range(qtd):
        veiculo = random.choice(disponiveis)
        # Marca o veículo como em manutenção
        supabase.table('veiculo') \
            .update({'statusdisponibilidade': 'Manutenção'}) \
            .eq('id', veiculo['id']) \
            .execute()
        
        data_inicio = fake.date_between_dates(date_start=inicio_min, date_end=hoje)
        
        # Determina data_fim e status_local conforme a regra:
        # Se status 'Concluído', a data de fim deverá ser anterior a hoje
        if status_manutencao == 'Concluído':
            if data_inicio >= hoje:
                status_local = 'Ativo'
            else:
                fim_limite = hoje - timedelta(days=1)
                min_fim = data_inicio + timedelta(days=1)
                if min_fim > fim_limite:
                    status_local = 'Ativo'
                else:
                    dias_range = (fim_limite - min_fim).days
                    duracao = random.randint(1, dias_range if dias_range > 0 else 1)
                    data_fim = min_fim + timedelta(days=duracao)
                    status_local = 'Concluído'
        # Se status 'Ativo', a data de fim deverá ser posterior ou igual a hoje
        if status_manutencao == 'Ativo' or ('status_local' in locals() and status_local == 'Ativo'):
            min_fim = max(hoje, data_inicio + timedelta(days=1))
            dias_range = (fim_max - min_fim).days
            duracao = random.randint(1, dias_range if dias_range > 0 else 1)
            data_fim = min_fim + timedelta(days=duracao)
            status_local = 'Ativo'
        
        # Constrói o registro de manutenção incluindo o campo 'status'
        # Utiliza strftime('%Y-%m-%d') para garantir que apenas a data seja armazenada
        manutencao = {
            'tipo': random.choice(['preventiva', 'corretiva']),
            'datainicio': data_inicio.isoformat(),
            'datafim': data_fim.strftime("%Y-%m-%d"),
            'custo': round(random.uniform(300, 5000), 2),
            'descricao': fake.sentence(),
            'status': status_local
        }
        manutencoes_data.append(manutencao)
        relacionamentos.append({
            'idveiculo': veiculo['id'],
            'data_inicio': data_inicio.isoformat()
        })
        disponiveis = [v for v in disponiveis if v['id'] != veiculo['id']]
    
    if not manutencoes_data:
        print("Nenhuma manutenção gerada.")
        return
    
    result = supabase.table('manutencao').insert(manutencoes_data).execute()
    
    for idx, m in enumerate(result.data):
        rel = relacionamentos[idx]
        supabase.table('historicomanutencao').insert({
            'idveiculo': rel['idveiculo'],
            'idmanutencao': m['id'],
            'dataregistro': m['datainicio']
        }).execute()
        # Libera o veículo após a manutenção
        supabase.table('veiculo') \
            .update({'statusdisponibilidade': 'Disponível'}) \
            .eq('id', rel['idveiculo']) \
            .execute()

def gerar_tudo(nivel: int):
    """
    Gera todos os dados (clientes, veículos, manutenções e aluguéis) de acordo com o nível.
    Parâmetro:
      nivel: int de 1 a 5, onde 1 gera poucos dados e 5 gera muitos dados.
    """
    if nivel < 1 or nivel > 5:
        raise ValueError("O nível deve estar entre 1 e 5.")
    
    # Novo mapeamento:
    qtd_clientes   = round(10 + (nivel - 1) * (50 - 10) / 4)
    qtd_veiculos   = round(5 + (nivel - 1) * (30 - 5) / 4)
    qtd_manutencoes = round(0 + (nivel - 1) * (2 - 0) / 4)    # Máximo de 2 manutenções
    qtd_alugueis   = round(2 + (nivel - 1) * (20 - 2) / 4)
    
    print(f"Gerando dados com nível {nivel}:")
    print(f"Clientes: {qtd_clientes}, Veículos: {qtd_veiculos}, Manutenções: {qtd_manutencoes}, Aluguéis: {qtd_alugueis}")
    
    gerar_clientes(qtd_clientes)
    gerar_veiculos(qtd_veiculos)
    gerar_manutencoes(qtd_manutencoes)
    gerar_alugueis(qtd_alugueis)

if __name__ == "__main__":
    # Exemplo: para gerar dados em nível 2 (pode ser ajustado conforme necessário)
    gerar_tudo(3)
    print("Dados inseridos com sucesso!")