"""
Página de Relatórios.

Módulo para visualização de relatórios e estatísticas de férias.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict


def render(database):
    """Renderiza a página de relatórios."""
    st.header("📊 Relatórios")
    
    # Verifica se há dados
    last_sync = database.buscar_ultimo_sync()
    if not last_sync:
        st.warning("⚠️ Nenhuma sincronização realizada. Vá para 'Sincronização' primeiro.")
        return
    
    # Tabs de relatórios
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👤 Por Funcionário",
        "📅 Por Período",
        "🧑‍💼 Por Gestor",
        "🔙 Retorno de Férias",
        "🚀 Saída de Férias",
        "📈 Estatísticas",
        "📆 Calendário Anual"
    ])
    
    with tab1:
        _render_relatorio_funcionario(database)
    
    with tab2:
        _render_relatorio_periodo(database)
    
    with tab3:
        _render_relatorio_gestor(database)
    
    with tab4:
        _render_relatorio_retorno(database)
    
    with tab5:
        _render_relatorio_saida(database)
    
    with tab6:
        _render_estatisticas(database)
    
    with tab7:
        _render_calendario_anual(database)


def _render_relatorio_funcionario(database):
    """Relatório de histórico de férias por funcionário."""
    st.subheader("👤 Histórico de Férias por Funcionário")
    
    # Busca todos os funcionários
    historico = database.buscar_historico_ferias_por_funcionario()
    
    if not historico:
        st.info("Nenhum registro de férias encontrado.")
        return
    
    # Campo de busca
    busca = st.text_input("🔍 Buscar funcionário:", placeholder="Digite o nome...")
    
    # Filtra se houver busca
    if busca:
        historico = {k: v for k, v in historico.items() if busca.lower() in k.lower()}
    
    if not historico:
        st.warning(f"Nenhum funcionário encontrado com '{busca}'")
        return
    
    # Seletor de funcionário
    nomes = sorted(historico.keys())
    funcionario_selecionado = st.selectbox(
        "Selecione um funcionário:",
        options=nomes,
        key="select_func_relatorio"
    )
    
    if funcionario_selecionado:
        dados = historico[funcionario_selecionado]
        ferias_list = dados["ferias"]
        
        # Métricas do funcionário
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total de Períodos", len(ferias_list))
        
        with col2:
            total_dias = sum(f.get("dias", 0) for f in ferias_list)
            st.metric("📅 Total de Dias", total_dias)
        
        with col3:
            if ferias_list:
                ultima = ferias_list[0]  # Já vem ordenado por data desc
                st.metric("🗓️ Última Férias", ultima.get("data_saida_fmt", "N/A"))
        
        st.divider()
        
        # Tabela de histórico
        st.markdown("**📋 Histórico Completo:**")
        
        if ferias_list:
            df = pd.DataFrame(ferias_list)
            
            # Seleciona e renomeia colunas para exibição
            colunas_exibir = []
            mapeamento = {}
            
            if "data_saida_fmt" in df.columns:
                colunas_exibir.append("data_saida_fmt")
                mapeamento["data_saida_fmt"] = "📅 Saída"
            if "data_retorno_fmt" in df.columns:
                colunas_exibir.append("data_retorno_fmt")
                mapeamento["data_retorno_fmt"] = "📅 Retorno"
            if "dias" in df.columns:
                colunas_exibir.append("dias")
                mapeamento["dias"] = "⏱️ Dias"
            if "motivo" in df.columns:
                colunas_exibir.append("motivo")
                mapeamento["motivo"] = "📝 Motivo"
            if "unidade" in df.columns:
                colunas_exibir.append("unidade")
                mapeamento["unidade"] = "👤 RH Solicitante"
            if "gestor" in df.columns:
                colunas_exibir.append("gestor")
                mapeamento["gestor"] = "👤 Gestor"
            
            if colunas_exibir:
                df_exibir = df[colunas_exibir].rename(columns=mapeamento)
                st.dataframe(df_exibir, width="stretch", hide_index=True)
        
        # Botão de exportar
        if ferias_list:
            csv = pd.DataFrame(ferias_list).to_csv(index=False)
            st.download_button(
                label="📥 Exportar CSV",
                data=csv,
                file_name=f"ferias_{funcionario_selecionado.replace(' ', '_')}.csv",
                mime="text/csv"
            )


def _render_relatorio_periodo(database):
    """Relatório de férias por período."""
    st.subheader("📅 Relatório por Período")
    
    # Tipo de filtro
    tipo_filtro = st.radio(
        "🔍 Filtrar por:",
        ["📅 Data de Saída", "📅 Data de Retorno", "📅 Em férias no período"],
        horizontal=True,
        key="tipo_filtro_periodo"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_inicio = st.date_input(
            "Data Início:",
            value=datetime.now().replace(day=1),
            key="data_inicio_relatorio"
        )
    
    with col2:
        data_fim = st.date_input(
            "Data Fim:",
            value=datetime.now() + timedelta(days=30),
            key="data_fim_relatorio"
        )
    
    if data_inicio > data_fim:
        st.error("❌ Data início deve ser menor que data fim")
        return
    
    # Busca funcionários no período com o tipo de filtro selecionado
    if tipo_filtro == "📅 Data de Saída":
        funcionarios = database.buscar_ferias_por_data_saida(
            data_inicio.strftime('%Y-%m-%d'),
            data_fim.strftime('%Y-%m-%d')
        )
    elif tipo_filtro == "📅 Data de Retorno":
        funcionarios = database.buscar_ferias_por_data_retorno(
            data_inicio.strftime('%Y-%m-%d'),
            data_fim.strftime('%Y-%m-%d')
        )
    else:  # Em férias no período
        funcionarios = database.buscar_ferias_por_periodo(
            data_inicio.strftime('%Y-%m-%d'),
            data_fim.strftime('%Y-%m-%d')
        )
    
    st.markdown(f"**📊 {len(funcionarios)} registro(s) encontrado(s) no período**")
    
    if funcionarios:
        # Converte para DataFrame
        df = pd.DataFrame(funcionarios)
        
        # Formata datas para exibição
        if "data_saida" in df.columns:
            df["📅 Saída"] = pd.to_datetime(df["data_saida"]).dt.strftime('%d/%m/%Y')
        if "data_retorno" in df.columns:
            df["📅 Retorno"] = pd.to_datetime(df["data_retorno"]).dt.strftime('%d/%m/%Y')
        
        # Seleciona colunas para exibição
        colunas = ["nome", "📅 Saída", "📅 Retorno", "unidade", "motivo", "gestor"]
        colunas_existentes = [c for c in colunas if c in df.columns]
        
        df_exibir = df[colunas_existentes].rename(columns={
            "nome": "👤 Nome",
            "unidade": "👤 RH Solicitante",
            "motivo": "📝 Motivo",
            "gestor": "👤 Gestor"
        })
        
        st.dataframe(df_exibir, width="stretch", hide_index=True)
        
        # Exportar
        csv = df[colunas_existentes].to_csv(index=False)
        st.download_button(
            label="📥 Exportar CSV",
            data=csv,
            file_name=f"ferias_{data_inicio}_{data_fim}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum registro encontrado no período selecionado.")


def _render_relatorio_gestor(database):
    """Relatório completo por Gestor."""
    st.subheader("🧑‍💼 Relatório por Gestor")
    
    # Meses em português
    meses_pt = {
        0: "Todos", 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Busca estatísticas por gestor (sem filtro para obter lista completa)
    todos_gestores = database.buscar_estatisticas_por_gestor(limite=1000)
    
    if not todos_gestores:
        st.info("Nenhum dado disponível.")
        return
    
    # ===== SEÇÃO 1: VISÃO GERAL =====
    total_gestores = len(todos_gestores)
    total_registros = sum(g["total"] for g in todos_gestores)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🧑‍💼 Total de Gestores", total_gestores)
    with col2:
        st.metric("📊 Total de Registros", total_registros)
    
    st.divider()
    
    # ===== SEÇÃO 2: RANKING DE GESTORES =====
    st.markdown("**📊 Ranking de Gestores (por quantidade de férias):**")
    
    df_gestores = pd.DataFrame(todos_gestores)
    df_gestores_chart = df_gestores.head(15).sort_values("total", ascending=True)
    st.bar_chart(df_gestores_chart.set_index("gestor")["total"])
    
    st.divider()
    
    # ===== SEÇÃO 3: FILTROS =====
    st.markdown("**🔍 Filtrar e Detalhar por Gestor:**")
    
    # Busca anos disponíveis
    anos_disponiveis = database.buscar_anos_disponiveis()
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        # Lista de gestores para seleção
        lista_gestores = sorted([g["gestor"] for g in todos_gestores if g["gestor"]])
        gestor_selecionado = st.selectbox(
            "🧑‍💼 Selecione o Gestor:",
            options=lista_gestores,
            key="select_gestor_relatorio"
        )
    
    with col_filtro2:
        ano_filtro = st.selectbox(
            "📅 Ano:",
            options=[0] + (anos_disponiveis if anos_disponiveis else []),
            format_func=lambda x: "Todos os anos" if x == 0 else str(x),
            key="filtro_ano_gestor"
        )
    
    with col_filtro3:
        mes_filtro = st.selectbox(
            "📅 Mês:",
            options=list(meses_pt.keys()),
            format_func=lambda x: meses_pt[x],
            key="filtro_mes_gestor"
        )
    
    st.divider()
    
    # ===== SEÇÃO 4: DETALHES DO GESTOR =====
    if gestor_selecionado:
        st.markdown(f"### 🧑‍💼 Detalhes: **{gestor_selecionado}**")
        
        # Busca funcionários do gestor com filtros
        funcionarios_gestor = database.buscar_funcionarios_por_gestor(
            gestor=gestor_selecionado,
            ano=ano_filtro if ano_filtro != 0 else None,
            mes=mes_filtro if mes_filtro != 0 else None
        )
        
        if not funcionarios_gestor:
            st.info("Nenhum registro encontrado para este gestor no período selecionado.")
            return
        
        # Métricas do gestor
        total_periodos = len(funcionarios_gestor)
        funcionarios_unicos = len(set(f["nome"] for f in funcionarios_gestor if f.get("nome")))
        
        # Verifica quem está em férias agora
        hoje = datetime.now().strftime('%Y-%m-%d')
        em_ferias_agora = [
            f for f in funcionarios_gestor 
            if f.get("data_saida") and f.get("data_retorno") 
            and f["data_saida"] <= hoje <= f["data_retorno"]
        ]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Períodos de Férias", total_periodos)
        with col2:
            st.metric("👥 Funcionários Únicos", funcionarios_unicos)
        with col3:
            st.metric("🏖️ Em Férias Agora", len(em_ferias_agora))
        
        # Destaque para quem está em férias agora
        if em_ferias_agora:
            st.success(f"🏖️ **Funcionários atualmente em férias:** {', '.join([f['nome'] for f in em_ferias_agora])}")
        
        st.divider()
        
        # Tabela de funcionários do gestor
        st.markdown("**📋 Lista de Férias:**")
        
        df = pd.DataFrame(funcionarios_gestor)
        
        # Calcula dias de férias
        def calcular_dias(row):
            try:
                if row.get("data_saida") and row.get("data_retorno"):
                    saida = datetime.strptime(row["data_saida"], '%Y-%m-%d')
                    retorno = datetime.strptime(row["data_retorno"], '%Y-%m-%d')
                    return (retorno - saida).days + 1
            except:
                pass
            return 0
        
        df["dias"] = df.apply(calcular_dias, axis=1)
        
        # Formata datas
        if "data_saida" in df.columns:
            df["📅 Saída"] = pd.to_datetime(df["data_saida"]).dt.strftime('%d/%m/%Y')
        if "data_retorno" in df.columns:
            df["📅 Retorno"] = pd.to_datetime(df["data_retorno"]).dt.strftime('%d/%m/%Y')
        
        # Seleciona e renomeia colunas
        colunas = ["nome", "📅 Saída", "📅 Retorno", "dias", "motivo"]
        colunas_existentes = [c for c in colunas if c in df.columns]
        
        df_exibir = df[colunas_existentes].rename(columns={
            "nome": "👤 Funcionário",
            "dias": "⏱️ Dias",
            "motivo": "📝 Motivo"
        })
        
        # Ordena por data de saída (mais recente primeiro)
        if "📅 Saída" in df_exibir.columns:
            df_exibir = df_exibir.sort_values("📅 Saída", ascending=False)
        
        st.dataframe(df_exibir, width="stretch", hide_index=True)
        
        # Botão de exportar
        csv = df_exibir.to_csv(index=False)
        st.download_button(
            label="📥 Exportar CSV",
            data=csv,
            file_name=f"ferias_gestor_{gestor_selecionado.replace(' ', '_')}.csv",
            mime="text/csv"
        )
        
        st.divider()
        
        # ===== SEÇÃO 5: RESUMO POR MÊS DO GESTOR =====
        if ano_filtro != 0 and mes_filtro == 0:
            st.markdown(f"**📆 Distribuição por Mês em {ano_filtro}:**")
            
            # Agrupa por mês
            contagem_mes = defaultdict(int)
            for f in funcionarios_gestor:
                mes = f.get("mes", 0)
                if mes and mes > 0:
                    contagem_mes[mes] += 1
            
            if contagem_mes:
                df_mes = pd.DataFrame([
                    {"Mês": meses_pt.get(m, m), "Total": t, "mes_num": m}
                    for m, t in contagem_mes.items()
                ])
                df_mes = df_mes.sort_values("mes_num")
                st.bar_chart(df_mes.set_index("Mês")["Total"])


def _render_estatisticas(database):
    """Estatísticas gerais do sistema."""
    st.subheader("📈 Estatísticas Gerais")
    
    # Meses em português
    meses_pt = {
        0: "Todos", 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Busca anos disponíveis
    anos_disponiveis = database.buscar_anos_disponiveis()
    if not anos_disponiveis:
        st.info("Nenhum dado disponível para estatísticas.")
        return
    
    # Filtros de Ano e Mês
    st.markdown("**🔍 Filtros:**")
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        ano_selecionado = st.selectbox(
            "📅 Ano:",
            options=[0] + anos_disponiveis,
            format_func=lambda x: "Todos os anos" if x == 0 else str(x),
            index=1 if anos_disponiveis else 0,
            key="filtro_ano_stats"
        )
    
    with col_filtro2:
        mes_selecionado = st.selectbox(
            "📅 Mês:",
            options=list(meses_pt.keys()),
            format_func=lambda x: meses_pt[x],
            index=0,
            key="filtro_mes_stats"
        )
    
    st.divider()
    
    # Busca estatísticas filtradas
    stats = database.buscar_estatisticas_filtradas(
        ano=ano_selecionado if ano_selecionado != 0 else None,
        mes=mes_selecionado if mes_selecionado != 0 else None
    )
    
    if not stats:
        st.info("Nenhum dado disponível para os filtros selecionados.")
        return
    
    # Título do período selecionado
    periodo_texto = ""
    if ano_selecionado != 0 and mes_selecionado != 0:
        periodo_texto = f"{meses_pt[mes_selecionado]}/{ano_selecionado}"
    elif ano_selecionado != 0:
        periodo_texto = f"Ano {ano_selecionado}"
    elif mes_selecionado != 0:
        periodo_texto = f"{meses_pt[mes_selecionado]} (todos os anos)"
    else:
        periodo_texto = "Todos os períodos"
    
    st.markdown(f"### 📊 Dados de: **{periodo_texto}**")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Registros", stats.get("total_registros", 0))
    
    with col2:
        st.metric("👥 Funcionários Únicos", stats.get("funcionarios_unicos", 0))
    
    with col3:
        st.metric("👤 RH Solicitantes", stats.get("total_unidades", 0))
    
    with col4:
        st.metric("👤 Gestores", stats.get("total_gestores", 0))
    
    st.divider()
    
    # Se filtrou por ano, mostra distribuição por mês
    if ano_selecionado != 0 and mes_selecionado == 0:
        st.markdown(f"**📆 Distribuição por Mês em {ano_selecionado}:**")
        dados_mes = database.buscar_ferias_por_mes(ano_selecionado)
        
        if dados_mes:
            df_meses = pd.DataFrame([
                {"Mês": meses_pt.get(d["mes"], d["mes"]), "Total": d["total"], "mes_num": d["mes"]}
                for d in dados_mes
            ])
            df_chart = df_meses.sort_values("mes_num").set_index("Mês")
            st.bar_chart(df_chart["Total"])
        
        st.divider()
    
    # Ranking de funcionários com mais férias (filtrado)
    st.markdown("**🏆 Funcionários com Mais Períodos de Férias:**")
    ranking = database.buscar_ranking_ferias_filtrado(
        limite=10,
        ano=ano_selecionado if ano_selecionado != 0 else None,
        mes=mes_selecionado if mes_selecionado != 0 else None
    )
    
    if ranking:
        df_ranking = pd.DataFrame(ranking)
        df_ranking["posicao"] = range(1, len(df_ranking) + 1)
        df_ranking = df_ranking.rename(columns={
            "posicao": "🏅",
            "nome": "👤 Nome",
            "total": "📊 Períodos"
        })
        
        st.dataframe(df_ranking[["🏅", "👤 Nome", "📊 Períodos"]], width="stretch", hide_index=True)
    else:
        st.info("Nenhum funcionário encontrado para o período selecionado.")
    
    st.divider()
    
    # Top gestores (filtrado)
    st.markdown("**👤 Gestores com Mais Subordinados em Férias:**")
    top_gestores = database.buscar_estatisticas_por_gestor_filtrado(
        limite=10,
        ano=ano_selecionado if ano_selecionado != 0 else None,
        mes=mes_selecionado if mes_selecionado != 0 else None
    )
    
    if top_gestores:
        df_gestores = pd.DataFrame(top_gestores)
        df_gestores = df_gestores.rename(columns={
            "gestor": "👤 Gestor",
            "total": "📊 Total de Férias"
        })
        
        st.dataframe(df_gestores, width="stretch", hide_index=True)
    else:
        st.info("Nenhum gestor encontrado para o período selecionado.")
    
    st.divider()
    
    # Top unidades (filtrado)
    st.markdown("**👤 RH Solicitantes com Mais Férias:**")
    top_unidades = database.buscar_estatisticas_por_unidade_filtrado(
        limite=10,
        ano=ano_selecionado if ano_selecionado != 0 else None,
        mes=mes_selecionado if mes_selecionado != 0 else None
    )
    
    if top_unidades:
        df_unidades = pd.DataFrame(top_unidades)
        df_unidades = df_unidades.rename(columns={
            "unidade": "👤 RH Solicitante",
            "total": "📊 Total de Férias"
        })
        
        st.dataframe(df_unidades, width="stretch", hide_index=True)
    else:
        st.info("Nenhum RH Solicitante encontrado para o período selecionado.")


def _render_calendario_anual(database):
    """Calendário anual de férias (heatmap por mês)."""
    st.subheader("📆 Calendário Anual de Férias")
    
    # Seletor de ano
    anos_disponiveis = database.buscar_anos_disponiveis()
    
    if not anos_disponiveis:
        st.info("Nenhum dado disponível.")
        return
    
    ano_atual = datetime.now().year
    ano_selecionado = st.selectbox(
        "Selecione o ano:",
        options=anos_disponiveis,
        index=anos_disponiveis.index(ano_atual) if ano_atual in anos_disponiveis else 0,
        key="ano_calendario"
    )
    
    # Busca dados por mês
    dados_mes = database.buscar_ferias_por_mes(ano_selecionado)
    
    if not dados_mes:
        st.info(f"Nenhum dado disponível para {ano_selecionado}.")
        return
    
    # Meses em português
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Prepara dados para exibição
    df_meses = pd.DataFrame([
        {"Mês": meses_pt.get(d["mes"], d["mes"]), "Total": d["total"], "mes_num": d["mes"]}
        for d in dados_mes
    ])
    
    # Gráfico de barras
    st.markdown(f"**📊 Distribuição de Férias em {ano_selecionado}:**")
    
    df_chart = df_meses.sort_values("mes_num").set_index("Mês")
    st.bar_chart(df_chart["Total"])
    
    st.divider()
    
    # Cards por mês (3 colunas x 4 linhas)
    st.markdown("**📅 Detalhamento Mensal:**")
    
    # Organiza em grid 4x3
    for row in range(4):
        cols = st.columns(3)
        for col_idx in range(3):
            mes = row * 3 + col_idx + 1
            with cols[col_idx]:
                mes_data = next((d for d in dados_mes if d["mes"] == mes), None)
                total = mes_data["total"] if mes_data else 0
                
                # Cor baseada na quantidade
                if total == 0:
                    cor = "🔵"
                elif total < 5:
                    cor = "🟢"
                elif total < 10:
                    cor = "🟡"
                else:
                    cor = "🔴"
                
                st.metric(
                    label=f"{cor} {meses_pt[mes]}",
                    value=total,
                    help=f"Total de funcionários em férias em {meses_pt[mes]}/{ano_selecionado}"
                )
    
    st.divider()
    
    # Mês com mais férias
    if dados_mes:
        mes_pico = max(dados_mes, key=lambda x: x["total"])
        st.info(f"📊 **Mês com mais férias:** {meses_pt.get(mes_pico['mes'], mes_pico['mes'])} com {mes_pico['total']} registro(s)")


def _render_relatorio_retorno(database):
    """Relatório de retorno de férias com status de acessos."""
    st.subheader("🔙 Relatório de Retorno de Férias")
    
    st.info("💡 Visualize funcionários que retornaram de férias e verifique se todos os acessos foram liberados.")
    
    # Configuração de data
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Mês passado
    if mes_atual == 1:
        mes_passado = 12
        ano_mes_passado = ano_atual - 1
    else:
        mes_passado = mes_atual - 1
        ano_mes_passado = ano_atual
    
    meses_nomes = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Opções de filtro
    opcoes_ciclo = [
        f"Último Ciclo ({meses_nomes[mes_passado]}/{ano_mes_passado} - {meses_nomes[mes_atual]}/{ano_atual})",
        f"Mês Atual ({meses_nomes[mes_atual]}/{ano_atual})",
        f"Mês Passado ({meses_nomes[mes_passado]}/{ano_mes_passado})",
        "Todos os períodos",
        "Período personalizado"
    ]
    
    col_filtro1, col_filtro2 = st.columns([2, 3])
    
    with col_filtro1:
        filtro_ciclo = st.selectbox(
            "📅 Filtrar por ciclo/período:",
            opcoes_ciclo,
            index=0,
            key="filtro_retorno_ciclo"
        )
    
    # Determina parâmetros de filtro
    data_inicio, data_fim = None, None
    
    if "Último Ciclo" in filtro_ciclo:
        data_inicio = datetime(ano_mes_passado, mes_passado, 1)
        if mes_atual == 12:
            data_fim = datetime(ano_atual + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano_atual, mes_atual + 1, 1) - timedelta(days=1)
    elif "Mês Atual" in filtro_ciclo:
        data_inicio = datetime(ano_atual, mes_atual, 1)
        if mes_atual == 12:
            data_fim = datetime(ano_atual + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano_atual, mes_atual + 1, 1) - timedelta(days=1)
    elif "Mês Passado" in filtro_ciclo:
        data_inicio = datetime(ano_mes_passado, mes_passado, 1)
        data_fim = datetime(ano_atual, mes_atual, 1) - timedelta(days=1)
    elif "Período personalizado" in filtro_ciclo:
        with col_filtro2:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                data_inicio = st.date_input(
                    "Data início (retorno):",
                    value=datetime(ano_mes_passado, mes_passado, 1),
                    key="retorno_data_inicio"
                )
            with col_d2:
                data_fim = st.date_input(
                    "Data fim (retorno):",
                    value=hoje,
                    key="retorno_data_fim"
                )
    
    # Busca funcionários que retornaram no período
    funcionarios = database.buscar_funcionarios()
    
    # Filtra por data de retorno
    retornados = []
    for f in funcionarios:
        if not f.get('data_retorno'):
            continue
        
        try:
            data_retorno = datetime.strptime(f['data_retorno'], '%Y-%m-%d')
        except:
            continue
        
        # Só mostra quem já retornou (data_retorno <= hoje)
        if data_retorno > hoje:
            continue
        
        # Aplica filtro de período se existir
        if data_inicio and data_fim:
            if isinstance(data_inicio, datetime):
                d_inicio = data_inicio
                d_fim = data_fim
            else:
                d_inicio = datetime.combine(data_inicio, datetime.min.time())
                d_fim = datetime.combine(data_fim, datetime.max.time())
            
            if not (d_inicio <= data_retorno <= d_fim):
                continue
        
        retornados.append(f)
    
    if not retornados:
        st.warning("Nenhum funcionário encontrado com retorno no período selecionado.")
        return
    
    # Analisa status dos acessos
    sistemas = ["AD", "VPN", "Gmail", "Admin", "Metrics", "TOTVS"]
    
    # Contadores
    total_liberados = 0
    total_pendentes = 0
    
    dados_tabela = []
    for f in retornados:
        acessos = f.get('acessos', {})
        
        # Verifica se todos os acessos estão liberados ou NA
        acessos_ok = True
        status_acessos = {}
        
        for sistema in sistemas:
            status = acessos.get(sistema, 'PENDENTE')
            status_acessos[sistema] = status
            if status == 'BLOQUEADO':
                acessos_ok = False
        
        if acessos_ok:
            total_liberados += 1
            status_geral = "✅ Liberado"
        else:
            total_pendentes += 1
            status_geral = "🔴 Bloqueado"
        
        dados_tabela.append({
            "Nome": f.get('nome', ''),
            "Retorno": f.get('data_retorno', ''),
            "Saída": f.get('data_saida', ''),
            "RH Solicitante": f.get('unidade', ''),
            "Gestor": f.get('gestor', ''),
            "Status Geral": status_geral,
            **{s: status_acessos.get(s, 'NB') for s in sistemas}
        })
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Retornados", len(retornados))
    with col2:
        st.metric("✅ Acessos Liberados", total_liberados)
    with col3:
        st.metric("🔴 Acessos Pendentes", total_pendentes)
    
    st.divider()
    
    # Filtro de status
    filtro_status = st.radio(
        "Filtrar por status:",
        ["Todos", "✅ Apenas Liberados", "🔴 Apenas com Bloqueio"],
        horizontal=True,
        key="filtro_status_retorno"
    )
    
    if filtro_status == "✅ Apenas Liberados":
        dados_tabela = [d for d in dados_tabela if "✅" in d["Status Geral"]]
    elif filtro_status == "🔴 Apenas com Bloqueio":
        dados_tabela = [d for d in dados_tabela if "🔴" in d["Status Geral"]]
    
    if not dados_tabela:
        st.info("Nenhum registro encontrado com o filtro selecionado.")
        return
    
    # Formata datas
    for d in dados_tabela:
        try:
            if d["Retorno"]:
                d["Retorno"] = datetime.strptime(d["Retorno"], '%Y-%m-%d').strftime('%d/%m/%Y')
            if d["Saída"]:
                d["Saída"] = datetime.strptime(d["Saída"], '%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            pass
    
    # Tabela
    df = pd.DataFrame(dados_tabela)
    
    # Estiliza status dos acessos
    def estilizar_acesso(val):
        if val == "LIBERADO":
            return "🟢"
        elif val == "BLOQUEADO":
            return "🔴"
        elif val in ["NA", "NB", "NP"]:
            return "⚪"
        else:
            return "⬜"
    
    for sistema in sistemas:
        if sistema in df.columns:
            df[sistema] = df[sistema].apply(estilizar_acesso)
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Exportar CSV
    if st.button("📥 Exportar CSV", key="export_retorno"):
        csv = df.to_csv(index=False)
        st.download_button(
            "📄 Baixar CSV",
            csv,
            f"retorno_ferias_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            key="download_retorno"
        )


def _render_relatorio_saida(database):
    """Relatório de saída de férias com status de acessos."""
    st.subheader("🚀 Relatório de Saída de Férias")
    
    st.info("💡 Visualize funcionários que saíram de férias e verifique se todos os acessos foram bloqueados.")
    
    # Configuração de data
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Mês passado
    if mes_atual == 1:
        mes_passado = 12
        ano_mes_passado = ano_atual - 1
    else:
        mes_passado = mes_atual - 1
        ano_mes_passado = ano_atual
    
    meses_nomes = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Opções de filtro
    opcoes_ciclo = [
        f"Último Ciclo ({meses_nomes[mes_passado]}/{ano_mes_passado} - {meses_nomes[mes_atual]}/{ano_atual})",
        f"Mês Atual ({meses_nomes[mes_atual]}/{ano_atual})",
        f"Mês Passado ({meses_nomes[mes_passado]}/{ano_mes_passado})",
        "Todos os períodos",
        "Período personalizado"
    ]
    
    col_filtro1, col_filtro2 = st.columns([2, 3])
    
    with col_filtro1:
        filtro_ciclo = st.selectbox(
            "📅 Filtrar por ciclo/período:",
            opcoes_ciclo,
            index=0,
            key="filtro_saida_ciclo"
        )
    
    # Determina parâmetros de filtro
    data_inicio, data_fim = None, None
    
    if "Último Ciclo" in filtro_ciclo:
        data_inicio = datetime(ano_mes_passado, mes_passado, 1)
        if mes_atual == 12:
            data_fim = datetime(ano_atual + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano_atual, mes_atual + 1, 1) - timedelta(days=1)
    elif "Mês Atual" in filtro_ciclo:
        data_inicio = datetime(ano_atual, mes_atual, 1)
        if mes_atual == 12:
            data_fim = datetime(ano_atual + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano_atual, mes_atual + 1, 1) - timedelta(days=1)
    elif "Mês Passado" in filtro_ciclo:
        data_inicio = datetime(ano_mes_passado, mes_passado, 1)
        data_fim = datetime(ano_atual, mes_atual, 1) - timedelta(days=1)
    elif "Período personalizado" in filtro_ciclo:
        with col_filtro2:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                data_inicio = st.date_input(
                    "Data início (saída):",
                    value=datetime(ano_mes_passado, mes_passado, 1),
                    key="saida_data_inicio"
                )
            with col_d2:
                data_fim = st.date_input(
                    "Data fim (saída):",
                    value=hoje,
                    key="saida_data_fim"
                )
    
    # Busca funcionários
    funcionarios = database.buscar_funcionarios()
    
    # Filtra por data de saída
    saidas = []
    for f in funcionarios:
        if not f.get('data_saida'):
            continue
        
        try:
            data_saida = datetime.strptime(f['data_saida'], '%Y-%m-%d')
        except:
            continue
        
        # Aplica filtro de período se existir
        if data_inicio and data_fim:
            if isinstance(data_inicio, datetime):
                d_inicio = data_inicio
                d_fim = data_fim
            else:
                d_inicio = datetime.combine(data_inicio, datetime.min.time())
                d_fim = datetime.combine(data_fim, datetime.max.time())
            
            if not (d_inicio <= data_saida <= d_fim):
                continue
        
        saidas.append(f)
    
    if not saidas:
        st.warning("Nenhum funcionário encontrado com saída no período selecionado.")
        return
    
    # Analisa status dos acessos
    sistemas = ["AD", "VPN", "Gmail", "Admin", "Metrics", "TOTVS"]
    
    # Contadores
    total_bloqueados = 0
    total_pendentes = 0
    total_em_ferias = 0
    
    dados_tabela = []
    for f in saidas:
        acessos = f.get('acessos', {})
        
        # Verifica se está em férias atualmente
        data_retorno = None
        try:
            data_retorno = datetime.strptime(f['data_retorno'], '%Y-%m-%d') if f.get('data_retorno') else None
        except:
            pass
        
        em_ferias = False
        if data_retorno and data_retorno >= hoje:
            em_ferias = True
            total_em_ferias += 1
        
        # Verifica se todos os acessos estão bloqueados ou NA
        acessos_ok = True
        status_acessos = {}
        
        for sistema in sistemas:
            status = acessos.get(sistema, 'PENDENTE')
            status_acessos[sistema] = status
            if status == 'LIBERADO' and em_ferias:
                acessos_ok = False
            elif status == 'PENDENTE':
                acessos_ok = False
        
        if acessos_ok:
            total_bloqueados += 1
            status_geral = "✅ Bloqueado" if em_ferias else "✅ OK"
        else:
            total_pendentes += 1
            status_geral = "⚠️ Pendente" if em_ferias else "⚠️ Verificar"
        
        # Adiciona indicador de em férias
        if em_ferias:
            status_geral = "🏖️ " + status_geral
        
        dados_tabela.append({
            "Nome": f.get('nome', ''),
            "Saída": f.get('data_saida', ''),
            "Retorno": f.get('data_retorno', ''),
            "Em Férias": "Sim" if em_ferias else "Não",
            "RH Solicitante": f.get('unidade', ''),
            "Gestor": f.get('gestor', ''),
            "Status Geral": status_geral,
            **{s: status_acessos.get(s, 'NB') for s in sistemas}
        })
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Saídas", len(saidas))
    with col2:
        st.metric("🏖️ Em Férias Agora", total_em_ferias)
    with col3:
        st.metric("✅ Acessos OK", total_bloqueados)
    with col4:
        st.metric("⚠️ Acessos Pendentes", total_pendentes)
    
    st.divider()
    
    # Filtros
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        filtro_status = st.radio(
            "Filtrar por status:",
            ["Todos", "✅ Apenas OK", "⚠️ Apenas Pendentes"],
            horizontal=True,
            key="filtro_status_saida"
        )
    
    with col_f2:
        filtro_ferias = st.radio(
            "Filtrar por situação:",
            ["Todos", "🏖️ Em férias agora", "📋 Já retornaram"],
            horizontal=True,
            key="filtro_ferias_saida"
        )
    
    # Aplica filtros
    if filtro_status == "✅ Apenas OK":
        dados_tabela = [d for d in dados_tabela if "✅" in d["Status Geral"]]
    elif filtro_status == "⚠️ Apenas Pendentes":
        dados_tabela = [d for d in dados_tabela if "⚠️" in d["Status Geral"]]
    
    if filtro_ferias == "🏖️ Em férias agora":
        dados_tabela = [d for d in dados_tabela if d["Em Férias"] == "Sim"]
    elif filtro_ferias == "📋 Já retornaram":
        dados_tabela = [d for d in dados_tabela if d["Em Férias"] == "Não"]
    
    if not dados_tabela:
        st.info("Nenhum registro encontrado com os filtros selecionados.")
        return
    
    # Formata datas
    for d in dados_tabela:
        try:
            if d["Saída"]:
                d["Saída"] = datetime.strptime(d["Saída"], '%Y-%m-%d').strftime('%d/%m/%Y')
            if d["Retorno"]:
                d["Retorno"] = datetime.strptime(d["Retorno"], '%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            pass
    
    # Tabela
    df = pd.DataFrame(dados_tabela)
    
    # Estiliza status dos acessos
    def estilizar_acesso(val):
        if val == "LIBERADO":
            return "🟢"
        elif val == "BLOQUEADO":
            return "🔴"
        elif val in ["NA", "NB", "NP"]:
            return "⚪"
        else:
            return "⬜"
    
    for sistema in sistemas:
        if sistema in df.columns:
            df[sistema] = df[sistema].apply(estilizar_acesso)
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Exportar CSV
    if st.button("📥 Exportar CSV", key="export_saida"):
        csv = df.to_csv(index=False)
        st.download_button(
            "📄 Baixar CSV",
            csv,
            f"saida_ferias_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            key="download_saida"
        )
