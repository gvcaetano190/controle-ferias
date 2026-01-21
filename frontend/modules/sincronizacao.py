"""
Página de Sincronização.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from datetime import datetime, timedelta
import subprocess

from config.settings import settings
from core.sync_manager import SyncManager


def _enviar_notificacao_sync(resultado: dict, database) -> None:
    """
    Envia notificação WhatsApp após sincronização manual.
    
    Args:
        resultado: Dict com resultado da sincronização
        database: Instância do Database para registrar logs
    """
    if not settings.SYNC_NOTIF_ENABLED:
        return
    
    try:
        from integrations.evolution_api import EvolutionAPI
        
        api = EvolutionAPI(
            url=settings.EVOLUTION_API_URL,
            numero=settings.EVOLUTION_NUMERO_SYNC or settings.EVOLUTION_NUMERO,
            api_key=settings.EVOLUTION_API_KEY
        )
        
        # Passa origem="manual" para diferenciar da automática
        resultado_notif = api.enviar_mensagem_sync(resultado, origem="manual")
        
        if resultado_notif.get("sucesso"):
            st.success("📱 Notificação WhatsApp enviada com sucesso!")
        else:
            st.warning(f"⚠️ Não foi possível enviar a notificação: {resultado_notif.get('mensagem', 'Erro desconhecido')}")
            
    except Exception as e:
        st.error(f"❌ Não foi possível enviar a notificação: {e}")
        # Registra log do erro de notificação
        database.registrar_log(
            tipo="notificacao",
            categoria="WhatsApp",
            status="erro",
            mensagem=f"Erro ao enviar notificação de sync: {str(e)}",
            origem="frontend_sync"
        )


def render(database):
    """Renderiza a página de sincronização."""
    st.header("🔄 Sincronização de Dados")
    
    last_sync = database.buscar_ultimo_sync()
    
    if last_sync:
        sync_at = last_sync.get("sync_at", "")
        sync_time = None
        
        if sync_at:
            # Tenta diferentes formatos de timestamp
            try:
                # Formato SQLite: YYYY-MM-DD HH:MM:SS
                sync_time = datetime.strptime(sync_at, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # Formato ISO com microsegundos: YYYY-MM-DDTHH:MM:SS.ffffff
                    sync_time = datetime.fromisoformat(sync_at.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        # Formato ISO sem separador T: YYYY-MM-DD HH:MM:SS.ffffff
                        if '.' in sync_at:
                            sync_at_clean = sync_at.split('.')[0]
                            sync_time = datetime.strptime(sync_at_clean, '%Y-%m-%d %H:%M:%S')
                        else:
                            sync_time = datetime.strptime(sync_at, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
        
        if sync_time:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📅 Última Sync", sync_time.strftime('%d/%m/%Y %H:%M'))
            with col2:
                st.metric("📊 Registros", last_sync.get('total_registros', 0))
            with col3:
                st.metric("📑 Abas", last_sync.get('total_abas', 0))
        else:
            # Se não conseguiu fazer parse, mostra mesmo assim sem formatação
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📅 Última Sync", sync_at)
            with col2:
                st.metric("📊 Registros", last_sync.get('total_registros', 0))
            with col3:
                st.metric("📑 Abas", last_sync.get('total_abas', 0))
    else:
        st.info("ℹ️ Nenhuma sincronização realizada ainda. Clique em 'Sincronizar Agora'.")
    
    st.divider()
    
    # Opções de sincronização
    col1, col2 = st.columns([3, 1])
    
    with col1:
        forcar = st.checkbox("Forçar download (ignora cache)", value=False)
    
    with col2:
        # Toggle para mostrar/esconder status do scheduler
        if 'mostrar_status_scheduler' not in st.session_state:
            st.session_state['mostrar_status_scheduler'] = False
        
        # Botão com label dinâmico
        label_botao = "📊 Status Scheduler" if not st.session_state['mostrar_status_scheduler'] else "❌ Fechar"
        tipo_botao = "primary" if not st.session_state['mostrar_status_scheduler'] else "secondary"
        
        if st.button(label_botao, help="Verificar se o scheduler está rodando", width="stretch", type=tipo_botao):
            st.session_state['mostrar_status_scheduler'] = not st.session_state['mostrar_status_scheduler']
            st.rerun()
    
    # Mostra informações do scheduler se estiver ativo
    if st.session_state.get('mostrar_status_scheduler', False):
            with st.spinner("Verificando..."):
                from pathlib import Path
                
                # Detecta se está em Docker
                em_docker = Path("/.dockerenv").exists()
                
                # Busca configurações de horários
                sync_hour = settings.SYNC_HOUR
                sync_minute = settings.SYNC_MINUTE
                manha_hour = settings.MENSAGEM_MANHA_HOUR
                manha_minute = settings.MENSAGEM_MANHA_MINUTE
                tarde_hour = settings.MENSAGEM_TARDE_HOUR
                tarde_minute = settings.MENSAGEM_TARDE_MINUTE
                
                # Calcula próximo horário
                agora = datetime.now()
                proximos_horarios = []
                
                if settings.SYNC_ENABLED:
                    sync_time = agora.replace(hour=sync_hour, minute=sync_minute, second=0, microsecond=0)
                    if sync_time < agora:
                        sync_time += timedelta(days=1)
                    proximos_horarios.append(("Sincronização", sync_time))
                
                if settings.MENSAGEM_MANHA_ENABLED:
                    manha_time = agora.replace(hour=manha_hour, minute=manha_minute, second=0, microsecond=0)
                    if manha_time < agora:
                        manha_time += timedelta(days=1)
                    proximos_horarios.append(("Mensagem Matutina", manha_time))
                
                if settings.MENSAGEM_TARDE_ENABLED:
                    tarde_time = agora.replace(hour=tarde_hour, minute=tarde_minute, second=0, microsecond=0)
                    if tarde_time < agora:
                        tarde_time += timedelta(days=1)
                    proximos_horarios.append(("Mensagem Vespertina", tarde_time))
                
                # Ordena e pega o próximo
                proximos_horarios.sort(key=lambda x: x[1])
                proximo = proximos_horarios[0] if proximos_horarios else None
                
                if em_docker:
                    # Verifica arquivo de lock
                    lock_file = Path("/app/data/.scheduler.lock")
                    if lock_file.exists():
                        try:
                            lock_content = lock_file.read_text().strip()
                            mensagem = f"✅ **Scheduler rodando** (container separado)\n\n"
                            mensagem += f"**� Horário Atual:** {agora.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                            mensagem += f"**�📅 Iniciado em:** {lock_content}\n\n"
                            mensagem += f"**⏰ Horários Configurados:**\n"
                            if settings.SYNC_ENABLED:
                                mensagem += f"- 🔄 Sincronização: {sync_hour:02d}:{sync_minute:02d}\n"
                            if settings.MENSAGEM_MANHA_ENABLED:
                                mensagem += f"- 🌅 Mensagem Matutina: {manha_hour:02d}:{manha_minute:02d}\n"
                            if settings.MENSAGEM_TARDE_ENABLED:
                                mensagem += f"- 🌆 Mensagem Vespertina: {tarde_hour:02d}:{tarde_minute:02d}\n"
                            if proximo:
                                mensagem += f"\n**⏭️ Próxima execução:**\n{proximo[0]} às {proximo[1].strftime('%H:%M:%S')}"
                            st.success(mensagem)
                        except:
                            st.success("✅ Scheduler rodando (container separado)")
                    else:
                        st.error("❌ Scheduler não está rodando\n\nO arquivo de lock não foi encontrado")
                else:
                    # Verifica localmente
                    try:
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
                                mensagem = f"✅ **Scheduler rodando**\n\n"
                                mensagem += f"**🕐 Horário Atual:** {agora.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                                mensagem += f"**PID(s):** {', '.join(pids)}\n\n"
                                mensagem += f"**⏰ Horários Configurados:**\n"
                                if settings.SYNC_ENABLED:
                                    mensagem += f"- 🔄 Sincronização: {sync_hour:02d}:{sync_minute:02d}\n"
                                if settings.MENSAGEM_MANHA_ENABLED:
                                    mensagem += f"- 🌅 Mensagem Matutina: {manha_hour:02d}:{manha_minute:02d}\n"
                                if settings.MENSAGEM_TARDE_ENABLED:
                                    mensagem += f"- 🌆 Mensagem Vespertina: {tarde_hour:02d}:{tarde_minute:02d}\n"
                                if proximo:
                                    mensagem += f"\n**⏭️ Próxima execução:**\n{proximo[0]} às {proximo[1].strftime('%H:%M:%S')}"
                                st.success(mensagem)
                            else:
                                st.error("❌ Scheduler não está rodando")
                        else:
                            st.error("❌ Scheduler não está rodando")
                    except Exception as e:
                        st.warning(f"⚠️ Não foi possível verificar: {e}")
    
    # Botão de sincronização
    if st.button("🔄 Sincronizar Agora", type="primary", width='stretch'):
        with st.spinner("Sincronizando dados do Google Sheets..."):
            try:
                sync = SyncManager()
                resultado = sync.sincronizar(forcar=forcar)
                
                if resultado["status"] == "success":
                    st.success(f"✅ Sincronização concluída com sucesso! {resultado.get('registros', 0)} registros processados.")
                    # Envia notificação WhatsApp se configurado
                    _enviar_notificacao_sync(resultado, database)
                    # Limpa caches
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    # Botão para recarregar a página
                    if st.button("🔄 Atualizar página", key="reload_success"):
                        st.rerun()
                elif resultado["status"] == "skipped":
                    st.info(f"⏭️ {resultado['message']}")
                    # Registra log de skip (sem alterações)
                    database.registrar_log(
                        tipo="sync",
                        categoria="Sincronização",
                        status="info",
                        mensagem="Sincronização ignorada (sem alterações)",
                        detalhes=resultado.get('message', ''),
                        origem="frontend_sync"
                    )
                else:
                    st.error(f"❌ Erro na sincronização: {resultado['message']}")
                    # Envia notificação WhatsApp de erro se configurado
                    _enviar_notificacao_sync(resultado, database)
                    # Registra log de erro
                    database.registrar_log(
                        tipo="sync",
                        categoria="Sincronização",
                        status="erro",
                        mensagem=f"Falha na sincronização manual",
                        detalhes=resultado.get('message', ''),
                        origem="frontend_sync"
                    )
                    
            except Exception as e:
                st.error(f"❌ Erro na sincronização: {e}")
                # Envia notificação WhatsApp de erro
                _enviar_notificacao_sync({"status": "error", "message": str(e)}, database)
                # Registra log de exceção
                database.registrar_log(
                    tipo="sync",
                    categoria="Sincronização",
                    status="erro",
                    mensagem=f"Exceção na sincronização: {str(e)}",
                    origem="frontend_sync"
                )
    
    st.divider()
    
    # Informações
    st.info("""
    **ℹ️ Sobre a sincronização:**
    
    1. O sistema baixa a planilha do Google Sheets
    2. Verifica se houve alterações (via hash MD5)
    3. Se houver alterações, processa e salva no banco local
    4. Os dados ficam disponíveis instantaneamente no dashboard
    
    **⏰ Sincronização automática:**
    - Configure o horário no arquivo `.env` (SYNC_HOUR e SYNC_MINUTE)
    - Execute `python -m scheduler.jobs` para rodar o daemon
    """)
    
    # Configurações atuais
    with st.expander("⚙️ Configurações atuais"):
        st.code(f"""
GOOGLE_SHEETS_URL: {settings.GOOGLE_SHEETS_URL[:50]}...
SYNC_HOUR: {settings.SYNC_HOUR}
SYNC_MINUTE: {settings.SYNC_MINUTE}
SYNC_ENABLED: {settings.SYNC_ENABLED}
CACHE_MINUTES: {settings.CACHE_MINUTES}
DATABASE_PATH: {settings.DATABASE_PATH}
        """)

