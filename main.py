import logging
import os
import asyncio
import psycopg2
from pgvector.psycopg2 import register_vector
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import google.generativeai as genai
from github import Github
from langfuse.decorators import observe, langfuse_context

# --- CONFIGURAÇÃO ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")
langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
# URL do Banco (Porta 5435 do Docker local)
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5435/postgres")

if not api_key or not github_token:
    raise ValueError("ERRO: Verifique suas chaves no .env")

genai.configure(api_key=api_key)
# Modelos
CHAT_MODEL = 'models/gemini-2.5-flash'
EMBED_MODEL = 'models/text-embedding-004'

try:
    model = genai.GenerativeModel(CHAT_MODEL)
except:
    model = genai.GenerativeModel('gemini-pro')

git_client = Github(github_token)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gitops-sentinel")

app = FastAPI(title="GitOps AI Sentinel")

# --- FUNÇÃO RAG (NOVIDADE) ---
def get_relevant_rules(query_text: str):
    """Busca regras no Postgres similares ao texto do código."""
    try:
        # 1. Gera embedding da query (o diff do código)
        emb_result = genai.embed_content(
            model=EMBED_MODEL,
            content=query_text[:2000], # Limite para não estourar
            task_type="retrieval_query"
        )
        query_vector = emb_result['embedding']

        # 2. Conecta no banco e busca por similaridade (Operador <->)
        conn = psycopg2.connect(db_url)
        register_vector(conn)
        cur = conn.cursor()
        
        # SQL Mágico: Traz as 3 regras mais próximas (distância cosseno menor)
        cur.execute("""
            SELECT content FROM company_rules 
            ORDER BY embedding <-> %s LIMIT 3
        """, (query_vector,))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        # Retorna lista de strings
        return [row[0] for row in results]
    except Exception as e:
        logger.error(f"Erro no RAG: {e}")
        return []

# --- CHATBOT ---
@observe(as_type="generation")
async def ask_gemini(prompt: str):
    try:
        loop = asyncio.get_running_loop()
        langfuse_context.update_current_observation(model=CHAT_MODEL, input=prompt)
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        langfuse_context.update_current_observation(output=response.text)
        return response.text
    except Exception as e:
        logger.error(f"Erro IA: {e}")
        return "Erro ao processar IA."

@observe()
@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        event_type = request.headers.get("X-GitHub-Event")
        payload = await request.json()
        print("Senha:12345")
        langfuse_context.update_current_trace(name=f"GH: {event_type}")

        if event_type == "push":
            repo_name = payload.get("repository", {}).get("full_name")
            pusher = payload.get("pusher", {}).get("name")
            commit_sha = payload.get("head_commit", {}).get("id")
            
            logger.info(f"🚀 Push de {pusher} em {repo_name}")
            
            repo = git_client.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            diff_text = ""
            for file in commit.files[:2]:
                diff_text += f"\nArq: {file.filename}\nDiff:\n{file.patch}\n"
            
            if not diff_text:
                return {"status": "ignored"}

            # --- RAG EM AÇÃO ---
            logger.info("🔍 Consultando Manual de Regras (RAG)...")
            rules_found = get_relevant_rules(diff_text)
            
            rules_context = ""
            if rules_found:
                rules_str = "\n- ".join(rules_found)
                rules_context = f"\n\n🚨 REGRAS INTERNAS IMPORTANTES:\n- {rules_str}\n(Se o código violar isso, seja implacável.)"
                logger.info(f"📚 Regras aplicadas: {rules_found}")
            # -------------------

            prompt = (
                f"Você é um Tech Lead Sênior e Sarcástico. "
                f"Analise este DIFF de código de '{pusher}'. "
                f"{rules_context}\n\n" # Injeta as regras aqui!
                f"Procure por: más práticas, segurança e violação das regras acima. "
                f"Seja breve.\n\n"
                f"--- CÓDIGO ---\n{diff_text}"
            )
            
            logger.info("🤔 Gerando review...")
            ai_reply = await ask_gemini(prompt)
            
            try:
                commit.create_comment(f"🤖 **Sentinel RAG Review:**\n{ai_reply}")
            except Exception as e:
                logger.error(f"GitHub Error: {e}")
            
        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Erro Geral: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)