"""
Página de Logs - Sistema de Controle de Férias

Exibe logs de atividades, sincronizações e mensagens do sistema.
"""

import sys
from pathlib import Path
from datetime import datetime
import os

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import Database


def get_database():
    """Retorna nova instância do banco."""
    return Database()


def _formatar_timestamp(timestamp_str):
    """Formata timestamp para exibição."""
    if not timestamp_str:
        return "N/A"
    
    try:
        # Tenta diferentes formatos
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
            try:
                dt = datetime.strptime(str(timestamp_str), fmt)
                return dt.strftime('%d/%m/%Y às %H:%M:%S')
            except ValueError:
                continue
        return str(timestamp_str)
    except Exception:
        return str(timestamp_str)


def _status_icon(status: str) -> str:
    """Retorna ícone baseado no status."""
    status_lower = (status or "").lower()
    icons = {
        "sucesso": "✅",
        "success": "✅",
        "erro": "❌",
        "error": "❌",
        "warning": "⚠️",
        "aviso": "⚠️",
        "info": "ℹ️",
        "pendente": "⏳",
        "pending": "⏳"
    }
    return icons.get(status_lower, "📝")


def _tipo_icon(tipo: str) -> str:
    """Retorna ícone baseado no tipo de log."""
    tipo_lower = (tipo or "").lower()
    icons = {
        "sync": "🔄",
        "mensagem": "💬",
        "whatsapp": "📱",
        "senha": "🔑",
        "erro": "❌",
        "acesso": "🔐",
        "sistema": "⚙️",
        "scheduler": "📆"
    }
    return icons.get(tipo_lower, "📋")


def _escape_html(text: str) -> str:
    """Escapa caracteres HTML para exibição segura."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;")


def _ler_arquivo_log(caminho: str, linhas: int = 100) -> list:
    """Lê últimas N linhas de um arquivo de log."""
    try:
        if not os.path.exists(caminho):
            return []
        
        with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
            todas_linhas = f.readlines()
            return todas_linhas[-linhas:] if len(todas_linhas) > linhas else todas_linhas
    except Exception as e:
        return [f"Erro ao ler arquivo: {str(e)}"]


def render():
    """Renderiza a página de logs."""
    st.header("📋 Central de Logs")
    
    db = get_database()
    
    # Tabs para diferentes tipos de logs
    tab_atividades, tab_sync, tab_mensagens, tab_arquivo = st.tabs([
        "📊 Atividades Gerais", 
        "🔄 Sincronizações", 
        "💬 Mensagens", 
        "📁 Arquivo de Log"
    ])
    
    # ==================== ABA: ATIVIDADES GERAIS ====================
    with tab_atividades:
        st.subheader("📊 Log de Atividades do Sistema")
        
        # Filtros
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            filtro_tipo = st.selectbox(
                "Tipo:",
                ["Todos", "sync", "mensagem", "senha", "erro", "acesso", "sistema"],
                key="filtro_tipo_log"
            )
        
        with col2:
            filtro_status = st.selectbox(
                "Status:",
                ["Todos", "sucesso", "erro", "warning", "info"],
                key="filtro_status_log"
            )
        
        with col3:
            limite = st.number_input("Limite:", 10, 500, 100, key="limite_logs")
        
        with col4:
            if st.button("🔄 Atualizar", key="btn_atualizar_logs"):
                st.rerun()
        
        # Busca logs com filtros
        tipo_filter = None if filtro_tipo == "Todos" else filtro_tipo
        status_filter = None if filtro_status == "Todos" else filtro_status
        
        logs = db.buscar_logs(limite=limite, tipo=tipo_filter, status=status_filter)
        
        if logs:
            st.info(f"📊 Exibindo {len(logs)} registros")
            
            for log in logs:
                tipo_ico = _tipo_icon(log.get('tipo', ''))
                status_ico = _status_icon(log.get('status', ''))
                timestamp = _formatar_timestamp(log.get('created_at'))
                
                # Cor de fundo baseada no status
                status_lower = (log.get('status') or '').lower()
                if status_lower in ['erro', 'error']:
                    bg_color = "#ffebee"
                    border_color = "#f44336"
                elif status_lower in ['sucesso', 'success']:
                    bg_color = "#e8f5e9"
                    border_color = "#4caf50"
                elif status_lower in ['warning', 'aviso']:
                    bg_color = "#fff3e0"
                    border_color = "#ff9800"
                else:
                    bg_color = "#e3f2fd"
                    border_color = "#2196f3"
                
                # Removemos toda a indentação do HTML para evitar que o Markdown interprete como código
                with st.container():
                    html_content = f"""
