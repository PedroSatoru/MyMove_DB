import os
from dotenv import load_dotenv
from supabase import create_client, Client
import random
from faker import Faker
from faker_vehicle import VehicleProvider
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
fake.add_provider(VehicleProvider)
fake.seed_instance(10)

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

MAKE_MODEL = {
    'Toyota': ['Yaris', 'Etios', 'RAV4', 'Corrola'],
    'Honda':  ['Fit', 'City', 'CR-V', 'Civic'],
    'Ford':   ['Fiesta', 'Focus', 'Mustang', 'Fusion'],
    'Chevrolet': ['Onix', 'Cruze', 'Tracker', 'Camaro'],
    'Volkswagen': ['Up', 'Polo', 'T-Cross', 'Tiguan'],
    'Hyundai': ['HB20', 'Elantra', 'Creta', 'Tucson']
}

def gerar_veiculos(qtd: int = 2):
    """Gera veículos com combinações reais de marca e modelo."""
    veiculos = []
    for _ in range(qtd):
        make = random.choice(list(MAKE_MODEL.keys()))
        models = MAKE_MODEL[make]  # Lista de modelos da marca escolhida
        model = random.choice(models)
        model_index = models.index(model)  # Índice do modelo na lista
        tier = 'Básico' if model_index < 2 else 'Avançado'
        veiculos.append({
            'placa': fake.unique.license_plate(),
            'modelo': f"{make} {model}",
            'ano': random.randint(2018, 2024),
            'statusdisponibilidade': 'Disponível',
            'tier': tier,
        })
    if veiculos:
        supabase.table('veiculo').insert(veiculos).execute()
    else:
        print("Nenhum veículo gerado.")

def gerar_mecanicos(qtd: int = 5):
    """Gera mecânicos para atribuir às manutenções com especialidade definida (preventiva ou corretiva)."""
    mecanicos = []
    for _ in range(qtd):
        mecanicos.append({
            'nome': fake.name(),
            # A especialidade agora é definida como 'preventiva' ou 'corretiva'
            'especialidade': random.choice(['preventiva', 'corretiva'])
        })
    if mecanicos:
        supabase.table('mecanico').insert(mecanicos).execute()

