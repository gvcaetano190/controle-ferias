#!/bin/bash
# ===========================================
# Script para iniciar o scheduler (daemon)
# Compatível com: Linux, macOS, Docker
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Ativa venv se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "📆 Iniciando Scheduler..."
echo "   Horário de sync: $(grep SYNC_HOUR .env | cut -d= -f2):$(grep SYNC_MINUTE .env | cut -d= -f2)"
echo ""

# Executa scheduler
python -m scheduler.jobs "$@"