<div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; border-left: 4px solid {border_color}; margin-bottom: 10px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="font-weight: bold;">{tipo_ico} {log.get('categoria', 'Sistema')} {status_ico}</span>
<span style="font-size: 0.8rem; color: #666;">🕐 {timestamp}</span>
</div>
<div style="margin-top: 5px;">{_escape_html(log.get('mensagem', 'Sem mensagem'))}</div>
{f'<div style="margin-top: 5px; font-size: 0.85rem; color: #555;"><b>Detalhes:</b> {_escape_html(log.get("detalhes", ""))}</div>' if log.get('detalhes') else ''}
<div style="margin-top: 5px; font-size: 0.75rem; color: #888;">Origem: {_escape_html(log.get('origem', 'sistema'))} | ID: {log.get('id')}</div>
</div>
"""
                    st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.info("📭 Nenhum log encontrado com os filtros selecionados.")
            st.caption("Os logs serão registrados conforme o sistema for utilizado.")
        
        # Botão para limpar logs antigos
        st.divider()
        col_limpar1, col_limpar2 = st.columns([3, 1])
        with col_limpar2:
            dias_limpar = st.number_input("Dias para manter:", 7, 365, 30, key="dias_limpar")
        with col_limpar1:
            if st.button("🗑️ Limpar Logs Antigos", key="btn_limpar_logs"):
                db.limpar_logs_antigos(dias=dias_limpar)
                st.success(f"✅ Logs com mais de {dias_limpar} dias removidos!")
                st.rerun()
    
    # ==================== ABA: SINCRONIZAÇÕES ====================
    with tab_sync:
        st.subheader("🔄 Histórico de Sincronizações")
        
        col_sync1, col_sync2 = st.columns([3, 1])
        with col_sync2:
            limite_sync = st.number_input("Exibir:", 10, 100, 50, key="limite_sync")
        
        sync_logs = db.buscar_sync_logs(limite=limite_sync)
        
        if sync_logs:
            # Estatísticas rápidas
            total = len(sync_logs)
            sucessos = len([s for s in sync_logs if (s.get('status') or '').lower() == 'sucesso'])
            erros = total - sucessos
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            col_stat1.metric("Total de Syncs", total)
            col_stat2.metric("✅ Sucesso", sucessos)
            col_stat3.metric("❌ Erros", erros)
            
            st.divider()
            
            for sync in sync_logs:
                status_ico = _status_icon(sync.get('status', ''))
                timestamp = _formatar_timestamp(sync.get('sync_at'))
                
                # Cor baseada no status
                status_lower = (sync.get('status') or '').lower()
                if status_lower in ['erro', 'error']:
                    bg_color = "#ffebee"
                    border_color = "#f44336"
                else:
                    bg_color = "#e8f5e9"
                    border_color = "#4caf50"
                
                with st.container():
                    html_content = f"""
<div style="background-color: {bg_color}; padding: 15px; border-radius: 8px; border-left: 4px solid {border_color}; margin-bottom: 10px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="font-weight: bold; font-size: 1.1rem;">🔄 Sincronização {status_ico}</span>
<span style="font-size: 0.85rem; color: #666;">🕐 {timestamp}</span>
</div>
<div style="margin-top: 10px; display: flex; gap: 20px;">
<span>📊 <b>Registros:</b> {sync.get('total_registros', 0)}</span>
<span>📑 <b>Abas:</b> {sync.get('total_abas', 0)}</span>
</div>
<div style="margin-top: 8px;">💬 {_escape_html(sync.get('mensagem', 'Sem mensagem'))}</div>
{f'<div style="margin-top: 5px; font-size: 0.8rem; color: #666;">Hash: {_escape_html(sync.get("arquivo_hash", "")[:20])}...</div>' if sync.get('arquivo_hash') else ''}
</div>
"""
                    st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.info("📭 Nenhuma sincronização registrada ainda.")
    
    # ==================== ABA: MENSAGENS ====================
    with tab_mensagens:
        st.subheader("💬 Log de Mensagens WhatsApp")
        
        # Busca logs específicos de mensagens
        mensagem_logs = db.buscar_logs(limite=100, tipo="mensagem")
        
        if mensagem_logs:
            # Estatísticas
            total_msg = len(mensagem_logs)
            enviadas = len([m for m in mensagem_logs if (m.get('status') or '').lower() == 'sucesso'])
            falhas = total_msg - enviadas
            
            col_msg1, col_msg2, col_msg3 = st.columns(3)
            col_msg1.metric("Total de Mensagens", total_msg)
            col_msg2.metric("✅ Enviadas", enviadas)
            col_msg3.metric("❌ Falhas", falhas)
            
            st.divider()
            
            for msg in mensagem_logs:
                status_ico = _status_icon(msg.get('status', ''))
                timestamp = _formatar_timestamp(msg.get('created_at'))
                
                status_lower = (msg.get('status') or '').lower()
                if status_lower in ['erro', 'error']:
                    bg_color = "#ffebee"
                    border_color = "#f44336"
                else:
                    bg_color = "#e8f5e9"
                    border_color = "#4caf50"
                
                with st.container():
                    html_content = f"""
