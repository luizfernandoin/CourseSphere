# [VULN-XX] Título Descritivo da Vulnerabilidade

---

## Metadados e Classificação
- **Identificador:** VULN-XX
- **Nome da Falha:** (ex.: Insecure Direct Object Reference em Deleção de Conversas)
- **Categoria OWASP:** A01:2021 — Broken Access Control
- **CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)
- **Severidade:** Alta | Média | Baixa | Crítica
- **CVSS v3.1 Base Score:** 8.1
- **CVSS v3.1 Vector:** `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:H`
- **Componente Afetado:** `backend/endpoints.py` (função `delete_chat`)
- **Status de Remediação:** Corrigido | Mitigado | Aceito

---

## 1. Descrição Técnica e Vetor de Ataque
Explicação objetiva de como a falha funciona, qual é o mecanismo inseguro no código e sob quais circunstâncias a vulnerabilidade pode ser explorada.

## 2. Pré-requisitos de Exploração
- Nível de autenticação necessário (ex.: usuário comum autenticado).
- Parâmetros ou tokens pré-requisito (ex.: identificador de conversa alvo `chat_id`).

## 3. Passo a Passo de Reprodução (Proof of Concept - PoC)
Comandos exatos e reprodutíveis via linha de comando (`curl` ou script Python):

### Passo 1: Autenticar como atacante e obter token
```bash
curl -X POST http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-key \
  -H "Content-Type: application/json" \
  -d '{"email":"bob@test.local","password":"password123","returnSecureToken":true}'
```

### Passo 2: Executar a requisição maliciosa contra o recurso da vítima
```bash
curl -i -X DELETE http://localhost:8080/chats/chat_alice_123 \
  -H "Authorization: Bearer <TOKEN_DE_BOB>"
```

### Evidência do Comportamento Vulnerável (HTTP Response):
```http
HTTP/1.1 200 OK
Content-Type: application/json

{"status": "success", "message": "Chat deleted"}
```

## 4. Impacto no Negócio
- **Confidencialidade:** Detalhar eventuais vazamentos de dados pessoais ou acadêmicos.
- **Integridade:** Alteração não autorizada de registros ou dados de outros usuários.
- **Disponibilidade:** Destruição ou indisponibilização de recursos sem possibilidade de recuperação.

## 5. Análise de Causa Raiz (Root Cause Analysis - RCA)
Identificação técnica exata da origem da vulnerabilidade:
- Por que o código permitiu a falha (ex.: falta de verificação de propriedade no banco de dados antes da exclusão).

## 6. Correção Aplicada (Remediação)
- **Commit:** `fix(VULN-XX): valida propriedade do recurso antes de processar operação`
- **Pull Request:** #X
- **Explicação da Solução:** Explicação detalhada de por que a alteração elimina a causa raiz e não apenas mascara o sintoma.

```python
# Trecho de código demonstrando a lógica segura implementada
```

## 7. Validação Pós-Correção (Re-teste)
Execução do mesmo payload contra a branch corrigida demonstrando bloqueio:
```http
HTTP/1.1 403 FORBIDDEN
Content-Type: application/json

{"error": "Acesso negado: o recurso não pertence ao usuário solicitante"}
```
- **Teste Automatizado de Regressão:** `backend/tests/test_auth_regression.py::test_user_cannot_delete_other_user_chat` (Status: PASS).

## 8. Recomendações Adicionais e Hardening
- Práticas de defesa em profundidade complementares (ex.: regras no Realtime Database, rate limit, logging de eventos suspeitos).

