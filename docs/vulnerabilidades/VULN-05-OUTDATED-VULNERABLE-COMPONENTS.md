# [VULN-05] Uso de Componentes Vulneráveis e Desatualizados (Frontend e Dependências)

---

## Metadados e Classificação
- **Identificador:** VULN-05
- **Nome da Falha:** Dependências de Terceiros com Vulnerabilidades Conhecidas e Imagem Base Descontinuada
- **Categoria OWASP:** A06:2021 — Vulnerable and Outdated Components
- **CWE:** CWE-1104 (Use of Unmaintained Third-Party Components) / CWE-1035 (Vulnerable Third-Party Component)
- **Severidade:** Alta
- **CVSS v3.1 Base Score:** 8.6
- **CVSS v3.1 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:H`
- **Componentes Afetados:** `frontend/package.json`, `frontend/package-lock.json` e `frontend/Dockerfile` original
- **Status de Remediação:** Em Análise / Parcialmente Mitigado na Fase 1 (Docker multi-stage) e Planejado para Resolução Definitiva na Fase 3

---

## 1. Descrição Técnica e Mecanismo da Falha

A análise de composição de software (SCA) executada contra a árvore de dependências do frontend revelou um ecossistema com acentuado débito técnico de segurança:

1. **Vulnerabilidades nas Dependências NPM:**
   A varredura consolidada em [`docs/evidencias/sca/npm-audit.json`](file:///c:/Users/luizf/OneDrive/Documentos/PROGRAMAÇÃO/PS/CourseSphere/docs/evidencias/sca/npm-audit.json) identificou **39 vulnerabilidades** nos pacotes transitivos:
   - **2 Críticas**
   - **19 Altas**
   - **17 Médias**
   - **1 Baixa**

### CVEs Críticas e de Destaque Identificadas:
- **CVE-2024-28863 / GHSA-m6fv-jmc8-4pc4 (`tar` < 6.2.1):** Vulnerabilidade de negação de serviço e sobreescrita arbitrária de arquivos através de links simbólicos e caminhos manipulados durante descompactação de arquivos.
- **CVE-2024-4068 / GHSA-grv7-fg5c-x5vh (`braces` < 3.0.3):** ReDoS (Regular Expression Denial of Service) através de expansões exponenciais de padrões numéricos e alfanuméricos.
- **CVE-2024-37890 / GHSA-3h5v-q93c-6h6q (`ws` < 8.17.1):** Vulnerabilidade de Negação de Serviço por consumo excessivo de memória em conexões WebSocket malformadas.

2. **Imagem de Contêiner Descontinuada (End-of-Life):**
   O Dockerfile original do frontend baseava-se em:
   ```dockerfile
   FROM node:16-alpine
   ```
   O Node.js 16 teve seu suporte e atualizações de segurança encerrados oficialmente em **11 de setembro de 2023** (EOL há mais de 3 anos). Imagens base sem manutenção acumulam vulnerabilidades não corrigidas no sistema operacional (glibc, musl, libcrypto, busybox).

---

## 2. Pré-requisitos de Exploração
- Varia conforme a dependência afetada. No caso de vulnerabilidades em ferramentas de build e empacotamento, a exploração pode ocorrer durante o processo de compilação ou execução do servidor de desenvolvimento.

---

## 3. Análise de Impacto no Negócio

- **Disponibilidade:** Ataques de negação de serviço (DoS/ReDoS) capazes de travar o processo da aplicação ou da ferramenta de build.
- **Integridade:** Risco de supply chain attack caso pacotes desatualizados sejam comprometidos no registro público de dependências.
- **Conformidade:** Violação de padrões de conformidade corporativa (SOC 2, ISO 27001) que proíbem o uso de sistemas operacionais e runtimes sem suporte oficial de segurança.

---

## 4. Análise de Causa Raiz (Root Cause Analysis - RCA)

Falta de um processo contínuo de gestão de dependências (*Software Supply Chain Security*), ausência de ferramentas de atualização automática de pacotes (como Dependabot ou Renovate) e manutenção de imagens base de contêiner desatualizadas no ciclo de vida do projeto.

---

## 5. Estratégia de Remediação (Planejada para Fase 3)

1. **Substituição da Imagem Base (Já implementada na Fase 1):**
   Migração para `node:20-alpine` (Node 20 LTS com suporte ativo até 2026) em estágio de build, e runtime estático com `nginx:1.27-alpine`.
2. **Atualização das Dependências Vulneráveis:**
   Executar atualização das dependências diretas e indiretas (`npm update` ou resolução forçada de sub-dependências com `overrides` no `package.json` para os pacotes `tar`, `braces`, `ws` e `semver`).
3. **Pinning Estrito no Backend:**
   Fixar versões com hashes estritos no `backend/requirements.txt` para impedir a instalação de versões divergentes ou suscetíveis a ataques de *dependency confusion*.

