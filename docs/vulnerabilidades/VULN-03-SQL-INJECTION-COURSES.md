# [VULN-03] Injeção de SQL via Interpolação de Strings no Catálogo de Cursos

---

## Metadados e Classificação
- **Identificador:** VULN-03
- **Nome da Falha:** SQL Injection por Interpolação Direta de f-strings em Consultas SQLite
- **Categoria OWASP:** A03:2021 — Injection
- **CWE:** CWE-89 (Improper Neutralization of Special Elements used in an SQL Command - SQL Injection)
- **Severidade:** Alta
- **CVSS v3.1 Base Score:** 7.5
- **CVSS v3.1 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
- **Componentes Afetados:** `backend/blueprints/courses.py` (linhas 30, 47, 64, 80, 96, 112)
- **Status de Remediação:** Em Análise / Planejado para Correção na Fase 3

---

## 1. Descrição Técnica e Mecanismo da Falha

No arquivo `backend/blueprints/courses.py`, o módulo responsável pela consulta de cursos acadêmicos utiliza interpolação de strings via Python f-strings para construir instruções SQL dinâmicas enviadas diretamente ao SQLite (`backend/db.py`):

```python
@courses_bp.route("/courses/<string:semester>", methods=["GET"])
def get_courses_by_semester(semester):
    courses = execute_query(
        f"SELECT * FROM courses WHERE semester = '{semester}'"
    ).fetchall()
    ...

@courses_bp.route("/courses/<string:department>", methods=["GET"])
def get_courses_by_department(department):
    courses = execute_query(
        f"SELECT * FROM courses WHERE department = '{department}'"
    ).fetchall()
    ...

@courses_bp.route("/courses/<string:instructor>", methods=["GET"])
def get_courses_by_instructor(instructor):
    courses = execute_query(
        f"SELECT * FROM courses WHERE instructor = '{instructor}'"
    ).fetchall()
    ...
```

O analisador estático **Bandit** reportou múltiplos alertas de severidade média (B608):
```text
[MEDIUM] B608 (hardcoded_sql_expressions): backend/blueprints/courses.py:80
Text: Possible SQL injection vector through string-based query construction.
Code: courses = execute_query(f"SELECT * FROM courses WHERE semester = '{semester}'").fetchall()
```

### Mecanismo de Exploração:
Como o parâmetro de rota `semester` é inserido diretamente entre aspas simples sem qualquer validação, sanitização ou parametrização, a inserção de caracteres especiais como apóstrofo (`'`) altera a semântica da consulta SQL.
- Se um parâmetro contendo `' OR '1'='1` for enviado, a consulta resultante torna-se:
  ```sql
  SELECT * FROM courses WHERE semester = '' OR '1'='1'
  ```
- Isso força a cláusula `WHERE` a avaliar como verdadeira para todos os registros da tabela, extraindo o conteúdo integral do banco ou permitindo o uso de cláusulas `UNION SELECT` para ler dados de outras tabelas (como `reddit_posts`, `reddit_comments` ou metadados de sistema do SQLite `sqlite_master`).

Além disso, há um vício estrutural no Flask: as rotas `/courses/<string:semester>`, `/courses/<string:department>` e `/courses/<string:instructor>` possuem a mesma assinatura, fazendo com que o roteador do Flask ofusque as duas últimas, roteando tudo para a função `get_courses_by_semester`.

---

## 2. Pré-requisitos de Exploração
- Nenhum privilégio ou autenticação necessária (rotas GET públicas).
- O blueprint de cursos estar registrado no Flask (código atualmente latente em `endpoints.py`, planejado para ativação segura).

---

## 3. Análise de Impacto no Negócio

- **Confidencialidade:** Extração não autorizada de dados acadêmicos, históricos de discussões do Reddit ou tabelas internas armazenadas no banco de dados SQLite.
- **Integridade:** Dependendo das permissões do driver e da versão do SQLite, risco de manipulação ou execução de comandos adicionais.
- **Disponibilidade:** Ataques baseados em sobrecarga de consultas ou comandos de `ATTACH DATABASE` podem degradar a performance ou corromper a base embarcada.

---

## 4. Análise de Causa Raiz (Root Cause Analysis - RCA)

Concatenação direta de entrada não confiável fornecida pelo usuário na montagem de comandos SQL. Ausência do uso de **Prepared Statements** (consultas parametrizadas com placeholders `?`), que é a única defesa recomendada e definitiva contra injeção de SQL.

---

## 5. Estratégia de Remediação (Planejada para Fase 3)

1. **Substituição por Consultas Parametrizadas:**
   Substituir toda interpolação de strings por placeholders posicionais (`?`) gerenciados pelo driver nativo do `sqlite3`:
   ```python
   def execute_query(query, params=()):
       conn = create_connection()
       cursor = conn.cursor()
       res = cursor.execute(query, params)
       conn.commit()
       return res
   ```
   E na rota:
   ```python
   @courses_bp.route("/courses/semester/<string:semester>", methods=["GET"])
   def get_courses_by_semester(semester):
       courses = execute_query(
           "SELECT * FROM courses WHERE semester = ?",
           (semester,)
       ).fetchall()
       ...
   ```
2. **Correção dos Caminhos de Rota no Flask:**
   Diferenciar explicitamente os prefixos de cada rota:
   - `/courses/semester/<string:semester>`
   - `/courses/department/<string:department>`
   - `/courses/instructor/<string:instructor>`
3. **Ativação Segura do Blueprint no `endpoints.py`:**
   Registrar formalmente o blueprint corrigido com `app.register_blueprint(courses_bp)`.
4. **Testes Automatizados:**
   Adicionar teste no Pytest enviando payloads de injeção e comprovando que o banco trata o parâmetro estritamente como dado literal e não como instrução executável.

