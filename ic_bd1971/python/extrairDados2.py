import sqlite3
from datetime import datetime

# Conecta com banco de dados
con_antigo = sqlite3.connect("../ic_bd2003/bd/Dados_brasileirao_2003_2023.db")
cur_antigo = con_antigo.cursor()

con_novo = sqlite3.connect("bd/dados_teste_1971.db")
cur_novo = con_novo.cursor()

# 5. Insere as edições
cur_antigo.execute("SELECT ID, campeonato_id, data FROM partidas;")
partidas_antigas = cur_antigo.fetchall()

edicoes_map = {}
for _, campeonato_id, data in partidas_antigas:
    ano = int(data[6:])
    chave = (campeonato_id, ano)
    if chave not in edicoes_map:
        cur_novo.execute("""
            INSERT INTO edicoes (campeonato_id, ano)
            VALUES (?, ?)
        """, (campeonato_id, ano))
        edicoes_map[chave] = cur_novo.lastrowid


# 6. inserir partidas
cur_antigo.execute("""
    SELECT ID, data, hora, campeonato_id, fase, mandante_id,
    mandante_placar, visitante_placar, visitante_id, mandante_penalti, visitante_penalti, prorrogacao
    FROM partidas;
""")

for row in cur_antigo.fetchall():
    (id_partida, data, hora, campeonato_id, fase, mandante_id,
     mandante_placar, visitante_placar, visitante_id,
     mandante_penalti, visitante_penalti, prorrogacao) = row

    ano = int(data[6:])
    edicao_id = edicoes_map[(campeonato_id, ano)]

    # Junta data e hora em um datetime único
    if hora:
        data_hora = f"{data} {hora}"
    else:
        data_hora = data

    cur_novo.execute("""
        INSERT INTO partidas (
            ID, edicao_id, estadio_id, data_hora, fase,
            mandante_id, visitante_id,
            mandante_placar, visitante_placar,
            mandante_penalti, visitante_penalti, prorrogacao
        )
        VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_partida, edicao_id, data_hora, fase,
        mandante_id, visitante_id,
        mandante_placar, visitante_placar,
        mandante_penalti, visitante_penalti, prorrogacao
    ))

con_novo.commit()
con_antigo.close()
con_novo.close()
