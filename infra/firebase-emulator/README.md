# Firebase Emulator Suite — CourseSphere

Este diretório contém a configuração completa e isolada do **Firebase Emulator Suite** para o projeto CourseSphere, cobrindo:
- **Firebase Authentication** (Porta `9099`)
- **Firebase Realtime Database** (Porta `9000`)
- **Emulator Suite UI** (Porta `4000`)

---

## Estrutura de Arquivos

- `firebase.json`: Definição de portas e configuração dos emuladores.
- `database.rules.json`: Regras iniciais da base vulnerável (permissivas).
- `database.rules.hardened.json`: Regras seguras com controle de acesso por `$uid` (para a Fase 4 - Hardening).
- `Dockerfile`: Imagem Docker pronta contendo Node 20 LTS, Java 17 headless e `firebase-tools`.

---

## Como Executar

### Opção 1: Via Docker (Recomendado)
```bash
# Subir apenas o emulador
docker compose up firebase-emulator -d

# Ou build direto:
docker build -t coursesphere-firebase-emulator infra/firebase-emulator
docker run -p 9099:9099 -p 9000:9000 -p 4000:4000 coursesphere-firebase-emulator
```

### Opção 2: Localmente via CLI (Requer Java 11+ e Node.js)
```bash
cd infra/firebase-emulator
npx firebase-tools emulators:start --project coursesphere-8bd9a --config firebase.json
```

A interface visual web ficará disponível em: **`http://localhost:4000`**

---

## Como Executar o Seed de Usuários (Alice e Bob)

Com o emulador rodando, execute na raiz do projeto:

```bash
python scripts/seed_firebase_emulator.py
```

### Usuários Criados no Seed:
1. **Alice (Usuário Vítima / Estudante Legítimo):**
   - **Email:** `alice@test.local`
   - **Senha:** `AlicePassword123!`
   - **Dados:** Perfil acadêmico pré-carregado (`users/user_alice_001/info`) e conversas salvas em `users/user_alice_001/chats/`.

2. **Bob (Atacante / Estudante 2):**
   - **Email:** `bob@test.local`
   - **Senha:** `BobPassword123!`
   - **Dados:** Perfil próprio e chats próprios para teste de autorização cruzada (IDOR).

