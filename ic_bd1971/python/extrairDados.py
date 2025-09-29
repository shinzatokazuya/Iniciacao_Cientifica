import sqlite3

# Conecta com banco de dados
con_antigo = sqlite3.connect("")
cur_antigo = con_antigo.cursor()

con_novo = sqlite3.connect("bd/dados_teste_1971.db")
cur_novo = con_novo.cursor()

# 1. Criar as tabelas no banco novo
cur_novo.executescript("""
    CREATE TABLE IF NOT EXISTS locais (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        cidade TEXT,
        UF TEXT,
        regiao TEXT,
        pais TEXT
    );

    CREATE TABLE IF NOT EXISTS clubes (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        clube TEXT,
        local_id INTEGER,
        FOREIGN KEY (local_id) REFERENCES locais(ID)
    );

    CREATE TABLE IF NOT EXISTS campeonatos (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        campeonato TEXT,
        pais TEXT,
        entidade TEXT
    );

    CREATE TABLE IF NOT EXISTS edicoes (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        campeonato_id INTEGER,
        ano INTEGER,
        FOREIGN KEY (campeonato_id) REFERENCES campeonatos(ID)
    );

    CREATE TABLE IF NOT EXISTS estadios (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        estadio TEXT,
        capacidade INTEGER,
        local_id INTEGER,
        FOREIGN KEY (local_id) REFERENCES locais(ID)
    );

    CREATE TABLE IF NOT EXISTS partidas (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        edicao_id INTEGER,
        estadio_id INTEGER,
        data TEXT,
        hora TEXT,
        fase TEXT,
        mandante_id INTEGER,
        visitante_id INTEGER,
        mandante_placar INTEGER,
        visitante_placar INTEGER,
        mandante_penalti INTEGER,
        visitante_penalti INTEGER,
        prorrogacao INTEGER DEFAULT 0,
        FOREIGN KEY (mandante_id) REFERENCES clubes(ID),
        FOREIGN KEY (visitante_id) REFERENCES clubes(ID),
        FOREIGN KEY (edicao_id) REFERENCES edicoes(ID),
        FOREIGN KEY (estadio_id) REFERENCES estadios(ID)
    );



    CREATE TABLE IF NOT EXISTS estatisticas_partida (
        partida_id INTEGER,
        clube_id INTEGER,
        chutes INTEGER,
        chutes_no_alvo INTEGER,
        posse_de_bola TEXT,
        passes INTEGER,
        precisao_passes TEXT,
        faltas INTEGER,
        cartao_amarelo INTEGER,
        cartao_vermelho INTEGER,
        impedimentos INTEGER,
        escanteios INTEGER,
        PRIMARY KEY (partida_id, clube_id),
        FOREIGN KEY (partida_id) REFERENCES partidas(ID),
        FOREIGN KEY (clube_id) REFERENCES clubes(ID)
    );


    CREATE TABLE IF NOT EXISTS jogadores (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        nascimento DATE,
        nacionalidade TEXT,
        clube_id INTEGER,
        FOREIGN KEY (clube_id) REFERENCES clubes(ID)
    );

    CREATE TABLE IF NOT EXISTS jogadores_em_partida (
        partida_id INTEGER,
        jogador_id INTEGER,
        titular BOOLEAN,
        minutos_jogados INTEGER,
        gols INTEGER,
        assistencias INTEGER,
        PRIMARY KEY (partida_id, jogador_id),
        FOREIGN KEY (partida_id) REFERENCES partidas(ID),
        FOREIGN KEY (jogador_id) REFERENCES jogadores(ID)
    );
""")

# 2. Lê os os dados do banco antigo
cur_antigo.execute("SELECT ID, clube, cidade, UF, regiao FROM clubes;")
clubes_antigos = cur_antigo.fetchall()

# 3. Cria locais únicos no banco novo
locais_map = {}
for _, _, cidade, uf, regiao in clubes_antigos:
    chave = (cidade, uf, regiao, "Brasil")
    if chave not in locais_map:
        cur_novo.execute("INSERT INTO locais (cidade, UF, regiao, pais) VALUES (?, ?, ?, ?)", chave)
        locais_map[chave] = cur_novo.lastrowid

# 4. Insere clubes no banco novo
for id_clube, clube, cidade, uf, regiao in clubes_antigos:
    local_id = locais_map[(cidade, uf, regiao, "Brasil")]
    cur_novo.execute("INSERT INTO clubes (ID, clube, local_id) VALUES (?, ?, ?)", (id_clube, clube, local_id))

# Salva e fecha
con_novo.commit()
con_antigo.close()
con_novo.close()


