# Relatório Técnico (AppSec e SRE)

**Plataforma:** CourseSphere  
**Alvo:** Backend Flask, Frontend React, Emulador Firebase, Cache Redis e Banco SQLite  
**Status:** Todas as vulnerabilidades remediadas, validadas e aprovadas em suíte automatizada.

---

## 1. Sumário Executivo

A avaliação de segurança da aplicação (**AppSec**) e engenharia de confiabilidade (**SRE**) na plataforma **CourseSphere** identificou seis vulnerabilidades reais de severidades crítica, alta e média. As falhas permitiam manipulação não autorizada de dados de terceiros (IDOR), injeção de comandos SQL (SQLi), vazamento de credenciais no repositório, execução de depurador interativo via modo debug, permissividade em políticas de CORS e exposição de tokens.

Todas as falhas foram reproduzidas localmente por Provas de Conceito (PoCs) e solucionadas na causa raiz. Adicionalmente, foram erguidos controles defensivos (rate limiting distribuído, headers OWASP e validação de esquemas), observabilidade completa com logs estruturados em JSON e métricas Prometheus, e escalabilidade horizontal com proxy Nginx em regime round-robin.

### Comparativo da Postura de Segurança e Operação

| Dimensão | Estado Inicial (Vulnerável) | Estado Atual (Remediado) |
| :--- | :--- | :--- |
| **Controle de Acesso** | Ausente; qualquer usuário alterava ou apagava chats alheios. | Decorador `@require_auth` e validação estrita de dono no Firebase RTDB. |
| **Integridade SQL** | Concatenação direta de strings permitindo SQLi e dump da base. | 100% das consultas parametrizadas com bind variables (`?`). |
| **Tratamento de Erros** | `debug=True` expondo caminhos internos e traceback em erro 500. | Debug desativado; respostas JSON neutras com correlation ID (`X-Request-ID`). |
| **Gestão de Segredos** | Chaves de serviço Firebase commitadas no histórico (`reddit_key.json`). | Segredos expurgados, `.gitignore` reforçado e modelos sanitizados. |
| **Tráfego & Origem** | CORS irrestrito (`*`) e token aceito na query string da URL. | CORS limitado a origens confiáveis e tokens aceitos apenas no header Bearer. |
| **Resiliência e Carga** | Instância única (SPOF) sem limites de taxa ou payload. | Cluster com 2 instâncias, Load Balancer Nginx e rate limiting com Redis 7. |
| **Observabilidade** | Logs em texto sem padrão, sem health checks ou métricas. | Logs JSON, correlation IDs, sondas `/health`, `/ready` e `/metrics`. |

---

## 2. Escopo e Metodologia

### 2.1 Escopo da Avaliação
- **Endpoints da API:** `/users/create`, `/users/info`, `/users/query`, `/chats/<chat_id>`, `/chats/<chat_id>/messages`, `/courses`, `/hash`.
- **Bancos e Serviços:** Firebase Realtime Database (regras de segurança), SQLite e Redis 7.
- **Ambiente de Testes:** 100% isolado localmente via Docker Compose e Firebase Emulator Suite, sem envio de dados ou credenciais para a nuvem.

### 2.2 Metodologia
A avaliação seguiu o padrão OWASP Top 10 e OWASP API Security Top 10, dividida em quatro etapas:
1. **Auditoria Estática (SAST & SCA):** Varredura de código com Bandit, auditoria de segredos com script dedicado no histórico Git e análise de dependências com pip-audit e npm-audit.
2. **Exploração Dinâmica (DAST / Pentest Manual):** Criação de PoCs automatizadas em Python com dois perfis de teste (Alice e Bob) simulando ataques reais.
3. **Remediação na Causa Raiz:** Correção de código, alteração de regras de infraestrutura e refatoração arquitetural.
4. **Verificação Automatizada de Regressão:** Bateria de testes em Pytest e re-execução das PoCs contra a aplicação corrigida.

---

## 3. Matriz de Vulnerabilidades

