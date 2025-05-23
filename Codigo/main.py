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
fake.seed_instance(10)

#Gera clientes com dados brasileiros, evitando duplicatas de email e cnh.
def gerar_clientes(qtd: int = 3):
    # Busca os registros atuais
    resp = supabase.table('cliente').select('email, cnh').execute()
    existentes = resp.data or []
    emails_existentes = {c['email'] for c in existentes if c.get('email')}
    cnhs_existentes   = {c['cnh']   for c in existentes if c.get('cnh')}

    #Gera novos clientes
    novos = []
    while len(novos) < qtd:
        nome     = fake.name()
        email    = fake.email()
        telefone = fake.phone_number()
        cnh      = fake.numerify(text='###########')
        if email in emails_existentes or any(c['email']==email for c in novos): #Evita duplicatas de email
            continue
        if cnh in cnhs_existentes or any(c['cnh']==cnh for c in novos): #Evita duplicatas de cnh
            continue
        novos.append({
            'nome': nome,
            'email': email,
            'telefone': telefone,
            'cnh': cnh
        })

    #Verifica se foi gerado algum cliente
    if novos:
        supabase.table('cliente').insert(novos).execute()
    else:
        print("Nenhum novo cliente para inserir.")


#Lista de marcas e modelos de veículos.
    #A lista de modelos tem a quantidade de modelos por marca ajustada para 4,
    #com os dois primeiros modelos sendo 'Básico' e os dois últimos 'Avançado'.
MAKE_MODEL = {
    'Toyota': ['Yaris', 'Etios', 'RAV4', 'Corrola'],
    'Honda':  ['Fit', 'City', 'CR-V', 'Civic'],
    'Ford':   ['Fiesta', 'Focus', 'Mustang', 'Fusion'],
    'Chevrolet': ['Onix', 'Cruze', 'Tracker', 'Camaro'],
    'Volkswagen': ['Up', 'Polo', 'T-Cross', 'Tiguan'],
    'Hyundai': ['HB20', 'Elantra', 'Creta', 'Tucson']
}

#Gera veículos com combinações reais de marca e modelo.
def gerar_veiculos(qtd: int = 2):
    veiculos = []
    for _ in range(qtd):
        make = random.choice(list(MAKE_MODEL.keys())) # Marca aleatoria
        models = MAKE_MODEL[make]  # Lista de modelos da marca escolhida
        model = random.choice(models) # Modelo aleatorio
        model_index = models.index(model)  # Índice do modelo na lista
        tier = 'Básico' if model_index < 2 else 'Avançado' # Define o tier do veiculo conforme o indice do modelo
        veiculos.append({
            'placa': fake.unique.license_plate(),
            'modelo': f"{make} {model}",
            'ano': random.randint(2018, 2024),
            'statusdisponibilidade': 'Disponível',
            'tier': tier,
        })
    #Verifica se foi gerado algum veiculo
    if veiculos:
        supabase.table('veiculo').insert(veiculos).execute()
    else:
        print("Nenhum veículo gerado.")

#Gera mecânicos para atribuir às manutenções com especialidade definida (preventiva ou corretiva).
def gerar_mecanicos(qtd: int = 5):
    mecanicos = []
    for _ in range(qtd):
        mecanicos.append({
            'nome': fake.name(),
            'especialidade': random.choice(['preventiva', 'corretiva'])
        })
    #Verifica se foi gerado algum mecanico
    if mecanicos:
        supabase.table('mecanico').insert(mecanicos).execute()
    else:
        print("Nenhum mecanico gerado.")

