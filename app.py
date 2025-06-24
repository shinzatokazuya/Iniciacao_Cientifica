# app.py
import functools
from flask import Flask, render_template, jsonify, request, redirect, g

from cs50 import SQL

app = Flask(__name__)

# Configura o banco de dados
db = SQL("sqlite:///Dados_brasileirao_2003_2023.db")

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

    # Obtém o último ano disponível para exibir as partidas iniciais
    ultimo_ano = max(g.DATAS) if g.DATAS else None
    primeiras_partidas = []
    if ultimo_ano:
        # Busca as primeiras partidas do último ano, ordenadas por rodada e data
        primeiras_partidas = db.execute("SELECT * FROM Full WHERE SUBSTR(data, 7, 4) = ? ORDER BY rodada, data", ultimo_ano)

    # Renderiza o template index.html com os dados
    return render_template("index.html", datas=g.DATAS, rankings=rankings_geral, clubes_json=g.json_clubes, primeiras_partidas=primeiras_partidas, ano_atual=ultimo_ano)


@app.route("/api/classificacao/<int:ano>")
def get_classificacao_por_ano_api(ano):
    """API para retornar a classificação final (rodada 0) de um ano específico."""
    # Chama a função auxiliar para obter a classificação final do ano
    rankings = get_classification_by_year_and_round(ano, 0)
    return jsonify(rankings)

@app.route("/api/classificacao/<int:ano>/<int:rodada>")
def get_classificacao_por_ano_e_rodada_api(ano, rodada):
    """API para retornar a classificação até uma rodada específica de um ano."""
    rankings = get_classification_by_year_and_round(ano, rodada)
    return jsonify(rankings)

@app.route("/api/jogos/<int:ano>")
def get_jogos_por_ano_api(ano):
    """API para retornar todos os jogos de um ano específico."""
    jogos = db.execute("SELECT * FROM Full WHERE SUBSTR(data, 7, 4) = ? ORDER BY rodada, data", ano)
    return jsonify(jogos)

@app.route("/api/jogos/<int:ano>/<int:rodada>")
def get_jogos_por_ano_e_rodada_api(ano, rodada):
    """API para retornar os jogos de uma rodada específica de um ano."""
    jogos = db.execute("SELECT * FROM Full WHERE SUBSTR(data, 7, 4) = ? AND rodada = ? ORDER BY data", ano, rodada)
    return jsonify(jogos)

@app.route("/api/max_rodada/<int:ano>")
def get_max_rodada(ano):
    """API para retornar o número máximo de rodadas para um ano específico."""
    max_round_result = db.execute("SELECT MAX(rodada) AS max_r FROM Full WHERE SUBSTR(data, 7, 4) = ?", ano)
    # Garante que max_round é um número inteiro, default 0 se não houver rodadas
    max_round = max_round_result[0]['max_r'] if max_round_result and max_round_result[0]['max_r'] is not None else 0
    # RETORNA APENAS O NÚMERO DA RODADA MÁXIMA, CONFORME ESPERADO PELO FRONTEND
    return jsonify(max_round)


@app.route("/search")
def search():
    """Renderiza a página de busca com resultados filtrados por clube, ano ou rodada."""
    q = request.args.get('q') # Parâmetro de busca por clube
    ano = request.args.get('data') # Parâmetro de busca por ano
    rodada_param = request.args.get("rodada") # Parâmetro de busca por rodada

    jogos = []
    classificacoes = []
    current_year = None
    current_round = None
    max_round = 0

    if ano:
        current_year = int(ano)

        # Primeiro, obtemos o número máximo de rodadas para o ano selecionado
        max_round_result = db.execute("SELECT MAX(rodada) AS max_r FROM Full WHERE SUBSTR(data, 7, 4) = ?", current_year)
        if max_round_result and max_round_result[0]['max_r'] is not None:
            max_round = max_round_result[0]['max_r']

        # Determina a rodada atual a ser exibida:
        # Se rodada_param for fornecido e válido, usa-o.
        # Caso contrário (ou se for 0), default para a rodada máxima do ano para classificação,
        # e busca todos os jogos do ano.
        if rodada_param and rodada_param.isdigit():
            current_round = int(rodada_param)
        else:
            # Se nenhuma rodada específica é solicitada na URL, mostra a classificação final do ano
            # e todos os jogos para o ano.
            current_round = max_round if max_round > 0 else 1 # Para classificação, 0 pode indicar "ano completo"

        # Busca os jogos:
        # Se nenhuma rodada específica for passada ou for 0, busca todos os jogos do ano.
        if rodada_param is None or (rodada_param.isdigit() and int(rodada_param) == 0):
            jogos = db.execute("SELECT * FROM Full WHERE SUBSTR(data, 7, 4) = ? ORDER BY rodada, data", current_year)
        else: # Busca jogos para uma rodada específica
            jogos = db.execute("SELECT * FROM Full WHERE SUBSTR(data, 7, 4) = ? AND rodada = ? ORDER BY data", current_year, current_round)

        # Busca a classificação, passando 0 para 'rodada' se quisermos a classificação final do ano.
        # Caso contrário, passa a rodada selecionada.
        classificacoes = get_classification_by_year_and_round(current_year, current_round)

    elif q: # Se há uma busca por clube (q)
        # Busca todos os jogos do clube (como mandante ou visitante)
        jogos = db.execute("SELECT * FROM Full WHERE mandante = ? OR visitante = ? ORDER BY SUBSTR(data, 7, 4)", q, q)
        classificacoes = [] # Não exibe classificação por clube individualmente nesta página

    else: # Se não há parâmetros válidos, redireciona para a página inicial
        return redirect("/")

    # Renderiza o template search.html com os dados filtrados
    return render_template(
        "search.html",
        jogos=jogos,
        classificacoes=classificacoes,
        q=q, # Nome do clube pesquisado
        ano_selecionado=current_year, # Ano que está sendo exibido
        rodada_selecionada=current_round, # Rodada que está sendo exibida (ou rodada final/primeira)
        max_rodada=max_round, # Rodada máxima para o ano
        datas=g.DATAS, # Todos os anos disponíveis
        clubes_json=g.json_clubes # Lista de clubes em formato JSON
    )

