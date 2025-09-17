import sqlite3
import csv

# Nome do seu banco de dados e arquivo CSV de saída
db_file = 'brasileirao_desde_1971.db'
csv_file = 'csv_br_1971/campeonatos.csv'
query = 'SELECT * FROM campeonatos;' # Substitua 'sua_tabela' pelo nome da sua tabela

try:
    # Conecta ao banco de dados SQLite
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Executa a consulta
    cursor.execute(query)
    rows = cursor.fetchall()

    # Obtém os nomes das colunas para o cabeçalho
    column_names = [description[0] for description in cursor.description]

    # Abre o arquivo CSV no modo de escrita com codificação UTF-8
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Escreve os nomes das colunas como cabeçalho
        writer.writerow(column_names)

        # Escreve as linhas de dados
        writer.writerows(rows)

    print(f"Dados exportados com sucesso para {csv_file} em UTF-8.")

except sqlite3.Error as e:
    print(f"Erro ao interagir com o banco de dados: {e}")
except IOError as e:
    print(f"Erro ao escrever no arquivo CSV: {e}")
finally:
    # Fecha a conexão com o banco de dados
    if conn:
        conn.close()
