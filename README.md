# 🤖 Chatbot — RAG + Django + Gemini + React

Sistema de chatbot organizado em **monorepo**, com frontend em React, backend em Django REST Framework, autenticação JWT, banco de dados **PostgreSQL com pgvector** e suporte a **RAG (Retrieval-Augmented Generation)** com a **Gemini API**.

---

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Padrões de Projeto](#padrões-de-projeto)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Requisitos](#requisitos)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Configuração do PostgreSQL + Docker](#configuração-do-postgresql--docker)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Configuração do Django](#configuração-do-django)
- [Rotas da API](#rotas-da-api)
- [Autenticação JWT](#autenticação-jwt)
- [Testando com Postman](#testando-com-postman)
- [Arquitetura RAG](#arquitetura-rag)
- [Erros Comuns](#erros-comuns)
- [Próximos Passos](#próximos-passos)

---

## Visão Geral

Este projeto é organizado como um **monorepo**: frontend e backend ficam no mesmo repositório, mas separados por responsabilidade.

| Parte | Tecnologia | Localização |
|---|---|---|
| Interface web | React + JavaScript | `frontend/` |
| API e chatbot | Python + Django REST Framework | `Backend/` |
| Configuração Django | Django | `config/` |
| Banco de dados | PostgreSQL 16 + pgvector | Docker |
| Ponto de entrada | Django CLI | `manage.py` |

---

## Estrutura do Projeto

```
Chatbot/
├── frontend/                         # Interface web em React
│   └── src/
│       ├── pages/
│       │   ├── Login.jsx
│       │   └── admin/
│       │       ├── DocumentsList.jsx
│       │       ├── DocumentCreate.jsx
│       │       ├── DocumentEdit.jsx
│       │       └── Categories.jsx
│       ├── components/
│       │   ├── Layout.jsx
│       │   ├── Sidebar.jsx
│       │   ├── DocumentForm.jsx
│       │   └── ConfirmDialog.jsx
│       ├── services/
│       │   ├── api.js
│       │   ├── authService.js
│       │   └── documentService.js
│       ├── routes/
│       │   └── AppRoutes.jsx
│       ├── App.jsx
│       └── main.jsx
│
├── Backend/
│   └── app/
│       ├── api/                      # Camada HTTP
│       │   ├── views/
│       │   │   ├── auth.py           # Login do admin
│       │   │   ├── chat.py           # Endpoint do chatbot
│       │   │   ├── documents.py      # CRUD de documentos
│       │   │   ├── categories.py
│       │   │   └── users.py
│       │   ├── serializers/
│       │   ├── factories.py          # Factory Method
│       │   ├── permissions.py
│       │   └── urls.py
│       ├── application/              # Casos de uso
│       │   ├── login_admin.py
│       │   ├── delete_document.py
│       │   ├── answer_question.py
│       │   ├── create_document.py
│       │   ├── list_documents.py
│       │   ├── update_document.py
│       │   ├── embedding_provider.py
│       │   ├── index_document.py
│       │   └── vector_store.py
│       ├── core/
│       │   └── app_settings.py
│       ├── domain/                   # Contratos e entidades
│       │   ├── entities/
│       │   └── repositories/
│       │       └── document_repository.py  # Interface abstrata
│       ├── infrastructure/           # Implementações concretas
│       │   ├── Database/
│       │   ├── embeddings/
│       │   ├── indexing/
│       │   ├── llm/
│       │   ├── repositories/
│       │   │   ├── in_memory/
│       │   │   │   ├── in_memory_chat_repository.py
│       │   │   │   └── in_memory_document_repository.py
│       │   │   └── sql/
│       │   │       └── postgres_document_repository.py
│       │   ├── security/
│       │   └── vectorstore/
│       └── documents/                # Models e indexação de PDFs
│           ├── models.py
│           ├── apps.py
│           └── management/commands/
│               └── indexar_documentos.py
│
├── config/                           # Configuração do Django
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── Documentos/                       # PDFs indexados no banco
│   ├── portarias/                    # 20 PDFs
│   ├── resolucoes/                   # 20 PDFs
│   └── rod/                          # 2 PDFs
│
├── migrations/
│   └── criar_indice_vetorial.sql     # Índice vetorial no PostgreSQL
│
├── docker-compose.yml                # PostgreSQL + pgvector via Docker
├── Dockerfile                        # Imagem do backend
├── init.sql                          # Habilita extensão pgvector
├── .env.example                      # Modelo de variáveis de ambiente
├── manage.py
└── requirements.txt
```

---

## Padrões de Projeto

O projeto aplica padrões do livro **"Padrões de Projeto" (Gang of Four)** para garantir flexibilidade, testabilidade e manutenção do código.

### 1. Factory Method (GoF p.112) — Criação

**Onde:** `Backend/app/api/factories.py`

As views nunca instanciam casos de uso diretamente. A Factory centraliza a criação e injeta as dependências corretas.

```
LoginView        → AuthFactory.make_login()   → LoginAdmin
DocumentDeleteView → DocumentFactory.make_delete() → DeleteDocument(PostgresDocumentRepository)
```

### 2. Strategy (GoF p.292) — Comportamental

**Onde:** `Backend/app/infrastructure/llm/` *(a implementar)*

Permite trocar o provedor de LLM (Gemini, OpenAI, etc.) sem alterar os casos de uso. O `AnswerQuestion` delega para um `LLMProvider` abstrato.

### 3. Repository (separação domínio/infraestrutura)

**Onde:** `Backend/app/domain/repositories/` e `infrastructure/repositories/`

A camada de aplicação depende apenas da interface abstrata `DocumentRepository`. As implementações concretas (`PostgresDocumentRepository`, `SQLiteDocumentRepository`, `InMemoryDocumentRepository`) são intercambiáveis.

---

## O que cada parte faz

### `frontend/`
Interface do sistema acessada pelo usuário no navegador. Telas de login, listagem e cadastro de documentos, páginas administrativas e comunicação com o backend via API.

### `Backend/app/api/`
Camada HTTP do backend. Recebe requisições, valida dados de entrada, chama os casos de uso e devolve respostas em JSON. Arquivos importantes: `views/`, `serializers/`, `urls.py`, `permissions.py`, `factories.py`.

### `Backend/app/application/`
Casos de uso do sistema — define **o que a aplicação faz**: criar, listar, atualizar e deletar documentos, responder perguntas e indexar conteúdo.

### `Backend/app/domain/`
Camada central da regra de negócio. Contém entidades, contratos de repositório e os conceitos principais do sistema.

### `Backend/app/infrastructure/`
Implementações concretas dos contratos definidos em `domain/`: conexão com banco de dados, autenticação e segurança, integração com Gemini, embeddings e vector store.

### `config/`
Configuração do Django: `settings.py`, rotas globais em `urls.py`, e entradas para execução/deploy.

---

## Tecnologias Utilizadas

### Frontend
- React, JavaScript, Axios, React Router

### Backend
- Python 3.10+, Django 5.1, Django REST Framework
- Simple JWT, django-cors-headers

### Banco de Dados
- PostgreSQL 16 + pgvector (via Docker)
- psycopg2-binary (driver Python)

### IA / RAG
- Gemini API, Embeddings, Vector Store (pgvector)

---

## Requisitos

- Python 3.10+
- Node.js 18+
- Docker Desktop
- Chave de API do Gemini

---

## Como rodar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/LES-Chatbot-KTP/Chatbot.git
cd Chatbot
```

### 2. Criar e ativar o ambiente virtual

**Windows PowerShell**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows CMD**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux / macOS**
```bash
python -m venv .venv
source .venv/bin/activate
```

> Quando o ambiente estiver ativo, o terminal exibirá `(.venv)` no início da linha.

### 3. Instalar dependências do backend

```bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers google-genai psycopg2-binary pypdf python-dotenv
```

Para salvar as dependências:
```bash
pip freeze > requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env e preencha GEMINI_API_KEY, POSTGRES_PASSWORD e SECRET_KEY
```

### 5. Subir o banco de dados

> O Docker Desktop precisa estar aberto antes desse passo.

```bash
docker-compose up -d db
```

### 6. Aplicar migrações

```bash
python manage.py makemigrations documents
python manage.py migrate
```

### 7. Criar o índice vetorial no PostgreSQL

**Windows PowerShell:**
```powershell
Get-Content migrations/criar_indice_vetorial.sql | docker exec -i chatbot_db psql -U chatbot_user -d chatbot
```

**Linux / macOS:**
```bash
docker exec -i chatbot_db psql -U chatbot_user -d chatbot < migrations/criar_indice_vetorial.sql
```

### 8. Indexar os documentos PDF

```bash
python manage.py indexar_documentos
```

Resultado esperado:
```
✅ Indexação concluída: 42 documento(s), 650 chunk(s)
```

### 9. Criar superusuário e iniciar o servidor

```bash
python manage.py createsuperuser
python manage.py runserver
```

O backend ficará disponível em **http://127.0.0.1:8000/**

Para encerrar o servidor: `Ctrl + C`

### 10. Rodar o frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

O frontend ficará disponível em **http://localhost:5173/**

---

## Configuração do PostgreSQL + Docker

O projeto usa **PostgreSQL 16 com a extensão pgvector** para armazenar documentos e embeddings vetoriais.

### Estrutura do banco

| Tabela | Descrição |
|---|---|
| `documents_documento` | 42 PDFs indexados (portarias, resoluções, RODs) |
| `documents_chunkdocumento` | 650 chunks de texto com embeddings vetoriais |

### Verificar se o banco está rodando

```bash
docker-compose ps
# chatbot_db   Up (healthy)   0.0.0.0:5432->5432/tcp
```

### Consultar dados no banco

```bash
docker exec -it chatbot_db psql -U chatbot_user -d chatbot
```

```sql
-- Documentos por tipo
SELECT tipo, COUNT(*) FROM documents_documento GROUP BY tipo;

-- Total de chunks
SELECT COUNT(*) FROM documents_chunkdocumento;

-- Ver IDs dos documentos
SELECT id, nome, tipo FROM documents_documento LIMIT 10;
```

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz baseado no `.env.example`:

| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Chave de acesso à API do Gemini |
| `CHAT_MODEL` | Modelo para gerar respostas (ex: gemini-1.5-flash) |
| `EMBEDDING_MODEL` | Modelo para embeddings (ex: models/text-embedding-004) |
| `TOP_K` | Quantidade de chunks recuperados na busca vetorial |
| `POSTGRES_DB` | Nome do banco de dados |
| `POSTGRES_USER` | Usuário do banco |
| `POSTGRES_PASSWORD` | Senha do banco |
| `DB_HOST` | Host do banco (localhost em dev, db no Docker) |
| `SECRET_KEY` | Chave secreta do Django |
| `DEBUG` | True em desenvolvimento, False em produção |
| `ALLOWED_HOSTS` | Hosts permitidos (ex: localhost,127.0.0.1) |

> ⚠️ Nunca suba o `.env` para o GitHub. Apenas o `.env.example`.

---

## Configuração do Django

Em `config/settings.py`, certifique-se de que as seguintes configurações estão presentes:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "Backend.app",
    "Backend.app.documents",
]

ROOT_URLCONF = "config.urls"
STATIC_URL = "/static/"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
```

---

## Rotas da API

### `POST /api/auth/login/`
Autentica o administrador e retorna tokens JWT.

```json
// Request
{ "username": "seu_usuario", "password": "sua_senha" }

// Response 200
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "username": "seu_usuario",
  "email": "email@exemplo.com"
}
```

Erros: `400` campos em branco · `401` credenciais inválidas ou usuário sem `is_staff`.

---

### `POST /api/auth/refresh/`
Renova o token de acesso usando o token de refresh.

```json
{ "refresh": "seu_refresh_token" }
```

---

### `POST /api/token/`
Geração de token JWT pelo endpoint padrão do SimpleJWT.

```json
// Request
{ "username": "seu_usuario", "password": "sua_senha" }

// Response
{ "refresh": "...", "access": "..." }
```

---

### `POST /api/token/refresh/`
Renova o token via endpoint padrão do SimpleJWT.

```json
{ "refresh": "seu_refresh_token" }
```

---

### `POST /api/chat/`
Recebe uma pergunta e retorna a resposta do chatbot.

```json
// Request
{ "question": "O que é RAG?" }

// Response
{ "answer": "RAG é uma abordagem que recupera contexto antes de gerar a resposta." }
```

---

### `GET /api/documents/`
Lista os arquivos enviados à API do Gemini. Requer autenticação JWT de administrador.

```http
GET http://127.0.0.1:8000/api/documents/
Authorization: Bearer SEU_ACCESS_TOKEN
```

```json
// Response 200
{
  "documentos": [
    {
      "name": "files/abc123",
      "display_name": "Portaria_001",
      "mime_type": "application/pdf",
      "size_bytes": 204800,
      "state": "ACTIVE",
      "create_time": "2026-03-23T10:00:00+00:00",
      "expiration_time": "2026-03-25T10:00:00+00:00",
      "uri": "https://generativelanguage.googleapis.com/v1beta/files/abc123"
    }
  ]
}
```

Erros: `401` sem token ou sem `is_staff` · `500` GEMINI_API_KEY não configurada.

---

### `POST /api/documents/`
Cadastra um novo documento: faz upload para o Gemini e salva o registro no banco. Requer autenticação JWT de administrador.

```http
POST http://127.0.0.1:8000/api/documents/
Authorization: Bearer SEU_ACCESS_TOKEN
Content-Type: multipart/form-data
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `nome` | string | sim | Nome do documento |
| `tipo` | string | sim | `portaria`, `resolucao` ou `rod` |
| `arquivo` | file | sim | Arquivo PDF a ser enviado |

```json
// Response 201
{
  "id": 1,
  "nome": "Portaria_001",
  "tipo": "portaria",
  "caminho_arquivo": "https://generativelanguage.googleapis.com/v1beta/files/abc123",
  "indexado_em": "2026-03-23T10:00:00+00:00"
}
```

Erros: `400` campo faltando ou tipo inválido · `401` sem token ou sem `is_staff` · `500` GEMINI_API_KEY não configurada.

---

### `PATCH /api/documents/<id>/`
Atualiza parcialmente um documento. Todos os campos são opcionais. Se um novo arquivo for enviado, o arquivo antigo é removido do Gemini e substituído. Requer autenticação JWT de administrador.

```http
PATCH http://127.0.0.1:8000/api/documents/1/
Authorization: Bearer SEU_ACCESS_TOKEN
Content-Type: multipart/form-data
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `nome` | string | não | Novo nome do documento |
| `tipo` | string | não | `portaria`, `resolucao` ou `rod` |
| `arquivo` | file | não | Novo arquivo (substitui o atual no Gemini) |

```json
// Response 200
{
  "id": 1,
  "nome": "Portaria_Atualizada",
  "tipo": "resolucao",
  "caminho_arquivo": "https://generativelanguage.googleapis.com/v1beta/files/xyz789",
  "atualizado_em": "2026-03-23T11:30:00+00:00"
}
```

Erros: `400` nenhum campo fornecido ou tipo inválido · `401` sem token ou sem `is_staff` · `404` ID não encontrado.

---

### `DELETE /api/documents/<id>/` — Passo 1: Solicitar exclusão
Inicia o fluxo de exclusão com confirmação. Retorna um token válido por **5 minutos** que deve ser enviado no passo 2. Requer autenticação JWT de administrador.

```http
DELETE http://127.0.0.1:8000/api/documents/1/
Authorization: Bearer SEU_ACCESS_TOKEN
```

```json
// Response 200
{
  "mensagem": "Para confirmar a exclusão de 'Portaria_001', envie o token no campo 'token' via POST para /confirm/.",
  "documento": {
    "id": 1,
    "nome": "Portaria_001",
    "tipo": "portaria"
  },
  "token": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "expira_em": "2026-03-23T11:35:00+00:00"
}
```

---

### `POST /api/documents/<id>/confirm/` — Passo 2: Confirmar exclusão
Confirma e executa a exclusão do documento usando o token recebido no passo anterior. O token é de uso único e expira em 5 minutos. Requer autenticação JWT de administrador.

```http
POST http://127.0.0.1:8000/api/documents/1/confirm/
Authorization: Bearer SEU_ACCESS_TOKEN
Content-Type: application/json
```

```json
// Request
{ "token": "f47ac10b-58cc-4372-a567-0e02b2c3d479" }

// Response 200
{
  "message": "Documento 'Portaria_001' excluído com sucesso.",
  "id": 1
}
```

Erros: `400` ID ou token inválido · `401` sem token ou sem `is_staff` · `403` token expirado ou incorreto · `404` ID não encontrado.

---

## Autenticação JWT

O fluxo de autenticação funciona da seguinte forma:

1. O usuário faz login via `POST /api/auth/login/`
2. A API retorna os tokens `access` e `refresh`
3. O token `access` é enviado no header das rotas protegidas:

```http
Authorization: Bearer SEU_TOKEN
```

4. Nas rotas administrativas, o token é validado e o `is_staff` é verificado.

---

## Testando com Postman

### Login do administrador

| Campo | Valor |
|---|---|
| Método | `POST` |
| URL | `http://127.0.0.1:8000/api/auth/login/` |
| Body | `raw → JSON` |

```json
{ "username": "seu_usuario", "password": "sua_senha" }
```

### Testar o chat

| Campo | Valor |
|---|---|
| Método | `POST` |
| URL | `http://127.0.0.1:8000/api/chat/` |
| Headers | `Content-Type: application/json` |
| Body | `raw → JSON` |

```json
{ "question": "oi" }
```

### Listar documentos do Gemini

| Campo | Valor |
|---|---|
| Método | `GET` |
| URL | `http://127.0.0.1:8000/api/documents/` |
| Headers | `Authorization: Bearer SEU_TOKEN` |

---

### Cadastrar um documento

| Campo | Valor |
|---|---|
| Método | `POST` |
| URL | `http://127.0.0.1:8000/api/documents/` |
| Headers | `Authorization: Bearer SEU_TOKEN` |
| Body | `form-data` |

Campos no form-data:

| Chave | Tipo | Valor de exemplo |
|---|---|---|
| `nome` | Text | `Portaria_001` |
| `tipo` | Text | `portaria` |
| `arquivo` | File | *(selecione o arquivo PDF)* |

---

### Editar um documento

| Campo | Valor |
|---|---|
| Método | `PATCH` |
| URL | `http://127.0.0.1:8000/api/documents/1/` |
| Headers | `Authorization: Bearer SEU_TOKEN` |
| Body | `form-data` |

Envie apenas os campos que deseja alterar. Exemplo atualizando só o nome:

| Chave | Tipo | Valor |
|---|---|---|
| `nome` | Text | `Portaria_Atualizada` |

---

### Excluir um documento (com confirmação)

**Passo 1 — Solicitar exclusão:**

| Campo | Valor |
|---|---|
| Método | `DELETE` |
| URL | `http://127.0.0.1:8000/api/documents/1/` |
| Headers | `Authorization: Bearer SEU_TOKEN` |

Copie o campo `token` da resposta.

**Passo 2 — Confirmar exclusão:**

| Campo | Valor |
|---|---|
| Método | `POST` |
| URL | `http://127.0.0.1:8000/api/documents/1/confirm/` |
| Headers | `Authorization: Bearer SEU_TOKEN` · `Content-Type: application/json` |
| Body | `raw → JSON` |

```json
{ "token": "f47ac10b-58cc-4372-a567-0e02b2c3d479" }
```

> O token expira em **5 minutos** e só pode ser usado uma vez.

---

## Arquitetura RAG

```
Pergunta do usuário
        ↓
  Geração de embedding (Gemini)
        ↓
  Busca vetorial no PostgreSQL (TOP_K chunks)
        ↓
  Contexto + Pergunta → Prompt
        ↓
     Gemini API
        ↓
  Resposta contextualizada
```

Arquivos envolvidos:

```
Backend/app/
├── application/
│   ├── answer_question.py    ← Facade (a implementar)
│   ├── embedding_provider.py
│   ├── vector_store.py
│   └── index_document.py
├── infrastructure/
│   ├── embeddings/
│   ├── vectorstore/
│   └── llm/                  ← Strategy (a implementar)
└── documents/
    └── management/commands/
        └── indexar_documentos.py
```

A integração com o Gemini fica **desacoplada da view**, dentro de `infrastructure/llm/`, o que facilita trocar de provedor, testar e manter o código organizado.

---

## Erros Comuns

### `open //./pipe/dockerDesktopLinuxEngine`
O Docker Desktop não está aberto. Abra-o e aguarde inicializar.

### `No module named 'psycopg2'`
```bash
pip install psycopg2-binary
```

### `No module named 'dotenv'`
```bash
pip install python-dotenv
```

### `No installed app with label 'documents'`
Certifique-se de que `"Backend.app.documents"` está em `INSTALLED_APPS` e que o arquivo `apps.py` existe em `Backend/app/documents/`.

### `ROOT_URLCONF not found` ou `STATIC_URL not set`
O `settings.py` está incompleto. Adicione:
```python
ROOT_URLCONF = "config.urls"
STATIC_URL = "/static/"
```

### `Operador '<' reservado` (PowerShell)
Use `Get-Content` no lugar de `<`:
```powershell
Get-Content arquivo.sql | docker exec -i chatbot_db psql -U chatbot_user -d chatbot
```

### `No module named 'app'`
Problema de import. Certifique-se de que existem `__init__.py` em:
```
Backend/
Backend/app/
Backend/app/api/
Backend/app/api/views/
```

### `404 Page not found`
A rota não foi registrada. Verifique `config/urls.py` e `Backend/app/api/urls.py`.

### `"O campo 'question' é obrigatório."`
No Postman: vá em **Body → raw → JSON** e envie:
```json
{ "question": "oi" }
```

### Superusuário sumiu após migrar para PostgreSQL
O superusuário estava no SQLite. O PostgreSQL é um banco novo e vazio. Recriar:
```bash
python manage.py createsuperuser
```

---

## Próximos Passos

- [x] Endpoint `GET /api/documents/` — listar documentos via Gemini Files API
- [x] Endpoint `POST /api/documents/` — cadastrar documento com upload para o Gemini
- [x] Endpoint `PATCH /api/documents/<id>/` — editar documento (nome, tipo e/ou arquivo)
- [x] Exclusão com confirmação em dois passos via token com TTL de 5 minutos
- [ ] Implementar Strategy Pattern — `infrastructure/llm/gemini_provider.py`
- [ ] Implementar Facade Pattern — `application/answer_question.py` (fluxo RAG completo)
- [ ] Gerar embeddings via Gemini e popular a coluna `embedding_vector`
- [ ] Implementar `permissions.py` — permissões customizadas para rotas admin
- [ ] Conectar o frontend ao login e ao chat
- [ ] Dashboard de métricas e relatórios (#68–#75)
- [ ] Adicionar testes automatizados

---

## ⚡ Resumo Rápido

### Backend
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1       # Windows
# source .venv/bin/activate      # Linux/macOS
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers google-genai psycopg2-binary pypdf python-dotenv
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Teste rápido do chat
```bash
POST http://127.0.0.1:8000/api/chat/
Content-Type: application/json

{ "question": "oi" }
```

---

> **Observações:** O backend foi migrado de FastAPI para Django REST Framework. O banco SQLite foi substituído por PostgreSQL via Docker. Os 42 documentos PDF estão indexados em 650 chunks. O Django está na raiz via `manage.py` e `config/`. A API do Gemini deve ser configurada via variável de ambiente. O projeto aplica os padrões Factory Method, Strategy e Repository do livro Gang of Four.