| ID | Classificação OWASP | CVSS v3.1 | Severidade | Impacto no Negócio |
| :--- | :--- | :---: | :---: | :--- |
| **VULN-01** | API1:2023 - Broken Object Level Authorization | 9.1 | **Crítica** | Violação de privacidade; exclusão de conversas confidenciais de terceiros. |
| **VULN-02** | A05:2021 - Security Misconfiguration | 7.5 | **Alta** | Vazamento de arquivos internos e potencial RCE pelo console Werkzeug. |
| **VULN-03** | A03:2021 - Injection (SQL Injection) | 9.8 | **Crítica** | Extração de dados da base acadêmica e evasão de filtros de catálogo. |
| **VULN-04** | A07:2021 - Identification & Auth Failures | 8.6 | **Alta** | Comprometimento de credenciais de serviço e abuso de quotas em APIs. |
| **VULN-05** | A06:2021 - Vulnerable & Outdated Components | 7.5 | **Alta** | Exposição a falhas conhecidas (CVEs) em pacotes desatualizados. |
| **VULN-06** | A01:2021 - Broken Access Control | 6.5 | **Média** | Roubo de sessão via logs de proxy e requisições cross-origin não autorizadas. |

---

## 4. Correções e Causa Raiz

### VULN-01: Broken Access Control / IDOR
- **Causa Raiz:** A rota `DELETE /chats/<chat_id>` e as operações de mensagem não validavam se o `chat_id` pertencia ao usuário autenticado, e as regras do Firebase RTDB estavam ausentes.
- **Solução Definitiva:**
  - Implementado o decorador `@require_auth` em `backend/security/auth.py`.
  - Checagem prévia de propriedade no banco antes de exclusões (`Firebase.get_chat(user_id, chat_id)`).
  - Regras em `database.rules.json` restringindo leitura e escrita para `auth.uid === $uid`.

### VULN-02: Modo Debug e Exposição de Informações
- **Causa Raiz:** Ponto de entrada rodando com `app.run(debug=True)` sem interceptadores globais de erro.
- **Solução Definitiva:**
  - Desativação do modo de depuração em produção e adoção do servidor Gunicorn.
  - Handlers centralizados `@app.errorhandler` para 400, 401, 403, 404, 405, 413, 500 em `backend/endpoints.py`.
  - Respostas com mensagens genéricas e correlação por `X-Request-ID`.

### VULN-03: Injeção de SQL (SQLi)
- **Causa Raiz:** O arquivo `backend/blueprints/courses.py` concatenava variáveis diretamente na consulta via f-strings: `f"WHERE semester LIKE '%{semester}%'"`.
- **Solução Definitiva:**
  - Substituição por consultas parametrizadas com `?` em `courses.py` e `backend/db.py`.
  - Caracteres maliciosos (`' OR '1'='1`) passam a ser interpretados estritamente como literais de string.

### VULN-04: Credenciais Sensíveis Versionadas
- **Causa Raiz:** Arquivo `reddit_key.json` commitado no histórico de versões.
- **Solução Definitiva:**
  - Remoção do rastreamento do Git (`git rm`).
  - Criação do modelo público `reddit_key.example.json` sem valores reais.
  - Regras de bloqueio adicionadas ao `.gitignore` (`*reddit_key.json`, `*.env*`, `*.pem`).

### VULN-05: Dependências Vulneráveis
- **Causa Raiz:** `backend/requirements.txt` sem fixação de versões mínimas.
- **Solução Definitiva:**
  - Dependências pinadas com versões seguras e auditadas via pip-audit e npm-audit.
  - Pipeline Docker construído com instalações limpas (`--no-cache-dir`).

### VULN-06: Permissividade em CORS e Token na URL
- **Causa Raiz:** `CORS(app)` global aberto (`*`) e rota `GET /users/info` aceitando token via parâmetro de busca na URL (`?id_token=...`).
- **Solução Definitiva:**
  - CORS configurado com lista explícita de origens permitidas (`ALLOWED_ORIGINS`).
  - Remoção de suporte a token na query string: credenciais aceitas apenas no cabeçalho `Authorization: Bearer`.

---

## 5. Hardening

Além das correções, foram adicionados controles de defesa em profundidade:
1. **Rate Limiting Distribuído:** Integrado ao Redis 7 via `Flask-Limiter` com chaveamento contextual (`g.uid` -> `X-Forwarded-For` -> `remote_addr`). Limitações globais e cotas restritas para criação de contas (10 req/min).
2. **Limite de Tamanho de Requisições:** Bloqueio imediato com HTTP 413 para payloads acima de 1MB (`MAX_CONTENT_LENGTH`).
3. **Cabeçalhos OWASP:** Injeção sistemática de `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` e `Referrer-Policy`.
4. **Validação de Schemas:** Validação de formato de e-mail, complexidade de senhas e sanitização de payloads JSON em `backend/security/validation.py`.

---

## 6. Confiabilidade e Observabilidade (SRE)

