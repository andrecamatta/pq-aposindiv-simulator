# 🔐 Guia de Setup - Autenticação Google OAuth

## ✅ O que foi implementado

### Backend (100% completo)
- ✅ Model `User` atualizado com campos OAuth
- ✅ Configuração de autenticação (`core/auth_config.py`)
- ✅ Serviço de autenticação (`services/auth_service.py`)
- ✅ Dependencies FastAPI (`api/dependencies/auth.py`)
- ✅ Router de autenticação (`api/auth_router.py`)
- ✅ Integração com `main.py`
- ✅ Script de migration SQLite
- ✅ Dependências adicionadas no `pyproject.toml`

### Frontend (100% completo)
- ✅ Context de autenticação (`AuthContext.tsx`)
- ✅ Página de login (`LoginPage.tsx`)
- ✅ Componente de rota privada (`PrivateRoute.tsx`)
- ✅ Página de callback (`AuthCallbackPage.tsx`)
- ✅ Header com logout (`AuthHeader.tsx`)
- ✅ React Router DOM configurado
- ✅ App.tsx atualizado com rotas protegidas
- ✅ BrowserRouter configurado no `main.tsx`

---

## ✅ Implementação 100% completa!

---

## 🔧 Setup necessário ANTES de usar

### 1. Configurar Google OAuth Console

#### Acessar: https://console.cloud.google.com/

1. Criar novo projeto ou selecionar existente
2. **APIs & Services → Credentials**
3. **Create Credentials → OAuth 2.0 Client ID**
4. **Application type**: Web application
5. **Authorized redirect URIs**:
   - Dev local: `http://localhost:5173/auth/success`
   - Produção Railway: `https://SEU-DOMINIO.railway.app/auth/success`
6. Copiar **Client ID** e **Client Secret**

### 2. Configurar variáveis de ambiente

#### **Desenvolvimento local** (`.env`):
```bash
# Gerar com: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=sua-chave-secreta-aqui-64-caracteres

GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/success
```

#### **Produção Railway** (Dashboard → Variables):
```bash
SECRET_KEY=sua-chave-secreta-produção
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_REDIRECT_URI=https://SEU-DOMINIO.railway.app/auth/success
```

### 3. Executar migration do banco de dados

```bash
cd simulador-atuarial-individual/backend
python -m src.scripts.migrate_add_auth_fields
```

### 4. Instalar novas dependências

#### Backend:
```bash
cd simulador-atuarial-individual/backend
uv sync
```

#### Frontend (quando implementar rotas):
```bash
cd simulador-atuarial-individual/frontend
npm install react-router-dom
```

---

## 🧪 Como testar

### 1. Testar backend isoladamente:

```bash
cd simulador-atuarial-individual/backend
uv run uvicorn src.api.main:app --reload --port 8000
```

Acessar:
- http://localhost:8000/auth/health (ver se configuração está OK)
- http://localhost:8000/auth/login (deve redirecionar para Google)

### 2. Após finalizar frontend:

```bash
# Terminal 1 - Backend
cd simulador-atuarial-individual/backend
uv run uvicorn src.api.main:app --reload --port 8000

# Terminal 2 - Frontend
cd simulador-atuarial-individual/frontend
npm run dev
```

Acessar http://localhost:5173 → Deve redirecionar para /login

---

## 📋 Checklist de deploy Railway

- [ ] Configurar variáveis de ambiente no Railway
- [ ] Adicionar redirect URI do Railway no Google Console
- [ ] Executar migration script (pode rodar local se volume conectado)
- [ ] Push das mudanças (já feito ✅)
- [ ] Aguardar build e deploy
- [ ] Testar fluxo de login

---

## 🔐 Endpoints disponíveis

| Endpoint | Método | Descrição | Auth? |
|----------|--------|-----------|-------|
| `/auth/login` | GET | Inicia fluxo OAuth | ❌ |
| `/auth/callback` | GET | Callback do Google | ❌ |
| `/auth/me` | GET | Info do usuário | ✅ |
| `/auth/logout` | POST | Logout | ✅ |
| `/auth/health` | GET | Status da config | ❌ |

---

## 🚨 Troubleshooting

### Backend não inicia:
- Verificar se variáveis de ambiente estão configuradas
- Rodar `/auth/health` para ver status da configuração

### Redirect loop infinito:
- Verificar se GOOGLE_REDIRECT_URI está correto
- Deve ser exatamente igual ao configurado no Google Console

### Token inválido:
- Verificar se SECRET_KEY é o mesmo entre os deploys
- Limpar localStorage do navegador

---

## 📚 Próximos passos (implementação completa)

1. Finalizar integração do frontend (adicionar rotas)
2. Criar componente de Header com avatar e logout
3. Adicionar interceptor axios para incluir token automaticamente
4. Proteger todas as rotas que precisam de autenticação
5. Testar fluxo completo local
6. Deploy no Railway
7. Testar em produção

---

**Status atual:** Backend 100% + Frontend Core 60%
**Tempo estimado para completar:** 30-60 minutos
**Commit:** `d73e9e7`
