"""
Página de Controle de Acessos.
"""

import sys
from pathlib import Path
from datetime import datetime

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
    
    # ==================== FUNCIONÁRIOS QUE RETORNARAM COM ACESSOS BLOQUEADOS ====================
    st.subheader("🚨 Funcionários que Retornaram com Acessos Bloqueados")
    
    # Configuração do filtro de período
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    # Mês passado
    if mes_atual == 1:
        mes_passado = 12
        ano_mes_passado = ano_atual - 1
    else:
        mes_passado = mes_atual - 1
        ano_mes_passado = ano_atual
    
    # Lista de meses para o selectbox
    meses_nomes = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Opções de filtro predefinidas
    opcoes_filtro = [
        f"Último Ciclo ({meses_nomes[mes_passado]}/{ano_mes_passado} - {meses_nomes[mes_atual]}/{ano_atual})",
        f"Mês Atual ({meses_nomes[mes_atual]}/{ano_atual})",
        f"Mês Passado ({meses_nomes[mes_passado]}/{ano_mes_passado})",
        "Todos os períodos",
        "Período personalizado"
    ]
    
    col_filtro1, col_filtro2 = st.columns([2, 3])
    
    with col_filtro1:
        filtro_selecionado = st.selectbox(
            "📅 Filtrar por período:",
            opcoes_filtro,
            index=0,  # Padrão: Último Ciclo
            key="filtro_retornados"
        )
    
    # Determina os parâmetros de filtro baseado na seleção
    mes_inicio, ano_inicio, mes_fim, ano_fim = None, None, None, None
    
    if "Último Ciclo" in filtro_selecionado:
        mes_inicio, ano_inicio = mes_passado, ano_mes_passado
        mes_fim, ano_fim = mes_atual, ano_atual
    elif "Mês Atual" in filtro_selecionado:
        mes_inicio, ano_inicio = mes_atual, ano_atual
        mes_fim, ano_fim = mes_atual, ano_atual
    elif "Mês Passado" in filtro_selecionado:
        mes_inicio, ano_inicio = mes_passado, ano_mes_passado
        mes_fim, ano_fim = mes_passado, ano_mes_passado
    elif "Período personalizado" in filtro_selecionado:
        with col_filtro2:
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            with col_p1:
                mes_inicio = st.selectbox("Mês início:", list(range(1, 13)), 
                                          format_func=lambda x: meses_nomes[x],
                                          index=mes_passado - 1,
                                          key="mes_inicio_retornados")
            with col_p2:
                ano_inicio = st.selectbox("Ano início:", list(range(ano_atual - 2, ano_atual + 1)),
                                          index=2 if ano_mes_passado == ano_atual else 1,
                                          key="ano_inicio_retornados")
            with col_p3:
                mes_fim = st.selectbox("Mês fim:", list(range(1, 13)),
                                       format_func=lambda x: meses_nomes[x],
                                       index=mes_atual - 1,
                                       key="mes_fim_retornados")
            with col_p4:
                ano_fim = st.selectbox("Ano fim:", list(range(ano_atual - 2, ano_atual + 1)),
                                       index=2,
                                       key="ano_fim_retornados")
    # "Todos os períodos" deixa todos None
    
    # Busca com filtros
    retornados_bloqueados = database.buscar_retornados_com_acessos_bloqueados(
        mes_inicio=mes_inicio,
        ano_inicio=ano_inicio,
        mes_fim=mes_fim,
        ano_fim=ano_fim
    )
    
    if retornados_bloqueados:
        st.error(f"⚠️ ATENÇÃO: {len(retornados_bloqueados)} funcionário(s) já retornaram de férias mas ainda têm acessos bloqueados!")
        st.info("💡 Esses funcionários deveriam ter seus acessos liberados. Verifique e atualize o status.")
        exibir_tabela_funcionarios(retornados_bloqueados)
    else:
        if filtro_selecionado == "Todos os períodos":
            st.success("✅ Nenhum funcionário retornado com acessos bloqueados!")
        else:
            st.success(f"✅ Nenhum funcionário retornado com acessos bloqueados no período selecionado!")
    
    st.divider()
    
    # Pendentes (em férias)
    pendentes = database.buscar_acessos_pendentes()
    
    if pendentes:
        st.subheader(f"⚠️ Funcionários com Acessos Pendentes ({len(pendentes)})")
        st.warning(f"Atenção: {len(pendentes)} funcionário(s) em férias com acessos não configurados!")
        exibir_tabela_funcionarios(pendentes)
    else:
        st.success("✅ Todos os funcionários em férias têm acessos configurados!")

