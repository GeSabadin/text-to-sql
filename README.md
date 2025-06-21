# Text-to-SQL com Gemini

Este projeto transforma perguntas em linguagem natural em consultas SQL e mostra o resultado em uma página web.

## Como rodar

1. Crie o ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Configure o arquivo `.env` com suas credenciais de banco e API.
    ```
    API_KEY=coloque_aqui_sua_api_key
    MYSQL_DB_HOST=localhost
    MYSQL_DB_USER=root
    MYSQL_DB_PASSWORD=sua_senha_de_acesso_mysql
    MYSQL_DB_NAME=seu_banco_(otimizado para employees)

    PG_DB_HOST=localhost
    PG_DB_USER=sabadin
    PG_DB_PASSWORD=sua_senha_postgres
    PG_DB_NAME=seu_banco_(otimizado dvdrental)
    PG_DB_PORT=5432  -porta padrão postgres, verificar se sua instalação é diferente

    ```

4. Inicie o servidor web:
   ```
   python app.py
   ```

5. Acesse [http://localhost:5000](http://localhost:5000) no navegador.

## Estrutura

- `app.py` — Código principal da aplicação Flask.
- `templates/index.html` — Página web.
- `.env.example` — Exemplo de configuração.
- `requirements.txt` — Dependências do projeto.

---

**Dica:** Para usar MySQL ou PostgreSQL, ajuste as variáveis no `.env` conforme seu banco.