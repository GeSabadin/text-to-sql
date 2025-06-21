# Text-to-SQL com Gemini

Este projeto transforma perguntas em linguagem natural em consultas SQL e mostra o resultado em uma página web. Você pode escolher entre os bancos de dados `employees` (MySQL) e `dvdrental` (PostgreSQL) pela interface web.

## Como rodar localmente

1. **Clone ou extraia o projeto em uma pasta:**
   ```sh
   git clone <url-do-repositorio>
   # ou extraia o .zip na pasta desejada
   ```

2. **Crie e ative um ambiente virtual:**
   ```sh
   python -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure o arquivo `.env`** com suas credenciais de banco e API Gemini.  
   Exemplo:
   ```
   API_KEY=sua_chave_gemini
   MYSQL_DB_HOST=localhost
   MYSQL_DB_USER=seu_usuario_mysql
   MYSQL_DB_PASSWORD=sua_senha_mysql
   MYSQL_DB_NAME=employees(esse é o que funciona melhor pois tem queries de exemplo mas outros devem funcionar também mas a efetividade vai certamente cair)

   PG_DB_HOST=localhost
   PG_DB_USER=seu_usuario_postgres
   PG_DB_PASSWORD=sua_senha_postgres
   PG_DB_NAME=dvdrental(esse é o que funciona melhor pois tem queries de exemplo mas outros devem funcionar também mas a efetividade vai certamente cair)
   ```

5. **Inicie o agente online:**
   ```sh
   python app.py
   ```

   5.1 **Inicie o agente offline:**
   ```sh
   python caht.py
   ```

6. **Acesse no navegador:**  
   [http://localhost:5000](http://localhost:5000)

## Observações

- Para usar MySQL ou PostgreSQL, basta selecionar o banco desejado na interface web.
- Certifique-se de que os bancos de dados `employees` (MySQL) e/ou `dvdrental` (PostgreSQL) estejam criados e acessíveis.