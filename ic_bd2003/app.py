# app.py
import functools
from flask import Flask, render_template, jsonify, request, redirect, g
from collections import defaultdict
from datetime import datetime
from cs50 import SQL

app = Flask(__name__)

# Configura o banco de dados
db = SQL("sqlite:///bd/Dados_brasileirao_2003_2023.db")

# Carrega os clubes únicos para uso global
CLUBES_QUERY = db.execute("SELECT DISTINCT mandante AS clube FROM Full UNION SELECT DISTINCT visitante AS clube FROM Full ORDER BY clube")
CLUBES = [row['clube'] for row in CLUBES_QUERY]

# Define os anos disponíveis
DATAS = list(range(2003, 2024))

@app.before_request
def pass_global_data():
    """Passa dados globais como CLUBES e DATAS para todos os templates."""
    # Converte a lista Python de clubes para string JSON para ser usada diretamente no JS do template
    g.json_clubes = jsonify(CLUBES).get_data(as_text=True)
    g.DATAS = DATAS # Anos disponíveis
    g.CLUBES = CLUBES # Lista de clubes para uso no backend, se necessário

@app.route("/")
def index():
    """Renderiza a página inicial com a classificação geral e as primeiras partidas do último ano."""
    # Query para a classificação geral (todos os anos combinados)
    rankings_geral = db.execute("""
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
                                    ROW_NUMBER() OVER (ORDER BY SUM(p.pontos) DESC, SUM(p.vitorias) DESC, (SUM(p.gm) - SUM(p.gc)) DESC, SUM(p.gm) DESC) AS posicao,
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
                                ORDER BY pontos DESC, vitorias DESC, sg DESC, gm DESC;
                                """)

    return render_template("index.html", rankings=rankings_geral, datas=g.DATAS, clubes_json=g.json_clubes)

@app.route("/search")
def search():
    """Permite buscar por clubes, anos ou rodadas."""
    q = request.args.get("q")
    ano = request.args.get("data")
    rodada_param = request.args.get("rodada")

    classificacoes = []
    jogos = []
    current_year = None
    current_round = None
    max_round = 0

    if q:
        # Lógica de busca por clube (já existente)
        jogos_clube, jogos_por_ano = get_jogos_por_clube(q)
        return render_template("clube.html", clube=q, jogos=jogos_clube, jogos_por_ano=jogos_por_ano)

    elif ano:
        current_year = int(ano)

        # Buscar a rodada máxima para o ano
        max_round_result = db.execute("SELECT MAX(rodada) AS max_r FROM Full WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ?", current_year)
        if max_round_result and max_round_result[0]['max_r'] is not None:
            max_round = max_round_result[0]['max_r']
        else:
            max_round = 0 # Fallback se não encontrar rodadas para o ano

        if rodada_param and rodada_param.isdigit():
            # Se uma rodada específica foi solicitada
            current_round = int(rodada_param)
            if current_round == 0: # 0 ainda será o sinal para classificação final e todos os jogos
                classificacoes = get_classification_by_year_and_round(current_year, 0)
                jogos = db.execute("SELECT * FROM Full WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ? ORDER BY data, rodada", current_year)
            else:
                classificacoes = get_classification_by_year_and_round(current_year, current_round)
                jogos = db.execute("SELECT * FROM Full WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ? AND rodada = ? ORDER BY data", current_year, current_round)
        else:
            # Se nenhuma rodada específica foi solicitada (ou rodada_param não é um número válido)
            # Define a rodada padrão como a última rodada (max_round) e busca os jogos dessa rodada.
            current_round = max_round
            classificacoes = get_classification_by_year_and_round(current_year, current_round)
            jogos = db.execute("SELECT * FROM Full WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ? AND rodada = ? ORDER BY data", current_year, current_round)

    return render_template("search.html",
                           classificacoes=classificacoes,
                           jogos=jogos,
                           q=q,
                           ano_selecionado=current_year,
                           rodada_selecionada=current_round,
                           max_rodada=max_round, # Passa max_rodada para o template, útil para JS
                           datas=g.DATAS,
                           clubes_json=g.json_clubes)


