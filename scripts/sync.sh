#!/bin/bash
# ===========================================
# Script para sincronização manual
# Compatível com: Linux, macOS, Docker
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Ativa venv se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Executa sincronização
python -m core.sync_manager "$@"
