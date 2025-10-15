# app.py
import functools
from flask import Flask, render_template, jsonify, request, redirect, g
from collections import defaultdict
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Configurações
DATABASE = "bd/dados_teste_1971.db"
DATAS = list(range(1971, 2025))

# ==================== DATABASE MANAGEMENT ====================

def get_db():
    """" Obtém uma conexão com o banco de dados. """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return g.db

@app.teardown_appcontext
def close_db(error):
    """ Fecha a conexão com o banco ao final do request. """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_clubes():
    """ Carrega a lista de clubes do banco. """
    db = get_db()
    clubes_query = db.execute("SELECT clube FROM clubes").fetchall()
    return [row['clube'] for row in clubes_query]

# ==================== BEFORE REQUEST ====================

@app.before_request
def pass_global_data():
    """ Passa dados globais como CLUBES e DATAS para todos os templates. """
    clubes = get_clubes()

    # Converte a lista Python de clubes para STRING JSON para ser usada diretamente no JS do template
    g.json_clubes = jsonify(clubes).get_data(as_text=True)
    g.DATAS = DATAS # Anos disponíveis
    g.CLUBES = clubes # Lista de clubes para uso no backend, se necessário

# ==================== ROUTES ====================

@app.route("/")
def index():
    """Renderiza a página inicial com a classificação geral."""
    db = get_db()

    # Query para classificação geral usando o schema correto
    rankings_geral = db.execute("""
        WITH jogos_mandante AS (
            SELECT
                c.clube,
                p.mandante_placar AS gols_pro,
                p.visitante_placar AS gols_sofrido,
                CASE
                    WHEN p.mandante_placar > p.visitante_placar THEN 3
                    WHEN p.mandante_placar = p.visitante_placar THEN 1
                    ELSE 0
                END AS pontos,
                CASE WHEN p.mandante_placar > p.visitante_placar THEN 1 ELSE 0 END AS vitorias,
                CASE WHEN p.mandante_placar = p.visitante_placar THEN 1 ELSE 0 END AS empates,
                CASE WHEN p.mandante_placar < p.visitante_placar THEN 1 ELSE 0 END AS derrotas
            FROM partidas p
            JOIN clubes c ON p.mandante_id = c.ID
        ),
        jogos_visitante AS (
            SELECT
                c.clube,
                p.visitante_placar AS gols_pro,
                p.mandante_placar AS gols_sofrido,
                CASE
                    WHEN p.visitante_placar > p.mandante_placar THEN 3
                    WHEN p.visitante_placar = p.mandante_placar THEN 1
                    ELSE 0
                END AS pontos,
                CASE WHEN p.visitante_placar > p.mandante_placar THEN 1 ELSE 0 END AS vitorias,
                CASE WHEN p.visitante_placar = p.mandante_placar THEN 1 ELSE 0 END AS empates,
                CASE WHEN p.visitante_placar < p.mandante_placar THEN 1 ELSE 0 END AS derrotas
            FROM partidas p
            JOIN clubes c ON p.visitante_id = c.ID
        ),
        todos_jogos AS (
            SELECT * FROM jogos_mandante
            UNION ALL
            SELECT * FROM jogos_visitante
        )
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY SUM(pontos) DESC,
                         SUM(vitorias) DESC,
                         (SUM(gols_pro) - SUM(gols_sofrido)) DESC,
                         SUM(gols_pro) DESC
            ) AS posicao,
            clube,
            COUNT(*) AS total_jogos,
            SUM(pontos) AS pontos,
            SUM(vitorias) AS vitorias,
            SUM(empates) AS empates,
            SUM(derrotas) AS derrotas,
            SUM(gols_pro) AS gm,
            SUM(gols_sofrido) AS gs,
            (SUM(gols_pro) - SUM(gols_sofrido)) AS sg
        FROM todos_jogos
        GROUP BY clube
        ORDER BY pontos DESC, vitorias DESC, sg DESC, gm DESC
    """).fetchall()

    return render_template("index.html", rankings=rankings_geral, datas=g.DATAS, clubes_json=g.json_clubes)

@app.route("/search")
def search():
    """ Permite buscar por clubes, anos ou rodadas. """
    db = get_db()
    q = request.args.get("q")
    ano = request.args.get("data")
    rodada_param = request.args.get("rodada")

    classificacoes = []
    jogos = []
    current_year = None
    current_round = None
    max_round = 0

    if q:
        # Busca por clube
        jogos_clube, jogos_por_ano = get_jogos_por_clube(q)
        return render_template("clube.html", clubes=q, jogos_por_ano=jogos_por_ano)

    elif ano:
        current_year = int(ano)

        # Buscar a rodada máxima para o ano
        max_round_result = db.execute("""
            SELECT MAX(CAST(p.fase AS INTEGER)) AS max_r
            FROM partidas p
            JOIN edicoes e ON p.edicao_id = e.ID
            WHERE e.ano = ? AND p.fase NOT LIKE '%Final%'
        """, (current_year,)).fetchone()

        if max_round_result and max_round_result['max_r'] is not None:
            max_round = max_round_result['max_r']
        else:
            max_round = 0

        if rodada_param and rodada_param.isdigit():
            current_round = int(rodada_param)
            if current_round == 0:
                classificacoes = get_classification_by_year_and_round(current_year, 0)
                jogos = get_jogos_by_year_and_round(current_year, None)
            else:
                classificacoes = get_classification_by_year_and_round(current_year, current_round)
                jogos = get_jogos_by_year_and_round(current_year, current_round)
        else:
            current_round = max_round
            classificacoes = get_classification_by_year_and_round(current_year, current_round)
            jogos = get_jogos_by_year_and_round(current_year, current_round)

    return render_template("search.html",
                           classificacoes=classificacoes,
                           jogos=jogos,
                           q=q,
                           ano_selecionado=current_year,
                           rodada_selecionada=current_round,
                           max_rodada=max_round,
                           datas=g.DATAS,
                           clubes_json=g.json_clubes)

@app.route("/clube/<string:nome>")
def clube(nome):
    """ Página de um clube específico. """
    jogos_clube, jogos_por_ano = get_jogos_por_clube(nome)
    return render_template("clube.html", clube=nome, jogos_por_ano=jogos_por_ano)

@app.route("/estatisticas/<int:jogos_id>")

