from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv


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

# ---------------------
# Funções básicas
# ---------------------

# Carrega as tabelas em um dataframe pandas
def carregarTabelas(table):
    print(f"🔄 Carregando dados da tabela {table}...")
    data = supabase.table(table).select("*").execute().data
    return pd.DataFrame(data)

# Verifica se há campos nulos na coluna
def checarNulos(df, colunas, nome=""):
    print(f"\n Verificando nulos na tabela {nome}...")
    for col in colunas:
        if col in df.columns:
            inconsistencias = df[df[col].isnull()] # Linhas nulos são adicionadas
            if not inconsistencias.empty:
                print(f"❌ Nulos em {col}: {len(inconsistencias)} inconsistências.")
            else:
                print(f"✅ {col} sem nulos.")

# Verifica se há campos com dados duplicados
def checarDuplicatas(df, colunas, nome):
    print(f"\n Verificando duplicatas em {nome}...")
    inconsistencias = df[df.duplicated(subset=colunas, keep=False)] # Linhas com dados duplicados são adicionadas
    if not inconsistencias.empty:
        print(f"❌ Duplicatas encontradas em {nome}: {len(inconsistencias)}")
    else:
        print(f"✅ {nome} sem duplicatas.")


# ---------------------
# Funções de validação
# ---------------------

# Verifica se as datas de inicio antecedem as datas de fim
def checarDatas(df, nome=""):
    if 'datainicio' in df.columns and 'datafim' in df.columns:
        inconsistencias = df[df['datainicio'] > df['datafim']] # Linhas com datas invalidas são adicionadas
        print(f"\n Verificando datas da tabela {nome}...")
        if not inconsistencias.empty:
            print(f"❌ {nome} contém datas inválidas! Quantidade: {len(inconsistencias)}")
        else:
            print(f"✅ {nome} contém datas válidas.")
    else:
        print(f"⚠️ Não foi possível verificar datas em {nome} - colunas necessárias não encontradas")


# Verifica os status dos alugueis
def checarStatusAluguel(df_aluguel):
    if all(col in df_aluguel.columns for col in ['status', 'datainicio', 'datafim']):
        print(f"\n Verificando status da tabela aluguel...")
        
        hoje = datetime.now().date() # Data atual

        # Aluguéis marcados como "Ativo", mas, com datafim no passado, são adicionados
        inconsistencias = df_aluguel[
            (df_aluguel['status'] == 'Ativo') & 
            (pd.to_datetime(df_aluguel['datafim']).dt.date < hoje)
        ]
        
        if not inconsistencias.empty:
            print(f"❌ Aluguéis marcados como 'Ativo' com data fim no passado! Quantidade: {len(inconsistencias)}")
        else:
            print("✅ Status dos aluguéis consistentes com as datas.")
    else:
        print("⚠️ Não foi possível verificar status do aluguel - colunas necessárias não encontradas")


# Verifica os status das manutenções
def checarStatusManutencao(df_manutencao):
    if all(col in df_manutencao.columns for col in ['status', 'datainicio', 'datafim']):
        print(f"\n Verificando status da tabela manutenção...")
        
        hoje = datetime.now().date() # Data atual
        # Manutenções marcadas como "Ativo", mas, com datafim no passado, são adicionadas
        inconsistencias = df_manutencao[
            (df_manutencao['status'] == 'Ativo') & 
            (pd.to_datetime(df_manutencao['datafim']).dt.date < hoje)
        ]
        
        if not inconsistencias.empty:
            print(f"❌ Manutenções marcadas como 'Ativo' com data fim no passado! Quantidade: {len(inconsistencias)}")
        else:
            print("✅ Status das manutenções consistentes com as datas.")
    else:
        print("⚠️ Não foi possível verificar status da manutenção - colunas necessárias não encontradas")


# Verifica se os mecânicos estão vinculados corretamente às manutenções
# e se a especialidade do mecânico corresponde ao tipo de manutenção
def checarMecanicos(df_mm, df_mec, df_man):
    if all(col in df_mm.columns for col in ['id_mecanico', 'id_manutencao']) and \
       'id' in df_mec.columns and \
       all(col in df_man.columns for col in ['id', 'tipo']):
        
        print(f"\n Verificando mecânicos vinculados à manutenção...")

        # Mesclar as tabelas: manutencao_mecanico -> mecanico -> manutencao
        df = df_mm.merge(df_mec, left_on='id_mecanico', right_on='id', suffixes=('_mm','_mec')).merge(df_man, left_on='id_manutencao', right_on='id', suffixes=('','_man'))
        inconsistencias = df[df['tipo'] != df['especialidade']] # Para cada mecanico vinculado em uma manutencao, verifica se a especialidade é compativel
        if not inconsistencias.empty:
            print(f"❌ Mecânicos com especialização incorreta vinculados! Quantidade: {len(inconsistencias)}")
        else:
            print("✅ Mecânicos vinculados corretamente.")
    else:
        print("⚠️ Não foi possível verificar mecânicos - colunas necessárias não encontradas")


