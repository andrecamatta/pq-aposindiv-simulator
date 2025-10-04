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