# [VULN-06] CORS Irrestrito Global e Trânsito Inseguro de Token JWT via Query String

---

## Metadados e Classificação
- **Identificador:** VULN-06
- **Nome da Falha:** Configuração Permissiva de CORS e Exposição de Token de Autenticação em Parâmetros de URL
- **Categoria OWASP:** A05:2021 — Security Misconfiguration / A02:2021 — Cryptographic Failures
- **CWE:** CWE-942 (Permissive Cross-Domain Policy with Untrusted Domains) / CWE-598 (Use of GET Request Method With Sensitive Query Strings)
- **Severidade:** Média
- **CVSS v3.1 Base Score:** 6.5
- **CVSS v3.1 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N`
- **Componentes Afetados:** `backend/endpoints.py` (linhas 8 e 55-63)
- **Status de Remediação:** Corrigido

---

## 1. Descrição Técnica e Mecanismo da Falha

Identificamos duas falhas combinadas de configuração de segurança e trânsito de credenciais no backend:

### 1.1 CORS Aberto Globalmente (`endpoints.py:8`)
```python
app = Flask(__name__)
CORS(app)
```
A invocação de `CORS(app)` sem o parâmetro `origins` configura a política de cabeçalhos de resposta para refletir ou autorizar qualquer origem:
```http
Access-Control-Allow-Origin: *
```
Isso permite que qualquer domínio externo malicioso execute requisições AJAX/Fetch contra a API do CourseSphere no navegador de um usuário legítimo.

### 1.2 Transmissão de Token JWT na URL via GET (`endpoints.py:55-63`)
```python
@app.route("/users/info", methods=["GET"])
def get_user_info(id_token=None):
    try:
        id_token = id_token if id_token is not None else request.args.get("id_token")
        uid = Firebase.verify_id_token(id_token).get('uid')
        user_info = Firebase.get_user_info(uid)
        return success_response(user_info, 200)
    except Exception as e:
        return error_response(f"Error getting user info: {str(e)}", 400)
```
A rota `/users/info` aceita o token de autenticação JWT através da Query String da URL (`?id_token=...`).

### Vetor de Risco:
Tokens de autenticação transmitidos na URL:
1. **Ficam Registrados em Logs de Servidor:** Logs de acesso do Nginx, Apache ou proxies reversos registram a URL completa, gravando credenciais de usuários em texto plano no disco.
2. **Histórico do Navegador:** O token JWT completo fica salvo no histórico de navegação do dispositivo do usuário.
3. **Vazamento por Cabeçalho Referer:** Se a página carregar recursos de terceiros (como CDNs ou imagens externas), a URL completa (incluindo o token) pode ser repassada no cabeçalho `Referer`.

---

## 2. Pré-requisitos de Exploração
- O usuário deve navegar em páginas que acionem o endpoint via GET ou ter seu tráfego registrado por logs/proxies intermediários.

---

## 3. Análise de Impacto no Negócio

- **Confidencialidade:** Vazamento de credenciais de sessão (JWT com validade de 1 hora), permitindo que intermediários ou operadores com acesso a logs de acesso personifiquem o usuário.
- **Conformidade:** Violação direta das recomendações OWASP e RFC 6750 (The OAuth 2.0 Authorization Framework: Bearer Token Usage), que proíbem explicitamente o uso de tokens em query strings de requisições GET para recursos sensíveis.

---

## 4. Análise de Causa Raiz (Root Cause Analysis - RCA)

- Configuração padrão e permissiva da extensão `Flask-CORS` sem definir uma lista explícita de origens permitidas (*allowlist*).
- Falta de padronização arquitetural no transporte de credenciais: enquanto algumas rotas usam o header `Authorization: Bearer <token>`, outras aceitam token no corpo JSON ou na query string.

---

## 5. Estratégia de Remediação (Planejada para Fase 3 / 4)

1. **Restringir CORS por Variável de Ambiente:**
   Configurar `Flask-CORS` para aceitar unicamente a origem do frontend legítimo:
   ```python
   allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
   CORS(app, origins=allowed_origins)
   ```
2. **Eliminar `id_token` da Query String:**
   Refatorar `GET /users/info` para extrair o token unicamente a partir do cabeçalho HTTP padrão:
   ```http
   Authorization: Bearer <ID_TOKEN>
   ```
3. **Injeção de Cabeçalhos Anti-Vazamento (Referrer-Policy):**
   Configurar `Referrer-Policy: strict-origin-when-cross-origin` (já ativo no Nginx do frontend).

---

## 6. Implementação Efetiva da Correção

1. **Restrição Estrita de Origens Permitidas no CORS:**
   Em `backend/endpoints.py`, a inicialização do CORS foi configurada via `ALLOWED_ORIGINS`, permitindo unicamente origens conhecidas (`http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:5173`) com `supports_credentials=True`.
2. **Eliminação de Token na URL Query String:**
   A rota `GET /users/info` foi protegida com o decorator `@require_auth`, extraindo o token estritamente via header `Authorization: Bearer <token>`. O suporte a `?id_token=` na query string foi completamente eliminado.

---

## 7. Validação Pós-Correção (Re-teste)

- **Script de Re-teste:** `scripts/pocs/test_vuln06_cors_and_token.py`
  - Resultado: **MITIGADA COM SUCESSO**
  - Preflight com `Origin: https://evil-attacker.site`: `Access-Control-Allow-Origin: None` (bloqueado).
  - Chamada `GET /users/info?id_token=...`: Retorna `HTTP 401 {"error": "Authorization header is required"}`.
- **Suite de Regressão Automatizada (Pytest):**
  - `tests/test_error_handling_and_cors.py::test_token_in_query_string_rejected` -> **PASSED**
  - `tests/test_error_handling_and_cors.py::test_cors_policy_rejects_untrusted_origins` -> **PASSED**


