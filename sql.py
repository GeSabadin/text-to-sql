import os
from dotenv import load_dotenv
import mysql.connector

# Carrega variáveis do .env
load_dotenv()
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# Conexão com o banco
conn = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

cursor = conn.cursor()

# Testa a conexão listando tabelas
cursor.execute("SHOW TABLES")
for tabela in cursor.fetchall():
    print(tabela)

cursor.close()
conn.close()