#Gera aluguéis sem permitir que um cliente tenha períodos sobrepostos e associa serviços.
def gerar_alugueis(qtd: int = 2):
    clientes = supabase.table('cliente').select('id').execute().data or []
    veiculos  = supabase.table('veiculo').select('id, statusdisponibilidade, tier').execute().data
    seguros   = supabase.table('seguro').select('*').execute().data

    # Carrega todos os alugueis existentes (ativos ou concluídos)
    resp = supabase.table('aluguel').select('idcliente, idveiculo, datainicio, datafim').execute().data or []

    # Mapa: cliente_id -> lista de tuplas com (datainicio, datafim)
    alug_map: dict[int, list[tuple[datetime.date, datetime.date]]] = {} # Dicionário que armazena, para cada cliente, os períodos em que ele alugou veículos.
    # Mapa: veiculo_id -> lista de tuplas com (datainicio, datafim)
    veh_map: dict[int, list[tuple[datetime.date, datetime.date]]] = {} # Dicionário que armazena, para cada veiculo, os períodos em que ele foi alugado.

    # Preenche os dicionarios com dados do banco
    for a in resp:
        cid = a['idcliente'] # Id do cliente
        vid = a['idveiculo'] # Id do veiculo
        s = datetime.fromisoformat(a['datainicio']).date() # Converte a data de inicio para o formato datetime.date
        e = datetime.fromisoformat(a['datafim']).date() # Converte a data de de fim para o formato datetime.date
        alug_map.setdefault(cid, []).append((s, e))
        veh_map.setdefault(vid, []).append((s, e))

    alugueis = [] # Lista para armazenar os alugueis
    hoje      = datetime.now().date() # Data atual
    # Período de escolha para novas datas
    inicio_min = hoje - timedelta(days=90) # No máximo 90 dias passados
    fim_max    = hoje + timedelta(days=60) # No máximo 60 dias futuros

    # Gera os alugueis
    for _ in range(qtd):
        data_inicio = fake.date_between_dates(date_start=inicio_min, date_end=hoje) # Data inicial aleatoria com limite final sendo o dia atual
        status_aluguel = random.choice(['Ativo', 'Concluído']) # Status aleatorio

        #Caso o status escolhido seja 'Concluído'
        if status_aluguel == 'Concluído':
            fim_lim = hoje - timedelta(days=1) # Garante que o aluguel já terminou (Antes de hoje)
            min_fim = data_inicio + timedelta(days=1) # Garante pelo menos um dia de aluguel
            if min_fim > fim_lim:
                status_aluguel = 'Ativo' # Caso o aluguel não tenha terminado, altera o status para 'Ativo' (Isso pode acontecer caso o inicio do aluguel seja recente)
            else:
                dias = (fim_lim - min_fim).days # Intervalo máximo do aluguel
                dur  = random.randint(1, dias if dias > 0 else 1) # Quantidade de dias aleatória dentro do intervalo máximo
                data_fim = min_fim + timedelta(days=dur) # Data final do aluguel

        #Caso o status escolhido seja 'Ativo'
        if status_aluguel == 'Ativo':
            # Garante que o aluguel tenha pelo menos um dia e termine dentro de 60 dias apartir da data atual
            min_fim = max(hoje, data_inicio + timedelta(days=1)) 
            dias = (fim_max - min_fim).days 
            dur  = random.randint(1, dias if dias > 0 else 1)
            data_fim = min_fim + timedelta(days=dur)

        # Filtra os veículos disponíveis
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

        # Escolhe aleatoriamente um veiculo, um cliente e um seguro validos
        veiculo = random.choice(disponiveis_validos)
        cliente = random.choice(dispon_clientes)
        seguro  = random.choice(seguros)

        # Calculo do valor do aluguel sem considerar os serviços (dias * precoDoTier + valorDoSeguro)
        valor_dia    = 80 if veiculo['tier'] == 'Básico' else 140
        seguro_valor = seguro.get('valorbasico' if veiculo['tier'] == 'Básico' else 'valoravancado', 0)
        valortotal   = valor_dia * (data_fim - data_inicio).days + seguro_valor

        # Adiciona um dicionario, com os dados, na lista de alugueis
        alugueis.append({
            'idcliente':  cliente['id'],
            'idveiculo':  veiculo['id'],
            'idseguro':   seguro['id'],
            'datainicio': data_inicio.strftime("%Y-%m-%d"),
            'datafim':    data_fim.strftime("%Y-%m-%d"),
            'valor': valortotal,
            'status':     status_aluguel
        })

        # Preenche os dicionarios de mapeamento
        alug_map.setdefault(cliente['id'], []).append((data_inicio, data_fim))
        veh_map.setdefault(veiculo['id'], []).append((data_inicio, data_fim))

        # Atualiza o status do veículo
        new_status = 'Alugado' if status_aluguel == 'Ativo' else 'Disponível'
        supabase.table('veiculo').update({'statusdisponibilidade': new_status}) \
            .eq('id', veiculo['id']).execute()

    if alugueis:
        # Insere alugueis e obtém registros com IDs
        result = supabase.table('aluguel').insert(alugueis).execute()
        # Busca lista de serviços
        servicos = supabase.table('servico').select('id, valorpadrao').execute().data or []
        alug_servicos = []

        # Para cada aluguel inserido, associa de 1 a 3 serviços
        for aluguel in result.data:
            escolhidos = random.sample(servicos, k=min(3, len(servicos)))
            for s in escolhidos:
                quantidade = random.randint(1, 2) # Quantidade de vezes que um mesmo serviço é escolhido (Ex: 2 motoristas adicionais)
                alug_servicos.append({
                    'id_aluguel': aluguel['id'],
                    'id_servico': s['id'],
                    'quantidade': quantidade,
                    'preco': round(s['valorpadrao'] * quantidade, 2)
                })
        # Insere os dados na tabela 'aluguel_servico'
        if alug_servicos:
            supabase.table('aluguel_servico').insert(alug_servicos).execute()
    else:
        print("Nenhum aluguel gerado.")


