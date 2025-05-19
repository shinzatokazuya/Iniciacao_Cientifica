import pandas as pd
import sqlite3
import os

# 1. Dicionário com nomes das tabelas e arquivos CSV correspondentes
tabelas_arquivos = {
    'jogoss': 'csv_data/campeonato_brasileiro_full.csv',
    'estatisticass': 'csv_data/campeonato_brasileiro_estatisticas.csv',
    'golss': 'csv_data/campeonato_brasileiro_gols.csv',
    'cartoess': 'csv_data/campeonato_brasileiro_cartoes.csv'
}

# 2. Conectar ao banco
con = sqlite3.connect('jogos.db')
cur = con.cursor()

# 3. Loop para processar cada arquivo
for nome_tabela, caminho_csv in tabelas_arquivos.items():
    if os.path.exists(caminho_csv):
        print(f"Importando: {caminho_csv} → Tabela: {nome_tabela}")

        # Ler CSV
        df = pd.read_csv(caminho_csv)

        # (Opcional) Forçar tipos ou tratar dados aqui se quiser   

        # Remover a tabela se já existir
        cur.execute(f'DROP TABLE IF EXISTS {nome_tabela};')

        # Criar a tabela com estrutura padrão do pandas (poderia ser manual se quiser mais controle)
        df.to_sql(nome_tabela, con, if_exists='replace', index=False)
    else:
        print(f"Arquivo não encontrado: {caminho_csv}")

# 4. Finalizar
con.commit()
con.close()