@app.route("/api/classificacao/<int:ano>/<int:rodada>")
def api_classificacao(ano, rodada):
    """Retorna a classificação para um dado ano e rodada."""
    classificacoes = get_classification_by_year_and_round(ano, rodada)
    return jsonify(classificacoes)

@app.route("/api/jogos/<int:ano>/<int:rodada>")
def api_jogos(ano, rodada):
    """Retorna os jogos para um dado ano e rodada, ou todos os jogos se rodada for 0."""
    if rodada == 0:
        jogos = db.execute("SELECT * FROM Full WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ? ORDER BY data, rodada", ano)
    else:
        jogos = db.execute("SELECT * FROM Full WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ? AND rodada = ? ORDER BY data", ano, rodada)
    return jsonify(jogos)

@app.route("/api/max_rodada/<int:ano>")
def api_max_rodada(ano):
    """Retorna o número máximo de rodadas para um dado ano."""
    print(f"DEBUG: Requisição recebida para /api/max_rodada/{ano} (tipo: {type(ano)})")

    # Store the query for clarity in debug
    query_string = "SELECT MAX(rodada) AS max_r FROM Full WHERE CAST(SUBSTR(data, 7, 4) AS INTEGER) = ?"
    print(f"DEBUG: Executando query: {query_string} com parâmetro: {ano}")

    result = db.execute(query_string, ano)

    print(f"DEBUG: Resultado bruto da query: {result}") # ADD THIS LINE

    if result and result[0]['max_r'] is not None:
        max_r = result[0]['max_r']
        print(f"DEBUG: Max rodada para {ano}: {max_r}")
        return jsonify(max_r)

    print(f"DEBUG: Nenhuma rodada encontrada para o ano: {ano}, retornando 0.")
    return jsonify(0)

@app.route("/estatisticas/<int:jogo_id>")
def estatisticas(jogo_id):
    # Estatísticas, gols e cartões
    estatisticas_jogo = db.execute("SELECT * FROM Estatisticas WHERE partida_id = ?", jogo_id)
    gols_jogo = db.execute("SELECT * FROM Gols WHERE partida_id = ? ORDER BY minuto ASC", jogo_id)
    cartoes_jogo = db.execute("SELECT * FROM Cartoes WHERE partida_id = ? ORDER BY CAST(SUBSTR(minuto, 1, INSTR(minuto, '+') - 1) AS INTEGER) ASC", jogo_id)

    # Buscar dados do confronto na tabela Full
    confronto = db.execute("SELECT mandante, visitante, mandante_Placar AS gols_mandante, formacao_mandante, visitante_Placar AS gols_visitante, formacao_visitante, data, arena, rodada, mandante_Estado FROM Full WHERE ID = ?", jogo_id)

    if confronto:
        confronto = confronto[0]  # transforma lista em dicionário
    else:
        confronto = {}

    return render_template(
        "estatisticas.html",
        estatisticas=estatisticas_jogo,
        gols=gols_jogo,
        cartoes=cartoes_jogo,
        confronto=confronto,
    )

@app.route("/clube/<string:nome>")
def clube(nome):
    jogos_clube, jogos_por_ano = get_jogos_por_clube(nome)
    return render_template("clube.html", clube=nome, jogos_por_ano=jogos_por_ano)

def get_jogos_por_clube(nome):
    """Mostra todos os jogos de um clube específico, separados por ano."""
    jogos_clube = db.execute(
        "SELECT * FROM Full WHERE mandante = ? OR visitante = ? ORDER BY rodada ASC",
        nome, nome
    )

    jogos_por_ano = {}
    jogos_adicionados = set()  # para evitar duplicados

    for jogo in jogos_clube:
        # converte a data do banco para datetime
        data_jogo = datetime.strptime(jogo["data"], "%d/%m/%Y")
        ano_jogo = data_jogo.year

        # Ajusta o ano da pandemia
        if ano_jogo == 2021 and data_jogo <= datetime(2021, 2, 25):
            ano_jogo = 2020

        # Evita duplicados
        jogo_id = jogo["ID"]
        if jogo_id in jogos_adicionados:
            continue
        jogos_adicionados.add(jogo_id)

        # Adiciona no dicionário por ano
        if ano_jogo not in jogos_por_ano:
            jogos_por_ano[ano_jogo] = []
        jogos_por_ano[ano_jogo].append(jogo)

    # Ordena os anos de forma decrescente
    jogos_por_ano = dict(sorted(jogos_por_ano.items(), reverse=True))

    # Ordena cada ano por rodada
    for ano in jogos_por_ano:
        jogos_por_ano[ano] = sorted(jogos_por_ano[ano], key=lambda x: x["rodada"])

    return jogos_clube, jogos_por_ano

