import sqlite3

# Conecta com banco de dados
con_antigo = sqlite3.connect("../ic_bd2003/bd/Dados_brasileirao_2003_2023.db")
cur_antigo = con_antigo.cursor()

con_novo = sqlite3.connect("bd/dados_teste_1971.db")
cur_novo = con_novo.cursor()

# 1. Migrar estádios (arena -> estadios)
cur_antigo.execute("SELECT DISTINCT arena FROM Full WHERE arena IS NOT NULL")
arenas = cur_antigo.fetchall()

for (arena,) in arenas:
    cur_novo.execute("INSERT INTO estadios (estadio) VALUES (?)", (arena,))

con_novo.commit()

# 2. Migrar estatisticas (Estatisticas -> estatisticas_partida)
cur_antigo.execute("""
    SELECT e.partida_id, f.data, e.rodada, e.clube, e.chutes, e.chutes_no_alvo,
           e.posse_de_bola, e.passes, e.precisao_passes, e.faltas,
           e.cartao_amarelo, e.cartao_vermelho, e.impedimentos, e.escanteios
    FROM Estatisticas e
    JOIN Full f ON e.partida_id = f.ID
""")
estatisticas = cur_antigo.fetchall()

for row in estatisticas:
    _, data_antiga, clube_nome, chutes, chutes_no_alvo, posse, passes, precisao, faltas, amarelo, vermelho, imped, escanteios = row

    # Pega pela correspondecia de data e nome do clube no banco novo
    cur_novo.execute("""
        SELECT p.id, c1.clube, c2.clube
        FROM partidas p
        JOIN clubes c1 ON p.mandante_id = c1.id
        JOIN clubes c2 ON p.visitante_id = c2.id
        WHERE DATE(p.data_hora) = ?
    """, (data_antiga,))
    resultado = cur_novo.fetchone()
    if resultado is None:
        print(f"Nenhuma partida encontrada na data: {data_antiga}.")
        continue
    partida_id = None
    clube_id = None

    for pid, mandante, visitante in resultado:
        if (clube_nome in (mandante, visitante)):
            partida_id = pid
            # Pega o ID do clube
            cur_novo.execute("SELECT ID from clubes WHERE clube = ?", (clube_nome,))
            clube_id = cur_novo.fetchone()[0]
            break

        if partida_id is None:
            print(f"Clube {clube_nome} não encontrado na data {data_antiga}.")
            continue

    # Insere nas estatisticas normalizadas
    cur_novo.execute("""
        INSERT OR IGNORE INTO estatisticas_partida
        (partida_id, clube_id, chutes, chutes_no_alvo, posse_de_bola, passes,
         precisao_passes, faltas, cartao_amarelo, cartao_vermelho, impedimentos, escanteios)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (partida_id, clube_id, chutes, chutes_no_alvo, posse, passes,
          precisao, faltas, amarelo, vermelho, imped, escanteios))

con_novo.commit()
con_antigo.close()
con_novo.close()
