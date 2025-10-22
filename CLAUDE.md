# Instruções do Projeto - Simulador Atuarial Individual

## 🐳 Subir com Containers (Podman/Docker) - RECOMENDADO

### Iniciar aplicação completa
```bash
cd simulador-atuarial-individual
./start-podman.sh
```

### URLs
- **Frontend**: http://localhost:8080
- **Backend**: http://localhost:8000

### Comandos úteis
```bash
# Ver logs
podman logs -f prevlab-backend
podman logs -f prevlab-frontend

# Parar containers
podman stop prevlab-backend prevlab-frontend

# Remover containers
podman rm prevlab-backend prevlab-frontend

# Rebuild imagens (após mudanças no código)
podman build --ulimit nofile=90000:90000 --network=none -f ./frontend/Dockerfile -t prevlab-frontend ./frontend
podman build --ulimit nofile=90000:90000 -f ./backend/Dockerfile -t prevlab-backend ./backend
```

### Detalhes técnicos
- **Networking**: `--network=host` (pasta networking para rootless)
- **Banco de dados**: SQLite com 17 tábuas de mortalidade pré-carregadas
- **Volumes**: `prevlab-backend-data` (banco), `prevlab-backend-logs` (logs)
- **Configuração**: `~/.config/containers/containers.conf` (pasta networking)

---

## 💻 Subir Localmente (Desenvolvimento)

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
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

---

## ☁️ Deploy em Produção (Railway.app)

### Deploy Rápido
```bash
cd simulador-atuarial-individual

# Conectar repositório ao Railway (via dashboard)
# https://railway.app/dashboard

# Ou via CLI
railway login
railway init
railway up
```

### Configuração necessária no Railway Dashboard

1. **Variáveis de ambiente**:
   ```bash
   DATABASE_URL=sqlite:///./data/db/prevlab.db
   LOG_LEVEL=info
   WORKERS=2
   CORS_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
   ```

2. **Volume persistente** (CRÍTICO para SQLite):
   - Mount Path: `/app/data`
   - Size: 1 GB (mínimo)

3. **Build**: Usa `Dockerfile.railway` automaticamente

### URLs
- **Produção**: `https://<seu-projeto>.railway.app`
- **Health Check**: `https://<seu-projeto>.railway.app/health`

### Documentação completa
Ver: `simulador-atuarial-individual/docs/DEPLOY_RAILWAY.md`