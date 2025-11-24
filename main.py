import logging
import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import google.generativeai as genai
from github import Github # Importando a lib do GitHub

# --- CONFIGURAÇÃO ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
github_token = os.getenv("GITHUB_TOKEN") # Nova variável

if not api_key or not github_token:
    raise ValueError("ERRO: Configure GEMINI_API_KEY e GITHUB_TOKEN no .env")

# Config IA
genai.configure(api_key=api_key)
MODEL_NAME = 'models/gemini-2.5-flash'
try:
    model = genai.GenerativeModel(MODEL_NAME)
except:
    model = genai.GenerativeModel('gemini-pro')

# Config GitHub
git_client = Github(github_token)

# Config Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gitops-sentinel")

app = FastAPI(title="GitOps AI Sentinel")

@app.get("/health")
async def health_check():
    return {"status": "active"}

async def ask_gemini(prompt: str):
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        return response.text
    except Exception as e:
        logger.error(f"Erro IA: {e}")
        return "Erro ao processar IA."

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        event_type = request.headers.get("X-GitHub-Event")
        payload = await request.json()
        
        if event_type == "push":
            repo_name = payload.get("repository", {}).get("full_name")
            pusher = payload.get("pusher", {}).get("name")
            commit_sha = payload.get("head_commit", {}).get("id") # O ID único do commit
            
            logger.info(f"🚀 Push de {pusher} em {repo_name} (Commit {commit_sha[:7]})")
            
            # 1. Usar a API do GitHub para pegar os arquivos reais modificados
            # Isso roda bloqueante, idealmente seria async, mas para MVP ok.
            repo = git_client.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            
            diff_text = ""
            # Pegamos os primeiros 2 arquivos para não estourar o limite (boas práticas)
            for file in commit.files[:2]:
                diff_text += f"\nArquivo: {file.filename}\nStatus: {file.status}\n"
                diff_text += f"Mudanças:\n{file.patch}\n" # .patch é o diff (+/- linhas)
            
            if not diff_text:
                logger.info("Nenhuma mudança de código detectada (talvez apenas docs/imagens).")
                return {"status": "ignored"}

            # 2. Prompt Técnico (Agora ele vê o código!)
            prompt = (
                f"Você é um Tech Lead Sênior e Sarcástico. "
                f"Analise este DIFF de código feito por '{pusher}'. "
                f"Procure por: más práticas, erros de segurança ou código feio. "
                f"Se estiver tudo ok, faça uma piada sobre como isso vai quebrar na sexta-feira.\n\n"
                f"--- CÓDIGO ---\n{diff_text}"
            )
            
            logger.info("🤔 Analisando o código com Gemini...")
            ai_reply = await ask_gemini(prompt)
            
            logger.info(f"\n{'='*40}\n🤖 CODE REVIEW AUTOMÁTICO:\n{ai_reply}\n{'='*40}")
            
        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Erro: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)