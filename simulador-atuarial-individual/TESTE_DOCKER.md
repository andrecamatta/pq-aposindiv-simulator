# Teste de Deploy Local com Podman - PrevLab

## ✅ Status: SUCESSO TOTAL

Conseguimos fazer deploy local completo usando Podman após resolver múltiplos problemas de kernel e configuração.

## 🔧 Problemas Encontrados e Soluções

### 1. Docker - Problemas de iptables (FALHOU)
**Erro**: `failed to create NAT chain DOCKER: iptables v1.8.10 (nf_tables): Could not fetch rule set generation id`

**Causa**: Conflito entre iptables-legacy e nf_tables no kernel do Pop!_OS

**Tentativas**:
- Switching to iptables-legacy: Falhou
- Carregar módulos do kernel: Falhou (módulos incompatíveis)
- Configurar Docker com `"iptables": false`: Falhou

**Solução**: Migrar para Podman

### 2. Podman - Networking netavark (RESOLVIDO)
**Erro**: `netavark: create bridge: Netlink error: Operation not supported (os error 95)`

**Causa**: Kernel não suporta operações netlink necessárias para bridge networking

**Solução**: Configurar pasta networking (rootless, userspace)
```bash
# ~/.config/containers/containers.conf
[network]
default_rootless_network_cmd = "pasta"
```

### 3. Frontend Build - EMFILE: too many open files (RESOLVIDO)
**Erro**: `EMFILE: too many open files` durante build do Vite

**Causa**: Limite padrão de file descriptors muito baixo para Vite build

**Solução**:
1. Aumentar ulimit durante build:
   ```bash
   podman build --ulimit nofile=90000:90000 ...
   ```

2. Configurar Vite para ignorar node_modules (vite.config.ts):
   ```typescript
   server: {
     watch: {
       usePolling: true,
       interval: 300,
       ignored: ['**/node_modules/**', '**/.git/**'],
     }
   }
   ```

### 4. Frontend Build - tailwind-merge não resolvido (RESOLVIDO)
**Erro**: `Rollup failed to resolve import "tailwind-merge"`

**Causa**: Build com networking habilitado causava problemas de resolução

**Solução**: Build frontend com `--network=none`:
```bash
podman build --network=none --ulimit nofile=90000:90000 ...
```

## 📦 Comandos de Build Finais

### Frontend
```bash
podman build --ulimit nofile=90000:90000 --network=none \
  -f ./frontend/Dockerfile \
  -t prevlab-frontend \
  --build-arg VITE_API_BASE_URL=/api \
  ./frontend
```

### Backend
```bash
podman build --ulimit nofile=90000:90000 \
  -f ./backend/Dockerfile \
  -t prevlab-backend \
  ./backend
```

## 🚀 Como Executar

### Opção 1: Script Automático (RECOMENDADO)
```bash
./start-podman.sh
```

### Opção 2: Manual
```bash
# Backend
podman run -d \
  --name prevlab-backend \
  --ulimit nofile=90000:90000 \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./data/db/prevlab.db \
  -e LOG_LEVEL=info \
  -v prevlab-backend-data:/app/data \
  localhost/prevlab-backend:latest

# Frontend
podman run -d \
  --name prevlab-frontend \
  --ulimit nofile=90000:90000 \
  -p 8080:80 \
  --add-host backend:host-gateway \
  localhost/prevlab-frontend:latest
```

## 🌐 Acessar Aplicação

- **Frontend**: http://localhost:8080
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📋 Comandos Úteis

### Ver Logs
```bash
podman logs -f prevlab-backend
podman logs -f prevlab-frontend
```

### Parar Containers
```bash
podman stop prevlab-backend prevlab-frontend
```

### Remover Containers
```bash
podman rm prevlab-backend prevlab-frontend
```

### Rebuild Imagens
```bash
# Limpar tudo
podman system prune -a -f

# Rebuild
podman build --ulimit nofile=90000:90000 --network=none -f ./frontend/Dockerfile -t prevlab-frontend ./frontend
podman build --ulimit nofile=90000:90000 -f ./backend/Dockerfile -t prevlab-backend ./backend
```

## 🔑 Configurações Importantes

### 1. Podman Networking (pasta)
Arquivo: `~/.config/containers/containers.conf`
```toml
[network]
default_rootless_network_cmd = "pasta"
```

### 2. Vite Watch Config
Arquivo: `frontend/vite.config.ts`
```typescript
server: {
  watch: {
    usePolling: true,
    interval: 300,
    ignored: ['**/node_modules/**', '**/.git/**'],
  }
}
```

### 3. Dockerfiles
- **Frontend**: Build com `--network=none` (não precisa de rede)
- **Backend**: Build com rede (precisa baixar pacotes apt e pip)
- **Ambos**: Usar registries completos (`docker.io/library/...`)

## 🎯 Arquitetura Final

```
┌─────────────────────────────────────────┐
│         Frontend (localhost:8080)        │
│         nginx + React/Vite build        │
│                                         │
│  - Usa pasta networking (userspace)     │
│  - ulimit: 90000 file descriptors      │
│  - Proxy /api → host-gateway:8000      │
└─────────────────────────────────────────┘
                    │
                    ├─ (host-gateway)
                    ↓
┌─────────────────────────────────────────┐
│         Backend (localhost:8000)         │
│         FastAPI + Python 3.11            │
│                                         │
│  - Usa pasta networking (userspace)     │
│  - ulimit: 90000 file descriptors      │
│  - SQLite database em volume            │
└─────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### Container não inicia
1. Verificar se pasta está configurado: `cat ~/.config/containers/containers.conf`
2. Ver logs: `podman logs <container-name>`
3. Verificar ulimit: `podman inspect <container> | grep -i ulimit`

### Build falha com EMFILE
1. Aumentar ulimit do sistema: `ulimit -n 90000`
2. Usar flag `--ulimit nofile=90000:90000` no build

### Networking não funciona
1. Verificar pasta instalado: `which pasta`
2. Recriar containers com `--add-host backend:host-gateway`
3. Verificar portas: `ss -tulpn | grep -E '8000|8080'`

## 📚 Referências

- [Podman Networking](https://www.redhat.com/en/blog/container-networking-podman)
- [Pasta Networking](https://github.com/containers/podman/blob/main/docs/tutorials/basic_networking.md)
- [Vite EMFILE Fix](https://github.com/vitejs/vite/issues/13912)
- [Podman Rootless](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md)

## ✨ Próximos Passos

1. ✅ Deploy local funcionando
2. ⏭️ Testar funcionalidades da aplicação (pymort tables, simulações)
3. ⏭️ Deploy em produção (Render.com/Fly.io)
4. ⏭️ CI/CD pipeline
