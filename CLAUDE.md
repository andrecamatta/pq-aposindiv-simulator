# Instruções do Projeto - Simulador Atuarial Individual

## 💻 Desenvolvimento Local

### Backend
```bash
cd simulador-atuarial-individual/backend
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd simulador-atuarial-individual/frontend
npm run dev
```

### URLs
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173

### Dependências

#### Backend (Python)
- Python 3.11+
- uv (gerenciador de pacotes)
- SQLite com banco de tábuas de mortalidade

#### Frontend (React/TypeScript)
- Node.js 20+
- npm

---

## ☁️ Deploy em Produção (Railway.app)

### Configuração Automática

O projeto está configurado para deploy automático no Railway via GitHub:

1. **Conecte o repositório** no Railway dashboard
2. **Railway detecta automaticamente**:
   - `Dockerfile` (na raiz do repositório)
   - `railway.toml` (configuração de build e deploy)
3. **Build e deploy automáticos** a cada push no branch `master`

### Variáveis de Ambiente Obrigatórias

Configure no Railway Dashboard (Settings → Variables):

```bash
DATABASE_URL=sqlite:///./data/simulador.db
LOG_LEVEL=info
WORKERS=2
CORS_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
```

### Volume Persistente (CRÍTICO)

O Railway **DEVE** ter um volume para persistir o banco SQLite:

- **Settings → Volumes → New Volume**
- **Mount Path**: `/app/data`
- **Size**: 1 GB (mínimo recomendado)

⚠️ **Sem volume, as tábuas de mortalidade serão perdidas a cada deploy!**

### URLs

- **Produção**: `https://<seu-projeto>.railway.app`
- **Health Check**: `https://<seu-projeto>.railway.app/health`
- **API**: `https://<seu-projeto>.railway.app/api/*`

### Arquitetura do Deploy

O Railway usa um **monorepo integrado** com:
- **Nginx** (porta dinâmica `$PORT`) servindo frontend + proxy para backend
- **Uvicorn** (porta 8000) rodando FastAPI backend
- **Supervisor** gerenciando ambos os processos
- **SQLite** persistido em volume

### Troubleshooting

Se o deploy falhar:

1. Verifique logs no Railway dashboard
2. Confirme que o volume foi criado e está montado em `/app/data`
3. Verifique se as variáveis de ambiente estão corretas
4. Healthcheck demora ~60s, aguarde antes de concluir falha

---

## 📚 Documentação

- Banco de dados: SQLite com 17+ tábuas de mortalidade pré-carregadas
- API: FastAPI com validação Pydantic
- Frontend: React 19 + TypeScript + Vite + Tailwind CSS
- Cálculos atuariais: Biblioteca Pymort
