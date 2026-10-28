# Relatório de Reconhecimento de Superfície e Auditoria Inicial (Fase 0)
**Projeto:** CourseSphere — Desafio Técnico AppSec & SRE  
**Data:** 27/10/2026  
**Commit de Referência:** `71616a0` (Tag: `baseline-vulneravel`)  
**Status da Fase:** Concluída com Sucesso

---

## 1. Visão Geral da Fase 0

A Fase 0 estabelece a fundação de segurança e controle de versão para todo o ciclo de vida do desafio. As ações executadas contemplaram:
1. Marcação imutável do baseline de código vulnerável original (`baseline-vulneravel`).
2. Varredura e auditoria automatizada de segredos em todo o histórico de commits do repositório (71 commits).
3. Diagnóstico de higiene do repositório, integridade do `.gitignore` e artefatos de lixo versionados.
4. Mapeamento formal da superfície de ataque, fronteiras de confiança, rotas e código latente.

---

## 2. Execução da Linha de Base (Baseline Git)

- **Ação:** Criação da tag Git imutável no commit herdado do upstream (`LambdaAK/CourseSphere`).
- **Comando executado:**
  ```bash
  git tag baseline-vulneravel 71616a0
  ```
- **Finalidade:** Permitir que a banca examinadora e qualquer avaliador retorne ao estado original com `git checkout baseline-vulneravel` e execute as Provas de Conceito (PoCs) ofensivas contra a aplicação vulnerável.

---

## 3. Auditoria de Segredos no Histórico Git (T0.2)

Foi desenvolvido e executado o script de varredura automatizada `scripts/scan_git_history.py` contra todos os 71 commits do repositório. O relatório consolidado foi salvo em `docs/evidencias/sast/git_secrets_audit.json`.

### 3.1 Resumo dos Achados de Segredos

| Severidade | Tipo de Segredo | Localização / Commit | Evidência / Detalhes | Status |
|---|---|---|---|---|
| **ALTA** | Reddit Client Secret & ID | `backend/cornell-course-sphere-data/reddit-data/reddit_key.json` (Commit `c979a1e`) | `client_id: 7rtaqvFp68AC8uOvSIUl_w`<br>`client_secret: pj00TE5ZN4__46HC4QiiwUVO3Kao3w` | **Exposto e ativo no repositório atual** |
| **MÉDIA** | Firebase Web API Key | `frontend/src/firebaseConfig.ts` (Commits `27bc032`, `9202c6d`) | `apiKey: AIzaSyD_i3HIL4SYkf2AEmKWs2dunhq7m1Glbc4` | Exposto no histórico e no código |
| **MÉDIA** | Realtime Database URL de Produção | `backend/firebase.py` (Commits `744564c`, `a11db47`, `dbb289b`, `68e6a44`) | `https://coursesphere-8bd9a-default-rtdb.firebaseio.com` | Hardcoded no backend e no frontend |
| **INFO** | OpenAI API Key | `config.json` | Não encontrada no histórico Git (bloqueada pelo `.gitignore` inicial) | Ausente do Git (correto) |

> ⚠️ **Regra de Segurança Estrita:** Nenhuma credencial encontrada no histórico Git foi ou será utilizada para testes contra projetos de terceiros. Todos os testes devem rodar contra o Firebase Emulator Suite local e com stubs de OpenAI.

---

## 4. Diagnóstico de Higiene e `.gitignore` (T0.3)

### 4.1 Arquivos Inadequados Versionados
Foram identificados artefatos de IDE e sistema operacional rastreados no Git:
- **macOS Metadata:**
  - `.DS_Store` (raiz)
  - `backend/.DS_Store`
  - `backend/cornell-course-sphere-data/.DS_Store`
  - `backend/cornell-course-sphere-data/reddit-data/.DS_Store`
- **JetBrains IDE Metadata:**
  - `.idea/CourseSphere.iml`
  - `.idea/workspace.xml`
  - `.idea/vcs.xml`
  - `.idea/modules.xml`
  - `.idea/misc.xml`
  - `.idea/inspectionProfiles/`

