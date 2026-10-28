# Documentação de Decisões de Arquitetura: Ambiente Isolado, Carga de Dados e Containerização (Fase 1)
**Projeto:** CourseSphere — Desafio Técnico AppSec & SRE  
**Data:** 27/10/2026  
**Documento:** `docs/01-ambiente-e-seed.md`  
**Status:** Fase 1 Concluída com Sucesso (100% Validada em Containers)

---

## 1. Visão Geral e Princípios de Engenharia

O edital do desafio técnico e as boas práticas de segurança ofensiva/defensiva impõem uma regra categórica:
> **Regra de Isolamento Estrito:** A aplicação deve ser testada e avaliada em ambiente 100% isolado e reprodutível. Nenhuma credencial ou projeto de terceiros deve ser acessado.

Para atender a esses requisitos sem depender de conexão com serviços em nuvem ou custos com APIs pagas, a Fase 1 arquitetou três pilares fundamentais:
1. **Emulação Local de Identidade e NoSQL:** Firebase Emulator Suite (Auth + Realtime Database).
2. **Persistência Relacional Fictícia e Determinística:** Banco SQLite estruturado para suportar o catálogo de cursos e discussões.
3. **Isolamento de Inteligência Artificial:** Mock/Stub determinístico para chamadas da OpenAI, eliminando falhas de boot por ausência de credenciais.
4. **Containerização Segura (Hardened Containers):** Dockerfiles multi-stage para backend e frontend com execução estrita como usuário não-root (Least Privilege) e headers defensivos.

---

## 2. Emulação do Firebase (Auth & Realtime Database)

### 2.1 Decisões Arquiteturais
- **Tecnologia:** Firebase Emulator Suite oficial rodando em container Docker isolado ([`infra/firebase-emulator/Dockerfile`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/infra/firebase-emulator/Dockerfile)).
- **Portas Padronizadas:**
  - `9099`: Firebase Authentication Emulator (emissão e validação de tokens JWT).
  - `9000`: Firebase Realtime Database Emulator (armazenamento de perfis e chats).
  - `4000`: Emulator Suite UI (interface gráfica para inspeção visual do estado do banco e usuários).
- **Separação de Regras de Segurança (Defesa em Profundidade):**
  - **Base Vulnerável (`database.rules.json`):** Permite leitura e escrita para qualquer usuário autenticado (`auth != null`), simulando a vulnerabilidade real onde um cliente do SDK pode extrair chats e dados de outros usuários.
  - **Base Endurecida (`database.rules.hardened.json`):** Restringe leitura e escrita estritamente ao próprio dono do registro (`auth != null && auth.uid === $uid`).

### 2.2 Seed de Usuários e Conversas (`scripts/seed_firebase_emulator.py`)
Para permitir testes de controle de acesso cruzado (IDOR) e auditoria de perfis, o script cria automaticamente:
- **Alice (`alice@test.local` / `AlicePassword123!`):** Representa o usuário legítimo/vítima (UID: `EJWzlNWcwQfevHPJluyiRAb62S6T`). Possui perfil acadêmico completo e chats de algoritmos e segurança.
- **Bob (`bob@test.local` / `BobPassword123!`):** Representa o segundo estudante / perfil atacante (UID: `VP3eJub8gZnw8A6XSmeK57iv6Vk5`).
- **Helper Dinâmico de Autenticação (`scripts/pocs/auth_helper.py`):** Função reutilizável em Python para obter tokens frescos sob demanda, prevenindo falhas de expiração de token durante suítes de teste demoradas.

---

## 3. Persistência Relacional (SQLite) e Resolução de Inconsistências

### 3.1 Inconsistências Identificadas no Código Original
Durante o reconhecimento da Fase 0 e análise do backend, identificamos falhas na camada de dados relacional:
1. **Inconsistência de Caminho (Typo no Nome da Pasta):**
   - O código em `backend/db.py` definia a conexão como `"cournell-course-sphere-data/roster_reviews.sqlite.db"` (com a letra "u"), enquanto a pasta real do repositório é `cornell-course-sphere-data` (sem "u").
2. **Sensibilidade ao Diretório de Execução:**
   - O caminho relativo dependia de onde o comando era disparado. Executar na raiz (`CourseSphere/`) procurava em um local diferente de executar dentro de `backend/`.
3. **Ausência do Arquivo de Banco Versionado:**
   - O arquivo `.gitignore` continha `*.db*`, fazendo com que o banco nunca fosse versionado. Consequentemente, uma nova instalação clonada quebrava imediatamente em qualquer consulta de cursos.

### 3.2 Solução Implementada (`scripts/seed_sqlite.py`)
Criamos um script idempotente em Python puro que:
1. Cria a estrutura de pastas e popula o banco `roster_reviews.sqlite.db` em todas as variações de caminho necessárias:
   - `backend/cornell-course-sphere-data/`
   - `cournell-course-sphere-data/`
   - `backend/cournell-course-sphere-data/`
