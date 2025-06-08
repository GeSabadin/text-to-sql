import os
from dotenv import load_dotenv # type: ignore
import google.generativeai as genai # type: ignore
import mysql.connector #type: ignore

# ===================================================================
# Carrega as variáveis de ambiente e conecta aos serviços.

load_dotenv()

# --- Conexão com o Gemini ---
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("ERRO: GEMINI_API_KEY não foi encontrada no arquivo .env")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
print("Conectado ao Google Gemini.")

# --- Conexão com o Banco de Dados MySQL ---
try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()
    print(f"Conectado ao banco de dados '{os.getenv('DB_NAME')}' com sucesso.")
except mysql.connector.Error as err:
    print(f"ERRO FATAL de conexão com o banco de dados: {err}")
    exit() # Encerra o script se não puder conectar ao banco

# PASSO 2: EXTRAÇÃO DO ESQUEMA (A "MEMÓRIA" DO AGENTE)
# O agente lê e memoriza a estrutura do seu banco de dados.

print("Lendo o esquema do banco de dados para aprender a estrutura...")
esquema_db = ""
try:
    cursor.execute("SHOW TABLES")
    tabelas = [t[0] for t in cursor.fetchall()]
    
    for tabela in tabelas:
        esquema_db += f"Tabela '{tabela}':\n"
        cursor.execute(f"DESCRIBE `{tabela}`") # Usar crase para nomes de tabelas
        colunas = cursor.fetchall()
        for col in colunas:
            esquema_db += f"  - `{col[0]}` ({col[1]})\n"
        esquema_db += "\n"
    
    print("Esquema lido e memorizado.")

except mysql.connector.Error as err:
    print(f"ERRO ao tentar ler o esquema do banco: {err}")
    conn.close()
    exit()

# PASSO 3: O "CÉREBRO" DO AGENTE (PROMPT TEMPLATE)
# Definimos as regras e o modelo de como o Gemini deve pensar.

PROMPT_TEMPLATE = """
Você é um analista de dados expert em MySQL e sua função é converter perguntas em linguagem natural para consultas SQL para o banco de dados 'employees'.

**REGRAS ESTRITAS:**
1.  **Use APENAS o dialeto MySQL.**
2.  **Analise o esquema, as relações e os exemplos abaixo** para garantir que a consulta seja precisa e eficiente.
3.  **Sua resposta deve conter APENAS o código SQL.** Não inclua texto, explicações ou formatação como ```sql```.
4.  Se a pergunta não puder ser respondida pelo esquema, retorne a mensagem: ERRO: Pergunta fora do escopo.

---
**ESQUEMA DO BANCO DE DADOS:**
{schema}

---
**RELAÇÕES IMPORTANTES ENTRE TABELAS:**
-   `employees.emp_no` é a chave primária que conecta todas as tabelas.
-   `employees.emp_no` se conecta com `salaries.emp_no`.
-   `employees.emp_no` se conecta com `titles.emp_no`.
-   `employees.emp_no` se conecta com `dept_emp.emp_no`.
-   `dept_emp.dept_no` se conecta com `departments.dept_no`.

---
**DICAS SOBRE O CONTEÚDO:**
-   A coluna `gender` na tabela `employees` usa 'M' para Masculino e 'F' para Feminino.
-   Para encontrar o salário atual de um funcionário, use `WHERE to_date > NOW()` na tabela `salaries`.

---
**EXEMPLOS DE PERGUNTAS E CONSULTAS CORRETAS:**

**Pergunta:** "Qual o nome e sobrenome do funcionário com o maior salário atual?"
**SQL:**
SELECT e.first_name, e.last_name, s.salary FROM employees e JOIN salaries s ON e.emp_no = s.emp_no WHERE s.to_date > NOW() ORDER BY s.salary DESC LIMIT 1;

**Pergunta:** "Quantos funcionários trabalham no departamento de Marketing?"
**SQL:**
SELECT count(e.emp_no) FROM employees e JOIN dept_emp de ON e.emp_no = de.emp_no JOIN departments d ON de.dept_no = d.dept_no WHERE d.dept_name = 'Marketing';

---
**PERGUNTA DO USUÁRIO:**
"{pergunta_usuario}"

**CONSULTA SQL:**
"""

print("Modelo de prompt e regras definidos.")
print("-" * 50)
print("Agente pronto! Agora você pode adicionar o loop de interação.")
print("-" * 50)


while True:
        pergunta_usuario = input("\nFaça sua pergunta sobre os dados (ou digite 'sair'): ")
        if pergunta_usuario.lower() == 'sair':
            break

        # Monta o prompt final
        prompt_final = PROMPT_TEMPLATE.format(
            schema=esquema_db, 
            pergunta_usuario=pergunta_usuario
        )

        print("Gerando consulta SQL com o Gemini...")
        response = model.generate_content(prompt_final)
        sql_gerado = response.text.strip()
        
        if sql_gerado.startswith("ERRO"):
            print(f"\nResposta do Agente: {sql_gerado}")
            continue

        print(f"\nSQL Gerado: \n{sql_gerado}\n")

        # Executa a consulta gerada
        print("Executando a consulta no banco de dados...")
        try:
            cursor = conn.cursor()
            cursor.execute(sql_gerado)
            resultados = cursor.fetchall()
            
            if resultados:
                # Imprime o cabeçalho
                nomes_colunas = [i[0] for i in cursor.description]
                print(" | ".join(nomes_colunas))
                print("-" * (len(" | ".join(nomes_colunas)) + 5))
                
                # Imprime os resultados
                for linha in resultados:
                    print(" | ".join(str(item) for item in linha))
            else:
                print("A consulta foi executada com sucesso, mas não retornou resultados.")

            cursor.close()

        except mysql.connector.Error as err:
            print(f"--- ERRO AO EXECUTAR O SQL ---")
            print(f"O SQL gerado pode ser inválido. Erro: {err}")

        finally:
            if conn and conn.is_connected():
                conn.close()
                print("\nConexão com o banco de dados fechada.")