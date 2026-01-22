"""
Página de Configurações do Sistema.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import subprocess
import os
import signal
import time
import traceback

from config.settings import settings
from core.config_manager import ConfigManager
from core.validar_planilha import validar_url_google_sheets, testar_planilha_completa
from core.sync_manager import SyncManager
from integrations.evolution_api import MensagensAutomaticas, EvolutionAPI
from integrations.onetimesecret import OneTimeSecretAPI
from integrations.kanbanize import KanbanizeAPI


def render(database):
    """Renderiza a página de configurações."""
    st.header("⚙️ Configurações do Sistema")
    
    # Mostra mensagem de sucesso/erro se existir no session_state
    if 'config_saved' in st.session_state:
        if st.session_state['config_saved']:
            message = st.session_state.get('config_message', 'Configurações salvas com sucesso!')
            st.success(f"✅ **{message}**")
            
            # Só mostra aviso de reinício manual se não estiver em Docker
            em_docker = Path("/.dockerenv").exists()
            if not em_docker:
                st.info("⚠️ **Importante:** Para aplicar as mudanças na sincronização automática, reinicie o scheduler (`./scripts/scheduler.sh` ou `python -m scheduler.jobs`)")
        else:
            error_msg = st.session_state.get('config_error', 'Erro desconhecido ao salvar')
            st.error(f"❌ **Erro ao salvar configurações: {error_msg}**")
            st.warning("💡 Verifique se você tem permissão para escrever no arquivo `.env` ou se há algum problema com o arquivo.")
        
        # Limpa o estado após mostrar
        if 'config_saved' in st.session_state:
            del st.session_state['config_saved']
        if 'config_error' in st.session_state:
            del st.session_state['config_error']
        if 'config_message' in st.session_state:
            del st.session_state['config_message']
    
    config_manager = ConfigManager()
    config_atual = config_manager.ler_config()
    
    # Inicializa variáveis com valores padrão (sempre disponíveis)
    evolution_numero_default = config_atual.get("EVOLUTION_NUMERO", "120363020985287866@g.us")
    evolution_numero_sync_default = "120363423378738083@g.us"  # Padrão para mensagens de sincronização
    evolution_url = config_atual.get("EVOLUTION_API_URL", "http://10.0.153.28:8081/message/sendText/zabbix")
    evolution_api_key = config_atual.get("EVOLUTION_API_KEY", "")
    evolution_numero = evolution_numero_default
    kanbanize_default_board_id = config_atual.get("KANBANIZE_DEFAULT_BOARD_ID", "0")
    kanbanize_base_url = config_atual.get("KANBANIZE_BASE_URL", "https://fmimpressosltda.kanbanize.com")
    kanbanize_api_key = config_atual.get("KANBANIZE_API_KEY", "")
    
    st.info("💡 As configurações são salvas no arquivo `.env`. Após alterar, reinicie o scheduler se estiver rodando.")
    
    st.divider()
    
    # ==================== SINCRONIZAÇÃO ====================
    st.subheader("🔄 Sincronização Automática")
    
    st.caption("ℹ️ A sincronização roda **uma vez por dia** no horário configurado. O sistema verifica se a planilha mudou (via hash MD5) antes de processar.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sync_hour = st.number_input(
            "Hora da sincronização (0-23):",
            min_value=0,
            max_value=23,
            value=int(config_atual.get("SYNC_HOUR", settings.SYNC_HOUR)),
            key="sync_hour",
            help="Horário em que a sincronização diária será executada"
        )
    
    with col2:
        sync_minute = st.number_input(
            "Minuto da sincronização (0-59):",
            min_value=0,
            max_value=59,
            value=int(config_atual.get("SYNC_MINUTE", settings.SYNC_MINUTE)),
            key="sync_minute"
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        sync_enabled = st.checkbox(
            "Habilitar sincronização automática",
            value=config_atual.get("SYNC_ENABLED", "true").lower() == "true",
            key="sync_enabled",
            help="Se desabilitado, a sincronização automática não será executada"
        )
    
    with col4:
        cache_minutes = st.number_input(
            "Tempo de cache (minutos):",
            min_value=1,
            max_value=1440,
            value=int(config_atual.get("CACHE_MINUTES", settings.CACHE_MINUTES)),
            help="Tempo mínimo entre downloads (evita baixar muito frequentemente)"
        )
    
    st.info(f"⏰ **Sincronização configurada para:** {sync_hour:02d}:{sync_minute:02d} {'(Habilitada)' if sync_enabled else '(Desabilitada)'}")
    
    # Sincronização com Notificação (13:00)
    st.subheader("🔔 Sincronização com Notificação (13:00)")
    
    st.caption("ℹ️ Executa uma sincronização adicional às 13:00 e envia um relatório via WhatsApp para um número alternativo.")
    
    sync_notif_enabled = st.checkbox(
        "Habilitar sincronização com notificação (13:00)",
        value=config_atual.get("SYNC_NOTIF_ENABLED", "false").lower() == "true",
        key="sync_notif_enabled",
        help="Executa sincronização às 13:00 e envia resultado via WhatsApp"
    )
    
    if sync_notif_enabled:
        col1, col2 = st.columns(2)
        
        with col1:
            sync_notif_hour = st.number_input(
                "Hora da sincronização com notificação (0-23):",
                min_value=0,
                max_value=23,
                value=int(config_atual.get("SYNC_NOTIF_HOUR", settings.SYNC_NOTIF_HOUR)),
                key="sync_notif_hour"
            )
        
        with col2:
            sync_notif_minute = st.number_input(
                "Minuto da sincronização com notificação (0-59):",
                min_value=0,
                max_value=59,
                value=int(config_atual.get("SYNC_NOTIF_MINUTE", settings.SYNC_NOTIF_MINUTE)),
                key="sync_notif_minute"
            )
        
        evolution_numero_sync = st.text_input(
            "Número/Grupo WhatsApp para notificações:",
            value=config_atual.get("EVOLUTION_NUMERO_SYNC", evolution_numero_sync_default),
            help="Número ou grupo padrão para mensagens de sincronização. Exemplos: 120363423378738083@g.us ou 11954175296",
            key="evolution_numero_sync"
        )
        
        if st.button("🚀 Executar Sincronização com Notificação Agora", key="executar_sync_notif_agora", type="secondary"):
            with st.spinner("Executando sincronização com notificação..."):
                try:
                    sync = SyncManager()
                    resultado_sync = sync.sincronizar()
                    
                    # Envia notificação
                    api = EvolutionAPI(
                        url=evolution_url,
                        numero=evolution_numero_sync or evolution_numero,
                        api_key=evolution_api_key
                    )
                    resultado_notif = api.enviar_mensagem_sync(resultado_sync)
                    
                    # Mostra resultados
                    if resultado_sync["status"] == "success":
                        st.success(f"✅ Sincronização: {resultado_sync['registros']} registros")
                    elif resultado_sync["status"] == "skipped":
                        st.info(f"⏭️ Sincronização: {resultado_sync['message']}")
                    else:
                        st.error(f"❌ Sincronização: {resultado_sync['message']}")
                    
                    if resultado_notif["sucesso"]:
                        st.success(f"📱 Notificação enviada para: {api.numero}")
                    else:
                        st.warning(f"⚠️ Falha ao notificar: {resultado_notif['mensagem']}")
                    
                    database.registrar_log(
                        tipo="sincronizacao",
                        categoria="Notificação",
                        status="sucesso",
                        mensagem="Sincronização + Notificação executadas manualmente",
                        detalhes=f"Sync: {resultado_sync.get('status')}; Notif: {'enviada' if resultado_notif['sucesso'] else 'falhou'}",
                        origem="configuracoes"
                    )
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
                    st.code(traceback.format_exc())
                    database.registrar_log(
                        tipo="sincronizacao",
                        categoria="Notificação",
                        status="erro",
                        mensagem="Erro ao executar sincronização + notificação",
                        detalhes=str(e),
                        origem="configuracoes"
                    )
        
        st.info(f"⏰ **Sincronização com notificação configurada para:** {sync_notif_hour:02d}:{sync_notif_minute:02d} (Habilitada)")
    else:
        sync_notif_hour = int(config_atual.get("SYNC_NOTIF_HOUR", settings.SYNC_NOTIF_HOUR))
        sync_notif_minute = int(config_atual.get("SYNC_NOTIF_MINUTE", settings.SYNC_NOTIF_MINUTE))
        evolution_numero_sync = config_atual.get("EVOLUTION_NUMERO_SYNC", evolution_numero_sync_default)
    
    # Sincronização Kanbanize
    st.subheader("🗂️ Sincronização Kanbanize")
    
    st.caption("ℹ️ Sincroniza automaticamente os cards do Kanbanize para o banco de dados em horários pré-definidos.")
    
    kanbanize_sync_enabled = st.checkbox(
        "Habilitar sincronização automática do Kanbanize",
        value=config_atual.get("KANBANIZE_SYNC_ENABLED", "false").lower() == "true",
        key="kanbanize_sync_enabled",
        help="Ativa os schedulers de sincronização do Kanbanize"
    )
    
    if kanbanize_sync_enabled:
        col1, col2 = st.columns(2)
        
        with col1:
            kanbanize_sync_09h30_enabled = st.checkbox(
                "Sincronizar às 09:30",
                value=config_atual.get("KANBANIZE_SYNC_09H30_ENABLED", "false").lower() == "true",
                key="kanbanize_sync_09h30_enabled",
                help="Sincroniza cards e envia notificação"
            )
        
        with col2:
            kanbanize_sync_18h00_enabled = st.checkbox(
                "Sincronizar às 18:00",
                value=config_atual.get("KANBANIZE_SYNC_18H00_ENABLED", "false").lower() == "true",
                key="kanbanize_sync_18h00_enabled",
                help="Sincroniza cards e envia notificação"
            )
        
        st.info(f"📋 **Board configurado:** ID {kanbanize_default_board_id}")
        st.caption("💡 As notificações serão enviadas para o número de sincronização (padrão: 120363423378738083@g.us)")
        
        if st.button("🚀 Sincronizar Agora", key="kanbanize_sync_manual", type="secondary"):
            with st.spinner("Sincronizando Kanbanize..."):
                try:
                    from core.database import Database
                    
                    api_kanbanize = KanbanizeAPI(kanbanize_base_url, kanbanize_api_key)
                    resultado = api_kanbanize.buscar_cards_completos_paralelo(
                        board_ids=[int(kanbanize_default_board_id)],
                        sem_detalhes=False  # Garante que os campos personalizados sejam buscados
                    )
                    
                    if resultado.get("sucesso"):
                        cards = resultado.get("dados", [])
                        db = Database()
                        cards_salvos = db.salvar_cards_kanbanize(cards, board_id=int(kanbanize_default_board_id))
                        
                        st.success(f"✅ {cards_salvos} cards sincronizados com sucesso!")
                        # Envia notificação via Evolution (mesmo comportamento dos jobs)
                        try:
                            if settings.EVOLUTION_ENABLED and (evolution_numero_sync or evolution_numero):
                                api_evolution = EvolutionAPI(
                                    url=evolution_url,
                                    numero=(evolution_numero_sync or evolution_numero),
                                    api_key=evolution_api_key
                                )
                                mensagem = f"✅ Kanbanize sincronizado (manual): {cards_salvos} cards atualizados"
                                resultado_msg = api_evolution.enviar_mensagem(mensagem)
                                if resultado_msg.get("sucesso"):
                                    st.success(f"📱 Notificação enviada para {api_evolution.numero}")
                                else:
                                    st.warning(f"⚠️ Falha ao notificar: {resultado_msg.get('mensagem')}")
                        except Exception as e:
                            st.warning(f"⚠️ Erro ao enviar notificação: {e}")

                        database.registrar_log(
                            tipo="kanbanize",
                            categoria="Sincronização",
                            status="sucesso",
                            mensagem=f"Sincronização manual: {cards_salvos} cards",
                            detalhes=f"Board ID: {kanbanize_default_board_id}",
                            origem="configuracoes"
                        )
                    else:
                        st.error(f"❌ Erro: {resultado.get('mensagem')}")
                        database.registrar_log(
                            tipo="kanbanize",
                            categoria="Sincronização",
                            status="erro",
                            mensagem="Erro na sincronização manual",
                            detalhes=resultado.get('mensagem', 'Erro desconhecido'),
                            origem="configuracoes"
                        )
                        # Tenta notificar falha
                        try:
                            if settings.EVOLUTION_ENABLED and (evolution_numero_sync or evolution_numero):
                                api_evolution = EvolutionAPI(
                                    url=evolution_url,
                                    numero=(evolution_numero_sync or evolution_numero),
                                    api_key=evolution_api_key
                                )
                                mensagem = f"❌ Falha na sincronização Kanbanize (manual): {resultado.get('mensagem', 'Erro desconhecido')}"
                                api_evolution.enviar_mensagem(mensagem)
                        except Exception:
                            pass
                except Exception as e:
                    st.error(f"❌ Erro ao sincronizar: {e}")
                    database.registrar_log(
                        tipo="kanbanize",
                        categoria="Sincronização",
                        status="erro",
                        mensagem="Erro ao sincronizar Kanbanize",
                        detalhes=str(e),
                        origem="configuracoes"
                    )
                    # Notifica erro
                    try:
                        if settings.EVOLUTION_ENABLED and (evolution_numero_sync or evolution_numero):
                            api_evolution = EvolutionAPI(
                                url=evolution_url,
                                numero=(evolution_numero_sync or evolution_numero),
                                api_key=evolution_api_key
                            )
                            mensagem = f"❌ Erro ao sincronizar Kanbanize (manual): {str(e)}"
                            api_evolution.enviar_mensagem(mensagem)
                    except Exception:
                        pass
    else:
        kanbanize_sync_09h30_enabled = config_atual.get("KANBANIZE_SYNC_09H30_ENABLED", "false").lower() == "true"
        kanbanize_sync_18h00_enabled = config_atual.get("KANBANIZE_SYNC_18H00_ENABLED", "false").lower() == "true"
    
    # Atualiza config_atual
    config_atual["KANBANIZE_SYNC_ENABLED"] = "true" if kanbanize_sync_enabled else "false"
    config_atual["KANBANIZE_SYNC_09H30_ENABLED"] = "true" if kanbanize_sync_09h30_enabled else "false"
    config_atual["KANBANIZE_SYNC_18H00_ENABLED"] = "true" if kanbanize_sync_18h00_enabled else "false"
    
    st.divider()
    
    # ==================== GOOGLE SHEETS ====================
    st.subheader("📊 Google Sheets")
    
    st.caption("ℹ️ A planilha precisa ser **pública** (qualquer um com o link pode ver). Use o botão abaixo para testar se o link está funcionando.")
    
    google_url = st.text_input(
        "URL da planilha do Google Sheets:",
        value=config_atual.get("GOOGLE_SHEETS_URL", settings.GOOGLE_SHEETS_URL),
        help="URL pública da planilha do Google Sheets",
        key="google_url"
    )
    
    # Botões de teste
    col1, col2 = st.columns([1, 3])
    
    with col1:
        testar_link = st.button("🔍 Testar Link", type="secondary", width='stretch')
    
    with col2:
        testar_completo = st.button("🧪 Teste Completo (Download + Processamento)", type="secondary", width='stretch')
    
    # Resultado do teste
    if testar_link:
        with st.spinner("Validando link..."):
            valido, mensagem, sheet_id = validar_url_google_sheets(google_url)
            
            if valido:
                st.success(mensagem)
                st.caption(f"📋 Sheet ID: `{sheet_id}`")
            else:
                st.error(mensagem)
    
    if testar_completo:
        with st.spinner("Testando download e processamento completo... Isso pode levar alguns segundos."):
            resultado = testar_planilha_completa(google_url)
            
            if resultado["sucesso"]:
                st.success(resultado["mensagem"])
                
                # Detalhes
                detalhes = resultado.get("detalhes", {})
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Funcionários", detalhes.get("total_funcionarios", 0))
                with col2:
                    st.metric("Abas", detalhes.get("total_abas", 0))
                with col3:
                    st.metric("Sheet ID", detalhes.get("sheet_id", "N/A"))
                
                # Lista de abas
                abas = detalhes.get("abas", [])
                if abas:
                    st.caption(f"📑 Abas encontradas: {', '.join(abas)}{'...' if len(abas) == 10 else ''}")
                
            else:
                st.error(resultado["mensagem"])
                if resultado.get("detalhes"):
                    st.json(resultado["detalhes"])
    
    st.divider()
    
    # ==================== EVOLUTION API ====================
    st.subheader("📱 Evolution API (WhatsApp)")
    
    evolution_enabled = st.checkbox(
        "Habilitar Evolution API",
        value=config_atual.get("EVOLUTION_ENABLED", "false").lower() == "true",
        key="evolution_enabled",
        help="Integração com WhatsApp via Evolution API"
    )
    
    # Inicializa variáveis de mensagens (se não inicializadas)
    if 'mensagem_manha_enabled' not in locals():
        mensagem_manha_enabled = config_atual.get("MENSAGEM_MANHA_ENABLED", "false").lower() == "true"
        manha_hour = int(config_atual.get("MENSAGEM_MANHA_HOUR", "8"))
        manha_minute = int(config_atual.get("MENSAGEM_MANHA_MINUTE", "0"))
        mensagem_tarde_enabled = config_atual.get("MENSAGEM_TARDE_ENABLED", "false").lower() == "true"
        tarde_hour = int(config_atual.get("MENSAGEM_TARDE_HOUR", "17"))
        tarde_minute = int(config_atual.get("MENSAGEM_TARDE_MINUTE", "0"))
    
    if evolution_enabled:
        evolution_url = st.text_input(
            "URL Completa do Endpoint:",
            value=evolution_url,
            help="URL completa do endpoint (ex: http://10.0.153.28:8081/message/sendText/zabbix)",
            key="evolution_url"
        )
        
        evolution_numero = st.text_input(
            "Número/Grupo do WhatsApp:",
            value=evolution_numero,
            help="Número ou ID do grupo (ex: 120363020985287866@g.us ou 11954175296)",
            key="evolution_numero"
        )
        
        evolution_api_key = st.text_input(
            "API Key:",
            value=evolution_api_key,
            help="Chave da API (opcional, se sua Evolution API exigir autenticação)",
            type="password",
            key="evolution_api_key"
        )
        
        st.divider()
        
        # ==================== MENSAGENS AUTOMÁTICAS ====================
        st.markdown("#### 📨 Mensagens Automáticas")
        
        # Mensagem da Manhã
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                mensagem_manha_enabled = st.checkbox(
                    "🌅 **Mensagem Matutina**",
                    value=mensagem_manha_enabled,
                    key="mensagem_manha_enabled",
                    help="Conteúdo: Quem sai hoje + Quem voltaria hoje mas ainda está bloqueado"
                )
            with col2:
                if mensagem_manha_enabled:
                    st.caption(f"⏰ {manha_hour:02d}:{manha_minute:02d}")
            
            if mensagem_manha_enabled:
                col1, col2, col3, col4 = st.columns([1, 1, 1.5, 1.5])
                with col1:
                    st.caption("Hora:")
                    manha_hour = st.number_input(
                        "Hora:",
                        min_value=0,
                        max_value=23,
                        value=manha_hour,
                        key="manha_hour",
                        label_visibility="collapsed"
                    )
                with col2:
                    st.caption("Minuto:")
                    manha_minute = st.number_input(
                        "Minuto:",
                        min_value=0,
                        max_value=59,
                        value=manha_minute,
                        key="manha_minute",
                        label_visibility="collapsed"
                    )
                with col3:
                    # Controla estado do preview
                    if 'preview_manha_aberto' not in st.session_state:
                        st.session_state['preview_manha_aberto'] = False
                    
                    if st.button("👁️ Preview" if not st.session_state['preview_manha_aberto'] else "👁️ Fechar Preview", 
                                key="preview_manha", width='stretch'):
                        st.session_state['preview_manha_aberto'] = not st.session_state['preview_manha_aberto']
                        st.rerun()
                    
                    # Mostra preview se estiver aberto
                    if st.session_state.get('preview_manha_aberto', False):
                        with st.spinner("Gerando preview..."):
                            api = EvolutionAPI(url=evolution_url, numero=evolution_numero, api_key=evolution_api_key)
                            mensagens = MensagensAutomaticas(api)
                            preview = mensagens.gerar_mensagem_manha()
                            st.code(preview, language=None)
                with col4:
                    if st.button("🚀 Enviar Agora", key="enviar_manha_agora", width='stretch'):
                        with st.spinner("Enviando..."):
                            api = EvolutionAPI(url=evolution_url, numero=evolution_numero, api_key=evolution_api_key)
                            mensagens = MensagensAutomaticas(api)
                            resultado = mensagens.enviar_mensagem_manha()
                            
                            if resultado["sucesso"]:
                                st.success("✅ Enviada!")
                                database.registrar_log(
                                    tipo="mensagem",
                                    categoria="WhatsApp",
                                    status="sucesso",
                                    mensagem="Mensagem matutina enviada manualmente",
                                    origem="configuracoes"
                                )
                            else:
                                st.error(f"❌ {resultado['mensagem']}")
                                database.registrar_log(
                                    tipo="mensagem",
                                    categoria="WhatsApp",
                                    status="erro",
                                    mensagem=f"Falha ao enviar mensagem matutina",
                                    detalhes=resultado.get('mensagem', ''),
                                    origem="configuracoes"
                                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Mensagem da Tarde
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                mensagem_tarde_enabled = st.checkbox(
                    "🌆 **Mensagem Vespertina**",
                    value=mensagem_tarde_enabled,
                    key="mensagem_tarde_enabled",
                    help="Conteúdo: Quem volta amanhã + Quem está de férias com acessos NB (pendentes)"
                )
            with col2:
                if mensagem_tarde_enabled:
                    st.caption(f"⏰ {tarde_hour:02d}:{tarde_minute:02d}")
            
            if mensagem_tarde_enabled:
                col1, col2, col3, col4 = st.columns([1, 1, 1.5, 1.5])
                with col1:
                    st.caption("Hora:")
                    tarde_hour = st.number_input(
                        "Hora:",
                        min_value=0,
                        max_value=23,
                        value=tarde_hour,
                        key="tarde_hour",
                        label_visibility="collapsed"
                    )
                with col2:
                    st.caption("Minuto:")
                    tarde_minute = st.number_input(
                        "Minuto:",
                        min_value=0,
                        max_value=59,
                        value=tarde_minute,
                        key="tarde_minute",
                        label_visibility="collapsed"
                    )
                with col3:
                    # Controla estado do preview
                    if 'preview_tarde_aberto' not in st.session_state:
                        st.session_state['preview_tarde_aberto'] = False
                    
                    if st.button("👁️ Preview" if not st.session_state['preview_tarde_aberto'] else "👁️ Fechar Preview", 
                                key="preview_tarde", width='stretch'):
                        st.session_state['preview_tarde_aberto'] = not st.session_state['preview_tarde_aberto']
                        st.rerun()
                    
                    # Mostra preview se estiver aberto
                    if st.session_state.get('preview_tarde_aberto', False):
                        with st.spinner("Gerando preview..."):
                            api = EvolutionAPI(url=evolution_url, numero=evolution_numero, api_key=evolution_api_key)
                            mensagens = MensagensAutomaticas(api)
                            preview = mensagens.gerar_mensagem_tarde()
                            st.code(preview, language=None)
                with col4:
                    if st.button("🚀 Enviar Agora", key="enviar_tarde_agora", width='stretch'):
                        with st.spinner("Enviando..."):
                            api = EvolutionAPI(url=evolution_url, numero=evolution_numero, api_key=evolution_api_key)
                            mensagens = MensagensAutomaticas(api)
                            resultado = mensagens.enviar_mensagem_tarde()
                            
                            if resultado["sucesso"]:
                                st.success("✅ Enviada!")
                                database.registrar_log(
                                    tipo="mensagem",
                                    categoria="WhatsApp",
                                    status="sucesso",
                                    mensagem="Mensagem vespertina enviada manualmente",
                                    origem="configuracoes"
                                )
                            else:
                                st.error(f"❌ {resultado['mensagem']}")
                                database.registrar_log(
                                    tipo="mensagem",
                                    categoria="WhatsApp",
                                    status="erro",
                                    mensagem=f"Falha ao enviar mensagem vespertina",
                                    detalhes=resultado.get('mensagem', ''),
                                    origem="configuracoes"
                                )
        
        st.divider()
        
        # ==================== AÇÕES ====================
        st.markdown("#### 🔧 Ações Rápidas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            testar_evolution = st.button("🧪 Testar Envio", type="secondary", width='stretch', help="Envia mensagem de teste")
            if testar_evolution:
                with st.spinner("Enviando mensagem de teste..."):
                    api = EvolutionAPI(url=evolution_url, numero=evolution_numero, api_key=evolution_api_key)
                    api.enabled = True
                    resultado = api.enviar_mensagem_teste()
                    
                    if resultado["sucesso"]:
                        st.success("✅ Teste enviado com sucesso!")
                        database.registrar_log(
                            tipo="mensagem",
                            categoria="WhatsApp",
                            status="sucesso",
                            mensagem="Mensagem de teste enviada com sucesso",
                            origem="configuracoes"
                        )
                    else:
                        st.error(f"❌ Erro: {resultado['mensagem']}")
                        database.registrar_log(
                            tipo="mensagem",
                            categoria="WhatsApp",
                            status="erro",
                            mensagem="Falha ao enviar mensagem de teste",
                            detalhes=resultado.get('mensagem', ''),
                            origem="configuracoes"
                        )
        
        with col2:
            executar_agora = st.button("▶️ Executar Todos Agora", type="secondary", width='stretch', 
                                      help="Executa todos os jobs agendados imediatamente")
            if executar_agora:
                with st.spinner("Executando jobs agendados..."):
                    try:
                        resultados = []
                        
                        # Sincronização
                        if sync_enabled:
                            try:
                                sync = SyncManager()
                                resultado = sync.sincronizar()
                                if resultado["status"] == "success":
                                    resultados.append(f"✅ Sincronização: {resultado['registros']} registros")
                                elif resultado["status"] == "skipped":
                                    resultados.append(f"⏭️ Sincronização: {resultado['message']}")
                                else:
                                    resultados.append(f"❌ Sincronização: {resultado['message']}")
                            except Exception as e:
                                resultados.append(f"❌ Erro na sincronização: {e}")
                        
                        # Mensagem Matutina
                        if mensagem_manha_enabled:
                            try:
                                api = EvolutionAPI(url=evolution_url, numero=evolution_numero, api_key=evolution_api_key)
                                mensagens = MensagensAutomaticas(api)
                                resultado = mensagens.enviar_mensagem_manha()
                                if resultado["sucesso"]:
                                    resultados.append("✅ Mensagem matutina enviada")
                                else:
                                    resultados.append(f"❌ Mensagem matutina: {resultado['mensagem']}")
                            except Exception as e:
                                resultados.append(f"❌ Erro na mensagem matutina: {e}")
                        
                        # Mensagem Vespertina
                        if mensagem_tarde_enabled:
                            try:
                                api = EvolutionAPI(url=evolution_url, numero=evolution_numero, api_key=evolution_api_key)
                                mensagens = MensagensAutomaticas(api)
                                resultado = mensagens.enviar_mensagem_tarde()
                                if resultado["sucesso"]:
                                    resultados.append("✅ Mensagem vespertina enviada")
                                else:
                                    resultados.append(f"❌ Mensagem vespertina: {resultado['mensagem']}")
                            except Exception as e:
                                resultados.append(f"❌ Erro na mensagem vespertina: {e}")
                        
                        # Mostra resultados e registra log
                        if resultados:
                            # Conta sucessos e erros
                            sucessos = len([r for r in resultados if r.startswith("✅")])
                            erros = len([r for r in resultados if r.startswith("❌")])
                            
                            for resultado in resultados:
                                if resultado.startswith("✅"):
                                    st.success(resultado)
                                elif resultado.startswith("⏭️"):
                                    st.info(resultado)
                                else:
                                    st.error(resultado)
                            
                            # Registra log da execução em lote
                            database.registrar_log(
                                tipo="sistema",
                                categoria="Scheduler",
                                status="sucesso" if erros == 0 else "warning",
                                mensagem=f"Execução manual de jobs: {sucessos} sucesso(s), {erros} erro(s)",
                                detalhes="; ".join(resultados),
                                origem="configuracoes"
                            )
                        else:
                            st.warning("⚠️ Nenhum job habilitado para executar")
                    except Exception as e:
                        st.error(f"❌ Erro ao executar: {e}")
                        st.code(traceback.format_exc())
                        database.registrar_log(
                            tipo="sistema",
                            categoria="Scheduler",
                            status="erro",
                            mensagem=f"Exceção ao executar jobs manualmente",
                            detalhes=str(e),
                            origem="configuracoes"
                        )
        
        with col3:
            reiniciar_scheduler = st.button("🔄 Reiniciar Scheduler", type="secondary", width='stretch',
                                           help="Para e reinicia o scheduler com as novas configurações")
            if reiniciar_scheduler:
                _reiniciar_scheduler(database)
        
        with col4:
            # Toggle para mostrar/esconder status
            if 'mostrar_status_servicos' not in st.session_state:
                st.session_state['mostrar_status_servicos'] = False
            
            # Botão com label dinâmico
            label_botao = "🔍 Verificar Todos Serviços" if not st.session_state['mostrar_status_servicos'] else "❌ Fechar Status"
            tipo_botao = "primary" if not st.session_state['mostrar_status_servicos'] else "secondary"
            
            verificar_status = st.button(label_botao, type=tipo_botao, width='stretch',
                                        help="Verifica o status de todos os serviços do sistema (Scheduler, BD, APIs)")
            
            if verificar_status:
                # Toggle o estado
                st.session_state['mostrar_status_servicos'] = not st.session_state['mostrar_status_servicos']
                st.rerun()
            
            # Mostra a seção de status se estiver ativa
            if st.session_state.get('mostrar_status_servicos', False):
                _verificar_status_servicos(database, config_atual)
        
        # ==================== RESUMO DO AGENDAMENTO ====================
        st.divider()
        with st.container():
            st.markdown("#### 📋 Resumo do Agendamento")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**🔄 Sincronização**")
                if sync_enabled:
                    st.success(f"✅ {sync_hour:02d}:{sync_minute:02d}")
                else:
                    st.error("❌ Desabilitada")
            
            with col2:
                st.markdown("**🔔 Sincronização + Notif**")
                if sync_notif_enabled:
                    st.success(f"✅ {sync_notif_hour:02d}:{sync_notif_minute:02d}")
                else:
                    st.error("❌ Desabilitada")
            
            with col3:
                st.markdown("**🗂️ Kanbanize Sync**")
                if kanbanize_sync_enabled and (kanbanize_sync_09h30_enabled or kanbanize_sync_18h00_enabled):
                    sync_status = []
                    if kanbanize_sync_09h30_enabled:
                        sync_status.append("09:30")
                    if kanbanize_sync_18h00_enabled:
                        sync_status.append("18:00")
                    st.success(f"✅ {' | '.join(sync_status)}")
                else:
                    st.warning("⚠️ Desabilitada")

            with col4:
                st.markdown("**📨 Mensagens**")
                if mensagem_manha_enabled or mensagem_tarde_enabled:
                    msg_status = []
                    if mensagem_manha_enabled:
                        msg_status.append(f"🌅 {manha_hour:02d}:{manha_minute:02d}")
                    if mensagem_tarde_enabled:
                        msg_status.append(f"🌆 {tarde_hour:02d}:{tarde_minute:02d}")
                    st.success(f"✅ {' | '.join(msg_status)}")
                else:
                    st.warning("⚠️ Nenhuma habilitada")
        
        st.divider()
    else:
        # evolution_url, evolution_numero, evolution_api_key já foram inicializados no topo
        sync_notif_enabled = config_atual.get("SYNC_NOTIF_ENABLED", "false").lower() == "true"
        sync_notif_hour = int(config_atual.get("SYNC_NOTIF_HOUR", settings.SYNC_NOTIF_HOUR))
        sync_notif_minute = int(config_atual.get("SYNC_NOTIF_MINUTE", settings.SYNC_NOTIF_MINUTE))
        evolution_numero_sync = config_atual.get("EVOLUTION_NUMERO_SYNC", evolution_numero_default)
        st.divider()
    
    st.divider()
    
    # ==================== NOTIFICAÇÕES ====================
    st.subheader("🔔 Notificações")
    
    notify_on_sync = st.checkbox(
        "Notificar após sincronização",
        value=config_atual.get("NOTIFY_ON_SYNC", "false").lower() == "true",
        key="notify_on_sync"
    )
    
    notify_dias = st.number_input(
        "Dias antes das férias para enviar aviso:",
        min_value=1,
        max_value=30,
        value=int(config_atual.get("NOTIFY_FERIAS_DIAS_ANTES", "1")),
        key="notify_dias"
    )
    
    st.divider()
    
    # ==================== ONETIMESECRET API ====================
    st.subheader("🔑 OneTimeSecret API")
    
    onetimesecret_enabled = st.checkbox(
        "Habilitar OneTimeSecret",
        value=config_atual.get("ONETIMESECRET_ENABLED", "true").lower() == "true",
        key="onetimesecret_enabled",
        help="Integração com OneTimeSecret para gerar links seguros de senhas"
    )
    
    onetimesecret_email_default = config_atual.get("ONETIMESECRET_EMAIL", "gvcaetano190@gmail.com")
    onetimesecret_api_key_default = config_atual.get("ONETIMESECRET_API_KEY", "5a19ff2da5a9dac1391971611b9a021d6c3aade8")
    
    if onetimesecret_enabled:
        onetimesecret_email = st.text_input(
            "Email:",
            value=onetimesecret_email_default,
            help="Email cadastrado no OneTimeSecret",
            key="onetimesecret_email"
        )
        
        onetimesecret_api_key = st.text_input(
            "API Key:",
            value=onetimesecret_api_key_default,
            type="password",
            help="Chave da API do OneTimeSecret",
            key="onetimesecret_api_key"
        )
        
        # Botão de teste
        if st.button("🧪 Testar OneTimeSecret", key="test_onetimesecret"):
            with st.spinner("Testando conexão..."):
                try:
                    api = OneTimeSecretAPI(
                        email=onetimesecret_email,
                        api_key=onetimesecret_api_key
                    )
                    
                    resultado = api.criar_senha("teste123", ttl=3600)
                    
                    if resultado.get("sucesso"):
                        st.success(f"✅ **Conexão bem-sucedida!**")
                        st.info(f"**Link de teste:** {resultado.get('link', 'N/A')}")
                        st.caption("⚠️ Este link pode ser aberto apenas uma vez.")
                    else:
                        st.error(f"❌ **Erro:** {resultado.get('mensagem', 'Erro desconhecido')}")
                except Exception as e:
                    st.error(f"❌ **Erro ao testar:** {e}")
        
        config_atual["ONETIMESECRET_ENABLED"] = "true" if onetimesecret_enabled else "false"
        config_atual["ONETIMESECRET_EMAIL"] = onetimesecret_email
        config_atual["ONETIMESECRET_API_KEY"] = onetimesecret_api_key
    else:
        config_atual["ONETIMESECRET_ENABLED"] = "false"
    
    st.divider()
    
    # ==================== KANBANIZE API ====================
    st.subheader("📋 Kanbanize API")
    
    kanbanize_enabled = st.checkbox(
        "Habilitar Kanbanize",
        value=config_atual.get("KANBANIZE_ENABLED", "false").lower() == "true",
        key="kanbanize_enabled",
        help="Integração com Kanbanize para visualizar boards e cards"
    )
    
    if kanbanize_enabled:
        kanbanize_base_url_input = st.text_input(
            "URL Base:",
            value=kanbanize_base_url,
            help="URL base do Kanbanize (ex: https://fmimpressosltda.kanbanize.com)",
            key="kanbanize_base_url_input"
        )
        kanbanize_base_url = kanbanize_base_url_input

        kanbanize_api_key_input = st.text_input(
            "API Key:",
            value=kanbanize_api_key,
            type="password",
            help="Chave da API do Kanbanize",
            key="kanbanize_api_key_input"
        )
        kanbanize_api_key = kanbanize_api_key_input

        kanbanize_default_board_id_input = st.number_input(
            "Board Padrão (ID):",
            min_value=0,
            value=int(kanbanize_default_board_id) if kanbanize_default_board_id.isdigit() else 0,
            step=1,
            help="ID do board padrão. Deixe em 0 para buscar em todos os boards. Este será o board usado por padrão nas buscas de cards.",
            key="kanbanize_default_board_id_input"
        )
        # Atualiza a variável principal com o valor do input
        kanbanize_default_board_id = str(kanbanize_default_board_id_input)
        
        st.info("💡 **Dica:** Você pode encontrar a documentação da API em: **{}/openapi/**".format(kanbanize_base_url))
        
        # Botão de teste
        if st.button("🧪 Testar Kanbanize", key="test_kanbanize"):
            with st.spinner("Testando conexão..."):
                try:
                    from integrations.kanbanize import KanbanizeAPI as KanbanizeAPILocal
                    
                    api = KanbanizeAPILocal(
                        base_url=kanbanize_base_url,
                        api_key=kanbanize_api_key
                    )
                    
                    # Testa a conexão fazendo uma requisição simples para buscar cards
                    # Se o board ID estiver definido, usa ele, senão testa com board_ids=None
                    board_id_teste = int(kanbanize_default_board_id) if kanbanize_default_board_id.isdigit() and int(kanbanize_default_board_id) > 0 else None
                    
                    if board_id_teste:
                        resultado = api.listar_workflows(board_id_teste)
                    else:
                        # Tenta buscar cards sem especificar board (pode listar todos)
                        resultado = api.buscar_cards_simples(page=1, per_page=1)
                    
                    if resultado.get("sucesso"):
                        st.success(f"✅ **Conexão bem-sucedida!**")
                        st.info("A API do Kanbanize está respondendo corretamente.")
                        if board_id_teste:
                            st.caption(f"✓ Board ID {board_id_teste} acessível")
                    else:
                        st.error(f"❌ **Erro:** {resultado.get('mensagem', 'Erro desconhecido')}")
                        st.info("""
                        💡 **Possíveis soluções:**
                        - Verifique se a URL base está correta
                        - Verifique se a API key está correta
                        - Verifique a documentação da API em: **{}/openapi/**
                        - A API do Kanbanize pode usar diferentes versões (v1, v2, etc.)
                        """.format(kanbanize_base_url))
                except Exception as e:
                    st.error(f"❌ **Erro ao testar:** {e}")
    
    # Atualiza config_atual sempre (para manter valores mesmo quando desabilitado)
    config_atual["KANBANIZE_ENABLED"] = "true" if kanbanize_enabled else "false"
    config_atual["KANBANIZE_BASE_URL"] = kanbanize_base_url
    config_atual["KANBANIZE_API_KEY"] = kanbanize_api_key
    config_atual["KANBANIZE_DEFAULT_BOARD_ID"] = str(kanbanize_default_board_id)
    
    st.divider()
    
    # Atualiza config_atual
    config_atual["KANBANIZE_SYNC_ENABLED"] = "true" if kanbanize_sync_enabled else "false"
    config_atual["KANBANIZE_SYNC_09H30_ENABLED"] = "true" if kanbanize_sync_09h30_enabled else "false"
    config_atual["KANBANIZE_SYNC_18H00_ENABLED"] = "true" if kanbanize_sync_18h00_enabled else "false"
    
    st.divider()
    
    # ==================== PADRÕES DE ACESSOS ====================
    st.subheader("🔧 Padrões de Processamento")
    
    st.caption("ℹ️ Configure os valores que indicam que um funcionário **não tem acesso** a determinada ferramenta na planilha.")
    
    # Carrega padrões atuais
    padroes_sem_acesso_atual = config_atual.get("PADROES_SEM_ACESSO", "N/P,N\\A,NA,N/A,NP")
    
    with st.expander("📋 Padrões de 'Não Possui' (NP)", expanded=True):
        st.info("""
        **O que são esses padrões?**
        
        Na planilha, algumas células indicam que a pessoa **não possui** acesso à ferramenta.
        Por exemplo: `NP`, `N/P`, `N/A`, etc.
        
        Esses valores serão mapeados para **"NP"** (Não Possui).
        
        **Regras de mapeamento:**
        - Célula vazia → `NB` (Não Bloqueado)
        - `-` (hífen) → `NP` (Não Possui)
        - `NP`, `N/P`, `N/A` → `NP` (Não Possui)
        - `Bloqueado` → `BLOQUEADO`
        - `Liberado` → `LIBERADO`
        """)
        
        padroes_sem_acesso = st.text_input(
            "Valores separados por vírgula:",
            value=padroes_sem_acesso_atual,
            help="Cada valor será mapeado para 'NP' (Não Possui). Ex: NP,N/P,N/A. Note: '-' é automaticamente tratado como NP.",
            key="padroes_sem_acesso"
        )
        
        # Preview dos padrões
        if padroes_sem_acesso:
            padroes_lista = [p.strip() for p in padroes_sem_acesso.split(",") if p.strip()]
            st.caption(f"**{len(padroes_lista)} padrões configurados:** {', '.join([f'`{p}`' for p in padroes_lista])}")
    
    st.divider()
    
    # ==================== BOTÃO SALVAR ====================
    if st.button("💾 Salvar Configurações", type="primary", width='stretch'):
        with st.spinner("Salvando configurações..."):
            novas_config = {
                "SYNC_HOUR": str(sync_hour),
                "SYNC_MINUTE": str(sync_minute),
                "SYNC_ENABLED": "true" if sync_enabled else "false",
                "CACHE_MINUTES": str(cache_minutes),
                "GOOGLE_SHEETS_URL": google_url,
                "EVOLUTION_ENABLED": "true" if evolution_enabled else "false",
                "SYNC_NOTIF_ENABLED": "true" if sync_notif_enabled else "false",
                "SYNC_NOTIF_HOUR": str(sync_notif_hour),
                "SYNC_NOTIF_MINUTE": str(sync_notif_minute),
                "EVOLUTION_NUMERO_SYNC": evolution_numero_sync,
                "NOTIFY_ON_SYNC": "true" if notify_on_sync else "false",
                "NOTIFY_FERIAS_DIAS_ANTES": str(notify_dias),
            }
            
            if evolution_enabled:
                novas_config["EVOLUTION_API_URL"] = evolution_url
                novas_config["EVOLUTION_NUMERO"] = evolution_numero
                novas_config["EVOLUTION_API_KEY"] = evolution_api_key
                
                # Mensagens automáticas
                novas_config["MENSAGEM_MANHA_ENABLED"] = "true" if mensagem_manha_enabled else "false"
                novas_config["MENSAGEM_MANHA_HOUR"] = str(manha_hour)
                novas_config["MENSAGEM_MANHA_MINUTE"] = str(manha_minute)
                
                novas_config["MENSAGEM_TARDE_ENABLED"] = "true" if mensagem_tarde_enabled else "false"
                novas_config["MENSAGEM_TARDE_HOUR"] = str(tarde_hour)
                novas_config["MENSAGEM_TARDE_MINUTE"] = str(tarde_minute)
            
            # OneTimeSecret
            novas_config["ONETIMESECRET_ENABLED"] = config_atual.get("ONETIMESECRET_ENABLED", "false")
            if onetimesecret_enabled:
                novas_config["ONETIMESECRET_EMAIL"] = onetimesecret_email
                novas_config["ONETIMESECRET_API_KEY"] = onetimesecret_api_key
            else:
                novas_config["ONETIMESECRET_EMAIL"] = config_atual.get("ONETIMESECRET_EMAIL", "")
                novas_config["ONETIMESECRET_API_KEY"] = config_atual.get("ONETIMESECRET_API_KEY", "")
            
            # Kanbanize - usa as variáveis que sempre estão definidas
            novas_config["KANBANIZE_ENABLED"] = "true" if kanbanize_enabled else "false"
            novas_config["KANBANIZE_BASE_URL"] = kanbanize_base_url
            novas_config["KANBANIZE_API_KEY"] = kanbanize_api_key
            novas_config["KANBANIZE_DEFAULT_BOARD_ID"] = str(kanbanize_default_board_id)
            
            # Kanbanize Sync - usar as variáveis do Streamlit (não de config_atual)
            novas_config["KANBANIZE_SYNC_ENABLED"] = "true" if kanbanize_sync_enabled else "false"
            novas_config["KANBANIZE_SYNC_09H30_ENABLED"] = "true" if kanbanize_sync_09h30_enabled else "false"
            novas_config["KANBANIZE_SYNC_18H00_ENABLED"] = "true" if kanbanize_sync_18h00_enabled else "false"
            
            # Padrões de processamento
            novas_config["PADROES_SEM_ACESSO"] = padroes_sem_acesso
            
            try:
                if config_manager.salvar_config(novas_config):
                    # Recarrega settings
                    settings.carregar_env()
                    
                    # Tenta reiniciar o scheduler automaticamente (apenas em Docker)
                    scheduler_reiniciado = False
                    em_docker = Path("/.dockerenv").exists()
                    
                    if em_docker:
                        try:
                            # No Docker, envia sinal para o container do scheduler
                            # O docker-compose deve ter configurado o volume compartilhado
                            lock_file = Path("/app/data/.scheduler.lock")
                            reload_flag = Path("/app/data/.scheduler.reload")
                            
                            # Cria flag para indicar que deve recarregar
                            reload_flag.write_text(f"{datetime.now().isoformat()}\n")
                            scheduler_reiniciado = True
                            
                            # Registra log
                            database.registrar_log(
                                tipo="sistema",
                                categoria="Configurações",
                                status="sucesso",
                                mensagem="Configurações salvas e sinal de reload enviado ao scheduler",
                                origem="configuracoes"
                            )
                        except Exception as e_docker:
                            # Se falhar, não é crítico
                            pass
                    
                    # Salva mensagem de sucesso no session_state
                    st.session_state['config_saved'] = True
                    st.session_state['config_error'] = None
                    if scheduler_reiniciado:
                        st.session_state['config_message'] = "Configurações salvas! O scheduler receberá as novas configurações automaticamente."
                    else:
                        st.session_state['config_message'] = "Configurações salvas com sucesso!"
                    
                    # Recarrega para mostrar a mensagem no topo
                    st.rerun()
                else:
                    st.session_state['config_saved'] = False
                    st.session_state['config_error'] = "Erro desconhecido ao salvar"
                    st.rerun()
            except Exception as e:
                st.session_state['config_saved'] = False
                st.session_state['config_error'] = str(e)
                st.rerun()
    
    st.divider()
    
    # ==================== INFORMAÇÕES ADICIONAIS ====================
    with st.expander("ℹ️ Informações sobre as configurações"):
        st.markdown("""
        **🔄 Sincronização Automática:**
        - A sincronização roda diariamente no horário configurado
        - Use `./scripts/scheduler.sh` para iniciar o daemon
        - O cache evita downloads desnecessários
        
        **📊 Google Sheets:**
        - A planilha precisa ser pública (qualquer um com o link pode ver)
        - O sistema baixa como Excel (.xlsx) para processar todas as abas
        
        **📱 Evolution API:**
        - Integração opcional para envio de mensagens via WhatsApp
        - Requer instalação e configuração da Evolution API separadamente
        
        **🔔 Notificações:**
        - As notificações funcionam apenas se a Evolution API estiver habilitada
        """)
    
    # ==================== CONFIGURAÇÕES AVANÇADAS ====================
    with st.expander("🔧 Configurações Avançadas"):
        st.caption("Altere estas configurações apenas se souber o que está fazendo.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_host = st.text_input(
                "API Host (futuro FastAPI):",
                value=config_atual.get("API_HOST", "0.0.0.0"),
                key="api_host",
                disabled=True
            )
        
        with col2:
            api_port = st.number_input(
                "API Port (futuro FastAPI):",
                min_value=1,
                max_value=65535,
                value=int(config_atual.get("API_PORT", "8000")),
                key="api_port",
                disabled=True
            )
        
        st.caption("⚠️ FastAPI ainda não está implementado. Estas configurações serão usadas no futuro.")


def _verificar_status_servicos(database, config_atual):
    """Verifica o status de todos os serviços do sistema."""
    st.markdown("### 🔍 Status dos Serviços")
    
    status_geral = {
        "scheduler": {"status": "unknown", "mensagem": "", "detalhes": ""},
        "banco_dados": {"status": "unknown", "mensagem": "", "detalhes": ""},
        "evolution_api": {"status": "unknown", "mensagem": "", "detalhes": ""},
        "onetimesecret": {"status": "unknown", "mensagem": "", "detalhes": ""},
        "google_sheets": {"status": "unknown", "mensagem": "", "detalhes": ""}
    }
    
    # 1. Verifica Scheduler
    try:
        # Detecta se está rodando em Docker
        em_docker = Path("/.dockerenv").exists()
        
        if em_docker:
            # No Docker, verifica o container scheduler
            try:
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=controle-ferias-scheduler", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip() and "Up" in result.stdout:
                    status_geral["scheduler"]["status"] = "sucesso"
                    status_geral["scheduler"]["mensagem"] = "Scheduler rodando em container"
                    status_geral["scheduler"]["detalhes"] = result.stdout.strip()
                else:
                    status_geral["scheduler"]["status"] = "erro"
                    status_geral["scheduler"]["mensagem"] = "Container scheduler não está rodando"
            except:
                # Fallback: verifica se o arquivo de lock existe (compartilhado entre containers)
                lock_file = Path("/app/data/.scheduler.lock")
                if lock_file.exists():
                    status_geral["scheduler"]["status"] = "sucesso"
                    status_geral["scheduler"]["mensagem"] = "Scheduler rodando (container separado)"
                    status_geral["scheduler"]["detalhes"] = "Detectado via lock file"
                else:
                    status_geral["scheduler"]["status"] = "warning"
                    status_geral["scheduler"]["mensagem"] = "Não foi possível verificar (Docker)"
        else:
            # Não está em Docker, verifica localmente
            result = subprocess.run(
                ["pgrep", "-f", "scheduler.jobs"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                pids = [pid.strip() for pid in pids if pid.strip()]
                if pids:
                    status_geral["scheduler"]["status"] = "sucesso"
                    status_geral["scheduler"]["mensagem"] = f"Scheduler rodando (PID: {', '.join(pids)})"
                    status_geral["scheduler"]["detalhes"] = f"{len(pids)} processo(s) ativo(s)"
                else:
                    status_geral["scheduler"]["status"] = "erro"
                    status_geral["scheduler"]["mensagem"] = "Scheduler não está rodando"
            else:
                # Tenta com ps aux (fallback)
                try:
                    result = subprocess.run(
                        ["ps", "aux"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        encontrado = False
                        for line in result.stdout.split('\n'):
                            if 'scheduler.jobs' in line and 'grep' not in line:
                                encontrado = True
                                parts = line.split()
                                if len(parts) > 1:
                                    status_geral["scheduler"]["status"] = "sucesso"
                                    status_geral["scheduler"]["mensagem"] = f"Scheduler rodando (PID: {parts[1]})"
                                    status_geral["scheduler"]["detalhes"] = "Processo encontrado"
                                break
                        if not encontrado:
                            status_geral["scheduler"]["status"] = "erro"
                            status_geral["scheduler"]["mensagem"] = "Scheduler não está rodando"
                    else:
                        status_geral["scheduler"]["status"] = "warning"
                        status_geral["scheduler"]["mensagem"] = "Não foi possível verificar (comando ps não disponível)"
                except:
                    status_geral["scheduler"]["status"] = "warning"
                    status_geral["scheduler"]["mensagem"] = "Não foi possível verificar o scheduler"
    except Exception as e:
        status_geral["scheduler"]["status"] = "erro"
        status_geral["scheduler"]["mensagem"] = f"Erro ao verificar: {str(e)}"
    
    # 2. Verifica Banco de Dados
    try:
        last_sync = database.buscar_ultimo_sync()
        if last_sync:
            status_geral["banco_dados"]["status"] = "sucesso"
            status_geral["banco_dados"]["mensagem"] = "Banco de dados conectado e funcionando"
            status_geral["banco_dados"]["detalhes"] = f"Última sync: {last_sync.get('sync_at', 'N/A')}"
        else:
            status_geral["banco_dados"]["status"] = "warning"
            status_geral["banco_dados"]["mensagem"] = "Banco conectado, mas sem dados de sincronização"
    except Exception as e:
        status_geral["banco_dados"]["status"] = "erro"
        status_geral["banco_dados"]["mensagem"] = f"Erro ao conectar no banco: {str(e)}"
    
    # 3. Verifica Evolution API
    evolution_url = config_atual.get("EVOLUTION_API_URL", "")
    evolution_api_key = config_atual.get("EVOLUTION_API_KEY", "")
    evolution_enabled = config_atual.get("EVOLUTION_ENABLED", "false").lower() == "true"
    
    if not evolution_enabled:
        status_geral["evolution_api"]["status"] = "info"
        status_geral["evolution_api"]["mensagem"] = "Evolution API desabilitada"
    elif not evolution_url or not evolution_api_key:
        status_geral["evolution_api"]["status"] = "warning"
        status_geral["evolution_api"]["mensagem"] = "Evolution API não configurada (URL ou API Key faltando)"
    else:
        try:
            api = EvolutionAPI(url=evolution_url, api_key=evolution_api_key)
            resultado = api.enviar_mensagem_teste()
            if resultado.get("sucesso"):
                status_geral["evolution_api"]["status"] = "sucesso"
                status_geral["evolution_api"]["mensagem"] = "Evolution API funcionando corretamente"
            else:
                status_geral["evolution_api"]["status"] = "erro"
                status_geral["evolution_api"]["mensagem"] = f"Erro na Evolution API: {resultado.get('mensagem', 'Erro desconhecido')}"
        except Exception as e:
            status_geral["evolution_api"]["status"] = "erro"
            status_geral["evolution_api"]["mensagem"] = f"Erro ao testar Evolution API: {str(e)}"
    
    # 4. Verifica OneTimeSecret
    ots_email = config_atual.get("ONETIMESECRET_EMAIL", "")
    ots_api_key = config_atual.get("ONETIMESECRET_API_KEY", "")
    ots_enabled = config_atual.get("ONETIMESECRET_ENABLED", "false").lower() == "true"
    
    if not ots_enabled:
        status_geral["onetimesecret"]["status"] = "info"
        status_geral["onetimesecret"]["mensagem"] = "OneTimeSecret desabilitado"
    elif not ots_email or not ots_api_key:
        status_geral["onetimesecret"]["status"] = "warning"
        status_geral["onetimesecret"]["mensagem"] = "OneTimeSecret não configurado (Email ou API Key faltando)"
    else:
        try:
            from integrations.onetimesecret import OneTimeSecretAPI
            api = OneTimeSecretAPI(email=ots_email, api_key=ots_api_key)
            # Tenta criar um segredo de teste (com TTL muito curto)
            resultado = api.criar_senha("teste_status", ttl=1)
            if resultado.get("sucesso"):
                status_geral["onetimesecret"]["status"] = "sucesso"
                status_geral["onetimesecret"]["mensagem"] = "OneTimeSecret funcionando corretamente"
            else:
                status_geral["onetimesecret"]["status"] = "erro"
                status_geral["onetimesecret"]["mensagem"] = f"Erro no OneTimeSecret: {resultado.get('mensagem', 'Erro desconhecido')}"
        except Exception as e:
            status_geral["onetimesecret"]["status"] = "erro"
            status_geral["onetimesecret"]["mensagem"] = f"Erro ao testar OneTimeSecret: {str(e)}"
    
    # 5. Verifica Google Sheets
    sheets_url = config_atual.get("GOOGLE_SHEETS_URL", "")
    if not sheets_url:
        status_geral["google_sheets"]["status"] = "warning"
        status_geral["google_sheets"]["mensagem"] = "URL do Google Sheets não configurada"
    else:
        try:
            from core.validar_planilha import validar_url_google_sheets
            # A função retorna (bool, str, Optional[str]) - 3 valores
            valido, mensagem, sheet_id = validar_url_google_sheets(sheets_url)
            if valido:
                status_geral["google_sheets"]["status"] = "sucesso"
                status_geral["google_sheets"]["mensagem"] = mensagem if mensagem else "URL do Google Sheets válida"
                if sheet_id:
                    status_geral["google_sheets"]["detalhes"] = f"Sheet ID: {sheet_id}"
            else:
                status_geral["google_sheets"]["status"] = "erro"
                status_geral["google_sheets"]["mensagem"] = f"URL inválida: {mensagem}"
        except Exception as e:
            status_geral["google_sheets"]["status"] = "erro"
            status_geral["google_sheets"]["mensagem"] = f"Erro ao validar URL: {str(e)}"
    
    # Exibe resultados
    col1, col2 = st.columns(2)
    
    with col1:
        # Scheduler
        _exibir_status_item("📆 Scheduler", status_geral["scheduler"])
        st.divider()
        
        # Banco de Dados
        _exibir_status_item("💾 Banco de Dados", status_geral["banco_dados"])
        st.divider()
        
        # Evolution API
        _exibir_status_item("📱 Evolution API", status_geral["evolution_api"])
    
    with col2:
        # OneTimeSecret
        _exibir_status_item("🔑 OneTimeSecret", status_geral["onetimesecret"])
        st.divider()
        
        # Google Sheets
        _exibir_status_item("📊 Google Sheets", status_geral["google_sheets"])
    
    # Resumo geral
    st.divider()
    total_servicos = len(status_geral)
    servicos_ok = len([s for s in status_geral.values() if s["status"] == "sucesso"])
    servicos_erro = len([s for s in status_geral.values() if s["status"] == "erro"])
    servicos_warning = len([s for s in status_geral.values() if s["status"] == "warning"])
    
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    col_res1.metric("Total", total_servicos)
    col_res2.metric("✅ OK", servicos_ok)
    col_res3.metric("⚠️ Avisos", servicos_warning)
    col_res4.metric("❌ Erros", servicos_erro)
    
    # Registra log
    status_log = "sucesso" if servicos_erro == 0 else ("warning" if servicos_warning > 0 else "erro")
    mensagem_log = f"Verificação de status: {servicos_ok} OK, {servicos_warning} avisos, {servicos_erro} erros"
    detalhes_log = "; ".join([f"{k}: {v['status']}" for k, v in status_geral.items()])
    
    database.registrar_log(
        tipo="sistema",
        categoria="Verificação de Status",
        status=status_log,
        mensagem=mensagem_log,
        detalhes=detalhes_log,
        origem="configuracoes"
    )


def _exibir_status_item(nome: str, status_info: dict):
    """Exibe um item de status formatado."""
    status = status_info.get("status", "unknown")
    mensagem = status_info.get("mensagem", "")
    detalhes = status_info.get("detalhes", "")
    
    # Cores baseadas no status
    if status == "sucesso":
        bg_color = "#e8f5e9"
        border_color = "#4caf50"
        icon = "✅"
    elif status == "erro":
        bg_color = "#ffebee"
        border_color = "#f44336"
        icon = "❌"
    elif status == "warning":
        bg_color = "#fff3e0"
        border_color = "#ff9800"
        icon = "⚠️"
    else:
        bg_color = "#e3f2fd"
        border_color = "#2196f3"
        icon = "ℹ️"
    
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; border-left: 4px solid {border_color}; margin-bottom: 10px;">
        <div style="font-weight: bold; font-size: 1rem; margin-bottom: 5px;">
            {icon} {nome}
        </div>
        <div style="font-size: 0.9rem; color: #333;">
            {mensagem}
        </div>
        {f'<div style="font-size: 0.8rem; color: #666; margin-top: 5px;">{detalhes}</div>' if detalhes else ''}
    </div>
    """, unsafe_allow_html=True)


def _reiniciar_scheduler(database=None):
    """Reinicia o scheduler."""
    with st.spinner("Reiniciando scheduler..."):
        try:
            project_dir = Path(__file__).parent.parent.parent
            scheduler_script = project_dir / "scripts" / "scheduler.sh"
            
            # 1. Encontra e mata processos do scheduler
            processos_encontrados = []
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "scheduler.jobs"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    processos_encontrados = [pid.strip() for pid in pids if pid.strip()]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                try:
                    result = subprocess.run(
                        ["ps", "aux"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'scheduler.jobs' in line and 'grep' not in line:
                                parts = line.split()
                                if len(parts) > 1:
                                    processos_encontrados.append(parts[1])
                except:
                    pass
            except:
                pass
            
            if processos_encontrados:
                for pid in processos_encontrados:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(0.5)
                    except (ProcessLookupError, ValueError):
                        pass
                st.success(f"⏹️ {len(processos_encontrados)} processo(s) do scheduler parado(s)")
                time.sleep(1)
            else:
                st.info("ℹ️ Nenhum processo do scheduler encontrado rodando (pode estar parado)")
            
            # 2. Inicia novo scheduler em background
            if scheduler_script.exists():
                try:
                    os.chmod(scheduler_script, 0o755)
                except:
                    pass
                
                log_file = project_dir / "scheduler.log"
                log_fd = open(log_file, 'a')
                
                process = subprocess.Popen(
                    ["bash", str(scheduler_script)],
                    cwd=str(project_dir),
                    stdout=log_fd,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
                
                time.sleep(2)
                
                if process.poll() is None:
                    st.success("✅ Scheduler reiniciado com sucesso!")
                    st.info(f"💡 O scheduler está rodando em background (PID: {process.pid}).")
                    
                    # Registra log
                    if database:
                        database.registrar_log(
                            tipo="sistema",
                            categoria="Scheduler",
                            status="sucesso",
                            mensagem="Scheduler reiniciado com sucesso",
                            detalhes=f"PID: {process.pid}",
                            origem="configuracoes"
                        )
                else:
                    st.warning("⚠️ Scheduler pode ter tido problemas ao iniciar.")
                    
                    # Registra log de erro
                    if database:
                        database.registrar_log(
                            tipo="sistema",
                            categoria="Scheduler",
                            status="erro",
                            mensagem="Falha ao reiniciar scheduler",
                            origem="configuracoes"
                        )
                    try:
                        if log_file.exists():
                            with open(log_file, 'r') as f:
                                linhas = f.readlines()
                                ultimas_linhas = linhas[-10:] if len(linhas) > 10 else linhas
                                erro_recente = '\n'.join(ultimas_linhas)
                                
                                if 'APScheduler não instalado' in erro_recente or 'APScheduler não disponível' in erro_recente:
                                    st.error("❌ **APScheduler não está instalado!**")
                                    st.info("💡 Execute no terminal:\n\n```bash\npip install apscheduler\n```")
                                else:
                                    st.code(erro_recente[-500:], language=None)
                    except:
                        pass
                    st.info("💡 Verifique os logs em `scheduler.log` ou execute manualmente no terminal.")
            else:
                st.error(f"❌ Script não encontrado: {scheduler_script}")
                if database:
                    database.registrar_log(
                        tipo="sistema",
                        categoria="Scheduler",
                        status="erro",
                        mensagem=f"Script não encontrado: {scheduler_script}",
                        origem="configuracoes"
                    )
                
        except Exception as e:
            st.error(f"❌ Erro ao reiniciar scheduler: {str(e)}")
            st.info("💡 **Instrução manual:**\n\n```bash\npkill -f scheduler.jobs\n./scripts/scheduler.sh\n```")
            
            # Registra log de exceção
            if database:
                database.registrar_log(
                    tipo="sistema",
                    categoria="Scheduler",
                    status="erro",
                    mensagem=f"Exceção ao reiniciar scheduler: {str(e)}",
                    origem="configuracoes"
                )