#Gera registros de manutenção para veículos disponíveis, sem permitir sobreposição de períodos e, associas mecânicos com especialidade compatível
def gerar_manutencoes(qtd: int = 1):
    # Busca os veículos disponíveis
    veiculos = supabase.table('veiculo').select('id, statusdisponibilidade').execute().data
    disponiveis = [v for v in veiculos if v['statusdisponibilidade'] == 'Disponível']
    if not disponiveis:
        print("Nenhum veículo disponível para manutenção.")
        return

    # Carrega manutenções já existentes para evitar sobreposição
    resp_manut = supabase.table('manutencao').select('idveiculo, datainicio, datafim').execute().data or []

    # Mapa: veiculo_id -> lista de tuplas com (datainicio, datafim)
    manut_map: dict[int, list[tuple[datetime.date, datetime.date]]] = {} # Dicionário que armazena, para cada veiculo, os períodos em que ele foi para manutenção.

    # Preenche o dicionario com dados do banco
    for m in resp_manut:
        vid = m['idveiculo'] # Id do veiculo
         # Converte as datas para datetime.date
        s = datetime.fromisoformat(m['datainicio']).date()
        e = datetime.fromisoformat(m['datafim']).date() if m.get('datafim') else s # Se datafim estiver nula, assume o mesmo dia
        manut_map.setdefault(vid, []).append((s, e))

    manutencoes_data = []
    hoje = datetime.now().date()  # Data atual
    # Período de escolha para novas datas
    inicio_min = hoje - timedelta(days=90) # Maximo de 90 dias passados
    fim_max = hoje + timedelta(days=60) # Maximo de 60 dias futuros

    # Gera registros de manutenção
    for _ in range(qtd):
        veiculo = random.choice(disponiveis)
        # Gere o período da manutenção
        data_inicio = fake.date_between_dates(date_start=inicio_min, date_end=hoje) # Data inicial aleatoria com limite final sendo o dia atual
        status_manutencao = random.choice(['Ativo', 'Concluído']) # Status aleatorio

        # Caso o status seja 'Concluído'
        if status_manutencao == 'Concluído':
            if data_inicio >= hoje:
                status_local = 'Ativo' 
            else:
                fim_limite = hoje - timedelta(days=1) # Garante que a datafim seja anterior a dataAtual
                min_fim = data_inicio + timedelta(days=1) # Garante pelo menos um dia de manutenção
                if min_fim > fim_limite:
                    status_local = 'Ativo' # Caso a manutenção não tenha terminado, altera o status para 'Ativo' (Isso pode acontecer caso a data de inicio seja recente)
                else:
                    dias_range = (fim_limite - min_fim).days # Intervalo máximo de manutenção
                    duracao = random.randint(1, dias_range if dias_range > 0 else 1) # Quantidade de dias aleatoria dentro do intervalo
                    data_fim = min_fim + timedelta(days=duracao)
                    status_local = 'Concluído'

        # Caso o status seja 'Ativo
        if status_manutencao == 'Ativo' or ('status_local' in locals() and status_local == 'Ativo'):
            # Garante que a manutenção tenha pelo menos um dia e termine dentro de 60 dias apartir da data atual
            min_fim = max(hoje, data_inicio + timedelta(days=1))
            dias_range = (fim_max - min_fim).days
            duracao = random.randint(1, dias_range if dias_range > 0 else 1)
            data_fim = min_fim + timedelta(days=duracao)
            status_local = 'Ativo'

        # Verifica se o veículo já possui manutenção neste período
        periodos_existentes = manut_map.get(veiculo['id'], [])
        conflito = any(data_inicio <= r_end and r_start <= data_fim for (r_start, r_end) in periodos_existentes)
        if conflito:
            print(f"Veículo {veiculo['id']} já possui manutenção em período sobreposto. Pulando este veículo.")
            continue

        # Define o tipo de manutenção (preventiva ou corretiva)
        manut_tipo = random.choice(['preventiva', 'corretiva'])
        
        # Adiciona os dados em um dicionario
        registro = {
            'idveiculo':  veiculo['id'],
            'tipo':       manut_tipo,
            'datainicio': data_inicio.strftime("%Y-%m-%d"),
            'datafim':    data_fim.strftime("%Y-%m-%d"),
            'custo':      round(random.uniform(300, 5000), 2),
            'descricao':  fake.sentence(),
            'status':     status_local
        }
        manutencoes_data.append(registro) # Adiciona o dicionario na lista de manutenções

        # Atualiza o mapa da manutenção para evitar sobreposição em futuras inserções
        manut_map.setdefault(veiculo['id'], []).append((data_inicio, data_fim))
        # Remove o veículo da lista de disponíveis para não ser escolhido novamente neste ciclo
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
    
    # Associa mecânicos compatíveis com o tipo da manutenção
    mecanicos = supabase.table('mecanico').select('id, especialidade').execute().data or []
    mm = []
    for m in result.data:
        mec_validos = [mech for mech in mecanicos if mech['especialidade'].lower() == m['tipo'].lower()]
        if mec_validos:
            escolhidos = random.sample(mec_validos, k=min(2, len(mec_validos))) # Mecanico valido aleatorio
            for mech in escolhidos:
                mm.append({
                    'id_manutencao':     m['id'],
                    'id_mecanico':       mech['id'],
                    'horas_trabalhadas': round(random.uniform(1, 4), 2)
                })
    # Adiciona os dados na tabela 'manutencao_mecanico'
    if mm:
        supabase.table('manutencao_mecanico').insert(mm).execute()