### 4.2 Lacunas no `.gitignore` Atual
O `.gitignore` original possuía apenas 8 linhas. É necessário atualizar para cobrir:
- Credenciais e segredos locais: `credentials.json`, `config.json`, `.env`, `.env.*`, `reddit_key.json`
- Python: `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `*.sqlite`, `*.db`
- Node/Frontend: `node_modules/`, `frontend/dist/`, `frontend/.vite/`
- Logs e relatórios temporários de teste: `*.log`, `.pytest_cache/`, `.coverage`

---

## 5. Mapeamento Formal de Rotas e Superfície de Ataque (T0.4)

### 5.1 Rotas Ativas em `backend/endpoints.py`

| Método | Endpoint | Autenticação / Extração de Usuário | Finalidade | Risco / Vulnerabilidade Identificada |
|---|---|---|---|---|
| `POST` | `/users/create` | Nenhuma | Cria usuário via Firebase Admin SDK | **A07 (Auth Failure):** Sem rate limiting, sem política de complexidade de senha, permite enumeração de e-mails via mensagens de erro. |
| `POST` | `/users/info` | Token no corpo JSON (`data.get("id_token")`) | Atualiza campos de perfil | Inconsistência de autenticação (não usa header Bearer padrão); vulnerável a mass assignment se novos campos forem adicionados sem validação. |
| `GET` | `/users/info` | Token na Query String (`?id_token=...`) | Consulta perfil do usuário | **A02 / A05:** Token JWT exposto na URL (query string vaza em logs de acesso HTTP, proxies e histórico do navegador). |
| `POST` | `/users/query` | Token no corpo JSON (`try_get_user_info`) | Consulta assistida por IA | **A03 / LLM:** Concatenação direta de query não sanitizada em prompt do modelo OpenAI; parse de JSON cego sobre a resposta do modelo; ausência de rate limiting. |
| `POST` | `/hash` | `Authorization: Bearer <token>` | Gera hash de mensagem | **A05:** Inconsistência de implementação; token é verificado mas `uid` é descartado; geração de hash usando Poisson não criptográfico. |
| `POST` | `/chats/<chat_id>/messages` | `Authorization: Bearer <token>` | Salva mensagens em conversa | Salva em `users/{user_id}/chats/{chat_id}/messages`. Falta validação de schema do array `messages`. |
| `DELETE` | `/chats/<chat_id>` | `Authorization: Bearer <token>` | Apaga conversa do usuário | Deleta em `users/{user_id}/chats/{chat_id}`. Falta validação se o `chat_id` realmente existe antes de responder sucesso. |

### 5.2 Configuração do Servidor e Plataforma
- **Modo Debug Habilitado:** `app.run(debug=True)` ao final de `endpoints.py`. Em caso de erro não tratado, expõe o depurador interativo Werkzeug com console PIN, permitindo execução remota de código (RCE).
- **CORS Aberto Globalmente:** `CORS(app)` sem parâmetro de origens aceita requisições cross-origin de qualquer domínio (`*`).
- **Dependência Fatal no Boot:** `endpoints.py` importa `from main import hashFunction`. Por sua vez, `main.py` executa no topo do módulo:
  ```python
  config = json.load(open("./config.json", "r"))
  client = OpenAI(api_key = config['openai_api_key'])
  ```
  Se `config.json` não existir, o backend sequer inicia (`FileNotFoundError`), impedindo o boot da aplicação em ambientes sem IA configurada.

### 5.3 Código Latente: Blueprint de Cursos (`backend/blueprints/courses.py`)

O blueprint está implementado, mas seu registro está comentado na linha 11 de `endpoints.py`:
`#app.register_blueprint(courses_bp)`

A análise estática do blueprint revelou vulnerabilidades críticas caso seja habilitado:
- **Injeção de SQL Direta por f-strings (A03:2021):**
  - Rota `/courses/<string:semester>`: `execute_query(f"SELECT * FROM courses WHERE semester = '{semester}'")`
  - Rota `/courses/<string:department>`: `execute_query(f"SELECT * FROM courses WHERE department = '{department}'")`
  - Rota `/courses/<string:instructor>`: `execute_query(f"SELECT * FROM courses WHERE instructor = '{instructor}'")`
- **Ambiguidade de Roteamento no Flask:** As três rotas utilizam o padrão `/courses/<string:param>`, fazendo com que as duas últimas nunca sejam alcançadas pelo roteador do Flask.

### 5.4 Frontend e Comunicação de Rede
- **URLs Hardcoded:** O arquivo `frontend/src/api.ts` e componentes utilizam URLs fixas como `http://127.0.0.1:5000/...` e rotas fictícias incompletas (ex.: `http://127.0.0.1:5000/theactualbackendlink` em `UserChats.tsx`).
- **Dependência de Node Obsoleta:** O `Dockerfile` do frontend baseia-se em `node:16-alpine` (versão sem suporte ativo e com vulnerabilidades conhecidas).

---

## 6. Diagrama de Fluxo de Dados e Fronteiras de Confiança (DFD)

```mermaid
flowchart TD
    subgraph Untrusted_Zone ["Zona Não Confiável (Internet / Cliente)"]
        Browser["Navegador do Usuário / Atacante"]
    end

    subgraph Trust_Boundary_1 ["Fronteira de Confiança 1: HTTP / API"]
        FlaskAPI["API Flask (endpoints.py) - debug=True - CORS Global"]
    end

    subgraph Trust_Boundary_2 ["Fronteira de Confiança 2: Serviços e Armazenamento"]
        FirebaseAuth["Firebase Authentication (Emulador / Cloud)"]
        FirebaseRTDB["Firebase Realtime Database (users/uid/...)"]
        SQLiteDB["Banco SQLite Local (roster_reviews.sqlite.db)"]
        OpenAIAPI["API Externa OpenAI (gpt-3.5-turbo-instruct)"]
    end

    Browser -- "1. Login / Cadastro (Email/Senha)" --> FirebaseAuth
    FirebaseAuth -- "2. Retorna ID Token JWT" --> Browser
    Browser -- "3. Requisições com Token (Body / Query / Bearer)" --> FlaskAPI
    Browser -. "4. Chamadas Diretas via Firebase Client SDK" .-> FirebaseRTDB

    FlaskAPI -- "5. Validação de Token (verify_id_token)" --> FirebaseAuth
    FlaskAPI -- "6. Admin SDK (ignora database.rules.json)" --> FirebaseRTDB
    FlaskAPI -- "7. Consultas SQL Manuais / f-strings" --> SQLiteDB
    FlaskAPI -- "8. Consultas IA (Prompt Concatenado)" --> OpenAIAPI
```

---

## 7. Próximas Ações Imediatas (Transição para Fase 1)

Com a Fase 0 concluída e documentada, o plano segue para a **Fase 1: Ambiente Local Isolado e Containerização**:
1. Criar `infra/firebase-emulator/` com `firebase.json` e `database.rules.json`.
2. Criar script de mock/seed para inicializar os usuários de teste `alice@test.local` e `bob@test.local`.
3. Criar `backend/Dockerfile` enxuto com usuário non-root e Gunicorn.
4. Ajustar `main.py` para não quebrar no boot caso `config.json` esteja ausente (usar mock offline para OpenAI).

