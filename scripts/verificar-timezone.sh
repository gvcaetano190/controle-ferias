#!/bin/bash
# ===========================================
# Script para verificar timezone do container
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Detecta docker-compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

echo "🕐 Verificando Timezone dos Containers"
echo "======================================"
echo ""

# Verifica se os containers estão rodando
FRONTEND_STATUS=$($DOCKER_COMPOSE ps -q frontend 2>/dev/null)
SCHEDULER_STATUS=$($DOCKER_COMPOSE ps -q scheduler 2>/dev/null)

if [ -z "$FRONTEND_STATUS" ] || [ -z "$SCHEDULER_STATUS" ]; then
    echo "❌ Containers não estão rodando!"
    echo ""
    echo "Iniciando containers..."
    $DOCKER_COMPOSE up -d
    echo "Aguardando inicialização..."
    sleep 5
fi

echo "📍 Timezone do Container Frontend:"
$DOCKER_COMPOSE exec frontend date
echo "   Timezone: $($DOCKER_COMPOSE exec frontend cat /etc/timezone 2>/dev/null || echo 'N/A')"
echo ""

echo "📍 Timezone do Container Scheduler:"
$DOCKER_COMPOSE exec scheduler date
echo "   Timezone: $($DOCKER_COMPOSE exec scheduler cat /etc/timezone 2>/dev/null || echo 'N/A')"
echo ""

echo "🕐 Horários Configurados no .env:"
echo "   Sincronização: $(grep SYNC_HOUR .env | cut -d= -f2):$(grep SYNC_MINUTE .env | cut -d= -f2)"
echo "   Mensagem Matutina: $(grep MENSAGEM_MANHA_HOUR .env | cut -d= -f2):$(grep MENSAGEM_MANHA_MINUTE .env | cut -d= -f2)"
echo "   Mensagem Vespertina: $(grep MENSAGEM_TARDE_HOUR .env | cut -d= -f2):$(grep MENSAGEM_TARDE_MINUTE .env | cut -d= -f2)"
echo ""

echo "✅ Verificação concluída!"