#Gera todos os dados (clientes, veículos, mecânicos, manutenções e aluguéis) de acordo com o nível.
def gerar_tudo(nivel: int):
    # Parâmetro:
    #   nivel: int de 1 a 5, onde 1 gera poucos dados e 5 gera muitos dados.
    if nivel < 1 or nivel > 5:
        raise ValueError("O nível deve estar entre 1 e 5.")
    
    # Mapeamento:
    qtd_clientes   = round(10 + (nivel - 1) * (50 - 10) / 4) # Varia de 10 até 50 clientes
    qtd_veiculos   = round(5 + (nivel - 1) * (30 - 5) / 4) # Varia de 5 até 30 veiculos
    qtd_manutencoes = round(1 + (nivel - 1) * (10 - 1) / 4) # Varia de 1 até 10 manutenções
    qtd_alugueis   = round(2 + (nivel - 1) * (20 - 2) / 4) # Varia de 2 até 20 alugueis
    
    print(f"Gerando dados com nível {nivel}:")
    print(f"Clientes: {qtd_clientes}, Veículos: {qtd_veiculos}, Manutenções: {qtd_manutencoes}, Aluguéis: {qtd_alugueis}")
    
    # Gerando dados
    gerar_clientes(qtd_clientes)
    gerar_veiculos(qtd_veiculos)
    gerar_mecanicos(5)            # popula tabela de mecânicos
    gerar_manutencoes(qtd_manutencoes)
    gerar_alugueis(qtd_alugueis)

if __name__ == "__main__":
    # Gera dados em nível 5 (pode ser ajustado conforme necessário)
    gerar_tudo(5)
    print("Dados inseridos com sucesso!")
