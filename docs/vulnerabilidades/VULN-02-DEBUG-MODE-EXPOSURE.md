# [VULN-02] Exposição de Depurador Werkzeug e Modo Debug em Produção

---

## Metadados e Classificação
- **Identificador:** VULN-02
- **Nome da Falha:** Modo de Depuração Ativo em Produção com Exposição de Traceback e Console Interativo
- **Categoria OWASP:** A05:2021 — Security Misconfiguration
- **CWE:** CWE-215 (Insertion of Sensitive Information into Debugging Code) / CWE-489 (Active Debug Code)
- **Severidade:** Alta / Crítica (se acessível publicamente)
- **CVSS v3.1 Base Score:** 8.5
- **CVSS v3.1 Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L`
- **Componentes Afetados:** `backend/endpoints.py` (linha 108)
- **Status de Remediação:** Em Análise / Planejado para Correção na Fase 3

---

## 1. Descrição Técnica e Mecanismo da Falha

No arquivo `backend/endpoints.py`, a inicialização do servidor Flask é declarada da seguinte forma:
```python
if __name__ == '__main__':
    app.run(debug=True)
```

O analisador estático **Bandit** sinalizou esta linha como finding crítico:
```text
[HIGH] B201 (flask_debug_true): backend/endpoints.py:108
Text: A Flask app appears to be run with debug=True, which exposes the Werkzeug debugger and allows the execution of arbitrary code.
```

### Mecanismo de Vulnerabilidade:
Quando o modo `debug=True` do Flask está ativo:
1. **Exposição de Informações Internas (Information Disclosure):** Qualquer exceção não capturada na aplicação retorna ao cliente uma página HTML detalhada contendo:
   - Caminhos absolutos do sistema operacional e do diretório de arquivos no servidor.
   - Versões exatas do interpretador Python e de todas as bibliotecas carregadas.
   - Trechos do código-fonte em volta da linha que causou a falha.
   - Variáveis locais da função e parâmetros de requisição.
2. **Depurador Interativo (Interactive Werkzeug Console):** O depurador do Werkzeug disponibiliza um console interativo em Python acessível na página de erro mediante a inserção de um PIN de depuração. Como o PIN é gerado a partir de atributos previsíveis da máquina (endereço MAC, ID da máquina, nome de usuário do sistema e caminho do Python), um atacante que colete essas informações através de outras falhas pode forjar o PIN e obter execução remota de código arbitrário (**RCE**).

---

## 2. Pré-requisitos de Exploração
- Nenhum privilégio ou autenticação necessária.
- Provocar uma exceção não tratada no backend (ex.: envio de corpo malformado em rota sem validação de tipos ou chamada a endpoint que dispara erro interno).

---

## 3. Análise de Impacto no Negócio

- **Confidencialidade:** Exposição total de dados de ambiente, variáveis internas, estrutura de pastas e segredos que estejam carregados na memória do processo no momento da exceção.
- **Integridade:** Risco de execução de código no servidor web caso o console interativo seja ativado ou desbloqueado.
- **Disponibilidade:** Facilita a elaboração de ataques direcionados de negação de serviço (DoS) a partir do mapeamento preciso das bibliotecas e pontos fracos da arquitetura.

---

## 4. Análise de Causa Raiz (Root Cause Analysis - RCA)

Uso de configuração de ambiente de desenvolvimento em código destinado à execução operacional. A aplicação depende do servidor de desenvolvimento interno do Werkzeug (`app.run`), em vez de utilizar um servidor de aplicação WSGI robusto e profissional para ambientes de produção.

---

## 5. Estratégia de Remediação (Planejada para Fase 3)

1. **Remover `debug=True`:**
   Desabilitar explicitamente o modo de depuração na inicialização do Flask:
   ```python
   app.run(debug=False)
   ```
2. **Utilizar Servidor de Aplicação de Produção (Gunicorn):**
   Executar a aplicação exclusivamente via servidor WSGI profissional (já preparado em `backend/Dockerfile` na Fase 1):
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 endpoints:app
   ```
3. **Implementar Tratamento Global de Erros (`@app.errorhandler(500)`):**
   Garantir que qualquer exceção interna inesperada seja capturada por um tratador genérico, registrando o log completo nos logs internos e devolvendo ao cliente uma mensagem JSON padronizada e sanitizada:
   ```json
   {
     "error": "Erro interno no servidor. Por favor, tente novamente mais tarde."
   }
   ```

