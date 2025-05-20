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


def carregarTabelas(table):
    print(f"🔄 Carregando dados da tabela {table}...")
    data = supabase.table(table).select("*").execute().data
    return pd.DataFrame(data)

def checarNulos(df, colunas, nome=""):
    print(f"\n Verificando nulos na tabela {nome}...")
    for col in colunas:
        if col in df.columns:
            inconsistencias = df[df[col].isnull()]
            if not inconsistencias.empty:
                print(f"❌ Nulos em {col}: {len(inconsistencias)} inconsistências.")
            else:
                print(f"✅ {col} OK (sem nulos).")

def checarDuplicatas(df, colunas, nome):
    print(f"\n Verificando duplicatas em {nome}...")
    inconsistencias = df[df.duplicated(subset=colunas, keep=False)]
    if not inconsistencias.empty:
        print(f"❌ Duplicatas encontradas em {nome}: {len(inconsistencias)}")
    else:
        print(f"✅ {nome} sem duplicatas.")

def checarDatas(df, nome=""):
    if 'datainicio' in df.columns and 'datafim' in df.columns:
        inconsistencias = df[df['datainicio'] > df['datafim']]
        print(f"\n Verificando datas do {nome}...")
        if not inconsistencias.empty:
            print(f"❌ {nome} contém datas inválidas! Quantidade: {len(inconsistencias)}")
        else:
            print(f"✅ {nome} contém datas válidas.")
    else:
        print(f"⚠️ Não foi possível verificar datas em {nome} - colunas necessárias não encontradas")

def checarStatusAluguel(df_aluguel):
    if all(col in df_aluguel.columns for col in ['status', 'datainicio', 'datafim']):
        print(f"\n Verificando status do aluguel com datas...")
        
        # Aluguéis marcados como "Ativo" mas com datafim no passado
        hoje = datetime.now().date()
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

def checarStatusManutencao(df_manutencao):
    if all(col in df_manutencao.columns for col in ['status', 'datainicio', 'datafim']):
        print(f"\n Verificando status da manutenção com datas...")
        
        hoje = datetime.now().date()
        inconsistencias = df_manutencao[
            (df_manutencao['status'] == 'Em andamento') & 
            (pd.to_datetime(df_manutencao['datafim']).dt.date < hoje)
        ]
        
        if not inconsistencias.empty:
            print(f"❌ Manutenções marcadas como 'Em andamento' com data fim no passado! Quantidade: {len(inconsistencias)}")
        else:
            print("✅ Status das manutenções consistentes com as datas.")
    else:
        print("⚠️ Não foi possível verificar status da manutenção - colunas necessárias não encontradas")

def checarMecanicos(df_mm, df_mec, df_man):
    if all(col in df_mm.columns for col in ['id_mecanico', 'id_manutencao']) and \
       'id' in df_mec.columns and \
       all(col in df_man.columns for col in ['id', 'tipo']):
        print(f"\n Verificando mecânicos vinculados à manutenção...")
        df = df_mm.merge(df_mec, left_on='id_mecanico', right_on='id', suffixes=('_mm','_mec')).merge(df_man, left_on='id_manutencao', right_on='id', suffixes=('','_man'))
        inconsistencias = df[df['tipo'] != df['especialidade']]
        if not inconsistencias.empty:
            print(f"❌ Mecânicos com especialização incorreta vinculados! Quantidade: {len(inconsistencias)}")
        else:
            print("✅ Mecânicos vinculados corretamente.")
    else:
        print("⚠️ Não foi possível verificar mecânicos - colunas necessárias não encontradas")

def checarPlacas(df):
    if 'placa' in df.columns:
        print(f"\n Verificando placas únicas e formato...")
        # Verifica duplicatas
        checarDuplicatas(df, ['placa'], 'veículo (placa)')
        
        # Verifica formato (exemplo: ABC1D23)
        placas_invalidas = df[~df['placa'].str.match(r'^[A-Z]{3}-\d[A-Z]\d{2}$|^[A-Z]{3}\d{4}$', na=False)]
        if not placas_invalidas.empty:
            print(f"❌ Placas com formato inválido! Quantidade: {len(placas_invalidas)}")
        else:
            print("✅ Formato das placas válido.")
    else:
        print("⚠️ Não foi possível verificar placas - coluna 'placa' não encontrada")

