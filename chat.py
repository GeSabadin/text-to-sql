import os
import sys # Usado para sair do programa de forma limpa
from dotenv import load_dotenv
import google.generativeai as genai
import mysql.connector
import psycopg2 # Importa a biblioteca para PostgreSQL
from tabulate import tabulate

# ===================================================================
# Carrega as variáveis de ambiente e conecta aos serviços
# ===================================================================

load_dotenv()

# --- Conexão com o Gemini ---
try:
    api_key = os.getenv("API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
    print("Conectado ao Gemini.")
except Exception as e:
    print(f" ERRO FATAL ao conectar com o Gemini: {e}")
    sys.exit()

# ===================================================================
# Funções Específicas para cada Banco de Dados
# ===================================================================

# --- Funções para MySQL (Employees) ---

def connect_to_mysql():
    """Conecta ao banco de dados MySQL."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_DB_HOST"),
            user=os.getenv("MYSQL_DB_USER"),
            password=os.getenv("MYSQL_DB_PASSWORD"),
            database=os.getenv("MYSQL_DB_NAME")
        )
        print(f"Conectado ao MySQL, banco '{os.getenv('MYSQL_DB_NAME')}'.")
        return conn
    except mysql.connector.Error as err:
        print(f"ERRO FATAL de conexão com o MySQL: {err}")
        sys.exit()

def get_mysql_schema(conn):
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
    print("Esquema MySQL memorizado.")
    return esquema_db

# --- Funções para PostgreSQL (DvdRental) ---

def connect_to_postgres():
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_DB_HOST"),
            user=os.getenv("PG_DB_USER"),
            password=os.getenv("PG_DB_PASSWORD"),
            dbname=os.getenv("PG_DB_NAME")
        )
        print(f"Conectado ao PostgreSQL, banco '{os.getenv('PG_DB_NAME')}'.")
        return conn
    except psycopg2.Error as err:
        print(f"ERRO FATAL de conexão com o PostgreSQL: {err}")
        sys.exit()

def get_postgres_schema(conn):
    """Extrai e formata o esquema de um banco de dados PostgreSQL."""
    esquema_db = ""
    cursor = conn.cursor()
    # Query para buscar tabelas e colunas no esquema 'public' do PostgreSQL
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
    print("👍 Esquema PostgreSQL memorizado.")
    return esquema_db

def carregar_prompt(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()

# ===================================================================
# Lógica Principal do Agente
# ===================================================================

if __name__ == "__main__":

    while True:
        db_choice = input("Qual banco de dados você quer acessar?\n1. MySQL (employees)\n2. PostgreSQL (dvdrental)\nEscolha (1 ou 2): ")
        if db_choice in ["1", "2"]:
            break
        print("Opção inválida. Por favor, digite 1 ou 2.")

    # Configuração baseada na escolha do usuário
    if db_choice == "1":
        conn = connect_to_mysql()
        esquema_db = get_mysql_schema(conn)
        prompt_template = carregar_prompt("prompt_mysql.txt")
        db_type = "MySQL"
    else:
        conn = connect_to_postgres()
        esquema_db = get_postgres_schema(conn)
        prompt_template = carregar_prompt("prompt_postgres.txt")
        db_type = "PostgreSQL"
    
    while True:
        pergunta_usuario = input("\nFaça sua pergunta (ou digite 'sair' para terminar): ")
        if pergunta_usuario.lower() == 'sair':
            break

        # Monta o prompt final
        prompt_final = prompt_template.format(
            schema=esquema_db,
            pergunta_usuario=pergunta_usuario
        )

        print("\n⏳ Gerando consulta SQL com o Gemini...")
        try:
            response = model.generate_content(prompt_final)
            sql_gerado = response.text.strip().replace("```sql", "").replace("```", "") # Limpeza extra
        except Exception as e:
            print(f"ERRO ao chamar a API do Gemini: {e}")
            continue

        if sql_gerado.startswith("ERRO"):
            print(f"\n Resposta do Agente: {sql_gerado}")
            continue

        print(f"\nSQL Gerado:\n{sql_gerado}\n")

        # Executa a consulta gerada
        print("Executando a consulta no banco de dados...")
        try:
            cursor = conn.cursor()
            cursor.execute(sql_gerado)
            
            # A consulta pode não retornar linhas (ex: UPDATE, INSERT), mas não é um erro.
            if cursor.description:
                resultados = cursor.fetchall()
                nomes_colunas = [i[0] for i in cursor.description]
                print(tabulate(resultados, headers=nomes_colunas, tablefmt="psql"))
            else:
                # Informa que a ação foi bem sucedida (ex: UPDATE, DELETE)
                conn.commit() # Importante para salvar as alterações
                print(f"Comando executado com sucesso. {cursor.rowcount} linhas afetadas.")

        except (mysql.connector.Error, psycopg2.Error) as err:
            print(f"--- ERRO AO EXECUTAR O SQL ---")
            print(f"O SQL gerado pode ser inválido para o dialeto {db_type}. Erro: {err}")
            conn.rollback() # Desfaz a transação em caso de erro
        finally:
            if cursor:
                cursor.close()

    # Fora do loop:
    if conn:
        conn.close()
        print("\n🔌 Conexão com o banco de dados fechada.")