def get_classification_by_year_and_round(year, round_num=None):
    """
    Calcula a classificação do campeonato até uma rodada específica ou a classificação final para um dado ano.
    :param year: O ano para o qual a classificação será calculada.
    :param round_num: A rodada até a qual a classificação deve ser considerada.
                      Se None ou 0, calcula a classificação final do ano.
    :return: Uma lista de dicionários com a classificação.
    """
    where_clause_parts = []
    params = []

    if year:
        where_clause_parts.append("CAST(SUBSTR(data, 7, 4) AS INTEGER) = ?")
        params.append(year)

    if round_num is not None and round_num != 0:
        where_clause_parts.append("rodada <= ?")
        params.append(round_num)

    final_where_clause = "WHERE " + " AND ".join(where_clause_parts) if where_clause_parts else ""

    num_sub_queries_using_where = 2
    num_sub_queries_using_where_total_jogos = 2

    flattened_params = params[:]
    full_params_for_query = flattened_params * (num_sub_queries_using_where + num_sub_queries_using_where_total_jogos)

    rankings = db.execute(f"""
        WITH placares_anuais AS (
            SELECT
                mandante AS clube,
                SUBSTR(data, 7, 4) AS ano,
                SUM(CASE WHEN mandante_Placar > visitante_Placar THEN 3 WHEN mandante_Placar = visitante_Placar THEN 1 ELSE 0 END) AS pontos,
                SUM(CASE WHEN mandante_Placar > visitante_Placar THEN 1 ELSE 0 END) AS vitorias,
                SUM(CASE WHEN mandante_Placar = visitante_Placar THEN 1 ELSE 0 END) AS empates,
                SUM(CASE WHEN mandante_Placar < visitante_Placar THEN 1 ELSE 0 END) AS derrotas,
                SUM(mandante_Placar) AS gm,
                SUM(visitante_Placar) AS gc
            FROM Full {final_where_clause}
            GROUP BY mandante, ano

            UNION ALL

            SELECT
                visitante AS clube,
                SUBSTR(data, 7, 4) AS ano,
                SUM(CASE WHEN visitante_Placar > mandante_Placar THEN 3 WHEN visitante_Placar = mandante_Placar THEN 1 ELSE 0 END) AS pontos,
                SUM(CASE WHEN visitante_Placar > mandante_Placar THEN 1 ELSE 0 END) AS vitorias,
                SUM(CASE WHEN visitante_Placar = mandante_Placar THEN 1 ELSE 0 END) AS empates,
                SUM(CASE WHEN visitante_Placar < mandante_Placar THEN 1 ELSE 0 END) AS derrotas,
                SUM(visitante_Placar) AS gm,
                SUM(mandante_Placar) AS gc
            FROM Full {final_where_clause}
            GROUP BY visitante, ano
        ),
        total_jogos_clube AS (
            SELECT
                clube,
                SUBSTR(data, 7, 4) AS ano,
                COUNT(*) AS total_jogos
            FROM (
                SELECT mandante AS clube, data FROM Full {final_where_clause}
                UNION ALL
                SELECT visitante AS clube, data FROM Full {final_where_clause}
            ) AS todos_os_clubes_ano
            GROUP BY clube, ano
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY SUM(p.pontos) DESC, SUM(p.vitorias) DESC, (SUM(p.gm) - SUM(p.gc)) DESC, SUM(p.gm) DESC) AS posicao,
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
        JOIN total_jogos_clube t ON p.clube = t.clube AND p.ano = t.ano
        GROUP BY p.ano, p.clube
        ORDER BY pontos DESC, vitorias DESC, sg DESC, gm DESC;
    """, *full_params_for_query)

    return rankings
