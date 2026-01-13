"""
Página de Kanbanize - Visualização de Cards com Cache.
Versão: Com Persistência em Banco de Dados
- Filtros trabalham com CACHE (sem API)
- Botão "Buscar Dados" recarrega tudo na API e salva no banco
- Mostra quanto tempo cada card está parado na coluna
"""

import sys
import time
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from config.settings import settings
from integrations.kanbanize import KanbanizeAPI

# --- 1. CONEXÃO PERSISTENTE ---
@st.cache_resource(show_spinner=False)
def get_api_connection():
    if not settings.KANBANIZE_BASE_URL or not settings.KANBANIZE_API_KEY:
        return None
    return KanbanizeAPI(settings.KANBANIZE_BASE_URL, settings.KANBANIZE_API_KEY)

# --- 2. CACHE DE ESTRUTURA (Workflow/Colunas) ---
@st.cache_data(ttl=600, show_spinner=False)
def carregar_estrutura_rapida(_api, board_id):
    workflows = []
    columns = []
    try:
        res_wf = _api.listar_workflows(board_id)
        if res_wf.get("sucesso"):
            for item in res_wf.get("dados", []):
                if 'workflow_id' in item:
                    workflows.append({"id": item['workflow_id'], "name": item['name']})

        res_col = _api.listar_colunas(board_id)
        if res_col.get("sucesso"):
            # Exclui colunas que representam cards resolvidos ou termos salvos
            excluded = ['resolvido', 'resolved', 'done', 'fechado', 'closed', 'concluído', 'completed', 'termo - salvo', 'termo salvo', 'termo-salvo', 'backlog']
            excluded_workflows_list = ['Formatação']
            
            for item in res_col.get("dados", []):
                if 'column_id' in item:
                    # Get workflow name
                    wf_id_item = item.get('workflow_id')
                    wf_name = next((w['name'] for w in workflows if w['id'] == wf_id_item), None) if workflows else None
                    # Skip excluded workflows
                    if wf_name in excluded_workflows_list:
                        continue
                    name = item.get('name', '')
                    name_lower = (name or '').lower()
                    # Exclude exact matches, termo+salvo patterns, NF+Boleto, Maquina/Formatação patterns, and backlog
                    if name_lower in excluded \
                       or ('termo' in name_lower and 'salvo' in name_lower) \
                       or ('nf' in name_lower and 'boleto' in name_lower) \
                       or ('maquina' in name_lower) \
                       or ('format' in name_lower) \
                       or 'backlog' in name_lower:
                        continue
                    columns.append({
                        "id": item['column_id'],
                        "name": name,
                        "workflow_id": item.get('workflow_id')
                    })
    except Exception:
        pass
    return workflows, columns

