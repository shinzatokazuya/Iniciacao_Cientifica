import sqlite3
from datetime import datetime

# Conecta com banco de dados
con_antigo = sqlite3.connect("../backup_br_1971.db")
cur_antigo = con_antigo.cursor()

con_novo = sqlite3.connect("bd/dados_teste_1971.db")
cur_novo = con_novo.cursor()

# 5. Insere as edições
cur_antigo.execute("SELECT ID, campeonato_id, data FROM partidas;")
partidas_antigas = cur_antigo.fetchall()

edicoes_map = {}
for _, campeonato_id, data in partidas_antigas:
    ano = int(data.split("/")[-1]) # Pega o ano (ex.: "31/07/1971" -> 1971)
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

    cur_novo.execute("""
        INSERT INTO partidas (
            ID, edicao_id, estadio_id, data, hora, fase,
            mandante_id, visitante_id,
            mandante_placar, visitante_placar,
            mandante_penalti, visitante_penalti, prorrogacao
        )
        VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_partida, edicao_id, data, hora, fase,
        mandante_id, visitante_id,
        mandante_placar, visitante_placar,
        mandante_penalti, visitante_penalti, prorrogacao
    ))

con_novo.commit()
con_antigo.close()
con_novo.close()
