# app.py
import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

# caminhos dos bancos
DB_1971 = "..ic_bd1971/bd/dados_teste_1971.db"
DB_2003 = "..ic_bd2003/bd/Dados_brasileirao_2003_2023.db"

def get_partidas_1971(ano):
    con = sqlite3.connect(DB_1971)
    cur = con.cursor()
    cur.execute("""
        SELECT p.ID, p.data, p.hora, c1.clube, c2.clube, p.mandante_placar, p.visitante_placar
        FROM partidas p
        JOIN clubes c1 ON p.mandante_id = c1.ID
        JOIN clubes c2 ON p.visitante_id = c2.ID
        JOIN edicoes e ON p.edicao_id = e.ID
        WHERE e.ano = ?
        ORDER BY p.data, p.hora
    """, (ano,))
    rows = cur.fetchall()
    con.close()
    return rows

def get_partidas_2003(ano):
    con = sqlite3.connect(DB_2003)
    cur = con.cursor()
    cur.execute("""
        SELECT ID, data, hora, mandante, visitante, mandante_Placar, visitante_Placar
        FROM Full
        WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ?
        ORDER BY data, hora
    """, (ano,))
    rows = cur.fetchall()
    con.close()
    return rows

@app.route("/partidas/<int:ano>")
def partidas(ano):
    partidas_1971 = get_partidas(DB_1971, ano)
    partidas_2003 = get_partidas(DB_2003, ano)

    return render_template("partidas.html", ano=ano,
                           partidas_1971=partidas_1971,
                           partidas_2003=partidas_2003)

