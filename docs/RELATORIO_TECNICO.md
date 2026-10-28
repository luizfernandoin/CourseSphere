# Relatório Técnico Consolidado: Avaliação de Segurança e Engenharia de Confiabilidade (AppSec & SRE)

**Plataforma:** CourseSphere — Ambiente de Ensino e Interação  
**Escopo da Análise:** Avaliação Ofensiva, Remediação de Vulnerabilidades, Hardening de Infraestrutura, Observabilidade SRE e Alta Disponibilidade  
**Status da Avaliação:** Concluído com Sucesso — Todas as Vulnerabilidades Remediadas e Validadas  

---

## 1. Sumário Executivo

A plataforma **CourseSphere** passou por uma revisão completa de Segurança da Aplicação (AppSec) e Engenharia de Confiabilidade de Sites (SRE). O objetivo primordial foi identificar vulnerabilidades críticas decorrentes da arquitetura original, eliminar vetores de exploração ofensiva (OWASP Top 10), estruturar mecanismos robustos de contenção e defesa em profundidade (*defense-in-depth*), e estabelecer garantias de confiabilidade operacional por meio de observabilidade em tempo real e alta disponibilidade.

### 1.1 Comparativo da Postura de Segurança e Confiabilidade

| Dimensão | Estado Inicial (Baseline Vulnerável) | Estado Atual (Remediado & Hardened) |
| :--- | :--- | :--- |
| **Controle de Acesso** | Ausente / Permissivo. Qualquer usuário manipulava dados de terceiros (IDOR/BOLA). | Verificação criptográfica de token Bearer via Firebase Admin SDK com checagem estrita de propriedade em nível de aplicação e banco de dados. |
| **Tratamento de Exceções** | `debug=True` ativo, expondo tracebacks completos, caminhos de sistema e versões de dependências em erros HTTP 500. | Modo de depuração desabilitado em produção; interceptadores centrais retornando payloads JSON sanitizados e neutros com rastreamento via `X-Request-ID`. |
| **Integridade de Consultas SQL** | Concatenação direta de strings formatadas (`f-string`) permitindo SQL Injection clássico, tautológico e por UNION. | Consultas 100% parametrizadas com bind variables (`?`), eliminando qualquer possibilidade de injeção de comandos SQL. |
| **Segredo e Credenciais** | Chaves de serviço Firebase em texto puro commitadas no controle de versão (`reddit_key.json`). | Remoção do histórico, expurgo de arquivos confidenciais, adição ao `.gitignore` e disponibilização de template sanitizado (`reddit_key.example.json`). |
| **Ciclo de Vida de Dependências** | Bibliotecas sem versionamento com falhas conhecidas de segurança (CVEs). | Dependências rigorosamente pinadas para releases seguras e auditadas via Pip / Bandit / Safety. |
| **Controle de Origem & Tráfego** | CORS totalmente aberto (`*`), aceitação de credenciais na query string da URL, ausência de rate limiting. | Política restrita de CORS (`ALLOWED_ORIGINS`), tokens aceitos exclusivamente via cabeçalho `Authorization: Bearer`, e rate limiting distribuído com Redis 7. |
| **Observabilidade & SRE** | Logs em texto não estruturado, ausência de métricas e de health checks. | Logs estruturados em formato JSON com correlação de `X-Request-ID`, sondas `/health` e `/ready`, e exportador Prometheus em `/metrics`. |
| **Disponibilidade & Resiliência** | Instância única suscetível a Single Point of Failure (SPOF). | Cluster com réplicas redundantes (`backend-1`, `backend-2`) orquestradas por Load Balancer Nginx com balanceamento *Round-Robin* e *failover* automático. |

---

## 2. Matriz de Vulnerabilidades e Remediações

Todas as vulnerabilidades catalogadas na fase de auditoria e pentest foram reproduzidas através de Provas de Conceito (PoCs) automatizadas, remediadas no código-fonte e submetidas a baterias de testes de regressão automatizados.

### 2.1 Tabela Consolidada de Riscos

