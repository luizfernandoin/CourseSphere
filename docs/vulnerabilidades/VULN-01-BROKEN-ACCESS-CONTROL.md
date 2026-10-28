# [VULN-01] Controle de Acesso Quebrado e Insegurança em Rotas de Chat

---

## Metadados e Classificação
- **Identificador:** VULN-01
- **Nome da Falha:** Broken Access Control / Insecure Direct Object Reference (IDOR) em Operações de Conversas
- **Categoria OWASP:** A01:2021 — Broken Access Control
- **CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key) / CWE-285 (Improper Authorization)
- **Severidade:** Alta
- **CVSS v3.1 Base Score:** 7.5
- **CVSS v3.1 Vector:** `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N`
- **Componentes Afetados:** `backend/endpoints.py` (linhas 85-104) e `infra/firebase-emulator/database.rules.json`
- **Status de Remediação:** Corrigido

---

## 1. Descrição Técnica e Mecanismo da Falha

A aplicação CourseSphere permite que usuários autenticados realizem operações sobre conversas acadêmicas através das rotas:
- `POST /chats/<chat_id>/messages`
- `DELETE /chats/<chat_id>`

No código original de `backend/endpoints.py`:
```python
@app.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    try:
        id_token = request.headers.get("Authorization").split("Bearer ")[1]
        user_id = Firebase.verify_id_token(id_token).get('uid')
        Firebase.delete_chat(user_id, chat_id)
        return success_response({'message': 'Message deleted successfully'}, 200)
    except Exception as e:
        return error_response(f"Error deleting message: {str(e)}", 400)
```

### Fragilidades Arquiteturais Identificadas:
1. **Ausência de Validação de Existência e Posse Prévia:** A função `Firebase.delete_chat(user_id, chat_id)` invoca `ref.delete()` diretamente no Firebase Realtime Database. Não há checagem prévia para confirmar se o `chat_id` pertence ao usuário ou se existe.
2. **Ausência de Controle de Integridade no Payload:** Em `POST /chats/<chat_id>/messages`, o código aceita um JSON genérico `messages` e itera gravando objetos sem validar estrutura, tamanho, autor original da mensagem ou data de criação.
3. **Regras Permissivas no Realtime Database (`database.rules.json`):**
   Na configuração herdada do baseline, as regras do Firebase Realtime Database estabeleciam:
   ```json
   {
     "rules": {
       ".read": "auth != null",
       ".write": "auth != null"
     }
   }
   ```
   Como o Frontend interage diretamente com o Firebase SDK do cliente (em `frontend/src/firebaseConfig.ts`), qualquer usuário autenticado que obtenha um ID Token JWT válido pode consultar o nó `users/<uid_vitima>/chats` diretamente na API REST ou SDK do Firebase, ignorando completamente o backend Flask.

---

## 2. Pré-requisitos de Exploração
- Estar autenticado no sistema com qualquer conta de usuário comum (ex.: credenciais de `bob@test.local`).
- Conhecer ou enumerar identificadores de conversa (`chat_id`).

---

## 3. Análise de Impacto no Negócio

- **Confidencialidade:** Violação da privacidade de conversas entre estudantes e conselheiros acadêmicos. Usuários podem ler histórico privado e anotações acadêmicas de outros estudantes.
- **Integridade:** Um usuário mal-intencionado pode injetar mensagens arbitrárias no histórico de outro estudante ou forjar respostas de assistente.
- **Disponibilidade:** Exclusão não autorizada de conversas armazenadas, causando perda irrecuperável de histórico.

---

## 4. Análise de Causa Raiz (Root Cause Analysis - RCA)

A falha decorre de duas causas primárias:
1. **Falta de Verificação no Nível de Aplicação:** O backend não adota uma política de autorização baseada em recursos (Resource-Based Authorization). A verificação limita-se a conferir a autenticidade do token JWT (`verify_id_token`), mas não estabelece se o usuário solicitante tem permissão explícita para interagir com o recurso específico (`chat_id`).
2. **Ausência de Defesa em Profundidade no Banco NoSQL:** A camada de persistência não possuía regras de controle de acesso granulares vinculando a leitura e escrita ao identificador de segurança (`auth.uid === $uid`).

---

## 5. Estratégia de Remediação (Planejada para Fase 3)

1. **Implementar Decorator Centralizado de Autorização (`@require_auth`):**
   Criar um middleware no Flask que:
   - Extrai o token do header `Authorization: Bearer <token>`.
   - Valida revogação (`check_revoked=True`).
   - Injeta o objeto de usuário autenticado no contexto da requisição.
2. **Validar Posse do Recurso no Backend:**
   Antes de processar qualquer alteração ou deleção, verificar se o nó `users/{uid}/chats/{chat_id}` existe para aquele `uid`. Caso contrário, retornar `HTTP 403 Forbidden` ou `HTTP 404 Not Found`.
3. **Endurecer as Regras do Firebase Realtime Database (`database.rules.hardened.json`):**
   ```json
   {
     "rules": {
       "users": {
         "$uid": {
           ".read": "auth != null && auth.uid === $uid",
           ".write": "auth != null && auth.uid === $uid"
         }
       }
     }
   }
   ```
4. **Adicionar Teste Automatizado de Regressão em Pytest:**
   Testar formalmente que Alice não consegue deletar nem alterar mensagens de Bob.

---

## 6. Implementação Efetiva da Correção

1. **Decorator `@require_auth` em `backend/security/auth.py`:**
   Implementado middleware centralizado que valida a presença e integridade do header `Authorization: Bearer <token>`, extrai o UID do usuário e anexa ao contexto da requisição (`g.uid`).
2. **Validação de Posse de Recurso em `backend/endpoints.py`:**
   Adicionada verificação prévia através de `Firebase.get_chat(user_id, chat_id)`. Caso o chat não pertença ao usuário autenticado, a requisição é rejeitada com `HTTP 404 Not Found`, impedindo qualquer tentativa de IDOR.
3. **Hardening no Firebase Realtime Database (`infra/firebase-emulator/database.rules.json`):**
   Regras restritas configuradas para permitir leitura e escrita exclusivamente onde `auth.uid === $uid`.

---

## 7. Validação Pós-Correção (Re-teste)

- **Script de Re-teste:** `scripts/pocs/test_vuln01_idor.py`
  - Resultado: **MITIGADA COM SUCESSO**
  - Tentativa de leitura direta no Realtime Database pelo atacante (Bob): `HTTP 401 Permission denied`.
  - Tentativa de deleção via API Backend pelo atacante (Bob): `HTTP 404 {"error": "Chat not found"}`.
- **Suite de Regressão Automatizada (Pytest):**
  - `tests/test_auth_regression.py::test_unauthenticated_request_rejected` -> **PASSED**
  - `tests/test_auth_regression.py::test_malformed_auth_header_rejected` -> **PASSED**
  - `tests/test_auth_regression.py::test_invalid_token_rejected` -> **PASSED**
  - `tests/test_auth_regression.py::test_user_cannot_delete_nonexistent_or_unowned_chat` -> **PASSED**
  - `tests/test_auth_regression.py::test_authorized_user_can_save_and_manage_own_chat` -> **PASSED**


