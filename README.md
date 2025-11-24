# 🛡️ GitOps AI Sentinel

Um Agente Autônomo de LLMOps que integra Inteligência Artificial Generativa diretamente ao ciclo de CI/CD.

## 📖 Sobre o Projeto

O GitOps AI Sentinel resolve o gargalo de Code Reviews manuais e tarefas repetitivas de localização (i18n). Ele atua como um "Engenheiro de DevOps Sênior" (com uma personalidade sarcástica configurável) que vive dentro do seu repositório.

Diferente de bots simples, este projeto implementa uma arquitetura robusta de LLMOps, focando em:

- **Observabilidade**: Rastreamento de custos, latência e qualidade de cada interação via Langfuse.
- **Contexto (RAG)**: Capacidade de validar código contra regras internas da empresa (Compliance).
- **Segurança**: Prevenção de vazamento de segredos em prompts.

## 🏗️ Arquitetura do Sistema

O sistema segue uma arquitetura orientada a eventos (Event-Driven), reagindo a Webhooks do GitHub em tempo real.

graph LR
User((Dev)) -->|Git Push| GitHub
GitHub -->|Webhook JSON| Sentinel[⚡ FastAPI Server]

```
subgraph "GitOps Sentinel Core"
    Sentinel -->|Async Task| AI_Orchestrator
    AI_Orchestrator -->|Get Context| VectorDB[(🐘 Postgres/pgvector)]
    AI_Orchestrator -->|Trace| Langfuse[🔍 Langfuse Ops]
    AI_Orchestrator -->|Inference| Gemini[🧠 Google Gemini 1.5]
end

Gemini -->|Review/Code| AI_Orchestrator
AI_Orchestrator -->|Post Comment| GitHub
```

## 🚀 Funcionalidades Principais

### 1. 🧐 Sarcastic Code Reviewer

Analisa o diff de cada Pull Request ou Push.

**Capacidade:** Identifica más práticas (ex: `print()` em produção), erros de segurança e complexidade ciclomática.

**Persona:** Configurável para atuar como um "Tech Lead Rabugento", tornando os reviews mais engajadores.

### 2. 🛡️ Compliance Guardrails (RAG)

**Feature de Destaque de Engenharia**

Utiliza RAG (Retrieval-Augmented Generation) para garantir que o código siga as normas da empresa.

**Como funciona:** O sistema indexa o manual de engenharia da empresa (ex: `CONTRIBUTING.md`) em um banco vetorial (pgvector).

**Aplicação:** Antes de revisar o código, o bot busca regras relevantes (ex: "Sempre use Logger ao invés de System.out"). Isso reduz alucinações e garante conformidade.

### 3. 🌍 Polyglot Translator (i18n)

Detecta alterações em arquivos de tradução (`.json`, `.properties`) e gera automaticamente as versões para outros idiomas (PT-BR, ES, EN), abrindo um PR automático com as correções.

## 🛠️ Tech Stack & Decisões de Engenharia

| Componente          | Tecnologia              | Justificativa Técnica                                              |
| ------------------- | ----------------------- | ------------------------------------------------------------------ |
| **Linguagem**       | Python 3.11+            | Ecossistema nativo de IA e bibliotecas robustas de Data Science.   |
| **API Framework**   | FastAPI                 | Suporte nativo a async/await e validação Pydantic.                 |
| **LLM Provider**    | Google Gemini 2.5 Flash | Janela de contexto massiva (1M tokens) com baixo custo e latência. |
| **Database**        | PostgreSQL + pgvector   | Dados relacionais + vetoriais em uma solução única.                |
| **Observabilidade** | Langfuse                | Traces, custos por token e datasets de avaliação.                  |
| **Container**       | Docker Compose          | Orquestração simples para dev e prod.                              |

## ⚡ Como Rodar Localmente

### Pré-requisitos

- Docker & Docker Compose
- Python 3.11+ & Poetry
- Conta no Google AI Studio (API Key) & GitHub

### 1. Clonar e Instalar

```bash
git clone https://github.com/seu-usuario/gitops-ai-sentinel.git
cd gitops-ai-sentinel
poetry install
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz baseado no exemplo:

```
GEMINI_API_KEY=sua_chave_aqui
GITHUB_TOKEN=seu_token_github
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

### 3. Subir a Infraestrutura (Docker)

Inicia o Banco de Dados e o Dashboard de Observabilidade.

```bash
sudo docker compose up -d
```

### 4. Iniciar o Agente

```bash
poetry run python main.py
```

### 5. Expor para a Internet

Para receber Webhooks do GitHub, use o Ngrok:

```bash
ngrok http 8000
```

Configure a URL gerada (`https://.../webhook`) no repositório do GitHub.

## 📊 LLMOps: Monitoramento e Custos

Este projeto leva a sério a engenharia financeira (FinOps) e performance.

Exemplo do que é monitorado no Langfuse:

- **Trace Latency**: Tempo entre o Webhook e o comentário no PR.
- **Token Usage**: Custo preciso por análise.
- **Quality Gate**: Score da utilidade da resposta da IA.

## 🔮 Próximos Passos (Roadmap)

- [ ] Implementar sistema de cache (Redis) para evitar re-analisar commits inalterados.
- [ ] Adicionar testes de avaliação automatizados (DeepEval) no pipeline de CI.
- [ ] Suporte a análise de imagens (Multimodal) para revisar capturas de tela de UI em PRs.

---

Made with ☕ and 🐍 by **Seu Nome**
