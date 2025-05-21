import pandas as pd
import pyodbc
import os

# 1. Dicionário com nomes das tabelas e arquivos CSV correspondentes
tabelas_arquivos = {
    'Full': 'campeonato_brasileiro_full.csv',
    'Estatisticas': 'campeonato_brasileiro_estatisticas.csv',
    'Gols': 'campeonato_brasileiro_gols.csv',
    'Cartoes': 'campeonato_brasileiro_cartoes.csv'
}

# 2. Conectar ao banco de dados SQL Server
# Substitua as credenciais abaixo com as suas informações
server = 'seu_servidor'  # Exemplo: 'localhost' ou '192.168.1.100'
database = 'seu_banco_de_dados'  # Nome do banco de dados
username = 'seu_usuario'
password = 'sua_senha'

# Criando a string de conexão
conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
con = pyodbc.connect(conn_str)
cur = con.cursor()

# 3. Loop para processar cada arquivo
for nome_tabela, caminho_csv in tabelas_arquivos.items():
    if os.path.exists(caminho_csv):
        print(f"Importando: {caminho_csv} → Tabela: {nome_tabela}")

        # Ler CSV
        df = pd.read_csv(caminho_csv)

        # (Opcional) Forçar tipos ou tratar dados aqui se necessário

        # Remover a tabela se já existir
        cur.execute(f'DROP TABLE IF EXISTS {nome_tabela};')

        # Criar a tabela com estrutura padrão do pandas (usando o to_sql do pandas)
        # Importante: no SQL Server, o pandas usa o SQLAlchemy, que pode ser configurado para funcionar com o pyodbc.
        # O 'if_exists' pode ser 'replace' para sobrescrever ou 'fail' para lançar erro se a tabela existir.
        # Abaixo, usamos o método .to_sql() que integra pandas com SQL Server usando o pyodbc.

        # Usando SQLAlchemy para criar conexão
        from sqlalchemy import create_engine

        # Criando a string de conexão para SQLAlchemy (usando o driver do pyodbc)
        engine = create_engine(f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=SQL+Server")

        # Enviar os dados para o SQL Server
        df.to_sql(nome_tabela, engine, if_exists='replace', index=False)

    else:
        print(f"Arquivo não encontrado: {caminho_csv}")

# 4. Finalizar
con.commit()
con.close()