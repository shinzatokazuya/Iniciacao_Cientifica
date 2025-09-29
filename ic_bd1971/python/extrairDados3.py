import sqlite3

# Conecta com banco de dados
con_antigo = sqlite3.connect("/workspaces/Iniciacao_Cientifica/Dados_brasileirao_2003_2023")
cur_antigo = con_antigo.cursor()

con_novo = sqlite3.connect("/workspaces/Iniciacao_Cientifica/ic_bd1971/bd/dados_teste_1971.db")
cur_novo = con_novo.cursor()

# 1. Migrar estádios (arena -> estadios)
cur_antigo.execute("SELECT DISTINCT arena FROM Full WHERE arena IS NOT NULL")
arenas = cur_antigo.fetchall()

for (arena,) in arenas:
    cur_novo.execute("INSERT INTO estadios (estadio) VALUES (?)", (arena,))

con_novo.commit()

# 2. Migrar estatisticas (Estatisticas -> estatisticas_partida)
cur_antigo.execute("""
    SELECT e.partida_id, e.rodada, e.clube, e.chutes, e.chute_no_alvo,
           e.posse_de_bola, e.passes, e.precisao_passes, e.faltas,
           e.cartao_amarelo, e.cartao_vermelho, e.impedimentos, e.escanteios
    FROM Estatisticas e
""")
estatisticas = cur_antigo.fetchall()

for row in estatisticas:
    partida_id, rodada, clube_nome, chutes, chutes_no_alvo, posse, passes, precisao, faltas, amarelo, vermelho, imped, escanteios = row

    # Pega ID do clube no banco novo
    cur_novo.execute("SELECT ID FROM clubes WHERE clube = ?", (clube_nome,))
    resultado = cur_novo.fetchone()
    if resultado is None:
        print(f"Clube não encontrado: {clube_nome}")
        continue
    clube_id = resultado[0]

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
