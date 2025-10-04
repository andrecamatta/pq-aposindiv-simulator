# 🚀 Guia de Deploy - PrevLab

Este guia apresenta diferentes opções para fazer deploy da plataforma PrevLab em produção.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Deploy com Docker](#deploy-com-docker)
- [Deploy no Render.com](#deploy-no-rendercom)
- [Deploy no Fly.io](#deploy-no-flyio)
- [Deploy em VPS](#deploy-em-vps)
- [Deploy Separado (Backend + Frontend)](#deploy-separado-backend--frontend)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Banco de Dados](#banco-de-dados)

---

## 🎯 Visão Geral

**Stack Tecnológica:**
- **Backend**: FastAPI (Python 3.11+) com Uvicorn
- **Frontend**: React + Vite + TypeScript
- **Banco de Dados**: SQLite (default) ou PostgreSQL (recomendado para produção)
- **Gerenciador de Pacotes Python**: uv

**Arquivos de Configuração:**
- `backend/Dockerfile` - Imagem Docker do backend
- `frontend/Dockerfile` - Imagem Docker do frontend
- `docker-compose.yml` - Orquestração completa
- `render.yaml` - Deploy no Render.com
- `.env.example` - Exemplo de variáveis de ambiente

---

## 🐳 Deploy com Docker

### Opção 1: Docker Compose (Recomendado para começar)

```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd simulador-atuarial-individual

# 2. Copie e configure o arquivo .env
cp .env.example .env
# Edite .env conforme necessário

# 3. Build e start
docker-compose up -d

# 4. Verifique os logs
docker-compose logs -f

# 5. Acesse a aplicação
# Frontend: http://localhost
# Backend: http://localhost:8000
```

**Parar os serviços:**
```bash
docker-compose down
```

**Atualizar após mudanças no código:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Opção 2: Build Manual das Imagens

```bash
# Backend
cd backend
docker build -t prevlab-backend .
docker run -d -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DATABASE_URL=sqlite:///./data/db/prevlab.db \
  prevlab-backend

# Frontend
cd ../frontend
docker build -t prevlab-frontend \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 .
docker run -d -p 80:80 prevlab-frontend
```

---

## 🌐 Deploy no Render.com

**Vantagens:**
- ✅ Deploy gratuito (com limitações)
- ✅ HTTPS automático
- ✅ Deploy direto do GitHub
- ✅ PostgreSQL gratuito incluído

### Passo a Passo:

#### 1. Preparar o Repositório

```bash
# Certifique-se de que render.yaml está na raiz
git add render.yaml
git commit -m "Add Render configuration"
git push origin main
```

#### 2. Criar Conta no Render

1. Acesse [render.com](https://render.com)
2. Faça login com GitHub
3. Clique em "New +" → "Blueprint"

#### 3. Conectar Repositório

1. Selecione o repositório do PrevLab
2. Render detectará automaticamente o `render.yaml`
3. Clique em "Apply"

#### 4. Configurar Banco de Dados (Opcional)

Se quiser usar PostgreSQL:

1. Crie um PostgreSQL database no Render
2. Copie a URL de conexão
3. Atualize a variável `DATABASE_URL` no backend service

#### 5. Aguardar Deploy

- Backend estará disponível em: `https://prevlab-backend.onrender.com`
- Frontend estará disponível em: `https://prevlab-frontend.onrender.com`

### Notas Importantes:

⚠️ **Plano gratuito do Render:**
- Serviços ficam inativos após 15 minutos sem uso
- Podem levar 30-60 segundos para "acordar"
- Banco de dados gratuito tem limite de 90 dias

---

## ✈️ Deploy no Fly.io

**Vantagens:**
- ✅ SQLite persistente com volumes
- ✅ Muito rápido e flexível
- ✅ Boa camada gratuita
- ✅ Deploy global

### Passo a Passo:

#### 1. Instalar Fly CLI

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

#### 2. Login

```bash
fly auth login
```

#### 3. Deploy Backend

```bash
cd backend

# Criar app
fly launch --name prevlab-backend --region gru

# Criar volume para SQLite (1GB)
fly volumes create prevlab_data --size 1 --region gru

# Configurar variáveis de ambiente
fly secrets set DATABASE_URL="sqlite:///./data/db/prevlab.db"
fly secrets set LOG_LEVEL="info"

# Deploy
fly deploy
```

#### 4. Deploy Frontend

```bash
cd ../frontend

# Criar app
fly launch --name prevlab-frontend --region gru

# Configurar URL da API
fly secrets set VITE_API_BASE_URL="https://prevlab-backend.fly.dev"

# Deploy
fly deploy
```

#### 5. Acessar

- Backend: `https://prevlab-backend.fly.dev`
- Frontend: `https://prevlab-frontend.fly.dev`

### Comandos Úteis:

```bash
# Ver logs
fly logs

# Abrir dashboard
fly dashboard

# Verificar status
fly status

# Escalar (aumentar recursos)
fly scale vm shared-cpu-1x --memory 512
```

---

## 🖥️ Deploy em VPS

**Vantagens:**
- ✅ Controle total
- ✅ Custo previsível
- ✅ Performance dedicada

**Recomendações de VPS:**
- DigitalOcean ($6/mês)
- Linode ($5/mês)
- Vultr ($6/mês)
- Hetzner (~€4/mês)

### Passo a Passo (Ubuntu 22.04):

#### 1. Preparar Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y \
  git \
  docker.io \
  docker-compose \
  nginx \
  certbot \
  python3-certbot-nginx

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. Clonar Repositório

```bash
cd /opt
sudo git clone <seu-repositorio> prevlab
cd prevlab/simulador-atuarial-individual
```

#### 3. Configurar Variáveis

```bash
sudo cp .env.example .env
sudo nano .env

# Configure:
# - DATABASE_URL (usar PostgreSQL para produção)
# - CORS_ORIGINS com seu domínio
# - VITE_API_BASE_URL com seu domínio
```

#### 4. Iniciar com Docker Compose

```bash
sudo docker-compose up -d
```

#### 5. Configurar Nginx como Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/prevlab
```

Conteúdo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

Ativar site:

```bash
sudo ln -s /etc/nginx/sites-available/prevlab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Configurar HTTPS com Let's Encrypt

```bash
sudo certbot --nginx -d seu-dominio.com
```

---

## 🔀 Deploy Separado (Backend + Frontend)

Opção recomendada para produção profissional com CDN global.

### Backend: Railway / Render / Fly.io

Escolha uma das opções acima para o backend.

### Frontend: Vercel / Netlify / Cloudflare Pages

#### Deploy no Vercel:

```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Configurar variável de ambiente no dashboard:
# VITE_API_BASE_URL = https://seu-backend.onrender.com
```

#### Deploy no Netlify:

```bash
# Instalar Netlify CLI
npm i -g netlify-cli

# Deploy
cd frontend
netlify deploy --prod

# Configurar variável no dashboard:
# VITE_API_BASE_URL = https://seu-backend.onrender.com
```

#### Deploy no Cloudflare Pages:

1. Acesse [dash.cloudflare.com](https://dash.cloudflare.com)
2. Pages → Create a project
3. Connect to Git → Selecione o repositório
4. Configure:
   - **Build command**: `cd frontend && npm run build`
   - **Build output directory**: `frontend/dist`
   - **Environment variable**: `VITE_API_BASE_URL=https://seu-backend.onrender.com`

---

## 📝 Variáveis de Ambiente

Consulte [.env.example](.env.example) para ver todas as variáveis disponíveis.

### Backend Essenciais:

```bash
DATABASE_URL=sqlite:///./data/db/prevlab.db  # ou PostgreSQL
LOG_LEVEL=info
WORKERS=1
CORS_ORIGINS=https://seu-frontend.com
```

### Frontend Essenciais:

```bash
VITE_API_BASE_URL=https://seu-backend.com
```

---

## 🗄️ Banco de Dados

### SQLite (Default)

**Vantagens:**
- Zero configuração
- Perfeito para MVPs e baixo tráfego
- Sem custos adicionais

**Limitações:**
- Não recomendado para múltiplos usuários simultâneos
- Precisa de volumes persistentes (Fly.io, VPS)
- Não funciona em serverless (AWS Lambda)

**Quando usar:**
- Desenvolvimento
- MVPs
- Baixo tráfego (<100 usuários/dia)
- Deploy com volumes (Fly.io, VPS, Docker)

### PostgreSQL (Recomendado para Produção)

**Vantagens:**
- Suporta milhares de conexões simultâneas
- Transações robustas
- Backup e replicação nativos
- Funciona em qualquer plataforma

**Onde obter PostgreSQL gratuito:**
- Render.com (PostgreSQL gratuito, 90 dias)
- Supabase (500MB gratuito, ilimitado)
- ElephantSQL (20MB gratuito)
- Railway ($5 crédito/mês)

**Migração SQLite → PostgreSQL:**

1. Instalar PostgreSQL:

```bash
# No projeto
cd backend
uv add psycopg2-binary
```

2. Atualizar DATABASE_URL:

```bash
# PostgreSQL URL format:
DATABASE_URL=postgresql://user:password@host:port/dbname
```

3. O SQLModel/SQLAlchemy detecta automaticamente o tipo de banco!

---

## 🔍 Troubleshooting

### Problema: "Erro ao conectar com API"

**Solução:**
1. Verifique se `VITE_API_BASE_URL` está configurado corretamente no build
2. Verifique CORS no backend (`CORS_ORIGINS`)
3. Teste a API diretamente: `curl https://seu-backend.com/health`

### Problema: "SQLite database is locked"

**Solução:**
- Use PostgreSQL em produção
- Se usar SQLite, configure apenas 1 worker: `WORKERS=1`

### Problema: "Out of memory" no build

**Solução:**
- Aumentar memória da instância
- Usar plano pago
- Build localmente e fazer push da imagem Docker

### Problema: "Frontend não encontra backend"

**Solução:**
1. Frontend deve ser buildado com a URL correta do backend
2. Se usar proxy reverso (nginx), configure as rotas `/api` e `/ws`
3. Verifique se HTTPS está configurado corretamente

---

## 📊 Comparação de Plataformas

| Plataforma        | Custo Inicial | SQLite | PostgreSQL | HTTPS | Complexidade |
|-------------------|---------------|--------|------------|-------|--------------|
| Docker Compose    | $0 (local)    | ✅     | ✅         | ⚠️    | ⭐           |
| Render.com        | $0            | ⚠️     | ✅         | ✅    | ⭐           |
| Fly.io            | $0            | ✅     | ✅         | ✅    | ⭐⭐         |
| Railway           | $5/mês        | ⚠️     | ✅         | ✅    | ⭐           |
| VPS (DigitalOcean)| $6/mês        | ✅     | ✅         | ✅    | ⭐⭐⭐       |
| Vercel + Render   | $0            | ❌     | ✅         | ✅    | ⭐⭐         |

**Legenda:**
- ✅ Suportado nativamente
- ⚠️ Funciona mas não é ideal
- ❌ Não suportado

---

## 🎯 Recomendações Finais

### Para Testes/MVP:
🏆 **Render.com** - Zero configuração, deploy em minutos

### Para Produção Pequena:
🏆 **Fly.io** - SQLite persistente, rápido, controle total

### Para Produção Média/Grande:
🏆 **Backend**: Railway/Render com PostgreSQL
🏆 **Frontend**: Vercel/Cloudflare Pages
🏆 **Banco**: Supabase/Render PostgreSQL

### Para Máximo Controle:
🏆 **VPS** (DigitalOcean/Hetzner) + Docker + PostgreSQL + Nginx

---

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no repositório
- Consulte a documentação das plataformas
- Verifique os logs: `docker-compose logs` / `fly logs` / etc.

---

**Boa sorte com seu deploy! 🚀**