<div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; border-left: 4px solid {border_color}; margin-bottom: 8px;">
<div style="display: flex; justify-content: space-between;">
<span style="font-weight: bold;">📱 WhatsApp {status_ico}</span>
<span style="font-size: 0.8rem; color: #666;">🕐 {timestamp}</span>
</div>
<div style="margin-top: 5px;">{_escape_html(msg.get('mensagem', 'Sem descrição'))}</div>
{f'<div style="margin-top: 5px; font-size: 0.85rem; color: #555;">{_escape_html(msg.get("detalhes", ""))}</div>' if msg.get('detalhes') else ''}
</div>
"""
                    st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.info("📭 Nenhuma mensagem registrada ainda.")
            st.caption("As mensagens enviadas pelo WhatsApp serão registradas aqui.")
    
    # ==================== ABA: ARQUIVO DE LOG ====================
    with tab_arquivo:
        st.subheader("📁 Arquivo de Log do Scheduler")
        
        # Caminhos dos arquivos de log
        log_paths = [
            str(ROOT_DIR / "logs" / "scheduler.log"),
            str(ROOT_DIR / "scheduler.log")
        ]
        
        col_arq1, col_arq2, col_arq3 = st.columns([2, 1, 1])
        
        with col_arq1:
            arquivo_selecionado = st.selectbox(
                "Arquivo:",
                log_paths,
                format_func=lambda x: os.path.basename(x),
                key="arquivo_log_selecionado"
            )
        
        with col_arq2:
            linhas_exibir = st.number_input("Últimas linhas:", 50, 500, 100, key="linhas_log")
        
        with col_arq3:
            auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, key="auto_refresh_log",
                                       help="Atualiza automaticamente a cada 5 segundos")
        
        # Botão de atualização manual
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🔄 Atualizar Agora", key="btn_atualizar_arquivo", use_container_width=True):
                st.rerun()
        
        # Container para o conteúdo do log (permite atualização dinâmica)
        log_container = st.empty()
        
        # Lê e exibe o arquivo
        linhas = _ler_arquivo_log(arquivo_selecionado, linhas_exibir)
        
        # Obtém timestamp de modificação do arquivo
        ultima_modificacao = None
        timestamp_atual = None
        if os.path.exists(arquivo_selecionado):
            try:
                ultima_modificacao = os.path.getmtime(arquivo_selecionado)
                timestamp_atual = ultima_modificacao
                ultima_modificacao_str = datetime.fromtimestamp(ultima_modificacao).strftime('%d/%m/%Y %H:%M:%S')
            except:
                ultima_modificacao_str = "N/A"
                timestamp_atual = None
        else:
            ultima_modificacao_str = "Arquivo não existe"
            timestamp_atual = None
        
        # Função para renderizar o conteúdo do log
        def _renderizar_log(linhas, arquivo_selecionado, ultima_modificacao_str):
            """Renderiza o conteúdo do log no container."""
            if linhas:
                # Info sobre o arquivo
                with log_container.container():
                    st.info(f"📄 Exibindo últimas {len(linhas)} linhas de `{os.path.basename(arquivo_selecionado)}` | 🕐 Última modificação: {ultima_modificacao_str}")
                    
                    # Exibe em um text_area com destaque
                    conteudo = "".join(linhas)
                    
                    # Container com scroll
                    st.markdown("""
