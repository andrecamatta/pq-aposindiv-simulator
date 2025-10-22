# Deploy no Railway.app - PrevLab

## 📋 Visão Geral

Este guia detalha o processo completo de deploy do **PrevLab** (Simulador Atuarial Individual) no Railway.app usando uma arquitetura de **monorepo integrado**.

### Arquitetura

- **Frontend**: React/Vite servido via Nginx (porta $PORT)
- **Backend**: FastAPI/Uvicorn (porta 8000)
- **Proxy**: Nginx faz proxy de `/api/*` para backend
- **Gerenciamento**: Supervisord coordena ambos os processos
- **Banco de dados**: SQLite em volume persistente

### 🌐 Nomenclatura e Domínio

**Nome sugerido do projeto**: `prevlab`

**Domínio gerado automaticamente pelo Railway**:
- `prevlab-production.up.railway.app` (mais comum)
- ou `prevlab.up.railway.app`

> ⚠️ **Importante**: Você NÃO pode escolher `prevlab.railway.app` (reservado). Railway gera domínios no formato `<nome-servico>-<ambiente>.up.railway.app` automaticamente.

**Guia detalhado de setup**: Ver [RAILWAY_SETUP_GUIDE.md](./RAILWAY_SETUP_GUIDE.md) para instruções passo-a-passo de como nomear o projeto corretamente.

---

## 🚀 Deploy Passo-a-Passo

### 1. Pré-requisitos

