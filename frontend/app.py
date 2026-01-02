#!/usr/bin/env python3
"""
FRONTEND STREAMLIT - Sistema de Controle de Férias

Lê dados diretamente do banco SQLite.
Sem dependência de API externa.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from datetime import datetime

from core.database import Database
from frontend.modules import dashboard, acessos, sincronizacao, gerar_senhas, configuracoes, logs, relatorios

# ==================== CONFIGURAÇÃO DA PÁGINA ====================

st.set_page_config(
    page_title="Controle de Férias",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .sync-info {
        background-color: #e8f4f8;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border-left: 4px solid #1e3a5f;
        font-size: 0.9rem;
    }
    .status-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ==================== INICIALIZAÇÃO ====================

def get_database():
    """Retorna nova instância do banco (sem cache para garantir dados atualizados)."""
    return Database()


# ==================== MAIN ====================

def main():
    """Função principal."""
    
    # Header
    st.markdown('<h1 class="main-header">🏖️ Sistema de Controle de Férias</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📌 Menu")
        
        pagina = st.radio(
            "Navegação:",
            ["📊 Dashboard", "📈 Relatórios", "🔐 Controle de Acessos", "🔑 Gerar Senhas", "🔄 Sincronização", "📋 Logs", "⚙️ Configurações"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Status do banco
        try:
            db = get_database()
            last_sync = db.buscar_ultimo_sync()
            if last_sync:
                st.success("✅ Banco conectado")
            else:
                st.warning("⚠️ Sem dados")
        except Exception as e:
            st.error(f"❌ Erro: {e}")
        
        st.divider()
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        st.caption("v2.0 - Python Puro")
    
    # Roteamento
    db = get_database()
    
    if pagina == "📊 Dashboard":
        dashboard.render(db)
    elif pagina == "📈 Relatórios":
        relatorios.render(db)
    elif pagina == "🔐 Controle de Acessos":
        acessos.render(db)
    elif pagina == "🔑 Gerar Senhas":
        gerar_senhas.render(db)
    elif pagina == "🔄 Sincronização":
        sincronizacao.render(db)
    elif pagina == "📋 Logs":
        logs.render()
    elif pagina == "⚙️ Configurações":
        configuracoes.render(db)


if __name__ == "__main__":
    main()
