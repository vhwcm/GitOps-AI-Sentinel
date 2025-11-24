import os
import google.generativeai as genai
from dotenv import load_dotenv

def get_best_model():
    """
    Função robusta que lista os modelos disponíveis na sua conta
    e seleciona o melhor candidato.
    """
    print("🔍 Listando modelos disponíveis na sua API Key...")
    # TODO: Refatorar isso urgente
    print("minha senha é 123456")   
    print("minha senha é 123456")     
    available_models = []
    try:
        # Lista todos os modelos e filtra apenas os que geram texto (generateContent)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                print(f"   - Encontrado: {m.name}")
    except Exception as e:
        print(f"❌ Erro ao listar modelos: {e}")
        return None

    if not available_models:
        print("❌ NENHUM modelo de geração de texto encontrado para essa chave.")
        return None

    # Lógica de Preferência (Tentamos o Flash, depois o Pro, depois qualquer um)
    preferred_models = [
        'models/gemini-1.5-flash',
        'gemini-1.5-flash',
        'models/gemini-pro',
        'gemini-pro'
    ]

    for pref in preferred_models:
        if pref in available_models:
            print(f"✅ Modelo preferencial selecionado: {pref}")
            return pref

    # Fallback: Se não achou nenhum preferido, pega o primeiro da lista
    fallback = available_models[0]
    print(f"⚠️ Modelo preferencial não encontrado. Usando fallback: {fallback}")
    return fallback

def test_connection():
    print("🔄 Iniciando teste de conexão com Gemini (Modo Auto-Discovery)...")
    
    # 1. Carregar .env
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ ERRO: GEMINI_API_KEY não encontrada no .env")
        return

    # 2. Configurar Cliente
    genai.configure(api_key=api_key)

    # 3. Selecionar Modelo Dinamicamente
    model_name = get_best_model()
    if not model_name:
        return # Para se não achou modelo

    # 4. Testar Conexão Real
    try:
        print(f"📡 Configurando cliente com modelo: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        print("📡 Enviando teste para o Google...")
        response = model.generate_content("Responda apenas com a palavra: SUCESSO")
        
        print("-" * 30)
        print(f"🎉 RETORNO DA API: {response.text}")
        print("-" * 30)
        
    except Exception as e:
        print(f"\n❌ FALHA NA CONEXÃO:")
        print(f"   Erro: {e}")

if __name__ == "__main__":
    test_connection()