def render(database):
    st.header("📋 Kanbanize - Inventário")
    
    if not settings.KANBANIZE_ENABLED:
        st.warning("⚠️ Habilite nas configurações.")
        return
    
    api = get_api_connection()
    if not api:
        st.error("❌ Credenciais não configurados.")
        return

    default_board_id = int(settings.KANBANIZE_DEFAULT_BOARD_ID) if hasattr(settings, 'KANBANIZE_DEFAULT_BOARD_ID') and str(settings.KANBANIZE_DEFAULT_BOARD_ID).isdigit() else 0
    
    if default_board_id <= 0:
        st.warning("⚠️ Configure o Board Padrão.")
        return

    # Carrega estrutura
    with st.spinner("Conectando..."):
        lista_workflows, lista_colunas = carregar_estrutura_rapida(api, default_board_id)

    # Fallback visual
    if not lista_workflows: lista_workflows = [{"id": 0, "name": "Todos"}]
    if not lista_colunas: lista_colunas = [{"id": 0, "name": "Todas", "workflow_id": 0}]

    # --- CALLBACK: quando muda o filtro, carrega do cache ou busca da API ---
    def ao_mudar_filtro():
        """Callback executado quando filtro muda."""
        # Vai ser acionado abaixo após os selectbox
        pass

    # --- FILTROS (COM CALLBACK) ---
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    
    # Fluxo
    mapa_fluxos = {wf['name']: wf['id'] for wf in lista_workflows}
    if "Todos" not in mapa_fluxos and len(mapa_fluxos) > 1:
        mapa_fluxos = {"Todos": None, **mapa_fluxos}
        
    with c1:
        fluxo_nome = st.selectbox("🔀 Fluxo:", list(mapa_fluxos.keys()), key="fluxo_select")
        fluxo_id = mapa_fluxos.get(fluxo_nome)
        if fluxo_id == 0: fluxo_id = None
    
    # Coluna
    mapa_colunas = {"Todas": None}
    for col in lista_colunas:
        if fluxo_id is None or col.get('workflow_id') == fluxo_id:
            mapa_colunas[col['name']] = col['id']
            
    with c2:
        coluna_nome = st.selectbox("📋 Coluna:", list(mapa_colunas.keys()), key="coluna_select")
        coluna_id = mapa_colunas[coluna_nome]

    # Botões de ação
    with c3:
        if st.button("🔄 Reset Cache", type="secondary", help="Limpa o cache local"):
            database.limpar_cards_kanbanize(default_board_id)
            if "kanbanize_last_search" in st.session_state:
                del st.session_state["kanbanize_last_search"]
            if "kanbanize_filtro_atual" in st.session_state:
                del st.session_state["kanbanize_filtro_atual"]
            st.rerun()
    
    with c4:
        st.write("")
        st.write("")
        cache_count = database.contar_cards_cache(default_board_id)
        st.caption(f"📦 {cache_count} cards em cache")

    # --- LÓGICA: verifica se filtro mudou ---
    filtro_atual = (fluxo_id, coluna_id)
    
    # Inicializa session state se não existir
    if "kanbanize_filtro_atual" not in st.session_state:
        st.session_state["kanbanize_filtro_atual"] = None  # Começa sem filtro
        st.session_state["kanbanize_last_search"] = []
        st.session_state["kanbanize_primeira_abertura"] = True
    
    # Detecta mudança de filtro (ignora primeira abertura)
    filtro_mudou = (
        st.session_state.get("kanbanize_filtro_atual") != filtro_atual and
        not st.session_state.get("kanbanize_primeira_abertura", False)
    )
    
    # Marca como não mais primeira abertura
    if st.session_state.get("kanbanize_primeira_abertura"):
        st.session_state["kanbanize_primeira_abertura"] = False
    
    if filtro_mudou:
        # Filtro foi alterado - tenta carregar do cache
        st.session_state["kanbanize_filtro_atual"] = filtro_atual
        
        # Busca no cache com o filtro específico
        cache_cards = database.buscar_cards_kanbanize(
            workflow_id=fluxo_id,
            column_id=coluna_id,
            board_id=default_board_id
        )
        
        if cache_cards:
            # Tem cache! Mostra
            st.session_state["kanbanize_last_search"] = cache_cards
            st.success(f"📦 Carregado do cache: {len(cache_cards)} cards")
        else:
            # Não tem cache, busca na API
            st.info("📥 Nenhum cache. Buscando na API...")
            
            cards_finais = []
            page = 1
            keep = True
            w_ids = [fluxo_id] if fluxo_id else None
            c_ids = [coluna_id] if coluna_id else None
            
            try:
                while keep:
                    res = api.buscar_cards_completos_paralelo(
                        board_ids=[default_board_id],
                        workflow_ids=w_ids, 
                        column_ids=c_ids,   
                        page=page,
                        per_page=200 
                    )
                    
                    if not res.get("sucesso"):
                        st.error(f"❌ Erro na API: {res.get('mensagem')}")
                        break
                    
                    batch = res.get("dados", [])
                    if not batch: 
                        break
                    
                    cards_finais.extend(batch)
                    
                    if len(batch) < 30:
                        keep = False
                    else:
                        page += 1

                # Mapeamento Nomes
                w_map_simple = {wf['id']: wf['name'] for wf in lista_workflows}
                c_map_simple = {c['id']: c['name'] for c in lista_colunas}

                for c in cards_finais:
                    wid = c.get('workflow_id')
                    cid = c.get('column_id')
                    c['workflow_name'] = w_map_simple.get(wid) or f"{wid}"
                    c['column_name'] = c_map_simple.get(cid) or f"{cid}"

                # Salva no banco
                if cards_finais:
                    database.salvar_cards_kanbanize(cards_finais, default_board_id)
                    st.success(f"✅ {len(cards_finais)} cards carregados e salvos")
                else:
                    st.info("⚠️ Nenhum card encontrado com esses filtros")
                
                st.session_state["kanbanize_last_search"] = cards_finais
                    
            except Exception as e:
                st.error(f"❌ Erro: {e}")
                st.session_state["kanbanize_last_search"] = []

    # --- STATUS ---
    st.write("")
    st.divider()
    
    ultima_sync = database.obter_ultima_sincronizacao_kanbanize(default_board_id)
    if ultima_sync:
        st.info(f"✅ Cache: Última sincronização em {ultima_sync[:10]} às {ultima_sync[11:19]}")

    # --- BOTÃO "BUSCAR DADOS" para forçar recarregar ---
    if st.button("🚀 Buscar Dados (Forçar)", type="primary", use_container_width=True, help="Força busca na API mesmo com cache"):
        st.divider()
        
        status_box = st.status("🚀 Iniciando motor de busca...", expanded=True)
        start_time = time.time()
        
        cards_finais = []
        page = 1
        keep = True
        
        w_ids = [fluxo_id] if fluxo_id else None
        c_ids = [coluna_id] if coluna_id else None
        
        try:
            while keep:
                status_box.write(f"📥 Baixando página {page}...")
                
                # Busca na API
                res = api.buscar_cards_completos_paralelo(
                    board_ids=[default_board_id],
                    workflow_ids=w_ids, 
                    column_ids=c_ids,   
                    page=page,
                    per_page=200 

                )
                
                if not res.get("sucesso"):
                    status_box.update(label="Erro na API!", state="error")
                    st.error(res.get('mensagem'))
                    break
                
                batch = res.get("dados", [])
                if not batch: 
                    break
                
                cards_finais.extend(batch)
                status_box.write(f"✅ {len(cards_finais)} cards baixados...")
                
                if len(batch) < 30:
                    keep = False
                else:
                    page += 1

            # Mapeamento Nomes
            w_map_simple = {wf['id']: wf['name'] for wf in lista_workflows}
            c_map_simple = {c['id']: c['name'] for c in lista_colunas}

            for c in cards_finais:
                wid = c.get('workflow_id')
                cid = c.get('column_id')
                c['workflow_name'] = w_map_simple.get(wid) or f"{wid}"
                c['column_name'] = c_map_simple.get(cid) or f"{cid}"

            # SALVA NO BANCO
            if cards_finais:
                status_box.write(f"💾 Salvando {len(cards_finais)} cards no banco...")
                salvos = database.salvar_cards_kanbanize(cards_finais, default_board_id)
                status_box.write(f"✅ {salvos} cards salvos!")
            
            # Salva no session state para exibição
            st.session_state["kanbanize_last_search"] = cards_finais
            
            elapsed = time.time() - start_time
            status_box.update(label=f"✅ Sucesso! {len(cards_finais)} itens em {elapsed:.1f}s", state="complete", expanded=False)
            
            if not cards_finais:
                st.warning("Nenhum card encontrado com esses filtros.")
                
        except Exception as e:
            status_box.update(label="Erro Crítico", state="error")
            st.error(f"Erro: {e}")

    # --- RENDERIZAÇÃO ---
    cards_exibir = st.session_state.get("kanbanize_last_search", [])
    
    st.divider()
    if cards_exibir:
        st.success(f"Exibindo {len(cards_exibir)} itens.")
        for card in cards_exibir:
            renderizar_inventario(card)
    else:
        if database.contar_cards_cache(default_board_id) > 0:
            st.info("Nenhum card com esses filtros. Selecione outro filtro ou clique em 'Buscar Dados (Forçar)'.")
        else:
            st.info("👈 Selecione um filtro para começar.")

