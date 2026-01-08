#!/bin/bash
# ===========================================
# Script para iniciar a aplicação (frontend)
# Compatível com: Linux, macOS, Docker
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🏖️ Sistema de Controle de Férias"
echo "================================="

# Ativa venv se existir
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment ativado"
fi

# Verifica dependências
if ! python -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit não encontrado. Execute: pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "🚀 Iniciando Aplicação Principal (Streamlit)..."
echo "   Acesse: http://localhost:8501"
echo ""

# Inicia Streamlit
streamlit run frontend/app.py --server.port 8501