### 6.1 Indicadores de Nível de Serviço (SLIs) e Objetivos (SLOs)
- **SLI 1 — Disponibilidade da API:** Proporção de requisições concluídas com código HTTP < 500 sobre o total de requisições válidas.
  - **SLO Proposto:** $\ge 99.5\%$ no período de 30 dias.
  - **Error Budget:** $0.5\%$ de indisponibilidade permitida (~3,6 horas por mês).
- **SLI 2 — Latência de Requisições:** Tempo de resposta do servidor medido no Load Balancer.
  - **SLO Proposto:** $95\%$ das requisições processadas em $\le 250\text{ms}$ (P95).
  - **Error Budget:** $5\%$ de requisições excedentes.

### 6.2 Sondas e Métricas
- `GET /health`: Sonda de vivacidade (*liveness*) para validação do processo da aplicação.
- `GET /ready`: Sonda de prontidão (*readiness*) profunda, testando conexões com SQLite, Redis e Firebase.
- `GET /metrics`: Exportador Prometheus nativo (`http_requests_total`, `http_request_duration_seconds`, `http_requests_in_flight`, `dependency_up`).
- **Tracing Distribuído:** Cabeçalho `X-Request-ID` propagado entre proxy, aplicação e logs estruturados em JSON.
- **Dashboard Grafana:** Painel pronto para importação disponibilizado em `infra/grafana/coursesphere-dashboard.json`.

---

## 7. Riscos de Disponibilidade e Resiliência

### 7.1 Riscos Arquiteturais Identificados
1. **Ponto Único de Falha (SPOF):** Originalmente, a aplicação rodava em uma única instância. Falhas de processo ou reinicializações derrubavam 100% do serviço.
2. **Exaustão de Memória por DoS:** Ausência de limite de payload permitia requisições gigantescas, consumindo recursos do worker.
3. **Saturação de Conexões de Banco:** Conexões SQLite concorrentes não controladas podiam gerar travamentos (*database is locked*).

### 7.2 Recomendações e Mitigações Implementadas
- **Cluster com Load Balancer:** Duas réplicas ativas (`backend-1` e `backend-2`) atrás do Nginx com balanceamento round-robin e failover automático (`proxy_next_upstream`).
- **Controle de Saturação:** Rate limiting distribuído no Redis e limite de 1MB por payload.
- **Desacoplamento de Estado:** Sessões stateless via JWT; tokens e limites compartilhados sem dependência de memória local da instância.

---

## 8. Recomendações Priorizadas

| Prioridade | Ação | Justificativa | Status |
| :---: | :--- | :--- | :---: |
| **P1 (Imediata)** | Parametrizar consultas SQL e aplicar controle de acesso em chats | Elimina risco de exfiltração de dados e violação de privacidade de estudantes. | Concluído |
| **P1 (Imediata)** | Desabilitar `debug=True` e expurgar chaves do repositório | Impede execução remota de código (RCE) e uso não autorizado de credenciais. | Concluído |
| **P2 (Curto Prazo)** | Implementar Rate Limiting distribuído e limite de payload | Protege a infraestrutura contra ataques de negação de serviço e força bruta. | Concluído |
| **P2 (Curto Prazo)** | Instrumentar sondas de health check e métricas Prometheus | Garante visibilidade da saúde dos nós e acionamento de auto-healing pelo orquestrador. | Concluído |
| **P3 (Médio Prazo)** | Integrar análise estática contínua na esteira de CI/CD | Previne que novos commits reintroduzam falhas ou dependências vulneráveis. | Concluído |

---

## 9. Evidências e Auditoria

Todas as evidências brutas e relatórios complementares estão disponíveis no repositório:
- **Testes de Regressão Automatizados:** Executáveis via `docker exec coursesphere-backend-1 pytest tests/ -v` (22/22 aprovados).
- **Relatório de Re-teste Ofensivo:** [`docs/evidencias/RELATORIO_EXECUCAO_RETESTE.md`](evidencias/RELATORIO_EXECUCAO_RETESTE.md).
- **Evidência de Balanceamento Nginx:** [`docs/evidencias/balanceamento/nginx-round-robin.log`](evidencias/balanceamento/nginx-round-robin.log).
- **Varredura SAST (Bandit):** [`docs/evidencias/sast/bandit.json`](evidencias/sast/bandit.json).
- **Auditoria de Dependências (SCA):** [`docs/evidencias/sca/pip-audit.json`](evidencias/sca/pip-audit.json) e [`docs/evidencias/sca/npm-audit.json`](evidencias/sca/npm-audit.json).
- **Modelagem de Ameaças STRIDE & DFD:** [`docs/threat-model.md`](threat-model.md).