@app.route("/clube/<nome>")
def clube(nome):
    """Renderiza a página de detalhes de um clube, mostrando seus jogos."""
    jogos = db.execute("SELECT * FROM Full WHERE mandante = ? OR visitante = ? ORDER BY SUBSTR(data, 7, 4)", nome, nome)
    return render_template("clube.html", clube=nome, jogos=jogos, clubes_json=g.json_clubes)

@app.route("/estatisticas/<int:partida_id>")
def estatisticas(partida_id):
    """Renderiza a página de estatísticas de uma partida específica."""
    estat = db.execute("SELECT * FROM Estatisticas WHERE partida_id = ?", partida_id)
    gols = db.execute("SELECT * FROM Gols WHERE partida_id = ?", partida_id)
    cartoes = db.execute("SELECT * FROM Cartoes WHERE partida_id = ?", partida_id)
    return render_template("estatisticas.html", estatisticas=estat, gols=gols, cartoes=cartoes, clubes_json=g.json_clubes)


def get_classification_by_year_and_round(year, round_num=None):
    """
    Função auxiliar para obter a classificação de clubes para um dado ano,
    até uma rodada específica. Se round_num é 0 ou None, retorna a classificação final do ano.
    """
    where_clause_base = "WHERE SUBSTR(data, 7, 4) = ?"
    params_base = [year]

    where_clause_parts = [where_clause_base]
    params_parts = [params_base]

    # Determina a rodada limite para a classificação
    if round_num is not None and round_num != 0:
        # Classificação até a rodada especificada
        where_clause_parts.append("AND rodada <= ?")
        params_parts.append([round_num])
    elif round_num == 0: # Caso seja 0, significa que o front-end quer a classificação final do ano.
        # Busca a rodada máxima para o ano para a classificação final
        max_round_result = db.execute("SELECT MAX(rodada) AS max_r FROM Full WHERE SUBSTR(data, 7, 4) = ?", year)
        max_round = max_round_result[0]['max_r'] if max_round_result and max_round_result[0]['max_r'] is not None else None
        if max_round:
            where_clause_parts.append("AND rodada <= ?")
            params_parts.append([max_round])
        # Se não há rodadas para o ano, a lista de parâmetros para o filtro de rodada não é adicionada,
        # e a query retornará vazio para este ano.

    # Constrói a cláusula WHERE completa e a lista de parâmetros para a execução final da query
    final_where_clause = " ".join(where_clause_parts)
    # Achata a lista de listas de parâmetros em uma única lista
    flattened_params = [item for sublist in params_parts for item in sublist]

    # A query SQL para calcular a classificação
    query = f"""
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
            FROM Full
            {final_where_clause}
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
            FROM Full
            {final_where_clause}
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
    """
    # Para executar a query, é necessário replicar os parâmetros para cada ocorrência de 'final_where_clause'
    # na query. A 'final_where_clause' aparece 4 vezes na sua query grande (2x em placares_anuais, 2x em total_jogos_clube).
    num_sub_queries_using_where = 4
    full_params_for_query = flattened_params * num_sub_queries_using_where

    return db.execute(query, *full_params_for_query)
