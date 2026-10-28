# [VULN-04] Exposição de Credenciais Hardcoded e Segredos no Repositório

---

## Metadados e Classificação
- **Identificador:** VULN-04
- **Nome da Falha:** Chaves Privadas e Segredos de Aplicação Versionados no Controle de Código
- **Categoria OWASP:** A02:2021 — Cryptographic Failures / A07:2021 — Identification and Authentication Failures
- **CWE:** CWE-798 (Use of Hard-coded Credentials) / CWE-312 (Cleartext Storage of Sensitive Information)
- **Severidade:** Alta
- **CVSS v3.1 Base Score:** 7.5
- **CVSS v3.1 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
- **Componentes Afetados:** `backend/cornell-course-sphere-data/reddit-data/reddit_key.json` (Commit `c979a1e`) e histórico Git
- **Status de Remediação:** Em Análise / Planejado para Correção na Fase 3

---

## 1. Descrição Técnica e Mecanismo da Falha

Durante a auditoria de histórico executada na Fase 0 através do [`scripts/scan_git_history.py`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/scripts/scan_git_history.py), foi identificado o commit `c979a1e756c308abf321b48d0ffe0fe964b1b9cb` (Data: 16/07/2024, Autor: `Dwain-Anderson`), no qual o arquivo `reddit_key.json` foi adicionado contendo chaves de API reais do Reddit:

```json
{
    "client_id": "7rtaqvFp68AC8uOvSIUl_w",
    "client_secret": "pj00TE5ZN4__46HC4QiiwUVO3Kao3w"
}
```

O arquivo permanece presente na árvore de trabalho da aplicação no caminho:
`backend/cornell-course-sphere-data/reddit-data/reddit_key.json`

### Mecanismo de Risco:
1. **Disponibilidade Imediata a Terceiros:** Quando o código for publicado em repositório público (conforme exigido pelo edital de entrega), qualquer usuário ou bot automatizado de varredura (ex.: GitGuardian, Shodan, GitHub Secret Scanning) tem acesso instantâneo ao `client_secret` associado à conta do desenvolvedor.
2. **Abuso de Autenticação OAuth2:** O par `client_id` + `client_secret` permite a emissão de tokens de acesso à API do Reddit sob a identidade da aplicação registrada, possibilitando coleta de dados, publicação não autorizada ou consumo das cotas de API.

---

## 2. Pré-requisitos de Exploração
- Nenhum privilégio ou autenticação necessária. Basta ter acesso de leitura ao repositório ou clonar o projeto.

---

## 3. Análise de Impacto no Negócio

- **Confidencialidade:** Violação de dados vinculados à conta da aplicação externa.
- **Integridade:** Risco de personificação e envio de conteúdo ou comentários maliciosos sob a identidade da conta vinculada ao Reddit.
- **Responsabilidade Jurídica / Financeira:** Bloqueio de conta, violação dos Termos de Serviço da plataforma de terceiros e eventual suspensão de serviços.

---

## 4. Análise de Causa Raiz (Root Cause Analysis - RCA)

Falha na higiene de desenvolvimento e ausência de pré-validação antes da execução do commit (`pre-commit hooks`). O arquivo de credenciais locais não foi incluído no `.gitignore` original nem substituído por um modelo de exemplo (`reddit_key.example.json`).

---

## 5. Estratégia de Remediação (Planejada para Fase 3)

1. **Remoção do Arquivo de Credenciais Reais:**
   Remover o arquivo `reddit_key.json` do rastreamento do Git e fornecer um modelo [`reddit_key.example.json`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/backend/cornell-course-sphere-data/reddit-data/reddit_key.example.json) com valores fictícios:
   ```json
   {
       "client_id": "YOUR_REDDIT_CLIENT_ID_HERE",
       "client_secret": "YOUR_REDDIT_CLIENT_SECRET_HERE"
   }
   ```
2. **Atualização Imediata do `.gitignore`:**
   Adicionar a regra `*reddit_key.json` e `*.key.json` no `.gitignore` da raiz e do submódulo.
3. **Carregamento via Variáveis de Ambiente:**
   Adaptar os scripts de coleta (`reddit_crawler.py`, `data-migrations.py`) para ler prioritariamente das variáveis `REDDIT_CLIENT_ID` e `REDDIT_CLIENT_SECRET`.
4. **Recomendação Operacional:**
   Revogar as credenciais expostas no painel de desenvolvedores do Reddit e gerar um novo par de chaves.

