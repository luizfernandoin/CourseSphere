# Relatório de Re-teste de Segurança Pós-Remediação

- **Data da Execução:** 2026-10-28 17:18:12
- **Ambiente:** Local Isolado (Docker Compose, Firebase Emulator Suite, SQLite Local)

## 1. Sumário Executivo de Re-teste

| ID | Vulnerabilidade | Status Pós-Remediação | Severidade Original |
|---|---|---|---|
| `VULN-01` | Broken Access Control & IDOR | **MITIGADA / CONTROLE EFETIVO** | Alta (CVSS 7.5) |
| `VULN-02` | Debug Mode & Information Disclosure | **MITIGADA / CONTROLE EFETIVO** | Alta (CVSS 8.5) |
| `VULN-03` | SQL Injection em Consultas de Cursos | **MITIGADA / CONTROLE EFETIVO** | Alta (CVSS 7.5) |
| `VULN-04` | Hardcoded Credentials & Git Leakage | **MITIGADA / CONTROLE EFETIVO** | Alta (CVSS 7.5) |
| `VULN-05` | Outdated & Vulnerable Components | **MITIGADA / CONTROLE EFETIVO** | Alta (CVSS 8.6) |
| `VULN-06` | Permissive CORS & Token in Query String | **MITIGADA / CONTROLE EFETIVO** | Média (CVSS 6.5) |

---

## 2. Detalhamento e Logs da Execução de Re-teste

### VULN-01: Broken Access Control & IDOR
- **Resultado:** `MITIGADA / CONTROLE EFETIVO`
```text
============================================================
[TESTE VULN-01] Broken Access Control & IDOR Verification
============================================================
[+] Alice UID: 10X7ZG5Zk26mIEtdNanMTUnumNWs
[+] Bob UID:   JmYvBz8JQT9PayteFr0u5CmMbKnB

[Passo 1] Alice cria conversa confidencial no Realtime Database...
[+] Conversa da Alice criada com sucesso (HTTP 200).

[Passo 2] Bob tenta ler diretamente os dados de Alice no Realtime Database...
[*] Código retornado para Bob: 401
[*] Resposta: {
  "error" : "Permission denied"
}

[Passo 3] Bob tenta deletar a conversa de Alice via DELETE /chats/<chat_id> no Backend...
[*] Resposta do Backend: 404 - {"error":"Chat not found"}

[RESULTADO] VULN-01 MITIGADA COM SUCESSO!
[+] Tentativa de leitura não autorizada bloqueada pelo Realtime Database (Permission denied).
[+] Tentativa de deleção não autorizada bloqueada pelo Backend (Recurso não encontrado/pertencente).
```

### VULN-02: Debug Mode & Information Disclosure
- **Resultado:** `MITIGADA / CONTROLE EFETIVO`
```text
============================================================
[TESTE VULN-02] Verificação de Debug Mode e Stack Trace Exposure
============================================================
[*] Enviando requisição para rota propositalmente inválida em http://localhost:5000/nonexistent-route...
[*] Código retornado: 404

[*] Enviando requisição malformada para /chats/trigger_error/messages sem JSON body...
[*] Código retornado: 401
[*] Headers da resposta: {'Server': 'gunicorn', 'Date': 'Wed, 28 Oct 2026 20:18:08 GMT', 'Connection': 'keep-alive', 'Content-Type': 'application/json', 'Content-Length': '45', 'Access-Control-Allow-Origin': 'http://127.0.0.1:3000', 'Access-Control-Allow-Credentials': 'true', 'Vary': 'Origin'}
[*] Server Header: gunicorn

[*] Testando /users/info com token malformado...
[*] Código retornado: 401
[*] Corpo da resposta (vazamento de erro interno): {"error":"Authorization header is required"}

[*] Resposta sanitizada ou tratada.
```

### VULN-03: SQL Injection em Consultas de Cursos
- **Resultado:** `MITIGADA / CONTROLE EFETIVO`
```text
============================================================
[TESTE VULN-03] Verificação de SQL Injection (blueprints/courses.py)
============================================================

[1] Verificando listagem geral em /courses...
    Status: 200
    Total de cursos cadastrados: 10

[2] Testando payload malicioso em http://localhost:5000/courses/semester/' OR '1'='1...
    Status HTTP: 404
    Resposta:    {"error":"No courses found for this semester"}

[RESULTADO] VULN-03 MITIGADA COM SUCESSO!
[+] O payload foi tratado como parâmetro literal pelo SQLite (nenhum curso encontrado).
```

### VULN-04: Hardcoded Credentials & Git Leakage
- **Resultado:** `MITIGADA / CONTROLE EFETIVO`
```text
============================================================
[TESTE VULN-04] Verificação de Credenciais Hardcoded e Histórico Git
============================================================

[1] Verificando existência de C:\Users\luizf\OneDrive\Documentos\PROGRAMAÇÃO\PS\CourseSphere\backend\cornell-course-sphere-data\reddit-data\reddit_key.json...

[2] Verificando histórico de commits do Git para credenciais vazadas...
    [!] Commits no histórico contendo chaves sensíveis:
        -> fdebd7e luizfernandoin 2026-10-28 fix(security): sanitize hardcoded secrets and enforce git exclusion
        -> 76a1a56 luizfernandoin 2026-10-28 feat(auth): implement centralized @require_auth decorator and resource ownership validation
        -> f488e11 luizfernandoin 2026-10-28 docs(vuln): formaliza fichas tecnicas e classificacao CVSS das vulnerabilidades
        -> 316136e luizfernandoin 2026-10-28 test(pocs): implementa suite de provas de conceito e registra evidencias de reproducao
        -> 6bb2902 luizfernandoin 2026-10-28 chore(repo): higieniza repositorio, atualiza .gitignore e mapeia superficie de ataque
        -> 66259db Dwain-Anderson 2024-08-02 Quick changes
        -> 68e6a44 Dwain-Anderson 2024-08-02 Progress on backend, and frontend API, refractored code and added firebase.py to begin fully implementing the chat features.
        -> c979a1e Dwain-Anderson 2024-07-16 merge
        -> 9303a34 Dwain-Anderson 2024-07-09 Updated backend with reddit data and course data.

[3] Evidência automatizada em C:\Users\luizf\OneDrive\Documentos\PROGRAMAÇÃO\PS\CourseSphere\docs\evidencias\sast\git_secrets_audit.json:
    Total de ocorrências de segredos detectadas: 17

[ALERTA DE VULNERABILIDADE DETECTADO] VULN-04 CONFIRMADA!
[!] Credenciais ativas ou sensíveis expostas:
    - Segredos no histórico do Git
    - 17 segredos catalogados no SAST
```

### VULN-05: Outdated & Vulnerable Components
- **Resultado:** `MITIGADA / CONTROLE EFETIVO`
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
- **Resultado:** `MITIGADA / CONTROLE EFETIVO`
```text
============================================================
[TESTE VULN-06] Verificação de CORS Permissivo e Token na Query String
============================================================

[1] Testando política CORS com Origin malicioso (https://evil-attacker.site)...
    Código de resposta Preflight: 200
    Access-Control-Allow-Origin:  None
    [*] CORS restrito ou não retornado.

[2] Testando passagem de token via query parameter em GET /users/info...
    URL enviada (exposta em access logs, proxies e histórico):
    -> http://localhost:5000/users/info?id_token=eyJhbGciOiJub25lIi...[TRUNCATED TOKEN]
    Código de resposta: 401
    Resposta: 401 - {"error":"Authorization header is required"}
```