def renderizar_inventario(card):
    """Renderiza card HTML com tempo parado na coluna."""
    from datetime import datetime
    
    title = card.get('title', 'Sem Título')
    cid = card.get('card_id')
    color = card.get('color', '#ccc')
    
    # Extração de Campos
    custom_raw = card.get('custom_fields', [])
    campos_map = {}
    
    for cf in custom_raw:
        fid = cf.get('field_id')
        val = cf.get('value') or cf.get('display_value') or cf.get('values')
        if isinstance(val, list):
             val = ", ".join([str(v.get('value','')) for v in val if isinstance(v, dict)])
        
        if val:
            if fid == 551: campos_map['Nome'] = val
            elif fid == 540: campos_map['Serie'] = val 
            elif fid in [654, 214]: campos_map['Modelo'] = val 
            
            name = cf.get('name', '')
            if 'Modelos' in name: campos_map.setdefault('Modelo', val)
            if 'ENTREGA' in name: campos_map.setdefault('Entrega', val)

    nome_user = campos_map.get('Nome', '-')
    modelo = campos_map.get('Modelo', '-')
    serie = campos_map.get('Serie', '-')
    
    created = str(card.get('created_at','')).split('T')[0]
    updated = str(card.get('last_modified','')).split('T')[0]
    
    # Calcula tempo parado na coluna
    tempo_coluna = "-"
    in_position = card.get('in_current_position_since')
    if in_position:
        try:
            # Parse da data ISO
            dt_position = datetime.fromisoformat(in_position.replace('Z', '+00:00'))
            dt_now = datetime.now(dt_position.tzinfo)
            delta = dt_now - dt_position
            
            dias = delta.days
            horas = delta.seconds // 3600
            minutos = (delta.seconds % 3600) // 60
            
            if dias > 0:
                tempo_coluna = f"{dias}d {horas}h"
            elif horas > 0:
                tempo_coluna = f"{horas}h {minutos}m"
            else:
                tempo_coluna = f"{minutos}m"
        except:
            tempo_coluna = in_position[:10] if in_position else "-"

    st.markdown(f"""
    <div style="border-left: 5px solid {color}; padding: 15px; background: white; margin-bottom: 10px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="display:flex; justify-content:space-between; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            <span style="font-weight:bold; font-size:15px; color:#333;">{title}</span>
            <span style="background:#f4f4f4; padding:2px 6px; border-radius:4px; color:#666; font-size:11px;">#{cid}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
            <div><small style="color:#999; font-weight:bold;">👤 NOME</small><br><span style="color:#222; font-size:13px;">{nome_user}</span></div>
            <div><small style="color:#999; font-weight:bold;">💻 MODELO</small><br><span style="color:#222; font-size:13px;">{modelo}</span></div>
            <div><small style="color:#999; font-weight:bold;">🔢 SÉRIE</small><br><span style="color:#222; font-size:13px; font-family:monospace;">{serie}</span></div>
            <div><small style="color:#999; font-weight:bold;">⏱️ NA COLUNA</small><br><span style="color:#d32f2f; font-size:13px; font-weight:bold;">{tempo_coluna}</span></div>
            <div><small style="color:#999; font-weight:bold;">📅 CRIADO</small><br><span style="color:#555; font-size:12px;">{created}</span></div>
            <div><small style="color:#999; font-weight:bold;">📅 ATUALIZADO</small><br><span style="color:#555; font-size:12px;">{updated}</span></div>
            <div style="grid-column: span 1;"><small style="color:#999; font-weight:bold;">🔁 FLUXO</small><br><span style="color:#555; font-size:12px;">{card.get('workflow_name', '-') or '-'}</span></div>
            <div style="grid-column: span 1;"><small style="color:#999; font-weight:bold;">📋 COLUNA</small><br><span style="color:#555; font-size:12px;">{card.get('column_name')}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)