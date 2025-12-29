#!/bin/bash
# ===========================================
# Gerenciador Docker - Sistema de Controle de Férias
# Compatível com: Linux, macOS, Docker
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Detecta docker-compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Função de ajuda
show_help() {
    echo "🐳 Gerenciador Docker - Sistema de Controle de Férias"
    echo "======================================================"
    echo ""
    echo "Uso: ./scripts/docker-manager.sh [comando]"
    echo ""
    echo "Comandos disponíveis:"
    echo ""
    echo "  start         Inicia os containers"
    echo "  stop          Para os containers"
    echo "  restart       Reinicia os containers"
    echo "  update        Atualiza código e reinicia (rápido)"
    echo "  rebuild       Reconstrui imagens e reinicia (após mudanças no código)"
    echo "  logs          Mostra logs em tempo real"
    echo "  status        Mostra status dos containers"
    echo "  shell         Acessa shell do container frontend"
    echo "  sync          Executa sincronização manual"
    echo "  clean         Remove containers, volumes e imagens (CUIDADO!)"
    echo "  help          Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./scripts/docker-manager.sh start"
    echo "  ./scripts/docker-manager.sh rebuild"
    echo "  ./scripts/docker-manager.sh logs"
}

# Comandos
case "${1:-help}" in
    start)
        echo "🚀 Iniciando containers..."
        $DOCKER_COMPOSE up -d
        echo "✅ Containers iniciados!"
        echo "   Dashboard: http://localhost:8501"
        ;;
    
    stop)
        echo "⏹️  Parando containers..."
        $DOCKER_COMPOSE down
        echo "✅ Containers parados!"
        ;;
    
    restart)
        echo "🔄 Reiniciando containers..."
        $DOCKER_COMPOSE restart
        echo "✅ Containers reiniciados!"
        ;;
    
    update)
        echo "🔄 Atualizando containers..."
        $DOCKER_COMPOSE down
        $DOCKER_COMPOSE up -d --build
        echo "✅ Containers atualizados!"
        ;;
    
    rebuild)
        echo "🔨 Reconstruindo imagens..."
        $DOCKER_COMPOSE down
        $DOCKER_COMPOSE build --no-cache
        $DOCKER_COMPOSE up -d
        echo "✅ Reconstruído e iniciado!"
        ;;
    
    logs)
        echo "📋 Logs dos containers (Ctrl+C para sair)..."
        $DOCKER_COMPOSE logs -f
        ;;
    
    status)
        echo "📊 Status dos containers:"
        $DOCKER_COMPOSE ps
        echo ""
        echo "💾 Uso de recursos:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" controle-ferias-frontend controle-ferias-scheduler 2>/dev/null || echo "Containers não estão rodando"
        ;;
    
    shell)
        echo "🐚 Acessando shell do container frontend..."
        $DOCKER_COMPOSE exec frontend bash
        ;;
    
    sync)
        echo "🔄 Executando sincronização manual..."
        $DOCKER_COMPOSE exec frontend ./scripts/sync.sh
        ;;
    
    clean)
        echo "⚠️  ATENÇÃO: Isso vai remover TUDO (containers, volumes, imagens)!"
        read -p "Tem certeza? (digite 'sim' para confirmar): " confirm
        if [ "$confirm" = "sim" ]; then
            echo "🧹 Limpando tudo..."
            $DOCKER_COMPOSE down -v --rmi all
            echo "✅ Limpeza concluída!"
        else
            echo "❌ Cancelado."
        fi
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        echo "❌ Comando desconhecido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac






