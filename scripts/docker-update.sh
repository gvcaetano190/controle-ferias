#!/bin/bash
# ===========================================
# Script para atualizar containers Docker
# Compatível com: Linux, macOS, Docker
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🔄 Atualizando containers Docker..."
echo "===================================="
echo ""

# Verifica se docker-compose está disponível
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale Docker primeiro."
    exit 1
fi

# Detecta se usa docker-compose ou docker compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Opções
REBUILD=false
NO_CACHE=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            REBUILD=true
            shift
            ;;
        --help|-h)
            echo "Uso: ./scripts/docker-update.sh [opções]"
            echo ""
            echo "Opções:"
            echo "  --rebuild      Reconstrui as imagens antes de iniciar"
            echo "  --no-cache     Reconstrui sem usar cache (mais lento, mas garante atualização)"
            echo "  --help, -h     Mostra esta ajuda"
            echo ""
            echo "Exemplos:"
            echo "  ./scripts/docker-update.sh              # Atualiza e reinicia containers"
            echo "  ./scripts/docker-update.sh --rebuild    # Reconstrui imagens antes de iniciar"
            echo "  ./scripts/docker-update.sh --no-cache   # Reconstrui tudo do zero"
            exit 0
            ;;
        *)
            echo "❌ Opção desconhecida: $1"
            echo "Use --help para ver opções disponíveis"
            exit 1
            ;;
    esac
done

# Para containers existentes
echo "⏹️  Parando containers existentes..."
$DOCKER_COMPOSE down 2>/dev/null || true

# Reconstrui se solicitado
if [ "$REBUILD" = true ]; then
    echo ""
    echo "🔨 Reconstruindo imagens..."
    if [ "$NO_CACHE" = true ]; then
        $DOCKER_COMPOSE build --no-cache
    else
        $DOCKER_COMPOSE build
    fi
fi

# Inicia containers
echo ""
echo "🚀 Iniciando containers..."
$DOCKER_COMPOSE up -d

# Aguarda um pouco para containers iniciarem
sleep 3

# Mostra status
echo ""
echo "📊 Status dos containers:"
$DOCKER_COMPOSE ps

echo ""
echo "✅ Atualização concluída!"
echo ""
echo "📝 Próximos passos:"
echo "   • Ver logs: docker-compose logs -f"
echo "   • Dashboard: http://localhost:8501"
echo "   • Parar: docker-compose down"
echo ""