def gerar_alugueis(qtd: int = 2):
    """Gera aluguéis sem permitir que um cliente tenha períodos sobrepostos e associa serviços."""
    clientes = supabase.table('cliente').select('id').execute().data or []
    veiculos  = supabase.table('veiculo').select('id, statusdisponibilidade, tier').execute().data
    seguros   = supabase.table('seguro').select('*').execute().data

    # Carrega todos os alugueis existentes (ativos ou concluídos)
    resp = supabase.table('aluguel').select('idcliente, idveiculo, datainicio, datafim').execute().data or []

    # Mapa: cliente_id -> list of (start_date, end_date)
    alug_map: dict[int, list[tuple[datetime.date, datetime.date]]] = {}
    # Mapa: veiculo_id -> list of (start_date, end_date)
    veh_map: dict[int, list[tuple[datetime.date, datetime.date]]] = {}

    for a in resp:
        cid = a['idcliente']
        vid = a['idveiculo']
        s = datetime.fromisoformat(a['datainicio']).date()
        e = datetime.fromisoformat(a['datafim']).date()
        alug_map.setdefault(cid, []).append((s, e))
        veh_map.setdefault(vid, []).append((s, e))

    alugueis = []
    hoje      = datetime.now().date()
    inicio_min = hoje - timedelta(days=90)
    fim_max    = hoje + timedelta(days=60)

    for _ in range(qtd):
        # Gera primeiro o período do aluguel
        data_inicio = fake.date_between_dates(date_start=inicio_min, date_end=hoje)
        status_aluguel = random.choice(['Ativo', 'Concluído'])
        if status_aluguel == 'Concluído':
            fim_lim = hoje - timedelta(days=1)
            min_fim = data_inicio + timedelta(days=1)
            if min_fim > fim_lim:
                status_aluguel = 'Ativo'
            else:
                dias = (fim_lim - min_fim).days
                dur  = random.randint(1, dias if dias > 0 else 1)
                data_fim = min_fim + timedelta(days=dur)
        if status_aluguel == 'Ativo':
            min_fim = max(hoje, data_inicio + timedelta(days=1))
            dias = (fim_max - min_fim).days
            dur  = random.randint(1, dias if dias > 0 else 1)
            data_fim = min_fim + timedelta(days=dur)

        # Agora, filtre veículos disponíveis sem conflitos
        veiculos = supabase.table('veiculo').select('id, statusdisponibilidade, tier').execute().data
        disponiveis = [v for v in veiculos if v['statusdisponibilidade'] == 'Disponível']
        disponiveis_validos = [v for v in disponiveis if 
            all(not (data_inicio <= r_end and r_start <= data_fim) for (r_start, r_end) in veh_map.get(v['id'], []))
        ]
        
        if not disponiveis_validos:
            print("Nenhum veículo livre nesse período.")
            continue

        # Filtra os clientes que não possuem conflito no período
        dispon_clientes = []
        for c in clientes:
            periodos = alug_map.get(c['id'], [])
            if all(not (data_inicio <= e and s <= data_fim) for (s, e) in periodos):
                dispon_clientes.append(c)
        if not dispon_clientes:
            print("Nenhum cliente livre para novo aluguel neste período.")
            break

        veiculo = random.choice(disponiveis_validos)
        cliente = random.choice(dispon_clientes)
        seguro  = random.choice(seguros)

        valor_dia    = 80 if veiculo['tier'] == 'Básico' else 140
        seguro_valor = seguro.get('valorbasico' if veiculo['tier'] == 'Básico' else 'valoravancado', 0)
        valortotal   = valor_dia * (data_fim - data_inicio).days + seguro_valor

        alugueis.append({
            'idcliente':  cliente['id'],
            'idveiculo':  veiculo['id'],
            'idseguro':   seguro['id'],
            'datainicio': data_inicio.strftime("%Y-%m-%d"),
            'datafim':    data_fim.strftime("%Y-%m-%d"),
            'valortotal': valortotal,
            'status':     status_aluguel
        })

        alug_map.setdefault(cliente['id'], []).append((data_inicio, data_fim))
        veh_map.setdefault(veiculo['id'], []).append((data_inicio, data_fim))

        # Atualiza status do veículo
        new_status = 'Alugado' if status_aluguel == 'Ativo' else 'Disponível'
        supabase.table('veiculo').update({'statusdisponibilidade': new_status}) \
            .eq('id', veiculo['id']).execute()

    if alugueis:
        # insere alugueis e obtém registros com IDs
        result = supabase.table('aluguel').insert(alugueis).execute()
        # busca lista de serviços
        servicos = supabase.table('servico').select('id, valorpadrao').execute().data or []
        alug_servicos = []
        # para cada aluguel inserido, associa de 1 a 3 serviços
        for aluguel in result.data:
            escolhidos = random.sample(servicos, k=min(3, len(servicos)))
            for s in escolhidos:
                alug_servicos.append({
                    'id_aluguel':   aluguel['id'],
                    'id_servico':   s['id'],
                    'preco':        round(s['valorpadrao'] * random.uniform(0.8, 1.2), 2),
                    'quantidade':   random.randint(1, 2)
                })
        if alug_servicos:
            supabase.table('aluguel_servico').insert(alug_servicos).execute()
    else:
        print("Nenhum aluguel gerado.")

