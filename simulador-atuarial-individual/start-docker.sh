#!/bin/bash

# Script para iniciar PrevLab com Docker
# Execute: bash start-docker.sh

set -e  # Para em caso de erro

echo "🚀 Iniciando PrevLab com Docker..."
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado!"
    exit 1
fi

# Verificar permissões Docker
if ! docker ps &> /dev/null; then
    echo "⚠️  Sem permissão para acessar Docker."
    echo "Execute: sudo usermod -aG docker $USER"
    echo "Depois faça logout/login ou execute: newgrp docker"
    echo ""
    echo "Ou execute este script com: sg docker -c './start-docker.sh'"
    exit 1
fi

echo "✅ Docker está funcionando!"
echo ""

# Limpar containers antigos se existirem
echo "🧹 Limpando containers antigos..."
docker-compose down 2>/dev/null || true
echo ""

# Build e start
echo "🔨 Fazendo build das imagens (isso pode levar 5-15 minutos)..."
docker-compose up -d --build

echo ""
echo "⏳ Aguardando containers iniciarem..."
sleep 5

# Verificar status
echo ""
echo "📊 Status dos containers:"
docker-compose ps

echo ""
echo "✅ Ambiente Docker iniciado!"
echo ""
echo "🌐 Acesse a aplicação em:"
echo "   Frontend: http://localhost"
echo "   Backend:  http://localhost:8000"
echo "   Health:   http://localhost:8000/health"
echo ""
echo "📋 Comandos úteis:"
echo "   Ver logs:        docker-compose logs -f"
echo "   Parar:          docker-compose down"
echo "   Reiniciar:      docker-compose restart"
echo "   Status:         docker-compose ps"
echo ""
