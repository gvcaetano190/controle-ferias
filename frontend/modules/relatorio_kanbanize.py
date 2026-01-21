"""
Aba de Relatório Kanbanize - Análise de Cards Parados
- Mostra cards parados > 5 dias
- Filtro por fluxo e coluna
- Identifica gargalos
- Exportação para PDF e Imagem
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import unicodedata
import io
import base64

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from config.settings import settings
from integrations.kanbanize import KanbanizeAPI


@st.cache_resource(show_spinner=False)
def get_api_connection():
    if not settings.KANBANIZE_BASE_URL or not settings.KANBANIZE_API_KEY:
        return None
    return KanbanizeAPI(settings.KANBANIZE_BASE_URL, settings.KANBANIZE_API_KEY)


# Colunas excluídas do relatório
COLUNAS_EXCLUIDAS = {
    ("Solicitações Dell", "Resolvido"),
    ("Tarefas TIME", "Concluído"),
    ("Solicitações Dell", "Backlog"),
    ("Requisição de Material", "NF + Boleto Enviado"),
}


@st.cache_data(ttl=300, show_spinner=False)  # Cache por 5 minutos
def _buscar_workflows_colunas(api_url: str, api_key: str, board_id: int):
    """Busca estrutura de workflows e colunas com cache."""
    api = KanbanizeAPI(api_url, api_key)
    res_wf = api.listar_workflows(board_id)
    workflows = []
    if res_wf.get("sucesso"):
        workflows = [{"id": wf['workflow_id'], "name": wf['name']} 
                    for wf in res_wf.get("dados", []) if 'workflow_id' in wf]
    
    res_col = api.listar_colunas(board_id)
    colunas = []
    if res_col.get("sucesso"):
        colunas = [{"id": col['column_id'], "name": col['name'], "workflow_id": col.get('workflow_id')}
                  for col in res_col.get("dados", []) if 'column_id' in col]
    
    return workflows, colunas


@st.cache_data(ttl=60, show_spinner=False)  # Cache por 1 minuto
def _processar_cards_parados(cards_json: str):
    """Processa cards parados com cache para evitar reprocessamento."""
    import json
    cards = json.loads(cards_json)
    
    # Filtra cards das colunas excluídas (normalizando nomes)
    def normalize(s):
        s = (s or '').strip().lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        return s

    COLUNAS_EXCLUIDAS_NORMALIZADAS = set((normalize(f), normalize(c)) for f, c in COLUNAS_EXCLUIDAS)
    cards_filtrados = []
    for card in cards:
        workflow_name_raw = card.get('workflow_name', '')
        column_name_raw = card.get('column_name', '')
        workflow_name = normalize(workflow_name_raw)
        column_name = normalize(column_name_raw)
        # Filtro exato
        excluido = (workflow_name, column_name) in COLUNAS_EXCLUIDAS_NORMALIZADAS
        # Filtro por substring para NF + Boleto, Termo Salvo GDr, Termo - Salvo
        if (
            'nf + boleto' in column_name
            or 'termo salvo gdr' in column_name
            or 'termo - salvo' in column_name
        ):
            excluido = True
        # Filtro para excluir colunas específicas (ignorando acentos)
        colunas_bloqueadas = {'formatacao', 'entrega / envi', 'maquina', 'done'}
        col_normalizada = normalize(column_name_raw)
        if col_normalizada in colunas_bloqueadas or 'maquina com pro' in col_normalizada:
            excluido = True
        # Filtro para excluir todo o fluxo 'Formatação'
        if normalize(workflow_name_raw) == 'formatacao':
            excluido = True
        if not excluido:
            cards_filtrados.append(card)
    
    cards_parados = []
    for card in cards_filtrados:
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
    
    # Ordena por fluxo (alfabético) e depois por dias (maiores primeiro)
    cards_parados.sort(key=lambda x: (
        x['card'].get('workflow_name', '').lower(),
        -x['dias']
    ))
    
    return cards_parados


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
        if st.button("🔄 Sincronizar Fluxo 75 (Rápido)", type="primary", width="stretch"):
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
    
    # Carrega estrutura com cache
    workflows, colunas = _buscar_workflows_colunas(
        settings.KANBANIZE_BASE_URL, 
        settings.KANBANIZE_API_KEY, 
        default_board_id
    )
    
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
    
    # Processa cards com cache (serializa para JSON para cache)
    import json
    cards_json = json.dumps(cards, default=str)
    cards_parados = _processar_cards_parados(cards_json)
    
    if cards_parados:
        st.warning(f"⚠️ {len(cards_parados)} cards parados > 5 dias")
        
        # Prepara dados para exportação (já ordenados por fluxo)
        dados_export = []
        fluxo_anterior = None
        num_no_fluxo = 0
        
        for item in cards_parados:
            card = item['card']
            dias = item['dias']
            horas = item['horas']
            fluxo = card.get('workflow_name', '-')
            
            # Reseta contador quando muda o fluxo
            if fluxo != fluxo_anterior:
                num_no_fluxo = 0
                fluxo_anterior = fluxo
            num_no_fluxo += 1
            
            dados_export.append({
                '#': num_no_fluxo,
                'Card ID': card['card_id'],
                'Título': card.get('title', 'N/A'),
                'Fluxo': fluxo,
                'Coluna': card.get('column_name', 'N/A'),
                'Dias Parado': dias,
                'Horas': horas,
                'Tempo Total': f"{dias}d {horas}h"
            })
        
        df_export = pd.DataFrame(dados_export)
        
        # Gera HTML do relatório (usado por vários botões)
        html_content = _gerar_html_relatorio(cards_parados, wf_nome, col_nome)
        
        # Botões de exportação
        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
        
        with col_exp1:
            # Enviar via WhatsApp
            if st.button("📱 WhatsApp", width="stretch", help="Envia imagem do relatório via WhatsApp"):
                with st.spinner("Gerando imagem e enviando..."):
                    resultado = _enviar_relatorio_whatsapp(html_content, len(cards_parados))
                    if resultado["sucesso"]:
                        st.success(f"✅ {resultado['mensagem']}")
                    else:
                        st.error(f"❌ {resultado['mensagem']}")
        
        with col_exp2:
            # Exportar Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Cards Parados')
            excel_data = buffer.getvalue()
            st.download_button(
                label="📥 Excel",
                data=excel_data,
                file_name=f"kanbanize_cards_parados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch"
            )
        
        with col_exp3:
            # Gerar PDF com WeasyPrint
            pdf_bytes = _gerar_pdf_do_html(html_content)
            
            if pdf_bytes:
                st.download_button(
                    label="📄 PDF",
                    data=pdf_bytes,
                    file_name=f"kanbanize_relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    width="stretch"
                )
            else:
                st.download_button(
                    label="📄 HTML",
                    data=html_content,
                    file_name=f"kanbanize_relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                    mime="text/html",
                    width="stretch",
                    help="WeasyPrint não instalado. Abra o HTML no navegador e use Ctrl+P para PDF."
                )
        
        with col_exp4:
            # Gerar Imagem PNG (passa total de cards para calcular altura)
            png_bytes = _gerar_imagem_do_html(html_content, total_cards=len(cards_parados))
            
            if png_bytes:
                st.download_button(
                    label="🖼️ Imagem",
                    data=png_bytes,
                    file_name=f"kanbanize_relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                    mime="image/png",
                    width="stretch"
                )
            else:
                st.button(
                    label="🖼️ Imagem",
                    disabled=True,
                    width="stretch",
                    help="Instale html2image e Chrome/Chromium para gerar imagens"
                )
        
        st.divider()
        
        # Tabela - agrupa por fluxo
        fluxo_atual = None
        contador = 0
        
        for item in cards_parados:
            card = item['card']
            dias = item['dias']
            horas = item['horas']
            workflow_name = card.get('workflow_name') or '-'
            
            # Cabeçalho de fluxo quando muda
            if workflow_name != fluxo_atual:
                if fluxo_atual is not None:
                    st.divider()  # Separador entre fluxos
                
                # Conta cards deste fluxo
                cards_no_fluxo = sum(1 for x in cards_parados if x['card'].get('workflow_name') == workflow_name)
                st.markdown(f"### 🔀 {workflow_name} ({cards_no_fluxo} cards)")
                
                # Cabeçalho da tabela
                cols = st.columns([0.5, 2.5, 1.5, 1])
                with cols[0]:
                    st.caption("**#**")
                with cols[1]:
                    st.caption("**Título**")
                with cols[2]:
                    st.caption("**Coluna**")
                with cols[3]:
                    st.caption("**Tempo**")
                
                fluxo_atual = workflow_name
                contador = 0
            
            contador += 1
            
            # Extrai nome
            custom_raw = card.get('custom_fields', [])
            nome = '-'
            serie = '-'
            for cf in custom_raw:
                if cf.get('field_id') == 551:
                    nome = cf.get('value') or '-'
                elif cf.get('field_id') == 540:
                    serie = cf.get('value') or '-'
            
            cols = st.columns([0.5, 2.5, 1.5, 1])
            with cols[0]:
                st.caption(str(contador))
            with cols[1]:
                st.caption(f"#{card['card_id']}: {card.get('title', 'N/A')[:35]}")
            with cols[2]:
                column_name = card.get('column_name') or 'N/A'
                st.caption(column_name[:20])
            with cols[3]:
                if dias > 10:
                    st.markdown(f"🔴 **{dias}d {horas}h**")
                elif dias > 7:
                    st.markdown(f"🟠 **{dias}d {horas}h**")
                else:
                    st.markdown(f"🟡 **{dias}d {horas}h**")
        
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
                # Registra log de erro
                database.registrar_log(
                    tipo="kanbanize",
                    categoria="Kanbanize",
                    status="erro",
                    mensagem="Erro na sincronização do Kanbanize",
                    detalhes=f"Erro: {res.get('mensagem')}",
                    origem="relatorio_kanbanize"
                )
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
        
        # Registra log de sucesso
        database.registrar_log(
            tipo="kanbanize",
            categoria="Kanbanize",
            status="sucesso",
            mensagem="Sincronização do Kanbanize concluída com sucesso",
            detalhes=f"Cards: {salvos}, Tempo: {elapsed:.1f}s, Board: {board_id}",
            origem="relatorio_kanbanize"
        )
        
    except Exception as e:
        status_box.update(label="❌ Erro Crítico", state="error")
        st.error(f"Erro: {e}")
        
        # Registra log de erro
        database.registrar_log(
            tipo="kanbanize",
            categoria="Kanbanize",
            status="erro",
            mensagem="Erro crítico na sincronização do Kanbanize",
            detalhes=str(e),
            origem="relatorio_kanbanize"
        )


def _gerar_html_relatorio(cards_parados: list, fluxo: str, coluna: str) -> str:
    """
    Gera HTML formatado do relatório para impressão/PDF, organizado por fluxo.
    """
    hoje = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    # Agrupa cards por fluxo
    from collections import defaultdict
    cards_por_fluxo = defaultdict(list)
    for item in cards_parados:
        workflow = item['card'].get('workflow_name', '-')
        cards_por_fluxo[workflow].append(item)
    
    # Gera seções por fluxo
    secoes_html = ""
    for workflow in sorted(cards_por_fluxo.keys()):
        cards_do_fluxo = cards_por_fluxo[workflow]
        # Ordena por dias dentro do fluxo
        cards_do_fluxo.sort(key=lambda x: -x['dias'])
        
        secoes_html += f"""
        <div class="fluxo-section">
            <h3>🔀 {workflow} ({len(cards_do_fluxo)} cards)</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width: 5%;">#</th>
                        <th style="width: 50%;">Título</th>
                        <th style="width: 25%;">Coluna</th>
                        <th style="width: 20%;">Tempo</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, item in enumerate(cards_do_fluxo, 1):
            card = item['card']
            dias = item['dias']
            horas = item['horas']
            
            cor_tempo = "#dc3545" if dias > 10 else "#fd7e14" if dias > 7 else "#ffc107"
            
            secoes_html += f"""
                    <tr>
                        <td style="text-align: center;">{i}</td>
                        <td><strong>#{card['card_id']}</strong>: {card.get('title', 'N/A')[:50]}</td>
                        <td>{card.get('column_name', 'N/A')}</td>
                        <td style="text-align: center; color: {cor_tempo}; font-weight: bold;">{dias}d {horas}h</td>
                    </tr>
            """
        
        secoes_html += """
                </tbody>
            </table>
        </div>
        """
    
    total_cards = len(cards_parados)
    media_dias = sum(x['dias'] for x in cards_parados) / total_cards if total_cards > 0 else 0
    total_fluxos = len(cards_por_fluxo)
    
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Kanbanize - Cards Parados</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
            padding: 20px; 
            background: #ffffff;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .header h1 {{ 
            color: #1e3a5f; 
            font-size: 32px; 
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{ 
            color: #6c757d; 
            font-size: 16px;
            font-weight: 500;
        }}
        .filtros {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 30px;
        }}
        .filtros span {{ color: #495057; }}
        .filtros strong {{ color: #1e3a5f; }}
        .resumo {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .resumo-item {{
            background: #e7f1ff;
            padding: 15px 25px;
            border-radius: 8px;
            text-align: center;
        }}
        .resumo-item .numero {{
            font-size: 28px;
            font-weight: bold;
            color: #1e3a5f;
        }}
        .resumo-item .label {{
            font-size: 12px;
            color: #6c757d;
        }}
        .fluxo-section {{
            margin-bottom: 30px;
        }}
        .fluxo-section h3 {{
            color: #1e3a5f;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 3px solid #1e3a5f;
            letter-spacing: -0.3px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
        }}
        th {{ 
            background: #1e3a5f; 
            color: white; 
            padding: 16px 12px; 
            text-align: left;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}
        td {{ 
            padding: 12px 12px; 
            border-bottom: 1px solid #e9ecef;
            font-size: 14px;
            font-weight: 500;
        }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        tr:hover {{ background: #e7f1ff; }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 11px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; }}
            .fluxo-section {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Relatório Kanbanize - Cards Parados</h1>
            <div class="subtitle">Gerado em {hoje}</div>
        </div>
        
        <div class="filtros">
            <span>🔀 Fluxo: <strong>{fluxo}</strong></span>
            <span>📋 Coluna: <strong>{coluna}</strong></span>
        </div>
        
        <div class="resumo">
            <div class="resumo-item">
                <div class="numero">{total_cards}</div>
                <div class="label">Cards Parados</div>
            </div>
            <div class="resumo-item">
                <div class="numero">{media_dias:.1f}</div>
                <div class="label">Média de Dias</div>
            </div>
            <div class="resumo-item">
                <div class="numero">{total_fluxos}</div>
                <div class="label">Fluxos</div>
            </div>
        </div>
        
        {secoes_html}
        
        <div class="footer">
            Sistema de Controle de Férias - Relatório Kanbanize<br>
            Para salvar como PDF: Ctrl+P → Salvar como PDF
        </div>
    </div>
</body>
</html>
    """
    
    return html


def _gerar_pdf_do_html(html_content: str) -> bytes | None:
    """
    Gera PDF a partir do HTML usando WeasyPrint.
    Retorna None se WeasyPrint não estiver instalado.
    """
    try:
        from weasyprint import HTML
        
        # Gera PDF em memória
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
    except ImportError:
        # WeasyPrint não instalado
        return None
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        return None


def _gerar_imagem_do_html(html_content: str, total_cards: int = 50) -> bytes | None:
    """
    Gera imagem PNG com renderização por software (sem GPU).
    Retorna None se html2image ou Chrome/Chromium não estiver disponível.
    
    Args:
        html_content: HTML a ser convertido
        total_cards: Número total de cards para calcular altura
    """
    try:
        from html2image import Html2Image
        import tempfile
        import os
        import subprocess
        
        # Suprime erros de GPU do Chrome
        import sys
        from io import StringIO
        
        # Calcula altura baseado no número de cards
        altura_base = 500
        altura_por_card = 50
        altura_headers_fluxo = 120
        
        num_fluxos = max(1, total_cards // 5)
        altura_calculada = altura_base + (total_cards * altura_por_card) + (num_fluxos * altura_headers_fluxo)
        altura_final = max(1000, min(altura_calculada, 15000))
        
        # Resolução moderada
        largura = 1200
        
        # Cria diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            hti = Html2Image(
                output_path=temp_dir,
                size=(largura, altura_final),
                custom_flags=[
                    '--no-sandbox',
                    '--disable-gpu',  # Desabilita GPU completamente
                    '--disable-software-rasterizer',  # Força rasterização por CPU
                    '--disable-extensions',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-background-networking',
                    '--disable-client-side-phishing-detection',
                    '--disable-hang-monitor',
                    '--disable-popup-blocking',
                    '--disable-prompt-on-repost',
                    '--disable-translated-click-to-define',
                    '--disable-plugin-power-saver',
                    '--disable-extensions',
                    '--no-default-browser-check',
                    '--hide-scrollbars',
                    '--virtual-time-budget=8000',  # 8s
                ]
            )
            
            # Redireciona stderr para suprimir erros de GPU
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            try:
                paths = hti.screenshot(
                    html_str=html_content,
                    save_as='relatorio.png'
                )
            finally:
                sys.stderr = old_stderr
            
            if paths and os.path.exists(paths[0]):
                with open(paths[0], 'rb') as f:
                    png_data = f.read()
                    print(f"[INFO] PNG gerado: {len(png_data)} bytes, {largura}x{altura_final}px")
                    return png_data
        
        return None
    except ImportError:
        return None
    except Exception as e:
        print(f"[ERROR] Ao gerar imagem: {e}")
        return None


def _enviar_relatorio_whatsapp(html_content: str, total_cards: int) -> dict:
    """
    Gera imagem do relatório e envia via WhatsApp usando Evolution API.
    
    Args:
        html_content: HTML do relatório a ser convertido em imagem
        total_cards: Número total de cards para calcular altura da imagem
        
    Returns:
        Dict com resultado: {"sucesso": bool, "mensagem": str}
    """
    from integrations.evolution_api import EvolutionAPI
    
    # Gera a imagem do relatório
    png_bytes = _gerar_imagem_do_html(html_content, total_cards=total_cards)
    
    if not png_bytes:
        return {
            "sucesso": False,
            "mensagem": "Não foi possível gerar a imagem do relatório. Verifique se html2image está instalado."
        }
    
    # Prepara a legenda
    data_hora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    caption = f"📊 *Relatório Kanbanize - Cards Parados*\n\n📅 {data_hora}\n📦 Total: {total_cards} cards\n\n_Gerado pelo Sistema de Controle de Férias_"
    
    # Envia via Evolution API
    api = EvolutionAPI()
    
    resultado = api.enviar_media(
        media_bytes=png_bytes,
        mediatype="image",
        caption=caption
    )
    
    if resultado.get("sucesso"):
        return {
            "sucesso": True,
            "mensagem": "Relatório enviado com sucesso via WhatsApp!"
        }
    else:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao enviar: {resultado.get('mensagem', 'Erro desconhecido')}"
        }