| ID | Vulnerabilidade | Classificação OWASP | CVSS v3.1 | Severidade | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **VULN-01** | Broken Access Control / IDOR na Gestão de Chats | API1:2023 - Broken Object Level Authorization | 9.1 | **Crítica** | Remediado |
| **VULN-02** | Exposição de Informações Sensíveis via Debug Mode | A05:2021 - Security Misconfiguration | 7.5 | **Alta** | Remediado |
| **VULN-03** | Injeção de SQL (SQLi) no Catálogo de Cursos | A03:2021 - Injection | 9.8 | **Crítica** | Remediado |
| **VULN-04** | Credenciais Fortes Hardcoded no Repositório | A07:2021 - Identification & Auth Failures | 8.6 | **Alta** | Remediado |
| **VULN-05** | Utilização de Componentes Vulneráveis e Desatualizados | A06:2021 - Vulnerable & Outdated Components | 7.5 | **Alta** | Remediado |
| **VULN-06** | CORS Permissivo e Credenciais em Parâmetro de URL | A01:2021 - Broken Access Control | 6.5 | **Média** | Remediado |

---

### 2.2 Detalhamento Técnico das Remediações

#### VULN-01: Broken Access Control & IDOR
- **Mecanismo Original:** Rotas de manipulação e exclusão de chats (`DELETE /chats/<chat_id>`) não validavam o usuário solicitante contra o proprietário do chat no Firebase Realtime Database.
- **Remediação:** 
  1. Criação do decorador central `@require_auth` em `backend/security/auth.py` com validação de token via `firebase_admin.auth.verify_id_token`.
  2. Implementação de checagem obrigatória de permissão em `Firebase.get_chat(user_id, chat_id)`, garantindo retorno `403 Forbidden` quando o `owner_id != uid`.
  3. Atualização das regras de segurança do Firebase RTDB (`database.rules.json`) restringindo operações estritamente para `auth.uid === $uid`.

#### VULN-02: Debug Mode e Vazamento de Traceback
- **Mecanismo Original:** Servidor Flask instanciado com `app.run(debug=True)`, provocando vazamento de variáveis de ambiente, paths do container e detalhes de drivers em qualquer exceção 500.
- **Remediação:** 
  1. Remoção de `debug=True` no ponto de entrada e substituição por Gunicorn multi-worker em ambiente produtivo.
  2. Registro de interceptadores centrais `@app.errorhandler` em `backend/endpoints.py` para códigos 400, 401, 403, 404, 405, 413, 500 e exceções genéricas.
  3. Mascaramento total de detalhes internos em respostas públicas e registro de rastros em logs auditáveis.

#### VULN-03: Injeção de SQL (SQLi)
- **Mecanismo Original:** A rota `/courses` montava consultas SQLite através de interpolação não tratada: `f"SELECT * FROM courses WHERE name LIKE '%{query}%'"`.
- **Remediação:** 
  1. Refatoração completa de `backend/blueprints/courses.py` e `backend/db.py` para adotar consultas preparadas com parâmetros posicionais:
     ```python
     cursor.execute("SELECT * FROM courses WHERE name LIKE ? OR category LIKE ?", (f"%{query}%", f"%{query}%"))
     ```
  2. O driver do SQLite agora trata caracteres de controle e quebras sintáticas (`' UNION SELECT ... --`) estritamente como literais de string.

#### VULN-04: Credenciais Sensíveis Versionadas
- **Mecanismo Original:** Arquivo `reddit_key.json` contendo chaves de conta de serviço Firebase estava sob versionamento direto no Git.
- **Remediação:**
  1. Exclusão completa do arquivo no repositório (`git rm reddit_key.json`).
  2. Criação de modelo seguro `reddit_key.example.json` contendo apenas placeholders não funcionais.
  3. Inclusão de regras restritivas no `.gitignore` (`*reddit_key.json`, `*.env*`, `*.pem`, `*.key`).

#### VULN-05: Dependências Vulneráveis
- **Mecanismo Original:** `backend/requirements.txt` possuía bibliotecas sem restrição de versão mínima, expondo a aplicação a bugs e CVEs conhecidas.
- **Remediação:**
  1. Posições de dependências fixadas com versões estáveis: `firebase-admin>=6.5.0`, `flask>=3.0.0`, `flask-cors>=4.0.0`, `flask-limiter>=3.5.0`, `redis>=5.0.0`, `prometheus-client>=0.20.0`, `pytest>=8.0.0`.
  2. O pipeline Docker executa instalações limpas com `--no-cache-dir`.

