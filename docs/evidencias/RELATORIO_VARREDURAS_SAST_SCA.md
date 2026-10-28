# Relatório de Varreduras Automatizadas (SAST & SCA)
**Projeto:** CourseSphere — Desafio Técnico AppSec & SRE  
**Data da Execução:** 27/10/2026  
**Status da Etapa:** Concluída com Sucesso

---

## 1. Visão Geral das Ferramentas Executadas

Em conformidade com o **Requisito 7 do Edital** ("Configurar ao menos uma ferramenta de análise estática SAST ou de dependências SCA no repositório e anexar o resultado da execução"), foram executadas ferramentas automatizadas de análise de código e dependências em ambas as camadas (Frontend e Backend):

| Categoria | Ferramenta | Alvo / Escopo | Arquivo de Evidência Bruta | Total de Achados |
|---|---|---|---|---|
| **SAST** | Bandit v1.9.4 | Código Python do Backend (`backend/`) | [`docs/evidencias/sast/bandit.json`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/docs/evidencias/sast/bandit.json) | **20 achados** (1 High, 15 Medium, 4 Low) |
| **SAST** | Git Secrets Scanner | Histórico Git completo (71 commits) | [`docs/evidencias/sast/git_secrets_audit.json`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/docs/evidencias/sast/git_secrets_audit.json) | **17 ocorrências** (Segredos Reddit, Firebase Keys) |
| **SCA** | pip-audit v2.10.1 | Dependências Python (`requirements.txt`) | [`docs/evidencias/sca/pip-audit.json`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/docs/evidencias/sca/pip-audit.json) | Dependências sem pinning de versão formal |
| **SCA** | NPM Audit / OSV | Dependências Node.js (`package-lock.json`) | [`docs/evidencias/sca/npm-audit.json`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/docs/evidencias/sca/npm-audit.json) | **39 vulnerabilidades** (2 Críticas, 19 Altas, 17 Médias, 1 Baixa) |

---

## 2. Principais Destaques do SAST (Bandit)

O Bandit identificou padrões críticos no código da aplicação:
1. **Exposição do Werkzeug Debugger (Severidade ALTA - B201):**
   - **Local:** `backend/endpoints.py:108`
   - **Código:** `app.run(debug=True)`
   - **Impacto:** Permite acesso ao console de depuração com execução arbitrária de comandos em caso de erro 500.
2. **Injeção de SQL via Interpolação de Strings (Severidade MÉDIA - B608):**
   - **Locais:** `backend/blueprints/courses.py` (linhas 30, 47, 64, 80, 96, 112) e `data-migrations.py`
   - **Código:** `execute_query(f"SELECT * FROM courses WHERE semester = '{semester}'")`
   - **Impacto:** Falha direta alinhada a OWASP A03:2021 (Injection), permitindo extração ou adulteração de dados no SQLite.
3. **Geração Insegura de Pseudo-Aleatórios (Severidade BAIXA - B311):**
   - **Local:** `backend/main.py:16`
   - **Código:** Uso de `random.choices` e distribuição de Poisson para geração de hash de identificação de mensagens.

---

## 3. Principais Destaques do SCA (NPM Audit & pip-audit)

1. **Vulnerabilidades Críticas e Altas no Frontend:**
   - **Total de 39 vulnerabilidades** registradas no ecossistema npm herdado do baseline.
   - **CVE-2024-28863 / GHSA-m6fv-jmc8-4pc4 (`tar`):** Arbitrary file overwrite e DoS.
   - **CVE-2024-4068 (`braces`):** ReDoS (Regular Expression Denial of Service).
   - **CVE-2024-37890 (`ws`):** Denial of Service via header crafting.
   - **Imagem Base Legada:** Dockerfile original referenciando `node:16-alpine` (End-of-Life).
2. **Ausência de Versões Fixadas no Backend:**
   - `backend/requirements.txt` original continha apenas nomes de pacotes sem declaração estrita de versão ou hash SHA-256 (`pip hash`), permitindo que builds futuros instalem versões vulneráveis ou incompatíveis.

---

Este relatório e os arquivos brutos em formato JSON servem como base empírica para a **Etapa 2: Comprovação Manual e Scripts de PoC das Vulnerabilidades**.

