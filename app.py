# app.py
from flask import Flask, render_template, jsonify, request, redirect
from cs50 import SQL

app = Flask(__name__)

db = SQL("sqlite:///Dados_brasileirao_2003_2023.db")

DATAS = ['2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023']

@app.route("/")
def index():
    rankings = db.execute("""
                            WITH placares AS (
                                SELECT
                                    mandante AS clube,
                                    SUM(CASE WHEN mandante_Placar > visitante_Placar THEN 3 WHEN mandante_Placar = visitante_Placar THEN 1 ELSE 0 END) AS pontos,
                                    SUM(CASE WHEN mandante_Placar > visitante_Placar THEN 1 ELSE 0 END) AS vitorias,
                                    SUM(CASE WHEN mandante_Placar = visitante_Placar THEN 1 ELSE 0 END) AS empates,
                                    SUM(CASE WHEN mandante_Placar < visitante_Placar THEN 1 ELSE 0 END) AS derrotas,
                                    SUM(mandante_Placar) AS gm,
                                    SUM(visitante_Placar) AS gc
                                FROM Full
                                GROUP BY mandante
                                UNION ALL
                                SELECT
                                    visitante AS clube,
                                    SUM(CASE WHEN visitante_Placar > mandante_Placar THEN 3 WHEN visitante_Placar = mandante_Placar THEN 1 ELSE 0 END) AS pontos,
                                    SUM(CASE WHEN visitante_Placar > mandante_Placar THEN 1 ELSE 0 END) AS vitorias,
                                    SUM(CASE WHEN visitante_Placar = mandante_Placar THEN 1 ELSE 0 END) AS empates,
                                    SUM(CASE WHEN visitante_Placar < mandante_Placar THEN 1 ELSE 0 END) AS derrotas,
                                    SUM(visitante_Placar) AS gm,
                                    SUM(mandante_Placar) AS gc
                                FROM Full
                                GROUP BY visitante
                                ),
                                total_jogos_clube AS (
                                    SELECT
                                        clube,
                                        COUNT(*) AS total_jogos
                                    FROM (
                                        SELECT mandante AS clube FROM Full
                                        UNION ALL
                                        SELECT visitante AS clube FROM Full
                                    ) AS todos_os_clubes
                                    GROUP BY clube
                                )
                                SELECT
                                p.clube,
                                t.total_jogos,
                                SUM(p.pontos) AS pontos,
                                SUM(p.vitorias) AS vitorias,
                                SUM(p.empates) AS empates,
                                SUM(p.derrotas) AS derrotas,
                                SUM(p.gm) AS gm,
                                SUM(p.gc) AS gc,
                                (SUM(p.gm) - SUM(p.gc)) AS sg
                                FROM placares p
                                JOIN total_jogos_clube t ON p.clube = t.clube
                                GROUP BY p.clube
                                ORDER BY pontos DESC, sg DESC, gm DESC;
                          """)
    return render_template("index.html", datas=DATAS, rankings=rankings)

@app.route("/search")
def search():
    q = request.args.get('q')
    ano = request.args.get('data')
    if q and ano:
        jogos = db.execute("SELECT * FROM Full WHERE (mandante LIKE ? OR visitante LIKE ?) AND SUBSTR(data, 7 , 4) LIKE ? ORDER BY rodada", q, q, ano)
        classificacoes = db.execute("""
                                    WITH placares_anuais AS (
                                        SELECT
                                            SUBSTR(data, 7, 4) AS ano,
                                            mandante AS clube,
                                            SUM(CASE WHEN mandante_Placar > visitante_Placar THEN 3 WHEN mandante_Placar = visitante_Placar THEN 1 ELSE 0 END) AS pontos,
                                            SUM(CASE WHEN mandante_Placar > visitante_Placar THEN 1 ELSE 0 END) AS vitorias,
                                            SUM(CASE WHEN mandante_Placar = visitante_Placar THEN 1 ELSE 0 END) AS empates,
                                            SUM(CASE WHEN mandante_Placar < visitante_Placar THEN 1 ELSE 0 END) AS derrotas,
                                            SUM(mandante_Placar) AS gm,
                                            SUM(visitante_Placar) AS gc
                                        FROM Full
                                        WHERE SUBSTR(data, 7, 4) = ?
                                        GROUP BY SUBSTR(data, 7, 4), mandante
                                        UNION ALL
                                        SELECT
                                            SUBSTR(data, 7, 4) AS ano,
                                            visitante AS clube,
                                            SUM(CASE WHEN visitante_Placar > mandante_Placar THEN 3 WHEN visitante_Placar = mandante_Placar THEN 1 ELSE 0 END) AS pontos,
                                            SUM(CASE WHEN visitante_Placar > mandante_Placar THEN 1 ELSE 0 END) AS vitorias,
                                            SUM(CASE WHEN visitante_Placar = mandante_Placar THEN 1 ELSE 0 END) AS empates,
                                            SUM(CASE WHEN visitante_Placar < mandante_Placar THEN 1 ELSE 0 END) AS derrotas,
                                            SUM(visitante_Placar) AS gm,
                                            SUM(mandante_Placar) AS gc
                                        FROM Full
                                        WHERE SUBSTR(data, 7, 4) = ?
                                        GROUP BY SUBSTR(data, 7, 4), visitante
                                        ),
                                        total_jogos_clube AS (
                                            SELECT
                                                clube,
                                                COUNT(*) AS total_jogos
                                            FROM (
                                                SELECT mandante AS clube FROM Full
                                                WHERE SUBSTR(data, 7, 4) = ?
                                                UNION ALL
                                                SELECT visitante AS clube FROM Full
                                                WHERE SUBSTR(data, 7, 4) = ?
                                            ) AS todos_os_clubes
                                            GROUP BY clube
                                        )
                                        SELECT
                                        p.ano,
                                        p.clube,
                                        t.total_jogos,
                                        SUM(p.pontos) AS pontos,
                                        SUM(p.vitorias) AS vitorias,
                                        SUM(p.empates) AS empates,
                                        SUM(p.derrotas) AS derrotas,
                                        SUM(p.gm) AS gm,
                                        SUM(p.gc) AS gc,
                                        (SUM(p.gm) - SUM(p.gc)) AS sg
                                        FROM placares_anuais p
                                        JOIN total_jogos_clube t ON p.clube = t.clube
                                        GROUP BY p.ano, p.clube
                                        ORDER BY p.ano DESC, pontos DESC, sg DESC, gm DESC;
                                   """, ano, ano, ano, ano)
        return render_template("search.html", jogos=jogos, classificacoes=classificacoes)
    return redirect("/")

@app.route("/clube/<nome>")
def clube(nome):
    jogos = db.execute("SELECT * FROM Full WHERE mandante = ? OR visitante = ? ORDER BY SUBSTR(data, 7, 4)", nome, nome)
    return render_template("clube.html", clube=nome, jogos=jogos)

@app.route("/estatisticas/<int:partida_id>")
def estatisticas(partida_id):
    estat = db.execute("SELECT * FROM Estatisticas WHERE partida_id = ?", partida_id)
    gols = db.execute("SELECT * FROM Gols WHERE partida_id = ?", partida_id)
    cartoes = db.execute("SELECT * FROM Cartoes WHERE partida_id = ?", partida_id)
    return render_template("estatisticas.html", estatisticas=estat, gols=gols, cartoes=cartoes)