<style>
.log-container {
background-color: #1e1e1e;
color: #d4d4d4;
font-family: 'Consolas', 'Monaco', monospace;
font-size: 0.85rem;
padding: 15px;
border-radius: 8px;
max-height: 500px;
overflow-y: auto;
white-space: pre-wrap;
word-wrap: break-word;
}
.log-error { color: #f44336; }
.log-success { color: #4caf50; }
.log-warning { color: #ff9800; }
.log-info { color: #2196f3; }
</style>
""", unsafe_allow_html=True)
                    
                    # Processa linhas para colorir
                    linhas_formatadas = []
                    for linha in linhas:
                        linha_html = linha.replace('<', '&lt;').replace('>', '&gt;')
                        if '❌' in linha or 'erro' in linha.lower() or 'error' in linha.lower():
                            linhas_formatadas.append(f'<span class="log-error">{linha_html}</span>')
                        elif '✅' in linha or 'sucesso' in linha.lower() or 'success' in linha.lower():
                            linhas_formatadas.append(f'<span class="log-success">{linha_html}</span>')
                        elif '⚠️' in linha or 'warning' in linha.lower() or 'aviso' in linha.lower():
                            linhas_formatadas.append(f'<span class="log-warning">{linha_html}</span>')
                        elif 'ℹ️' in linha or 'info' in linha.lower():
                            linhas_formatadas.append(f'<span class="log-info">{linha_html}</span>')
                        else:
                            linhas_formatadas.append(linha_html)
                    
                    conteudo_formatado = "".join(linhas_formatadas)
                    st.markdown(f'<div class="log-container">{conteudo_formatado}</div>', unsafe_allow_html=True)
                    
                    # Botão para download
                    st.download_button(
                        label="📥 Download Log Completo",
                        data=conteudo,
                        file_name=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            else:
                with log_container.container():
                    st.warning(f"⚠️ Arquivo de log não encontrado ou vazio: `{arquivo_selecionado}`")
        
        # Renderiza o log inicialmente
        _renderizar_log(linhas, arquivo_selecionado, ultima_modificacao_str)
        
        # Auto-refresh se habilitado
        if auto_refresh:
            # Inicializa variáveis de controle no session_state
            if 'log_last_timestamp' not in st.session_state:
                st.session_state['log_last_timestamp'] = timestamp_atual if timestamp_atual else 0
                st.session_state['log_last_check'] = datetime.now()
            
            # Verifica se passou tempo suficiente desde a última verificação (8 segundos)
            ultima_verificacao = st.session_state.get('log_last_check')
            if ultima_verificacao:
                tempo_decorrido = (datetime.now() - ultima_verificacao).total_seconds()
                
                # Se passou 8 segundos, verifica se o arquivo mudou
                if tempo_decorrido >= 8:
                    st.session_state['log_last_check'] = datetime.now()
                    
                    # Obtém timestamp atual do arquivo para comparação
                    timestamp_atual_verificacao = timestamp_atual
                    if os.path.exists(arquivo_selecionado):
                        try:
                            timestamp_atual_verificacao = os.path.getmtime(arquivo_selecionado)
                        except:
                            timestamp_atual_verificacao = timestamp_atual
                    
                    # Se o arquivo mudou OU se é a primeira verificação, recarrega
                    timestamp_anterior = st.session_state.get('log_last_timestamp', 0)
                    if timestamp_atual_verificacao and timestamp_atual_verificacao != timestamp_anterior:
                        st.session_state['log_last_timestamp'] = timestamp_atual_verificacao
                        st.rerun()
                    elif timestamp_atual_verificacao:
                        # Atualiza timestamp mesmo se não mudou (para próxima comparação)
                        st.session_state['log_last_timestamp'] = timestamp_atual_verificacao
            
            # Mostra indicador de auto-refresh com última atualização
            ultima_atualizacao = st.session_state.get('log_last_check', datetime.now())
            tempo_desde_atualizacao = (datetime.now() - ultima_atualizacao).total_seconds()
            st.caption(f"🔄 Auto-refresh ativo | Última verificação: {int(tempo_desde_atualizacao)}s atrás")
    
    # Rodapé com informações
    st.divider()
    st.caption("💡 **Dica:** Os logs são gerados automaticamente pelo sistema durante sincronizações, envio de mensagens e outras operações.")