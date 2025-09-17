import csv
import sqlite3

# Conectar ao banco
con = sqlite3.connect("br_1971.db")
cur = con.cursor()

# Criar a tabela (ajuste os campos ao seu CSV)
cur.execute("""
CREATE TABLE partidas (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    hora TEXT,
    campeonato_id,
    fase TEXT,
    mandante_id INTEGER,
    mandante_placar INTEGER,
    visitante_placar INTEGER,
    visitante_id INTEGER,
    mandante_penalti INTEGER,
    visitante_penalti INTEGER,
    prorrogacao INTEGER DEFAULT 0,
    FOREIGN KEY (mandante_id) REFERENCES clubes(ID),
    FOREIGN KEY (visitante_id) REFERENCES clubes(ID),
    FOREIGN KEY (campeonato_id) REFERENCES campeonatos(ID)
)
""")

# Ler CSV e inserir
with open("csv_br_1971/partidasTeste.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=";")
    next(reader)  # pula cabeçalho
    for row in reader:
        row = row[1:]
        cur.execute("INSERT INTO partidas (data, hora, campeonato_id, fase, mandante_id, mandante_placar, visitante_placar, visitante_id, mandante_penalti, visitante_penalti, prorrogacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)

con.commit()
con.close()
