"""
Aba de Relatório Kanbanize - Análise de Cards Parados
- Mostra cards parados > 5 dias
- Filtro por fluxo e coluna
- Identifica gargalos
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from config.settings import settings
from integrations.kanbanize import KanbanizeAPI


@st.cache_resource(show_spinner=False)
def get_api_connection():
    if not settings.KANBANIZE_BASE_URL or not settings.KANBANIZE_API_KEY:
        return None
    return KanbanizeAPI(settings.KANBANIZE_BASE_URL, settings.KANBANIZE_API_KEY)


def render(database):
    st.header("📊 Relatório Kanbanize - Cards Parados")
    
    if not settings.KANBANIZE_ENABLED:
        st.warning("⚠️ Habilite nas configurações.")
        return
    
    api = get_api_connection()
    if not api:
        st.error("❌ Credenciais não configuradas.")
        return

    default_board_id = int(settings.KANBANIZE_DEFAULT_BOARD_ID) if hasattr(settings, 'KANBANIZE_DEFAULT_BOARD_ID') and str(settings.KANBANIZE_DEFAULT_BOARD_ID).isdigit() else 0
    
    if default_board_id <= 0:
        st.warning("⚠️ Configure o Board Padrão.")
        return

    # --- BOTÃO: Sincronizar TUDO ---
    c1, c2, c3 = st.columns([2, 2, 2])
    # variável de coluna inicializada para evitar UnboundLocalError
    col_id = None
    
    # Sincronização travada para o workflow id 75 (Tech infra)
    with c1:
        if st.button("🔄 Sincronizar Fluxo 75 (Rápido)", type="primary", use_container_width=True):
            # Sincroniza o board (default_board_id) — inclui TODOS os fluxos/colunas dentro dele
            sincronizar_tudo(api, database, default_board_id)
    
    with c2:
        total_cards = database.contar_cards_cache(default_board_id)
        st.metric("📦 Cards em Cache", total_cards)
    
    with c3:
        ultima_sync = database.obter_ultima_sincronizacao_kanbanize(default_board_id)
        if ultima_sync:
            st.caption(f"✅ Última: {ultima_sync[:10]} {ultima_sync[11:19]}")
        else:
            st.caption("⏳ Nunca sincronizado")

    st.divider()

    # --- FILTROS ---
    c1, c2 = st.columns([2, 2])
    
    # Carrega estrutura
    res_wf = api.listar_workflows(default_board_id)
    workflows = []
    if res_wf.get("sucesso"):
        workflows = [{"id": wf['workflow_id'], "name": wf['name']} 
                    for wf in res_wf.get("dados", []) if 'workflow_id' in wf]
    
    res_col = api.listar_colunas(default_board_id)
    colunas = []
    if res_col.get("sucesso"):
        colunas = [{"id": col['column_id'], "name": col['name'], "workflow_id": col.get('workflow_id')}
                  for col in res_col.get("dados", []) if 'column_id' in col]
    
    mapa_wf = {wf['name']: wf['id'] for wf in workflows}
    if "Todos" not in mapa_wf:
        mapa_wf = {"Todos": None, **mapa_wf}
    
    with c1:
        wf_nome = st.selectbox("🔀 Fluxo:", list(mapa_wf.keys()), key="rel_fluxo")
        wf_id = mapa_wf.get(wf_nome)
        if wf_id == 0: wf_id = None
    
    # Coluna filtrada por workflow
    mapa_col = {"Todas": None}
    for col in colunas:
        if wf_id is None or col.get('workflow_id') == wf_id:
            mapa_col[col['name']] = col['id']
    
    with c2:
        col_nome = st.selectbox("📋 Coluna:", list(mapa_col.keys()), key="rel_coluna")
        col_id = mapa_col.get(col_nome)

    # --- ANÁLISE: Cards parados > 5 dias ---
    st.divider()
    st.subheader("⏱️ Cards Parados > 5 Dias")
    
    cards = database.buscar_cards_kanbanize(
        workflow_id=wf_id,
        column_id=col_id,
        board_id=default_board_id
    )
    
    cards_parados = []
    for card in cards:
        in_position = card.get('in_current_position_since')
        if in_position:
            try:
                dt_position = datetime.fromisoformat(in_position.replace('Z', '+00:00'))
                dt_now = datetime.now(dt_position.tzinfo)
                delta = dt_now - dt_position
                dias = delta.days
                
                if dias > 5:
                    cards_parados.append({
                        'card': card,
                        'dias': dias,
                        'horas': delta.seconds // 3600
                    })
            except:
                pass
    
    if cards_parados:
        st.warning(f"⚠️ {len(cards_parados)} cards parados > 5 dias")
        
        # Ordena por dias (maiores primeiro)
        cards_parados.sort(key=lambda x: x['dias'], reverse=True)
        
        # Tabela
        cols = st.columns([0.5, 2, 1.5, 1.5, 1, 1])
        with cols[0]:
            st.caption("**#**")
        with cols[1]:
            st.caption("**Título**")
        with cols[2]:
            st.caption("**Responsável**")
        with cols[3]:
            st.caption("**Série**")
        with cols[4]:
            st.caption("**Tempo**")
        with cols[5]:
            st.caption("**Coluna**")
        
        st.divider()
        
        for i, item in enumerate(cards_parados, 1):
            card = item['card']
            dias = item['dias']
            horas = item['horas']
            
            # Extrai nome
            custom_raw = card.get('custom_fields', [])
            nome = '-'
            serie = '-'
            for cf in custom_raw:
                if cf.get('field_id') == 551:
                    nome = cf.get('value') or '-'
                elif cf.get('field_id') == 540:
                    serie = cf.get('value') or '-'
            
            cols = st.columns([0.5, 2, 1.5, 1.5, 1, 1.2, 1])
            with cols[0]:
                st.caption(str(i))
            with cols[1]:
                st.caption(f"#{card['card_id']}: {card.get('title', 'N/A')[:30]}")
            with cols[2]:
                st.caption(nome[:20])
            with cols[3]:
                st.caption(serie[:15])
            with cols[4]:
                st.markdown(f"🔴 **{dias}d {horas}h**")
            with cols[5]:
                workflow_name = card.get('workflow_name') or 'N/A'
                st.caption(workflow_name[:15])
            with cols[6]:
                column_name = card.get('column_name') or 'N/A'
                st.caption(column_name[:15])
        
        # Resumo
        st.divider()
        total_dias = sum(x['dias'] for x in cards_parados)
        media_dias = total_dias / len(cards_parados)
        st.info(f"📊 Total: {len(cards_parados)} cards | Média: {media_dias:.1f} dias parado")
        
    else:
        st.success("✅ Nenhum card parado > 5 dias neste filtro!")


def sincronizar_tudo(api, database, board_id, workflow_id: int = None, column_id: int = None):
    """Sincroniza cards do board usando modo rápido (sem detail calls).

    Se `workflow_id` ou `column_id` forem fornecidos, sincroniza apenas esse filtro (mais rápido).
    """
    st.divider()
    
    status_box = st.status("🔄 Sincronizando tudo (modo rápido)...", expanded=True)
    start_time = time.time()
    
    try:
        cards_total = []
        page = 1
        keep = True
        
        while keep:
            status_box.write(f"📥 Baixando página {page}...")
            # Passa sem_detalhes=True para pular detail calls e usar fields na summary
            res = api.buscar_cards_completos_paralelo(
                board_ids=[board_id],
                workflow_ids=[workflow_id] if workflow_id else None,
                column_ids=[column_id] if column_id else None,
                page=page,
                per_page=200,
                sem_detalhes=True  # <-- Modo rápido: apenas summaries com fields
            )
            
            if not res.get("sucesso"):
                status_box.update(label="❌ Erro na API!", state="error")
                st.error(res.get('mensagem'))
                return
            
            batch = res.get("dados", [])
            if not batch:
                break
            
            cards_total.extend(batch)
            status_box.write(f"✅ {len(cards_total)} cards baixados...")
            
            if len(batch) < 200:
                keep = False
            else:
                page += 1
        
        # Busca workflows e colunas para mapear nomes
        res_wf = api.listar_workflows(board_id)
        workflows = {}
        if res_wf.get("sucesso"):
            for wf in res_wf.get("dados", []):
                if 'workflow_id' in wf:
                    workflows[wf['workflow_id']] = wf['name']
        
        res_col = api.listar_colunas(board_id)
        colunas = {}
        if res_col.get("sucesso"):
            for col in res_col.get("dados", []):
                if 'column_id' in col:
                    colunas[col['column_id']] = col['name']
        
        # Adiciona nomes
        for card in cards_total:
            wf_id = card.get('workflow_id')
            col_id = card.get('column_id')
            card['workflow_name'] = workflows.get(wf_id, f"WF_{wf_id}")
            card['column_name'] = colunas.get(col_id, f"Col_{col_id}")
        
        # Salva no banco
        status_box.write(f"💾 Salvando {len(cards_total)} cards no banco...")
        salvos = database.salvar_cards_kanbanize(cards_total, board_id)
        
        elapsed = time.time() - start_time
        status_box.update(
            label=f"✅ Completo! {salvos} cards em {elapsed:.1f}s",
            state="complete",
            expanded=False
        )
        
        st.success(f"✅ {salvos} cards sincronizados e salvos!")
        
    except Exception as e:
        status_box.update(label="❌ Erro Crítico", state="error")
        st.error(f"Erro: {e}")