def checarCNH(df):
    if 'cnh' in df.columns:
        print(f"\n Verificando CNH únicas...")
        checarDuplicatas(df, ['cnh'], 'cliente (CNH)')
    else:
        print("⚠️ Não foi possível verificar CNH - coluna 'cnh' não encontrada")

def checarEmail(df):
    if 'email' in df.columns:
        print(f"\n Verificando Email únicos e formato...")
        checarDuplicatas(df, ['email'], 'cliente (Email)')
        
        # Verifica formato de email
        emails_invalidos = df[~df['email'].str.contains(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', na=False)]
        if not emails_invalidos.empty:
            print(f"❌ Emails com formato inválido! Quantidade: {len(emails_invalidos)}")
        else:
            print("✅ Formato dos emails válido.")
    else:
        print("⚠️ Não foi possível verificar emails - coluna 'email' não encontrada")

def checarValorTotalAluguel(df_aluguel, df_veiculo, df_aluguel_servico, df_servico):
    if all(col in df_aluguel.columns for col in ['id', 'idveiculo', 'valortotal']) and \
       all(col in df_veiculo.columns for col in ['id', 'valorlocacao']) and \
       all(col in df_aluguel_servico.columns for col in ['idaluguel', 'idservico']) and \
       all(col in df_servico.columns for col in ['id', 'valor']):
        
        print(f"\n Verificando valores totais de aluguel...")
        
        # Calcula valor esperado (valor locação + serviços adicionais)
        df_servicos_contratados = df_aluguel_servico.merge(df_servico, left_on='idservico', right_on='id')
        valor_servicos = df_servicos_contratados.groupby('idaluguel')['valor'].sum().reset_index()
        
        df_completo = df_aluguel.merge(df_veiculo, left_on='idveiculo', right_on='id') \
                               .merge(valor_servicos, left_on='id', right_on='idaluguel', how='left')
        
        df_completo['valor_servicos'] = df_completo['valor'].fillna(0)
        df_completo['valor_esperado'] = df_completo['valorlocacao'] + df_completo['valor_servicos']
        
        inconsistencias = df_completo[abs(df_completo['valortotal'] - df_completo['valor_esperado']) > 0.01]
        
        if not inconsistencias.empty:
            print(f"❌ Valores totais de aluguel inconsistentes! Quantidade: {len(inconsistencias)}")
        else:
            print("✅ Valores de aluguel consistentes com veículo e serviços.")
    else:
        print("⚠️ Não foi possível verificar valores de aluguel - colunas necessárias não encontradas")

def checarSeguroVeiculo(df_aluguel, df_veiculo, df_seguro):
    """
    Verifica se o valor total dos aluguéis está consistente com o cálculo esperado,
    ou seja: (valor do carro por dia * número de dias) + valor fixo do seguro.
    
    Para veículos 'Básico', usa diária = 80 e seguro = valorbasico;
    Para veículos 'Avançado', usa diária = 140 e seguro = valoravancado.
    """
    required_alug = ['id', 'idveiculo', 'idseguro', 'datainicio', 'datafim', 'valor']
    required_veic = ['id', 'tier']
    required_segu = ['id', 'valorbasico', 'valoravancado']
    
    if all(col in df_aluguel.columns for col in required_alug) and \
       all(col in df_veiculo.columns for col in required_veic) and \
       all(col in df_seguro.columns for col in required_segu):
        
        print(f"\n Verificando valores totais de aluguel (valor da locação + seguro)...")
        
        # Mesclar as tabelas: aluguel -> veiculo -> seguro
        df_merged = df_aluguel.merge(df_veiculo[['id', 'tier']], left_on='idveiculo', right_on='id', suffixes=('', '_veiculo'))
        df_merged = df_merged.merge(df_seguro[['id', 'valorbasico', 'valoravancado']], left_on='idseguro', right_on='id', suffixes=('', '_seguro'))
        
        # Converter datas para datetime caso necessário
        df_merged['datainicio'] = pd.to_datetime(df_merged['datainicio']).dt.date
        df_merged['datafim'] = pd.to_datetime(df_merged['datafim']).dt.date
        
        # Função para calcular o valor esperado
        def calc_valor_esperado(row):
            dias = (row['datafim'] - row['datainicio']).days
            if row['tier'] == 'Básico':
                diaria = 80
                seguro_valor = row['valorbasico']
            else:
                diaria = 140
                seguro_valor = row['valoravancado']
            return diaria * dias + seguro_valor
        
        df_merged['valor_esperado'] = df_merged.apply(calc_valor_esperado, axis=1)
        
        # Identifica inconsistências
        df_merged['dif'] = abs(df_merged['valor'] - df_merged['valor_esperado'])
        inconsistencias = df_merged[df_merged['dif'] > 0.01]
        
        if not inconsistencias.empty:
            print(f"❌ Valores totais de aluguel inconsistentes! Quantidade: {len(inconsistencias)}")
            print(inconsistencias[['id', 'valor', 'valor_esperado', 'tier', 'datainicio', 'datafim']])
        else:
            print("✅ Valores totais de aluguel consistentes com o cálculo esperado.")
    else:
        print("⚠️ Não foi possível verificar valores de aluguel - colunas necessárias não encontradas")

def checarStatusVeiculo(df_veiculo, df_aluguel, df_manutencao):
    if all(col in df_veiculo.columns for col in ['id', 'status']) and \
       'idveiculo' in df_aluguel.columns and \
       'idveiculo' in df_manutencao.columns:
        print(f"\n Verificando status de veículos...")
        
        # Veículos alugados
        veiculos_alugados = df_aluguel[df_aluguel['datafim'].isnull()]['idveiculo'].unique()
        inconsistencias_aluguel = df_veiculo[df_veiculo['id'].isin(veiculos_alugados) & (df_veiculo['status'] != 'Alugado')]
        
        # Veículos em manutenção
        veiculos_manutencao = df_manutencao[df_manutencao['datafim'].isnull()]['idveiculo'].unique()
        inconsistencias_manutencao = df_veiculo[df_veiculo['id'].isin(veiculos_manutencao) & (df_veiculo['status'] != 'Em Manutenção')]
        
        # Veículos que deveriam estar disponíveis
        veiculos_ocupados = set(veiculos_alugados).union(set(veiculos_manutencao))
        inconsistencias_disponivel = df_veiculo[
            (~df_veiculo['id'].isin(veiculos_ocupados)) & 
            (df_veiculo['status'] != 'Disponível')
        ]
        
        inconsistencias = pd.concat([inconsistencias_aluguel, inconsistencias_manutencao, inconsistencias_disponivel])
        
        if not inconsistencias.empty:
            print(f"❌ Status de veículo inconsistente! Quantidade: {len(inconsistencias)}")
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
    checarNulos(dfs['aluguel'], ['datainicio','datafim','valortotal','idcliente','idveiculo','idseguro'], 'aluguel')
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

if all(tabela in dfs for tabela in ['aluguel', 'veiculo', 'aluguel_servico', 'servico']):
    checarValorTotalAluguel(dfs['aluguel'], dfs['veiculo'], dfs['aluguel_servico'], dfs['servico'])

if all(tabela in dfs for tabela in ['aluguel', 'veiculo', 'seguro']):
    checarSeguroVeiculo(dfs['aluguel'], dfs['veiculo'], dfs['seguro'])

if all(tabela in dfs for tabela in ['veiculo', 'aluguel', 'manutencao']):
    checarStatusVeiculo(dfs['veiculo'], dfs['aluguel'], dfs['manutencao'])

print("\n✅ Auditoria finalizada.")