2. Cria e normaliza as tabelas exigidas pelo blueprint `courses.py` e scripts do Reddit:
   - `courses`: `id`, `name`, `section_id`, `semester`, `department`, `instructor`.
   - `course_descriptions`: `id`, `course_id`, `description`.
   - `reddit_posts` e `reddit_comments`: suporte às tabelas auxiliares do schema original.
3. Insere 10 cursos acadêmicos reais/fictícios (CS 4820, CS 4410, CS 5430, etc.) e suas respectivas ementas.

---

## 4. Isolamento da OpenAI e Correção de Falha Fatal no Boot

### 4.1 Diagnóstico do Problema Original
O arquivo `backend/endpoints.py` importava `main.py`, que executava no escopo global do módulo a abertura de `config.json` e a chamada remota à OpenAI em tempo de importação. Sem `config.json` e chave paga, a aplicação sofria `FileNotFoundError` e **sequer iniciava**.

### 4.2 Decisões de Refatoração e Stub Implementadas em `backend/main.py`
1. **Resolução Dinâmica e Segura de Configuração:**
   - O caminho de `config.json` e `query_types.json` passou a ser resolvido em relação à localização física do script (`os.path.dirname(os.path.abspath(__file__))`), garantindo funcionamento independente do diretório de onde o Flask é iniciado.
   - Fornecimento de `backend/config.example.json` e fallback automático para variável de ambiente `OPENAI_API_KEY`.
2. **Modo Mock Offline Automático (`is_mock_mode`):**
   - Se a chave informada começar com `sk-mock` ou se a variável `OPENAI_OFFLINE_MOCK=true` estiver ativa, a aplicação opera em modo simulado determinístico, retornando JSON compatível com a inferência esperada sem tocar em nenhuma rede externa.
3. **Proteção do Ponto de Entrada (`if __name__ == '__main__':`):**
   - A execução da chamada de teste foi movida para dentro do guard padrão do Python, garantindo que a importação de funções auxiliares (como `hashFunction`) pelo Flask não dispare requisições nem efeitos colaterais.

---

## 5. Containerização Segura e Hardening (Backend & Frontend)

### 5.1 Backend Dockerfile (`backend/Dockerfile`)
- **Imagem Base:** `python:3.11-slim-bookworm` (Debian minimalista e estável).
- **Princípio do Menor Privilégio (Non-Root User):**
  - Criação de usuário e grupo de sistema dedicados (`appuser:10001` / `appgroup:10001`) sem permissões de superusuário e sem shell de login interativo (`/sbin/nologin`).
  - Troca explícita para `USER appuser` antes da execução.
- **Servidor WSGI de Produção:**
  - Substituição do servidor embutido de desenvolvimento do Flask (`debug=True`) pelo **Gunicorn** (`gunicorn --workers 2 --threads 2 endpoints:app`).
- **Resolução do Parser ASN.1 de Chave Privada:**
  - O `google-auth` e o `cryptography` exigem uma chave RSA PKCS#8 válida de 2048 bits para instanciar as credenciais de serviço local. Foi gerada e configurada uma chave ASN.1 perfeitamente estruturada em `backend/credentials.dummy.json`.
- **Validação de Execução:**
  - Container testado na porta `5000`, respondendo HTTP 200 OK com logs de acesso estruturados.

### 5.2 Frontend Dockerfile (`frontend/Dockerfile`)
- **Arquitetura Multi-Stage Build:**
  - **Stage 1 (Builder):** `node:20-alpine` (Node 20 LTS substituindo a versão obsoleta e vulnerável `node:16-alpine`). Instala dependências e compila os estáticos com Vite (`npx vite build`).
  - **Stage 2 (Runtime):** `nginx:1.27-alpine` servindo apenas o diretório compilado `/usr/share/nginx/html`. Reduz o tamanho final da imagem em mais de 80% e descarta completamente compiladores, código-fonte e `devDependencies`.
- **Roteamento SPA e Headers de Segurança Embutidos:**
  - Configuração customizada do Nginx ([`frontend/nginx.conf`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO\PS\CourseSphere\frontend\nginx.conf)) com fallback `try_files $uri $uri/ /index.html` (evitando erro 404 em rotas do React Router).
  - Injeção imediata de cabeçalhos de segurança HTTP em todas as respostas estáticas:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `Referrer-Policy: strict-origin-when-cross-origin`
- **Execução Não-Privilegiada:** Container opera como usuário `nginx` (`USER nginx`).

---

## 6. Orquestração Unificada (`docker-compose.yml`)

Criado o arquivo [`docker-compose.yml`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/docker-compose.yml) orquestrando a rede privada `coursesphere-net`:
- **`firebase-emulator`:** portas `9099`, `9000`, `4000` (UI).
- **`backend`:** porta `5000`, configurado para apontar para os emuladores internos (`firebase-emulator:9099` e `firebase-emulator:9000`).
- **`frontend`:** porta `3000`, servindo a interface compilada via Nginx.

Comando único para subir todo o ambiente:
```bash
docker compose up --build -d
```
