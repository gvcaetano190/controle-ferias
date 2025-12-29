"""
Página de Controle de Acessos.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from frontend.components import exibir_tabela_funcionarios, exibir_resumo_acessos


def render(database):
    """Renderiza a página de controle de acessos."""
    st.header("🔐 Controle de Acessos")
    
    # Resumo
    resumo = database.buscar_resumo_acessos()
    exibir_resumo_acessos(resumo)
    
    st.divider()
    
    # Pendentes
    pendentes = database.buscar_acessos_pendentes()
    
    if pendentes:
        st.subheader(f"⚠️ Funcionários com Acessos Pendentes ({len(pendentes)})")
        st.warning(f"Atenção: {len(pendentes)} funcionário(s) em férias com acessos não configurados!")
        exibir_tabela_funcionarios(pendentes)
    else:
        st.success("✅ Todos os funcionários em férias têm acessos configurados!")