#### VULN-06: Permissividade em CORS e Token via URL
- **Mecanismo Original:** Rota `GET /users/info` aceitava `?token=<jwt>` na URL (expondo-o em logs de servidores proxy e histórico do navegador) e CORS configurado com wildcard `*`.
- **Remediação:**
  1. Configuração de CORS restrito apontando para os domínios homologados da aplicação (`ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"`).
  2. Remoção do suporte a tokens em query strings: extração obrigatória via cabeçalho `Authorization: Bearer <token>`.

---

## 3. Controles Adicionais de Hardening

Além da correção pontual das falhas apontadas, foram erguidos múltiplos anéis de segurança:

1. **Rate Limiting Distribuído (Anti-Brute Force / Anti-DoS):**
   - Implementado via `Flask-Limiter` com backend centralizado no Redis 7.
   - Algoritmo de identificação inteligente (`get_client_identifier`): prioriza UID autenticado (`g.uid`), recorrendo ao IP real do cliente (`X-Forwarded-For`) ou `remote_addr`.
   - Limites definidos: `200 per day`, `50 per hour` globais; rotas de autenticação e busca protegidas com quotas mais rigorosas (`10 per minute`).
2. **Proteção Contra Payloads Excessivos (Memory Exhaustion / DoS):**
   - Configurado `MAX_CONTENT_LENGTH = 1 * 1024 * 1024` (1MB).
   - Rejeição imediata com HTTP `413 Request Entity Too Large` para payloads anômalos.
3. **Cabeçalhos de Segurança HTTP (OWASP Secure Headers):**
   - Aplicados em duas camadas: via middleware Flask (`backend/middleware/security_headers.py`) e no proxy reverso (`infra/nginx/nginx.conf`).
   - `Content-Security-Policy: default-src 'self' ...`
   - `X-Frame-Options: DENY` (Mitigação de Clickjacking)
   - `X-Content-Type-Options: nosniff` (Prevenção de MIME Sniffing)
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: geolocation=(), camera=(), microphone=()`

---

## 4. Engenharia de Confiabilidade (SRE) e Observabilidade

A infraestrutura foi enriquecida com os quatro pilares de confiabilidade do Google SRE:

1. **Rastreamento Distribuído (Distributed Tracing):**
   - Middleware `backend/middleware/logging.py` injeta um `X-Request-ID` único em toda requisição caso não fornecido pelo cliente.
   - Logs no formato estruturado JSON com os campos: `timestamp`, `level`, `request_id`, `method`, `path`, `status_code`, `latency_ms`, `client_ip`, `instance_id`.
2. **Health Checks e Sondas de Orquestração:**
   - `/health`: *Liveness Probe* imediata para confirmação de que o processo Python/Gunicorn está responsivo.
   - `/ready`: *Readiness Probe* profunda que avalia conectividade com SQLite, Redis e Firebase. Retorna 200 (UP) ou 503 (DOWN).
3. **Métricas Operacionais (Prometheus):**
   - Endpoint `/metrics` exporta contadores e histogramas:
     - `http_requests_total`: volume particionado por método, status e endpoint.
     - `http_request_duration_seconds`: histograma de latência de resposta.
     - `http_requests_in_flight`: saturação instantânea de concorrência.
     - `dependency_up`: saúde individual das dependências críticas.
4. **Governança de SLI, SLO e Error Budget:**
   - Documentado integralmente em `docs/SRE_OBSERVABILIDADE.md`.
   - SLO de Disponibilidade: 99.5% de requisições válidas com status < 500 no período móvel de 30 dias.
   - SLO de Latência: 95% das requisições processadas em menos de 250ms.

---

## 5. Alta Disponibilidade e Balanceamento de Carga

Para garantir a operação contínua sem pontos únicos de falha:
- **Balanceador de Carga Nginx:** Instanciado na porta 5000 e 8080 distribuindo tráfego para `backend-1:5000` e `backend-2:5000`.
- **Algoritmo Round-Robin:** Alternância sequencial uniforme comprovada por bateria automatizada de testes.
- **Failover Transparente:** Diretiva `proxy_next_upstream` encaminha o tráfego instantaneamente para a réplica saudável caso uma instância sofra instabilidade.

---

## 6. Procedimentos de Reprodução e Auditoria

Consulte o arquivo `README.md` na raiz do projeto para o passo a passo completo de inicialização dos contêiners, execução das Provas de Conceito e bateria de testes automatizados.

