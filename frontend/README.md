# Frontend - Chatbot IFES

Aplicacao web em React + Vite para interface do chatbot e area administrativa.

## Stack

- React 19
- Vite 8
- Axios
- React Router DOM
- ESLint

## Requisitos

- Node.js 18+
- npm 9+
- Backend rodando em http://127.0.0.1:8000

## Instalar e rodar

Na pasta frontend:

```bash
npm install
npm run dev
```

Aplicacao disponivel em:

- http://localhost:5173

## Scripts disponiveis

- npm run dev: inicia servidor de desenvolvimento
- npm run build: gera build de producao
- npm run preview: sobe preview local da build
- npm run lint: executa lint

## Integracao com API

Cliente HTTP principal:

- src/services/api.jsx

Configuracao atual:

- baseURL: http://127.0.0.1:8000
- injecao automatica de token JWT no header Authorization
- tratamento global de 401 (limpa tokens e redireciona para /)

Autenticacao no frontend:

- src/services/authService.js usa POST /api/token/

## Estrutura principal

```text
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   │   ├── api.jsx
│   │   └── authService.js
│   ├── App.jsx
│   └── main.jsx
├── public/
├── package.json
└── vite.config.js
```

## Fluxo de chat (resumo)

- A tela de chat envia perguntas para POST /api/chat/pergunta/
- O frontend armazena conversa_id retornado pela API para continuidade da conversa
- Em caso de erro, exibe mensagem de fallback para o usuario

## Observacoes

- Nao ha variavel de ambiente de API no frontend neste momento; a URL esta fixa em src/services/api.jsx.
- Se quiser preparar para multiplos ambientes (dev/homolog/prod), o proximo passo recomendado e migrar baseURL para VITE_API_URL.
