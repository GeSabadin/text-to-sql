from flask import Flask, render_template, request
import os
from dotenv import load_dotenv
import google.generativeai as genai
import mysql.connector
import psycopg2
from tabulate import tabulate

app = Flask(__name__)
load_dotenv()

# --- Configuração do Gemini ---
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

# --- Configuração do Banco (ajuste para seu banco preferido) ---
DB_TYPE = os.getenv("DB_TYPE", "mysql").lower()  # ou use um select no site
if DB_TYPE == "mysql":
    db_label = "MySQL"
    db_name = os.getenv("MYSQL_DB_NAME")
    def connect():
        return mysql.connector.connect(
            host=os.getenv("MYSQL_DB_HOST"),
            user=os.getenv("MYSQL_DB_USER"),
            password=os.getenv("MYSQL_DB_PASSWORD"),
            database=os.getenv("MYSQL_DB_NAME")
        )
    def get_schema(conn):
        esquema_db = ""
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tabelas = [t[0] for t in cursor.fetchall()]
        for tabela in tabelas:
            esquema_db += f"Tabela '{tabela}':\n"
            cursor.execute(f"DESCRIBE `{tabela}`")
            colunas = cursor.fetchall()
            for col in colunas:
                esquema_db += f" - {col[0]} ({col[1]})\n"
            esquema_db += "\n"
        cursor.close()
        return esquema_db
    prompt_path = "prompt_mysql.txt"
else:
    db_label = "PostgreSQL"
    db_name = os.getenv("PG_DB_NAME")
    def connect():
        return psycopg2.connect(
            host=os.getenv("PG_DB_HOST"),
            user=os.getenv("PG_DB_USER"),
            password=os.getenv("PG_DB_PASSWORD"),
            dbname=os.getenv("PG_DB_NAME")
        )
    def get_schema(conn):
        esquema_db = ""
        cursor = conn.cursor()
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        cursor.execute(query)
        tabela_atual = ""
        for row in cursor.fetchall():
            nome_tabela, nome_coluna, tipo_dado = row
            if nome_tabela != tabela_atual:
                tabela_atual = nome_tabela
                esquema_db += f"\nTabela '{tabela_atual}':\n"
            esquema_db += f" - {nome_coluna} ({tipo_dado})\n"
        cursor.close()
        return esquema_db
    prompt_path = "prompt_postgres.txt"

def carregar_prompt(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = ""
    sql_gerado = ""
    erro = ""

    # Banco padrão na primeira visita
    if request.method == "POST":
        db_name = request.form.get("db_name", "employees")
    else:
        db_name = "employees"

    if db_name == "employees":
        db_label = "MySQL"
        def connect():
            return mysql.connector.connect(
                host=os.getenv("MYSQL_DB_HOST"),
                user=os.getenv("MYSQL_DB_USER"),
                password=os.getenv("MYSQL_DB_PASSWORD"),
                database=os.getenv("MYSQL_DB_NAME")
            )
        def get_schema(conn):
            esquema_db = ""
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tabelas = [t[0] for t in cursor.fetchall()]
            for tabela in tabelas:
                esquema_db += f"Tabela '{tabela}':\n"
                cursor.execute(f"DESCRIBE `{tabela}`")
                colunas = cursor.fetchall()
                for col in colunas:
                    esquema_db += f" - {col[0]} ({col[1]})\n"
                esquema_db += "\n"
            cursor.close()
            return esquema_db
        prompt_path = "prompt_mysql.txt"
    else:  # dvdrental
        db_label = "PostgreSQL"
        def connect():
            return psycopg2.connect(
                host=os.getenv("PG_DB_HOST"),
                user=os.getenv("PG_DB_USER"),
                password=os.getenv("PG_DB_PASSWORD"),
                dbname=os.getenv("PG_DB_NAME")
            )
        def get_schema(conn):
            esquema_db = ""
            cursor = conn.cursor()
            query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
            """
            cursor.execute(query)
            tabela_atual = ""
            for row in cursor.fetchall():
                nome_tabela, nome_coluna, tipo_dado = row
                if nome_tabela != tabela_atual:
                    tabela_atual = nome_tabela
                    esquema_db += f"\nTabela '{tabela_atual}':\n"
                esquema_db += f" - {nome_coluna} ({tipo_dado})\n"
            cursor.close()
            return esquema_db
        prompt_path = "prompt_postgres.txt"

    if request.method == "POST":
        pergunta_usuario = request.form["pergunta"]
        try:
            conn = connect()
            esquema_db = get_schema(conn)
            prompt_template = carregar_prompt(prompt_path)
            prompt_final = prompt_template.format(
                schema=esquema_db,
                pergunta_usuario=pergunta_usuario
            )
            response = model.generate_content(prompt_final)
            sql_gerado = response.text.strip().replace("```sql", "").replace("```", "")
            cursor = conn.cursor()
            cursor.execute(sql_gerado)
            if cursor.description:
                resultados = cursor.fetchall()
                nomes_colunas = [i[0] for i in cursor.description]
                resultado = tabulate(resultados, headers=nomes_colunas, tablefmt="html")
            else:
                conn.commit()
                resultado = f"Comando executado com sucesso. {cursor.rowcount} linhas afetadas."
            cursor.close()
            conn.close()
        except Exception as e:
            erro = f"Erro: {e}"

    return render_template(
        "index.html",
        resultado=resultado,
        sql_gerado=sql_gerado,
        erro=erro,
        db_label=db_label,
        db_name=db_name
    )

if __name__ == "__main__":
    app.run(debug=True)