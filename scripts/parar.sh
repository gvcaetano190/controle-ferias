#!/bin/bash
# ===========================================
# Script para parar o sistema
# Compatível com: Linux, macOS, Docker
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🛑 Parando Sistema de Controle de Férias..."

# Para API
if [ -f "$PROJECT_DIR/.api.pid" ]; then
    kill $(cat "$PROJECT_DIR/.api.pid") 2>/dev/null
    rm "$PROJECT_DIR/.api.pid"
fi

# Para Streamlit
if [ -f "$PROJECT_DIR/.streamlit.pid" ]; then
    kill $(cat "$PROJECT_DIR/.streamlit.pid") 2>/dev/null
    rm "$PROJECT_DIR/.streamlit.pid"
fi

# Mata processos remanescentes
pkill -f "api-server" 2>/dev/null
pkill -f "streamlit run" 2>/dev/null

echo "✅ Sistema parado!"

