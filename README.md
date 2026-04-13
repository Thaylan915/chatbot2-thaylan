# Chatbot IFES - RAG com Django, Gemini e React

Monorepo com backend em Django REST Framework, frontend em React (Vite), autenticação JWT, PostgreSQL com pgvector e fluxo RAG para perguntas sobre documentos institucionais.

## Visao geral

- Backend API: Django + DRF
- Frontend web: React + Vite
- Banco: PostgreSQL 16 + pgvector (Docker)
- IA: Gemini (geracao e embeddings)
- Documento base: PDFs em Documentos/

## Estrutura atual do projeto

```text
chatbot2-thaylan/
├── manage.py
├── config/
├── Backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── urls.py
│   │   │   └── views/
│   │   ├── application/
│   │   ├── documents/
│   │   ├── domain/
│   │   └── infrastructure/
│   └── tests/
├── frontend/
│   ├── src/
│   └── package.json
├── Documentos/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Tecnologias

### Backend
- Python 3.11 (compatibilidade com 3.10+)
- Django 5.1.15
- Django REST Framework 3.17.0
- djangorestframework-simplejwt 5.5.1
- django-cors-headers 4.9.0
- psycopg2-binary 2.9.11
- pypdf 6.9.1
- python-dotenv 1.2.2
- google-generativeai 0.8.6

### Frontend
- React 19
- Vite 8
- Axios
- React Router DOM

## Requisitos

- Python 3.10+
- Node.js 18+
- Docker Desktop
- Chave GEMINI_API_KEY

## Configuracao de ambiente

1. Crie o arquivo .env a partir do exemplo.

```bash
cp .env.example .env
```

No Windows PowerShell, se preferir:

```powershell
Copy-Item .env.example .env
```

2. Ajuste as variaveis principais no .env:

- GEMINI_API_KEY
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- DB_HOST
- DB_PORT
- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- CHAT_MODEL
- EMBEDDING_MODEL
- TOP_K

Valores recomendados para ambiente local:

- DB_HOST=127.0.0.1
- DB_PORT=5555
- CHAT_MODEL=gemini-1.5-flash
- EMBEDDING_MODEL=embedding-001
- TOP_K=5

Observacao importante:
- O docker-compose publica o PostgreSQL na porta 5555 (host) para 5432 (container).

## Como rodar localmente

### 1) Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Suba apenas o banco com Docker:

```powershell
docker-compose up -d db
```

Rode migracoes:

```powershell
python manage.py migrate
```

Opcional (primeiro acesso admin):

```powershell
python manage.py createsuperuser
```

Inicie a API:

```powershell
python manage.py runserver
```

API em:
- http://127.0.0.1:8000

### 2) Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend em:
- http://localhost:5173

## Indexacao de documentos

Comando:

```powershell
python manage.py indexar_documentos
```

Opcoes uteis:

```powershell
python manage.py indexar_documentos --forcar
python manage.py indexar_documentos --gerar-embeddings
python manage.py indexar_documentos --pasta Documentos
```

## Rotas da API (estado atual)

### Auth e JWT
- POST /api/auth/login/
- POST /api/auth/refresh/
- POST /api/token/
- POST /api/token/refresh/

### Chat
- POST /api/chat/iniciar/
- POST /api/chat/pergunta/
- GET /api/chat/<conversa_id>/historico/

### Documentos (admin)
- GET /api/documents/
- POST /api/documents/
- POST /api/documents/create/
- PATCH /api/documents/<id_documento>/
- DELETE /api/documents/<id_documento>/delete/
- DELETE /api/documents/<id_documento>/
- POST /api/documents/<id_documento>/confirm/

### Usuarios e perfil
- POST /api/users/register/
- GET /api/users/
- GET /api/users/me/
- PATCH /api/users/<user_id>/role/

### Logs admin
- GET /api/admin-logs/

## Testes

Suite validada nesta base:

```powershell
.\.venv\Scripts\python.exe manage.py test Backend.tests.api -v 2
```

Resultado observado:
- 20 testes executados
- 20 testes passando

## Arquitetura resumida

- api/views: camada HTTP
- application: casos de uso
- domain: contratos e regras
- infrastructure: implementacoes concretas
- documents: modelos e comando de indexacao

## Observacoes importantes

- O arquivo Backend/manage.py existe, mas esta vazio e nao e usado como entrada.
- A entrada correta do Django e o manage.py na raiz.
- Existe codigo legado/prototipo em partes do repositorio (ex.: referencias antigas em Backend/app/main.py e pasta chatbot/).
- O docker-compose define servico frontend com Dockerfile dentro de frontend/, mas esse arquivo nao existe atualmente.
- A biblioteca google-generativeai funciona no projeto, mas ja sinaliza descontinuacao futura em favor de google.genai.

## Problemas comuns

### Erro de import do Django
Se aparecer No module named django, execute os comandos com o Python da virtualenv:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

### Docker Desktop nao iniciado
Suba o Docker Desktop antes de rodar docker-compose.

### Erro de conexao com banco
Confirme:
- container chatbot_db em estado healthy
- DB_HOST e DB_PORT corretos
- porta 5555 disponivel no host

## Proximos passos recomendados

- Padronizar login do frontend para usar apenas um endpoint (custom ou SimpleJWT).
- Migrar integracao de IA de google-generativeai para google.genai.
- Revisar e remover codigo legado que nao participa do fluxo Django atual.
- Adicionar CI para executar testes automaticamente.