def gerar_manutencoes(qtd: int = 1):
    """
    Gera registros de manutenção para veículos disponíveis, armazenando idveiculo na tabela manutenção.
    Apenas mecânicos com especialidade compatível com o tipo de manutenção serão associados.
    """
    veiculos = supabase.table('veiculo').select('id, statusdisponibilidade').execute().data
    disponiveis = [v for v in veiculos if v['statusdisponibilidade'] == 'Disponível']
    if not disponiveis:
        print("Nenhum veículo disponível para manutenção.")
        return

    manutencoes_data = []
    hoje = datetime.now().date()  # utilizando date para consistência
    inicio_min = hoje - timedelta(days=90)
    fim_max = hoje + timedelta(days=60)

    for _ in range(qtd):
        veiculo = random.choice(disponiveis)
        # Marca o veículo como em manutenção
        supabase.table('veiculo') \
            .update({'statusdisponibilidade': 'Manutenção'}) \
            .eq('id', veiculo['id']) \
            .execute()
        
        data_inicio = fake.date_between_dates(date_start=inicio_min, date_end=hoje)
        
        # Define status aleatório para manutenção e determina data_fim
        status_manutencao = random.choice(['Ativo', 'Concluído'])
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
        if status_manutencao == 'Ativo' or ('status_local' in locals() and status_local == 'Ativo'):
            min_fim = max(hoje, data_inicio + timedelta(days=1))
            dias_range = (fim_max - min_fim).days
            duracao = random.randint(1, dias_range if dias_range > 0 else 1)
            data_fim = min_fim + timedelta(days=duracao)
            status_local = 'Ativo'
        
        # Define o tipo de manutenção (preventiva ou corretiva)
        manut_tipo = random.choice(['preventiva', 'corretiva'])
        
        manutencoes_data.append({
            'idveiculo':  veiculo['id'],
            'tipo':       manut_tipo,
            'datainicio': data_inicio.strftime("%Y-%m-%d"),
            'datafim':    data_fim.strftime("%Y-%m-%d"),
            'custo':      round(random.uniform(300, 5000), 2),
            'descricao':  fake.sentence(),
            'status':     status_local
        })
        disponiveis = [v for v in disponiveis if v['id'] != veiculo['id']]
    
    if not manutencoes_data:
        print("Nenhuma manutenção gerada.")
        return
    
    # Inserir manutenções e obter registros com IDs
    result = supabase.table('manutencao').insert(manutencoes_data).execute()
    
    # Atualiza status do veículo após inserção
    for m in result.data:
        novo_status = 'Disponível' if m['status'] == 'Concluído' else 'Manutenção'
        supabase.table('veiculo').update(
            {'statusdisponibilidade': novo_status}
        ).eq('id', m['idveiculo']).execute()
    
    # Após inserir manutenções, associa mecânicos compatíveis com a especialidade da manutenção
    mecanicos = supabase.table('mecanico').select('id, especialidade').execute().data or []
    mm = []
    for m in result.data:
        # Filtra os mecânicos cuja especialidade é compatível com o tipo da manutenção
        mec_validos = [mech for mech in mecanicos if mech['especialidade'].lower() == m['tipo'].lower()]
        if mec_validos:
            escolhidos = random.sample(mec_validos, k=min(2, len(mec_validos)))
            for mech in escolhidos:
                mm.append({
                    'id_manutencao':     m['id'],
                    'id_mecanico':       mech['id'],
                    'horas_trabalhadas': round(random.uniform(1, 4), 2)
                })
    if mm:
        supabase.table('manutencao_mecanico').insert(mm).execute()

def gerar_tudo(nivel: int):
    """
    Gera todos os dados (clientes, veículos, mecânicos, manutenções e aluguéis) de acordo com o nível.
    Parâmetro:
      nivel: int de 1 a 5, onde 1 gera poucos dados e 5 gera muitos dados.
    """
    if nivel < 1 or nivel > 5:
        raise ValueError("O nível deve estar entre 1 e 5.")
    
    # Novo mapeamento:
    qtd_clientes   = round(10 + (nivel - 1) * (50 - 10) / 4)
    qtd_veiculos   = round(5 + (nivel - 1) * (30 - 5) / 4)
    # Agora varia de 1 até 10 manutenções
    qtd_manutencoes = round(1 + (nivel - 1) * (10 - 1) / 4)
    qtd_alugueis   = round(2 + (nivel - 1) * (20 - 2) / 4)
    
    print(f"Gerando dados com nível {nivel}:")
    print(f"Clientes: {qtd_clientes}, Veículos: {qtd_veiculos}, Manutenções: {qtd_manutencoes}, Aluguéis: {qtd_alugueis}")
    
    gerar_clientes(qtd_clientes)
    gerar_veiculos(qtd_veiculos)
    gerar_mecanicos(5)            # popula tabela de mecânicos
    gerar_manutencoes(qtd_manutencoes)
    gerar_alugueis(qtd_alugueis)

if __name__ == "__main__":
    # Exemplo: para gerar dados em nível 2 (pode ser ajustado conforme necessário)
    gerar_tudo(5)
    print("Dados inseridos com sucesso!")