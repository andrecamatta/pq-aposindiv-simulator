#!/bin/bash

# Script para rodar os containers do PrevLab com Podman
# Usa pasta networking (rootless) em vez de bridge networks

echo "🚀 Iniciando PrevLab com Podman..."

# Limpar containers anteriores
echo "🧹 Limpando containers anteriores..."
podman stop prevlab-backend prevlab-frontend 2>/dev/null || true
podman rm prevlab-backend prevlab-frontend 2>/dev/null || true

# Criar volumes se não existirem
echo "📦 Criando volumes..."
podman volume create prevlab-backend-data 2>/dev/null || true
podman volume create prevlab-backend-logs 2>/dev/null || true

# Copiar banco de dados da imagem para o volume (se ainda não existe)
echo "💾 Copiando banco de dados para o volume..."
podman run --rm -v prevlab-backend-data:/volume localhost/prevlab-backend:latest sh -c "
  if [ ! -f /volume/simulador.db ]; then
    cp -v /app/data/simulador.db /volume/simulador.db
    echo '  ✅ Banco copiado com sucesso!'
  else
    echo '  ℹ️  Banco já existe no volume'
  fi
"

# Rodar backend com network=host
echo "🔧 Iniciando backend..."
podman run -d \
  --name prevlab-backend \
  --network=host \
  --ulimit nofile=90000:90000 \
  -e DATABASE_URL=sqlite:///./data/db/prevlab.db \
  -e LOG_LEVEL=info \
  -e WORKERS=1 \
  -e CORS_ORIGINS="http://localhost,http://localhost:8080,http://localhost:8000" \
  -v prevlab-backend-data:/app/data \
  -v prevlab-backend-logs:/app/logs \
  localhost/prevlab-backend:latest

# Aguardar backend iniciar
echo "⏳ Aguardando backend iniciar..."
sleep 5

# Rodar frontend com network=host
echo "🎨 Iniciando frontend..."
podman run -d \
  --name prevlab-frontend \
  --network=host \
  --ulimit nofile=90000:90000 \
  localhost/prevlab-frontend:latest

echo ""
echo "✅ PrevLab iniciado com sucesso!"
echo ""
echo "📍 Acesse:"
echo "   Frontend: http://localhost:8080"
echo "   Backend:  http://localhost:8000"
echo ""
echo "📋 Para ver logs:"
echo "   podman logs -f prevlab-backend"
echo "   podman logs -f prevlab-frontend"
echo ""
echo "🛑 Para parar:"
echo "   podman stop prevlab-backend prevlab-frontend"
echo ""