- Conta no [Railway.app](https://railway.app)
- Repositório Git do projeto (GitHub, GitLab ou Bitbucket)
- Railway CLI (opcional, mas recomendado)

```bash
# Instalar Railway CLI (opcional)
npm install -g @railway/cli

# Login
railway login
```

### 2. Criar Novo Projeto no Railway

> 💡 **Dica**: Nomeie o projeto/serviço como `prevlab` para gerar domínio `prevlab-production.up.railway.app`. Ver [RAILWAY_SETUP_GUIDE.md](./RAILWAY_SETUP_GUIDE.md) para detalhes.

#### Via Dashboard (Recomendado)

1. Acesse https://railway.app/dashboard
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Autorize Railway a acessar seu repositório
5. Selecione o repositório `pq_aposindiv`
6. **IMPORTANTE**: Antes de clicar "Deploy":
   - Nomeie o serviço como: `prevlab`
   - Configure **Root Directory**: `simulador-atuarial-individual`
   - **Builder**: Dockerfile (detectado automaticamente)

#### Via CLI

```bash
cd /path/to/pq_aposindiv/simulador-atuarial-individual
railway init
railway up
```

### 3. Configurar Variáveis de Ambiente

No dashboard do Railway, vá em **Variables** e adicione:

```bash
# Backend
DATABASE_URL=sqlite:///./data/db/prevlab.db
LOG_LEVEL=info
WORKERS=2
PYTHONUNBUFFERED=1

# CORS - Adicionar domínio Railway após deploy
CORS_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
```

**Importante**: A variável `PORT` é injetada automaticamente pelo Railway.

### 4. Configurar Volume Persistente

⚠️ **CRÍTICO**: SQLite precisa de volume persistente ou dados serão perdidos a cada deploy!

1. No dashboard, vá em **Settings** → **Volumes**
2. Clique em **"New Volume"**
3. Configure:
   - **Mount Path**: `/app/data`
   - **Size**: `1 GB` (mínimo recomendado)
4. Clique em **"Add Volume"**

### 5. Fazer Deploy

#### Primeira vez

Após configurar variáveis e volume, o Railway inicia o build automaticamente.

#### Deploys subsequentes

Railway detecta commits no branch configurado (geralmente `main`/`master`) e faz deploy automático.

Para forçar redeploy:
```bash
railway up --detach
```

### 6. Acessar Aplicação

Após build bem-sucedido (~5-10 min), acesse:

```
https://<seu-projeto>.railway.app
```

O domínio é gerado automaticamente. Para ver:
- Dashboard → **Settings** → **Domains**

---

## 🔧 Configurações Avançadas

### Domínio Customizado

1. No dashboard: **Settings** → **Domains** → **Custom Domain**
2. Adicione seu domínio (ex: `prevlab.com.br`)
3. Configure DNS:
   ```
   CNAME: prevlab.com.br → <seu-projeto>.railway.app
   ```
4. Aguarde propagação DNS (~15 min)

### Escalar Aplicação

```bash
# Aumentar workers Uvicorn
railway variables set WORKERS=4

# Aumentar réplicas (plano Pro)
railway settings set replicas=2
```

### Monitoramento

1. **Logs em tempo real**:
   ```bash
   railway logs
   ```

2. **Métricas**:
   - Dashboard → **Metrics**
   - CPU, Memória, Requisições, Latência

3. **Health Check**:
   - Automático via `/health`
   - Configure alertas em **Settings** → **Health Check**

### Banco de Dados PostgreSQL (Opcional)

Se quiser migrar de SQLite para PostgreSQL:

1. Adicione serviço PostgreSQL:
   ```bash
   railway add --plugin postgresql
   ```

2. Railway cria automaticamente `DATABASE_URL`

3. Atualize código backend para usar PostgreSQL:
   ```python
   # src/config.py
   DATABASE_URL = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
   ```

4. Migre dados:
   ```bash
   # Script de migração SQLite → PostgreSQL
   python scripts/migrate_sqlite_to_postgres.py
   ```

---

## 🐛 Troubleshooting

### Build Falha

**Sintoma**: Build fica travado ou retorna erro.

**Soluções**:

1. Verificar logs:
   ```bash
   railway logs --build
   ```

2. Verificar Dockerfile:
   ```bash
   # Testar localmente
   docker build -f Dockerfile.railway -t prevlab-test .
   ```

3. Aumentar timeout (se build > 10min):
   - Settings → Build → Timeout: `20 minutes`

### Aplicação não inicia

**Sintoma**: Deploy bem-sucedido, mas aplicação offline.

**Soluções**:

1. Verificar logs runtime:
   ```bash
   railway logs
   ```

2. Verificar health check:
   ```bash
   curl https://<seu-projeto>.railway.app/health
   ```

3. Verificar variáveis de ambiente:
   - Dashboard → Variables
   - Confirmar `PORT`, `DATABASE_URL`, `CORS_ORIGINS`

### Banco de dados zerado

**Sintoma**: Após deploy, tábuas de mortalidade sumiram.

**Causa**: Volume não configurado corretamente.

**Solução**:

1. Verificar volume:
   - Dashboard → Settings → Volumes
   - Mount path DEVE ser `/app/data`

2. Reiniciar serviço:
   ```bash
   railway restart
   ```

### Erro de CORS

**Sintoma**: Frontend não consegue chamar API (erro 403/CORS).

**Solução**:

1. Atualizar `CORS_ORIGINS`:
   ```bash
   railway variables set CORS_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
   ```

2. Se usar domínio customizado:
   ```bash
   railway variables set CORS_ORIGINS=https://prevlab.com.br
   ```

### Performance lenta

**Soluções**:

1. Aumentar workers:
   ```bash
   railway variables set WORKERS=4
   ```

2. Upgrade plano Railway (mais CPU/memória)

3. Considerar PostgreSQL:
   - SQLite tem limitações de concorrência
   - PostgreSQL é mais robusto para múltiplos usuários

---

## 💰 Custos Estimados

| Item | Custo |
|------|-------|
| Serviço base (512MB RAM) | ~$5/mês |
| Volume 1GB (persistente) | ~$0.25/mês |
| **Total** | **~$5.25/mês** |

**Notas**:
- Railway cobra por uso (pay-as-you-go)
- Plano Hobby: $5/mês (500h CPU grátis)
- Plano Pro: $20/mês (uso ilimitado)
- Volumes: $0.25/GB/mês

---

## 📊 Checklist de Deploy

- [ ] Código commitado no Git
- [ ] Projeto criado no Railway
- [ ] Repositório conectado
- [ ] Variáveis de ambiente configuradas
- [ ] Volume persistente criado (`/app/data`)
- [ ] Build executado com sucesso
- [ ] Health check respondendo (`/health`)
- [ ] Frontend acessível
- [ ] API respondendo (`/api/...`)
- [ ] Tábuas de mortalidade carregadas
- [ ] WebSocket funcionando (se aplicável)
- [ ] CORS configurado para domínio Railway

---

## 🔄 Workflow Recomendado

### Desenvolvimento

```bash
# Local
npm run dev          # Frontend: http://localhost:5173
uvicorn src.api.main:app --reload  # Backend: http://localhost:8000
```

### Staging (Branch feature)

```bash
git checkout -b feature/nova-feature
git push origin feature/nova-feature

# Railway: criar ambiente separado para feature
railway environment --name staging
railway up
```

### Produção (Branch main)

```bash
git checkout main
git merge feature/nova-feature
git push origin main

# Railway faz deploy automático
```

---

## 📚 Recursos Adicionais

- [Documentação Railway](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## 🆘 Suporte

**Problemas com Railway**:
- Discord: https://discord.gg/railway
- Email: team@railway.app

**Problemas com PrevLab**:
- Issues: https://github.com/seu-user/pq_aposindiv/issues
- Email: [seu email]

---

**Última atualização**: 2025-10-22
