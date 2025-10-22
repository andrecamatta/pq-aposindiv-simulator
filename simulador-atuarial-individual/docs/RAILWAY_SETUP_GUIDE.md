# Guia de Setup Railway - PrevLab

## 🎯 Objetivo

Configurar o projeto **PrevLab** no Railway com o nome `prevlab`, gerando um domínio como:
- `prevlab-production.up.railway.app` ou
- `prevlab.up.railway.app`

---

## 📋 Pré-requisitos

- Conta no Railway.app (gratuita)
- Repositório Git do projeto em GitHub/GitLab/Bitbucket
- Código commitado e pushed

---

## 🚀 Setup Passo-a-Passo

### Etapa 1: Criar Conta Railway

1. Acesse https://railway.app
2. Clique em **"Start a New Project"** ou **"Login"**
3. Autentique com GitHub (recomendado) ou email
4. Confirme sua conta via email se necessário

### Etapa 2: Conectar Repositório GitHub

1. No dashboard Railway (https://railway.app/dashboard):
   - Clique em **"New Project"**
   - Selecione **"Deploy from GitHub repo"**

2. Autorizar Railway:
   - Clique em **"Configure GitHub App"**
   - Selecione o repositório `pq_aposindiv`
   - Clique em **"Install & Authorize"**

3. Selecionar repositório:
   - Na lista de repositórios, clique em `pq_aposindiv`

### Etapa 3: Configurar Projeto como "prevlab"

**IMPORTANTE**: O nome do projeto determina o domínio Railway!

#### Opção A: Nomear durante criação (Recomendado)

1. Após selecionar o repositório, Railway mostra configuração
2. **ANTES** de clicar em "Deploy", veja o campo **"Service Name"** ou **"Project Name"**
3. Digite: `prevlab`
4. Clique em **"Deploy Now"**

#### Opção B: Renomear após criação

1. Se já criou o projeto com nome diferente:
   - Vá em **Settings** (ícone de engrenagem)
   - Seção **"Service"** → Campo **"Name"**
   - Altere para: `prevlab`
   - Clique em **"Save"**

2. Para renomear o projeto (opcional):
   - No menu superior, clique no nome do projeto
   - Clique em **"Settings"**
   - Seção **"General"** → Campo **"Project Name"**
   - Altere para: `PrevLab` ou `prevlab`
   - Clique em **"Save"**

### Etapa 4: Configurar Root Directory

Railway precisa saber onde está o código do monorepo.

1. Em **Settings** → **"Source"**:
   - **Root Directory**: `simulador-atuarial-individual`
   - **Branch**: `main` (ou `master`)
   - Clique em **"Save"**

### Etapa 5: Configurar Variáveis de Ambiente

1. No menu lateral, clique em **"Variables"**
2. Adicione as seguintes variáveis (uma por vez):

```bash
DATABASE_URL = sqlite:///./data/db/prevlab.db
LOG_LEVEL = info
WORKERS = 2
PYTHONUNBUFFERED = 1
```

3. **CORS**: Adicione após deploy inicial (precisamos do domínio):
```bash
CORS_ORIGINS = https://${{RAILWAY_PUBLIC_DOMAIN}}
```

   ⚠️ **Importante**: Use exatamente `${{RAILWAY_PUBLIC_DOMAIN}}` - Railway substitui automaticamente!

### Etapa 6: Configurar Volume Persistente

**CRÍTICO**: SQLite precisa de volume persistente!

1. No menu lateral, clique em **"Settings"**
2. Role até **"Volumes"**
3. Clique em **"+ New Volume"**
4. Configure:
   - **Mount Path**: `/app/data`
   - **Size**: `1` GB (mínimo recomendado)
5. Clique em **"Add Volume"**

### Etapa 7: Iniciar Deploy

1. Se o deploy não iniciou automaticamente:
   - Clique em **"Deploy"** no menu
   - Ou vá em **Settings** → **"Redeploy"**

2. Aguarde o build (~5-10 minutos na primeira vez)
   - Railway baixa código
   - Executa `Dockerfile.railway`
   - Build do frontend (Vite)
   - Instalação de dependências Python
   - Cria imagem Docker
   - Inicia container

3. Monitore o progresso:
   - Clique em **"Deployments"** para ver logs em tempo real
   - Procure por mensagens de erro (linhas vermelhas)

### Etapa 8: Obter Domínio Gerado

1. Após deploy bem-sucedido (status verde):
   - Vá em **"Settings"** → **"Domains"**
   - Railway gerou automaticamente um domínio:
     - Formato: `prevlab-production.up.railway.app`
     - Ou: `prevlab.up.railway.app`

2. Copie o domínio e teste:
```bash
# Health check
curl https://prevlab-production.up.railway.app/health

# Deve retornar algo como:
{"status": "ok", "version": "0.1.0"}
```

3. Acesse no navegador:
```
https://prevlab-production.up.railway.app
```

### Etapa 9: Atualizar CORS com Domínio Real

1. Volte em **"Variables"**
2. Edite a variável `CORS_ORIGINS`:
   - **Antes**: `https://${{RAILWAY_PUBLIC_DOMAIN}}`
   - **Depois**: `https://prevlab-production.up.railway.app` (seu domínio real)

   ⚠️ Ou mantenha `${{RAILWAY_PUBLIC_DOMAIN}}` para funcionar automaticamente!

3. Clique em **"Save"**
4. Railway redeploy automaticamente

---

## 🔍 Verificação de Funcionamento

### 1. Health Check
```bash
curl https://prevlab-production.up.railway.app/health
```

Esperado:
```json
{"status": "ok", "version": "0.1.0"}
```

### 2. Frontend
Acesse no navegador:
```
https://prevlab-production.up.railway.app
```

Deve carregar a interface do simulador.

### 3. API Backend
```bash
curl https://prevlab-production.up.railway.app/api/health
```

Deve retornar o mesmo JSON do health check.

### 4. Tábuas de Mortalidade
No frontend:
1. Vá em **"Tábuas de Mortalidade"**
2. Verifique se as 17 tábuas estão listadas
3. Se estiverem vazias, o volume não foi configurado corretamente!

---

## 📊 Domínios Railway - Entendendo o Formato

Railway gera domínios automaticamente baseado em:

### Formato Padrão
```
<nome-do-servico>-<ambiente>.up.railway.app
```

**Exemplos**:
- `prevlab-production.up.railway.app` (mais comum)
- `prevlab.up.railway.app` (mais raro)
- `prevlab-staging.up.railway.app` (se tiver ambiente staging)

### Você NÃO pode escolher:
- ❌ `prevlab.railway.app` (reservado para Railway)
- ❌ `meudominio.railway.app` (não existe essa opção)

### Você PODE configurar:
- ✅ Nome do serviço: `prevlab` (gera `prevlab-production.up.railway.app`)
- ✅ Domínio customizado próprio: `prevlab.com.br` (requer DNS)

---

## 🌐 Configurar Domínio Customizado (Opcional)

Se você tiver um domínio próprio (ex: `prevlab.com.br`):

### 1. Adicionar Domínio no Railway

1. Em **Settings** → **"Domains"**
2. Clique em **"+ Custom Domain"**
3. Digite: `prevlab.com.br`
4. Railway fornece um CNAME: `<hash>.railway.app`

### 2. Configurar DNS

No seu provedor DNS (Registro.br, Cloudflare, etc):

```bash
# Adicione registro CNAME
Tipo: CNAME
Nome: @  (ou prevlab)
Valor: <hash>.railway.app  (fornecido pelo Railway)
TTL: 3600
```

### 3. Aguardar Propagação

- DNS leva 5 minutos a 48 horas para propagar
- Verifique com: `dig prevlab.com.br`

### 4. Atualizar CORS

```bash
CORS_ORIGINS = https://prevlab.com.br
```

---

## 🐛 Troubleshooting Comum

### Domínio não está acessível

**Sintoma**: `502 Bad Gateway` ou `Service Unavailable`

**Soluções**:
1. Verificar logs:
   - **Deployments** → Último deploy → **View Logs**
2. Verificar se build completou:
   - Status deve estar verde
3. Verificar health check:
   ```bash
   curl https://prevlab-production.up.railway.app/health
   ```

### Tábuas de mortalidade vazias

**Sintoma**: Interface carrega, mas tábuas não aparecem

**Causa**: Volume não configurado

**Solução**:
1. **Settings** → **Volumes** → Verificar se existe volume
2. Mount path DEVE ser `/app/data`
3. Redeploy: **Settings** → **"Redeploy"**

### Erro de CORS

**Sintoma**: Console do navegador mostra erro CORS

**Solução**:
```bash
# Atualizar variável
CORS_ORIGINS = https://${{RAILWAY_PUBLIC_DOMAIN}}
```

### Build muito lento (>15 min)

**Causa**: Railway pode estar com alta demanda

**Soluções**:
1. Aguardar (normal na primeira vez)
2. Verificar se `.railwayignore` está correto
3. Considerar upgrade para plano Pro (build prioritário)

---

## 💡 Dicas Importantes

1. **Nome do serviço**: Use `prevlab` (minúsculas, sem espaços)
2. **Volume**: SEMPRE configure ANTES do primeiro deploy
3. **CORS**: Use `${{RAILWAY_PUBLIC_DOMAIN}}` para funcionar automaticamente
4. **Logs**: Monitore logs durante primeiro deploy
5. **Custos**: ~$5/mês (monitorar no dashboard)

---

## 📚 Próximos Passos

Após deploy bem-sucedido:

1. ✅ Testar todas as funcionalidades
2. ✅ Configurar monitoramento (Railway Metrics)
3. ✅ Configurar alertas de downtime
4. ✅ Documentar domínio final para equipe
5. ✅ (Opcional) Configurar domínio customizado

---

## 🆘 Suporte

**Railway**:
- Discord: https://discord.gg/railway
- Docs: https://docs.railway.app
- Status: https://status.railway.app

**PrevLab**:
- Issues: GitHub do projeto
- Email: [seu email de suporte]

---

**Última atualização**: 2025-10-22
