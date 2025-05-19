import sqlite3
import pandas as pd

df = pd.read_csv('campeonato_brasileiro_cartoes.csv', usecols=['partida_id'])

con = sqlite3.connect('campeonato_brasileiro_cartoes.db')
cur = con.cursor()

# Criar a tabela manualmente com base nas colunas do DataFrame
colunas = df.columns
sql_create = f"CREATE TABLE IF NOT EXISTS partida_id ({'partida_id'} INT PRIMARY KEY)"
cur.execute(sql_create)

# Inserir os dados linha por linha
for valor in df['partida_id']:
    cur.execute(f"INSERT INTO partida_id ({'partida_id'}) VALUES (?)", (valor,))

con.commit()
con.close()