# Verifica se as placas dos veículos estão no formato correto e se são únicas
# Formato esperado: ABC-1D23 ou ABC1234
def checarPlacas(df):
    if 'placa' in df.columns:
        print(f"\n Verificando placas únicas e formato...")
        checarDuplicatas(df, ['placa'], 'veículo (placa)') # Verifica duplicatas
        
        # Verifica formato (exemplo: ABC-1D23)
        placas_invalidas = df[~df['placa'].str.match(r'^[A-Z]{3}-\d[A-Z]\d{2}$|^[A-Z]{3}\d{4}$', na=False)] # Placas fora do formato são adicionadas
        if not placas_invalidas.empty:
            print(f"❌ Placas com formato inválido! Quantidade: {len(placas_invalidas)}")
        else:
            print("✅ Formato das placas válido.")
    else:
        print("⚠️ Não foi possível verificar placas - coluna 'placa' não encontrada")


# Verifica se as CNHs dos clientes estão no formato correto e se são únicas
# Formato esperado: 12345678900
def checarCNH(df):
    if 'cnh' in df.columns:
        print(f"\n Verificando CNH únicas e formato...")
        checarDuplicatas(df, ['cnh'], 'cliente (CNH)') # Verifica duplicatas

        # Verifica formato (exemplo: 01234567890)
        cnh_invalidas = df[~df['cnh'].str.match(r'^\d{11}$', na=False)] # CNHs fora do formato são adicionadas
        if not cnh_invalidas.empty:
            print(f"❌ Placas com formato inválido! Quantidade: {len(cnh_invalidas)}")
        else:
            print("✅ Formato das placas válido.")
    else:
        print("⚠️ Não foi possível verificar CNH - coluna 'cnh' não encontrada")


