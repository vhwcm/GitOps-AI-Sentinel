import os
import psycopg2
from pgvector.psycopg2 import register_vector
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Configuração
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5435/postgres") # Porta 5435 do Docker

if not api_key:
    raise ValueError("Falta GEMINI_API_KEY no .env")

genai.configure(api_key=api_key)

# 2. Conectar ao Banco
print("🔌 Conectando ao Postgres...")
conn = psycopg2.connect(db_url)
conn.autocommit = True

# Habilita a extensão de vetores no banco
cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
register_vector(conn)

# 3. Criar Tabela
print("🔨 Criando tabela de regras...")
cur.execute("DROP TABLE IF EXISTS company_rules")
cur.execute("""
    CREATE TABLE company_rules (
        id bigserial PRIMARY KEY,
        content text,
        embedding vector(768) 
    )
""")
# Nota: 768 é o tamanho do vetor do modelo 'text-embedding-004' do Google

# 4. Ler e Vetorizar
print("📖 Lendo regras do arquivo...")
with open("company_rules.txt", "r") as f:
    rules = [line.strip() for line in f.readlines() if line.strip()]

print(f"🧠 Gerando embeddings para {len(rules)} regras...")
model = "models/text-embedding-004"

for rule in rules:
    # Chama API do Google para criar o Embedding
    embedding_result = genai.embed_content(
        model=model,
        content=rule,
        task_type="retrieval_document"
    )
    vector = embedding_result['embedding']
    
    # Salva no banco
    cur.execute(
        "INSERT INTO company_rules (content, embedding) VALUES (%s, %s)",
        (rule, vector)
    )
    print(f"   ✅ Regra indexada: {rule[:30]}...")

print("\n🎉 Ingestão concluída com sucesso! O banco agora tem cérebro.")
cur.close()
conn.close()