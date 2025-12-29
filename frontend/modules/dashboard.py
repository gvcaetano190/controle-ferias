"""
Página do Dashboard.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict

from frontend.components import exibir_tabela_funcionarios


def render(database):
    """Renderiza a página do dashboard."""
    st.header("📊 Dashboard")
    
    # Status da última sync
    last_sync = database.buscar_ultimo_sync()
    
    if not last_sync:
        st.warning("⚠️ Nenhuma sincronização realizada. Vá para 'Sincronização' e clique em 'Sincronizar Agora'.")
        return
    
    # Info de sincronização
    sync_at = last_sync.get("sync_at", "")
    if sync_at:
        try:
            # Tenta diferentes formatos de timestamp
            sync_time = None
            # Formato SQLite: YYYY-MM-DD HH:MM:SS
            try:
                sync_time = datetime.strptime(sync_at, '%Y-%m-%d %H:%M:%S')
            except:
                # Formato ISO
                try:
                    sync_time = datetime.fromisoformat(sync_at.replace('Z', '+00:00'))
                except:
                    pass
            
            if sync_time:
                st.markdown(f"""
                <div class="sync-info">
                    📅 Última sincronização: <strong>{sync_time.strftime('%d/%m/%Y às %H:%M')}</strong> | 
                    📊 {last_sync.get('total_registros', 0)} registros | 
                    📑 {last_sync.get('total_abas', 0)} abas
                </div>
                """, unsafe_allow_html=True)
        except:
            pass
    
    st.divider()
    
    # Busca dados do banco
    abas = database.buscar_abas()
    saindo_hoje = database.buscar_saindo_hoje()
    voltando_amanha = database.buscar_voltando_amanha()
    em_ferias = database.buscar_em_ferias()
    proximos_sair = database.buscar_proximos_a_sair(dias=7)
    
    # Determina texto para "voltando" baseado no dia da semana
    hoje = datetime.now()
    dia_semana = hoje.weekday()  # 0=segunda, 4=sexta, 5=sábado, 6=domingo
    if dia_semana >= 4:  # Sexta (4), Sábado (5) ou Domingo (6)
        texto_voltando = "Voltando Segunda"
        # Calcula dias até segunda
        if dia_semana == 4:  # Sexta
            dias_ate_segunda = 3
        elif dia_semana == 5:  # Sábado
            dias_ate_segunda = 2
        else:  # Domingo
            dias_ate_segunda = 1
        proxima_segunda = (hoje + timedelta(days=dias_ate_segunda)).strftime('%d/%m/%Y')
        texto_voltando_completo = f"Voltando Segunda ({proxima_segunda})"
    else:
        texto_voltando = "Voltando Amanhã"
        amanha = (hoje + timedelta(days=1)).strftime('%d/%m/%Y')
        texto_voltando_completo = f"Voltando Amanhã ({amanha})"
    
    # Seletor de aba
    if abas:
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        aba_default = None
        for aba in abas:
            if aba.get("mes") == mes_atual and aba.get("ano") == ano_atual:
                aba_default = aba["nome"]
                break
        
        nomes_abas = [a["nome"] for a in abas]
        
        aba_selecionada = st.selectbox(
            "📅 Selecionar mês para visualizar:",
            options=nomes_abas,
            index=nomes_abas.index(aba_default) if aba_default and aba_default in nomes_abas else 0,
            key="aba_selecionada"
        )
        
        funcionarios_aba = database.buscar_funcionarios(aba=aba_selecionada)
    else:
        funcionarios_aba = []
        aba_selecionada = None
    
    # Métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🏖️ Saindo Hoje", len(saindo_hoje))
    with col2:
        st.metric(f"📅 {texto_voltando}", len(voltando_amanha))
    with col3:
        st.metric("🌴 Em Férias", len(em_ferias))
    with col4:
        st.metric("📆 Próximos 7 dias", len(proximos_sair))
    with col5:
        st.metric("📊 Total na Aba", len(funcionarios_aba))
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"📋 {aba_selecionada or 'Funcionários'} ({len(funcionarios_aba)})",
        f"🏖️ Saindo Hoje ({len(saindo_hoje)})",
        f"📆 Próximos a Sair ({len(proximos_sair)})",
        f"📅 {texto_voltando_completo} ({len(voltando_amanha)})",
        f"🌴 Em Férias ({len(em_ferias)})"
    ])
    
    with tab1:
        if funcionarios_aba:
            st.subheader(f"📋 Funcionários - {aba_selecionada}")
            exibir_tabela_funcionarios(funcionarios_aba)
        else:
            st.info(f"Nenhum funcionário encontrado na aba {aba_selecionada}")
    
    with tab2:
        if saindo_hoje:
            st.subheader("🏖️ Funcionários Saindo de Férias Hoje")
            exibir_tabela_funcionarios(saindo_hoje)
        else:
            st.success("✅ Nenhum funcionário saindo de férias hoje")
    
    with tab3:
        if proximos_sair:
            st.subheader("📆 Funcionários Saindo nos Próximos 7 Dias")
            st.info(f"⚠️ {len(proximos_sair)} funcionário(s) vão sair de férias nos próximos dias. Verifique os acessos!")
            exibir_tabela_funcionarios(proximos_sair)
        else:
            st.success("✅ Nenhum funcionário saindo nos próximos 7 dias")
    
    with tab4:
        if voltando_amanha:
            st.subheader(f"📅 Funcionários {texto_voltando_completo}")
            exibir_tabela_funcionarios(voltando_amanha)
        else:
            st.success(f"✅ Nenhum funcionário {texto_voltando_completo.lower()}")
    
    with tab5:
        if em_ferias:
            st.subheader("🌴 Funcionários em Férias Agora")
            exibir_tabela_funcionarios(em_ferias)
        else:
            st.success("✅ Nenhum funcionário em férias no momento")

