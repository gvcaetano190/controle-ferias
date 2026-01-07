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


def render(database):
    """Renderiza a página de configurações."""
    st.header("⚙️ Configurações do Sistema")
    
    # Mostra mensagem de sucesso/erro se existir no session_state
    if 'config_saved' in st.session_state:
        if st.session_state['config_saved']:
            message = st.session_state.get('config_message', 'Configurações salvas com sucesso!')
            st.success(f"✅ **{message}**")
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
    
    # Inicializa variáveis com valores padrão (sempre disponíveis)
    evolution_url_default = config_atual.get("EVOLUTION_API_URL", "http://10.0.153.28:8081/message/sendText/zabbix")
    evolution_numero_default = config_atual.get("EVOLUTION_NUMERO", "120363020985287866@g.us")
    evolution_api_key_default = config_atual.get("EVOLUTION_API_KEY", "")
    mensagem_manha_enabled = config_atual.get("MENSAGEM_MANHA_ENABLED", "false").lower() == "true"
    manha_hour = int(config_atual.get("MENSAGEM_MANHA_HOUR", "8"))
    manha_minute = int(config_atual.get("MENSAGEM_MANHA_MINUTE", "0"))
    mensagem_tarde_enabled = config_atual.get("MENSAGEM_TARDE_ENABLED", "false").lower() == "true"
    tarde_hour = int(config_atual.get("MENSAGEM_TARDE_HOUR", "17"))
    tarde_minute = int(config_atual.get("MENSAGEM_TARDE_MINUTE", "0"))
    
    if evolution_enabled:
        evolution_url = st.text_input(
            "URL Completa do Endpoint:",
            value=evolution_url_default,
            help="URL completa do endpoint (ex: http://10.0.153.28:8081/message/sendText/zabbix)",
            key="evolution_url"
        )
        
        evolution_numero = st.text_input(
            "Número/Grupo do WhatsApp:",
            value=evolution_numero_default,
            help="Número ou ID do grupo (ex: 120363020985287866@g.us ou 11954175296)",
            key="evolution_numero"
        )
        
        evolution_api_key = st.text_input(
            "API Key:",
            value=evolution_api_key_default,
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
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔄 Sincronização**")
                if sync_enabled:
                    st.success(f"✅ Habilitada às **{sync_hour:02d}:{sync_minute:02d}**")
                else:
                    st.error("❌ Desabilitada")
            
            with col2:
                st.markdown("**📨 Mensagens Automáticas**")
                if mensagem_manha_enabled:
                    st.info(f"🌅 Matutina: **{manha_hour:02d}:{manha_minute:02d}**")
                if mensagem_tarde_enabled:
                    st.info(f"🌆 Vespertina: **{tarde_hour:02d}:{tarde_minute:02d}**")
                if not mensagem_manha_enabled and not mensagem_tarde_enabled:
                    st.warning("⚠️ Nenhuma mensagem agendada")
        
        st.divider()
    else:
        evolution_url = evolution_url_default
        evolution_numero = evolution_numero_default
        evolution_api_key = evolution_api_key_default
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
    
    # ==================== PADRÕES DE ACESSOS ====================
    st.subheader("🔧 Padrões de Processamento")
    
    st.caption("ℹ️ Configure os valores que indicam que um funcionário **não tem acesso** a determinada ferramenta na planilha.")
    
    # Carrega padrões atuais
    padroes_sem_acesso_atual = config_atual.get("PADROES_SEM_ACESSO", "N/P,N\\A,NA,N/A,NP,-,NB")
    
    with st.expander("📋 Padrões de 'Sem Acesso' (NA)", expanded=True):
        st.info("""
        **O que são esses padrões?**
        
        Na planilha, algumas células indicam que a pessoa não utiliza determinada ferramenta.
        Por exemplo: `NB`, `NP`, `N/A`, `-`, etc.
        
        Esses valores serão mapeados para o status **"NA"** (Não Aplicável) e não aparecerão como pendentes.
        """)
        
        padroes_sem_acesso = st.text_input(
            "Valores separados por vírgula:",
            value=padroes_sem_acesso_atual,
            help="Cada valor separado por vírgula será tratado como 'Não tem acesso'. Ex: NB,NP,N/A,-",
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
            
            # Padrões de processamento
            novas_config["PADROES_SEM_ACESSO"] = padroes_sem_acesso
            
            try:
                if config_manager.salvar_config(novas_config):
                    # Recarrega settings
                    settings.carregar_env()
                    
                    # Salva mensagem de sucesso no session_state
                    st.session_state['config_saved'] = True
                    st.session_state['config_error'] = None
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

