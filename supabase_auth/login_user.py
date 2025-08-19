from supabase import create_client
from dotenv import load_dotenv
import os

# Carrega variáveis do .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMAIL = os.getenv("SUPABASE_EMAIL")
PASSWORD = os.getenv("SUPABASE_PASSWORD")

# Cria o cliente
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # Faz login
    response = supabase.auth.sign_in_with_password({
        "email": EMAIL,
        "password": PASSWORD
    })

    # Extrai token
    access_token = response.session.access_token
    print("Access Token:", access_token)

    # Testa o token fazendo uma query na tabela conversations
    print("\nTestando query na tabela conversations:")
    result = supabase.table("conversations").select("*").execute()
    print("Dados:", result.data)

except Exception as e:
    print("Erro:", str(e))
    exit()