# Verifica se os emails dos clientes estão no formato correto e se são únicos
# Formato esperado: joao@gmail.com
def checarEmail(df):
    if 'email' in df.columns:
        print(f"\n Verificando Email únicos e formato...")
        checarDuplicatas(df, ['email'], 'cliente (Email)') # Verifica duplicatas
        
        # Verifica formato de email
        emails_invalidos = df[~df['email'].str.contains(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', na=False)] # emails fora do formato são adicionados
        if not emails_invalidos.empty:
            print(f"❌ Emails com formato inválido! Quantidade: {len(emails_invalidos)}")
        else:
            print("✅ Formato dos emails válido.")
    else:
        print("⚠️ Não foi possível verificar emails - coluna 'email' não encontrada")


# Verifica se a diaria dos aluguéis + seguro está consistente com o cálculo esperado
#(valor do carro por dia * número de dias) + valor fixo do seguro.
def checarDiariaSeguro(df_aluguel, df_veiculo, df_seguro):
    
    #Para veículos 'Básico', usa diária = 80 e seguro = valorbasico;
    #Para veículos 'Avançado', usa diária = 140 e seguro = valoravancado.

    # Colunas de necessárias para verificação
    required_alug = ['id', 'idveiculo', 'idseguro', 'datainicio', 'datafim', 'valor']
    required_veic = ['id', 'tier']
    required_segu = ['id', 'valorbasico', 'valoravancado']
    
    if all(col in df_aluguel.columns for col in required_alug) and \
       all(col in df_veiculo.columns for col in required_veic) and \
       all(col in df_seguro.columns for col in required_segu):
        
        print(f"\n Verificando valores parciais de aluguel (valor da locação + seguro)...")
        
        # Mesclar as tabelas: aluguel -> veiculo -> seguro
        df_merged = df_aluguel.merge(df_veiculo[['id', 'tier']], left_on='idveiculo', right_on='id', suffixes=('', '_veiculo'))
        df_merged = df_merged.merge(df_seguro[['id', 'valorbasico', 'valoravancado']], left_on='idseguro', right_on='id', suffixes=('', '_seguro'))
        
        # Converter datas para datetime
        df_merged['datainicio'] = pd.to_datetime(df_merged['datainicio']).dt.date
        df_merged['datafim'] = pd.to_datetime(df_merged['datafim']).dt.date
        
        # Função para calcular o valor esperado
        def calc_valor_esperado(row):
            dias = (row['datafim'] - row['datainicio']).days # Dias de loação
            # Para tier básico
            if row['tier'] == 'Básico':
                diaria = 80
                seguro_valor = row['valorbasico']
            # Para tier avançado
            else: 
                diaria = 140
                seguro_valor = row['valoravancado']

            return diaria * dias + seguro_valor
        
        df_merged['valor_esperado'] = df_merged.apply(calc_valor_esperado, axis=1) # Nova coluna com o valor esperado para cada aluguel
        
        # Identifica inconsistências
        df_merged['dif'] = abs(df_merged['valor'] - df_merged['valor_esperado']) # Nova coluna com a diferença entre o valor esperado e o valor salvo
        inconsistencias = df_merged[df_merged['dif'] > 0.01]
        
        if not inconsistencias.empty:
            print(f"❌ Valores parciais de aluguel inconsistentes! Quantidade: {len(inconsistencias)}")
            print(inconsistencias[['id', 'valor', 'valor_esperado', 'tier', 'datainicio', 'datafim']])
        else:
            print("✅ Valores parciais de aluguel consistentes com o cálculo esperado.")
    else:
        print("⚠️ Não foi possível verificar valores de aluguel - colunas necessárias não encontradas")


# Verifica se o status dos veículos está consistente de acordo com as atividades
def checarStatusVeiculo(df_veiculo, df_aluguel, df_manutencao):

      #- Veículos com aluguel ativo (ou seja, onde datafim > hoje) devem ter status 'Alugado'
      #- Veículos em manutenção ativa (ou seja, onde datafim > hoje) devem ter status 'Em Manutenção'
      #- Veículos sem atividades ativas devem ter status 'Disponível'
    
    hoje = datetime.now().date() # Data Atual

    # Verifica se as colunas necessárias existem:
    if all(col in df_veiculo.columns for col in ['id', 'statusdisponibilidade']) and \
       'idveiculo' in df_aluguel.columns and \
       'idveiculo' in df_manutencao.columns:
        print("\nVerificando status de veículos...")
        
        # Considera um aluguel ativo se a datafim for maior que hoje
        veiculos_alugados = df_aluguel[pd.to_datetime(df_aluguel['datafim']).dt.date > hoje]['idveiculo'].unique()
        # Adiciona veiculos status inconsistentes (!= Alugado)
        inconsistencias_aluguel = df_veiculo[
            (df_veiculo['id'].isin(veiculos_alugados)) & 
            (df_veiculo['statusdisponibilidade'] != 'Alugado')
        ]
        
        # Considera uma manutenção ativa se a datafim for maior que hoje
        veiculos_manutencao = df_manutencao[pd.to_datetime(df_manutencao['datafim']).dt.date > hoje]['idveiculo'].unique()
        # Adiciona veiculos status inconsistentes (!= Manutenção)
        inconsistencias_manutencao = df_veiculo[
            (df_veiculo['id'].isin(veiculos_manutencao)) & 
            (df_veiculo['statusdisponibilidade'] != 'Manutenção')
        ]
        
        # Veículos que não estão em nenhuma atividade ativa devem estar Disponíveis
        veiculos_ocupados = set(veiculos_alugados).union(set(veiculos_manutencao))
        # Adiciona veiculos status inconsistentes (!= Disponível)
        inconsistencias_disponivel = df_veiculo[
            (~df_veiculo['id'].isin(veiculos_ocupados)) & 
            (df_veiculo['statusdisponibilidade'] != 'Disponível')
        ]
        
        # Concatena todas as inconsistências
        inconsistencias = pd.concat([inconsistencias_aluguel, inconsistencias_manutencao, inconsistencias_disponivel])
        
        if not inconsistencias.empty:
            print(f"❌ Status de veículo inconsistente! Quantidade: {len(inconsistencias)}")
            print(inconsistencias[['id', 'placa', 'modelo', 'statusdisponibilidade']])
        else:
            print("✅ Status dos veículos consistentes.")
    else:
        print("⚠️ Não foi possível verificar status de veículos - colunas necessárias não encontradas")

        
# ---------------------
# Execução da Auditoria
# ---------------------
print("\n----------------------------")
print("🔍 Iniciando Auditoria Geral")
print("----------------------------")

# Carregar tabelas
tabelas = ["veiculo", "seguro", "cliente", "aluguel", "manutencao", 
           "servico", "aluguel_servico", "mecanico", "manutencao_mecanico"]

dfs = {}
for tabela in tabelas:
    try:
        dfs[tabela] = carregarTabelas(tabela)
    except Exception as e:
        print(f"⚠️ Erro ao carregar tabela {tabela}: {str(e)}")

print("\n✅ Tabelas carregadas!")

# Rodar verificações apenas para tabelas que foram carregadas com sucesso
if 'aluguel' in dfs:
    checarNulos(dfs['aluguel'], ['datainicio','datafim','valor','idcliente','idveiculo','idseguro'], 'aluguel')
    checarDatas(dfs['aluguel'], 'aluguel')
    checarStatusAluguel(dfs['aluguel'])
    
if 'manutencao' in dfs:
    checarNulos(dfs['manutencao'], ['datainicio','datafim','idveiculo','custo'], 'manutenção')
    checarDatas(dfs['manutencao'], 'manutenção')
    checarStatusManutencao(dfs['manutencao'])

if all(tabela in dfs for tabela in ['manutencao_mecanico', 'mecanico', 'manutencao']):
    checarMecanicos(dfs['manutencao_mecanico'], dfs['mecanico'], dfs['manutencao'])

if 'veiculo' in dfs:
    checarPlacas(dfs['veiculo'])
    
if 'cliente' in dfs:
    checarCNH(dfs['cliente'])
    checarEmail(dfs['cliente'])

if all(tabela in dfs for tabela in ['aluguel', 'veiculo', 'seguro']):
    checarDiariaSeguro(dfs['aluguel'], dfs['veiculo'], dfs['seguro'])

if all(tabela in dfs for tabela in ['veiculo', 'aluguel', 'manutencao']):
    checarStatusVeiculo(dfs['veiculo'], dfs['aluguel'], dfs['manutencao'])

print("\n✅ Auditoria finalizada.")
