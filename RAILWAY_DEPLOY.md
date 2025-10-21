# 🚂 Deploy no Railway.app - PrevLab

Guia completo para fazer deploy do PrevLab no Railway.app (gratuito!)

## 💰 Plano Gratuito

Railway oferece:
- ✅ **$5 de crédito grátis por mês**
- ✅ ~500 horas de uso (suficiente para pequenos projetos)
- ✅ Backend sempre ativo (sem cold starts)
- ✅ Banco SQLite persistente em volume
- ✅ Deploy automático via GitHub

---

## 📋 Passo a Passo

### 1. Criar conta no Railway

1. Acesse https://railway.app
2. Clique em **"Start a New Project"** ou **"Login"**
3. Faça login com **GitHub** (recomendado)

### 2. Criar novo projeto

1. No dashboard, clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Autorize o Railway a acessar seus repositórios
4. Procure e selecione: **`andrecamatta/pq-aposindiv-simulator`**
5. Selecione a branch: **`claude/investigate-upload-issue-011CULWLF2YGczz4r3yAshuT`**

### 3. Configurar Backend

Após conectar o repositório:

1. Railway vai detectar o monorepo - clique em **"Add a service"**
2. Selecione **"Backend"** ou configure manualmente:
   - **Root Directory**: `simulador-atuarial-individual/backend`
   - **Build Command**: (deixe vazio - Railway detecta automaticamente)
   - **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

3. **Configurar variáveis de ambiente**:
   - Vá em **Settings → Variables**
   - Adicione:
     ```
     PYTHON_VERSION=3.11
     DATABASE_URL=sqlite:///./data/simulador.db
     LOG_LEVEL=info
     WORKERS=1
     ```

4. **Adicionar volume persistente** (para SQLite):
   - Vá em **Settings → Volumes**
   - Clique em **"New Volume"**
   - Mount Path: `/app/data`
   - Confirme

### 4. Configurar Frontend

1. No mesmo projeto, clique em **"New Service"** → **"GitHub Repo"**
2. Selecione o mesmo repositório
3. Configure:
   - **Root Directory**: `simulador-atuarial-individual/frontend`
   - **Build Command**: `npm run build`
   - **Start Command**: (Railway serve static files automaticamente)

4. **Configurar variáveis de ambiente**:
   - Vá em **Settings → Variables**
   - Adicione:
     ```
     NODE_VERSION=20
     VITE_API_BASE_URL=https://seu-backend.up.railway.app
     ```

   ⚠️ **Importante**: Substitua `seu-backend.up.railway.app` pela URL real do backend (copie da aba do backend)

### 5. Fazer Deploy

1. Railway vai fazer deploy automaticamente dos dois serviços
2. Aguarde o build completar (~5-10 minutos)
3. Verifique os logs em tempo real

### 6. Acessar aplicação

Após deploy completo:

1. **Backend**:
   - Vá em Settings → Networking → Generate Domain
   - URL: `https://seu-backend.up.railway.app`
   - Teste: `https://seu-backend.up.railway.app/health`

2. **Frontend**:
   - Vá em Settings → Networking → Generate Domain
   - URL: `https://seu-frontend.up.railway.app`
   - Acesse no navegador!

---

## 🔧 Configuração de CORS

Após obter a URL do frontend, volte ao backend e adicione variável:

```
CORS_ORIGINS=https://seu-frontend.up.railway.app
```

---

## 📊 Monitoramento

Railway mostra:
- ✅ Uso de CPU e RAM
- ✅ Logs em tempo real
- ✅ Créditos restantes ($5/mês)
- ✅ Métricas de deploy

---

## 🐛 Troubleshooting

### Backend não inicia
- Verifique logs para erros de dependência
- Confirme que `PYTHON_VERSION=3.11`
- Verifique se o volume está montado em `/app/data`

### Frontend não carrega backend
- Verifique `VITE_API_BASE_URL` está correto
- Confirme CORS configurado no backend
- Teste URL do backend diretamente

### Banco de dados vazio
- Confirme que volume está montado
- O banco será criado automaticamente na primeira execução

---

## 💡 Dicas

1. **Deploy automático**: Qualquer push no GitHub faz redeploy
2. **Logs**: Use Railway CLI para ver logs localmente
3. **Domínio customizado**: Disponível em Settings → Networking
4. **Upgrade**: Se acabar os $5/mês, upgrade por ~$5-10/mês

---

## 🆘 Precisa de ajuda?

Se algo não funcionar, compartilhe:
- Logs do Railway
- Mensagem de erro específica
- URL do serviço (backend ou frontend)

Boa sorte! 🚀
