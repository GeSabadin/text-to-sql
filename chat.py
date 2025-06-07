import os
from dotenv import load_dotenv
import google.generativeai as genai

# Carrega o .env e a chave da API
load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    print("Erro: API_KEY não encontrada no arquivo .env")
    exit(1)

# Configura o modelo
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

# Entrada interativa do usuário
mensagem = input("Digite sua pergunta: ")

response = model.generate_content(mensagem)
print("\nResposta do Gemini:\n")
print(response.text.strip())