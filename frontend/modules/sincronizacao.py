"""
Página de Sincronização.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from datetime import datetime

from config.settings import settings
from core.sync_manager import SyncManager


def render(database):
    """Renderiza a página de sincronização."""
    st.header("🔄 Sincronização de Dados")
    
    last_sync = database.buscar_ultimo_sync()
    
    if last_sync:
        sync_at = last_sync.get("sync_at", "")
        try:
            # Tenta diferentes formatos de timestamp
            sync_time = None
            if sync_at:
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
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📅 Última Sync", sync_time.strftime('%d/%m/%Y %H:%M'))
                with col2:
                    st.metric("📊 Registros", last_sync.get('total_registros', 0))
                with col3:
                    st.metric("📑 Abas", last_sync.get('total_abas', 0))
            else:
                st.warning(f"⚠️ Formato de data não reconhecido: {sync_at}")
        except Exception as e:
            st.warning(f"⚠️ Erro ao ler data: {e}")
    else:
        st.info("ℹ️ Nenhuma sincronização realizada ainda. Clique em 'Sincronizar Agora'.")
    
    st.divider()
    
    # Opções de sincronização
    col1, col2 = st.columns([3, 1])
    
    with col1:
        forcar = st.checkbox("Forçar download (ignora cache)", value=False)
    
    with col2:
        # Botão para verificar status do scheduler
        if st.button("📊 Status Scheduler", help="Verificar se o scheduler está rodando", use_container_width=True):
            with st.spinner("Verificando..."):
                import subprocess
                from pathlib import Path
                from datetime import datetime, timedelta
                
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
                
                proximos_horarios.append(("Verificação Férias", agora.replace(hour=9, minute=0, second=0, microsecond=0)))
                
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
                            mensagem += f"**📅 Iniciado em:** {lock_content}\n\n"
                            mensagem += f"**⏰ Horários Configurados:**\n"
                            if settings.SYNC_ENABLED:
                                mensagem += f"- 🔄 Sincronização: {sync_hour:02d}:{sync_minute:02d}\n"
                            mensagem += f"- 📅 Verificação Férias: 09:00\n"
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
                                mensagem += f"**PID(s):** {', '.join(pids)}\n\n"
                                mensagem += f"**⏰ Horários Configurados:**\n"
                                if settings.SYNC_ENABLED:
                                    mensagem += f"- 🔄 Sincronização: {sync_hour:02d}:{sync_minute:02d}\n"
                                mensagem += f"- 📅 Verificação Férias: 09:00\n"
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
                    st.success(f"✅ {resultado['message']}")
                    # Limpa caches e recarrega
                    st.cache_data.clear()
                    st.cache_resource.clear()
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
                    st.rerun()
                else:
                    st.error(f"❌ {resultado['message']}")
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
                st.error(f"❌ Erro: {e}")
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

