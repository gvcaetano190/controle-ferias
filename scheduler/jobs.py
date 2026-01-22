"""
Agendador de tarefas.

Gerencia a execução periódica de:
- Sincronização diária de dados
- Verificação de férias próximas
- Envio de notificações (futuro)

Uso:
    python -m scheduler.jobs          # Inicia daemon
    python -m scheduler.jobs --once   # Executa uma vez
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from core.sync_manager import SyncManager
from utils.formatadores import FORMATO_ISO, FORMATO_HORA, agora_formatado


def _eh_dia_util():
    """Verifica se hoje é dia útil (segunda a sexta)."""
    return datetime.now().weekday() < 5  # 0=segunda, 4=sexta, 5=sábado, 6=domingo


def _get_controle_file():
    """Retorna o caminho do arquivo de controle de jobs."""
    return Path(settings.DATA_DIR) / ".jobs_executados.txt"


def _verificar_job_executado(job_nome: str) -> bool:
    """
    Verifica se um job já foi executado hoje.
    
    Args:
        job_nome: Nome do job (ex: 'manha', 'tarde', 'sync', 'ferias')
    
    Returns:
        True se já foi executado hoje, False caso contrário
    """
    controle_file = _get_controle_file()
    hoje_str = agora_formatado(FORMATO_ISO)
    
    if not controle_file.exists():
        return False
    
    try:
        conteudo = controle_file.read_text().strip()
        if conteudo.startswith(hoje_str):
            partes = conteudo.split("|")
            if len(partes) > 1:
                jobs_executados = set(partes[1].split(","))
                return job_nome in jobs_executados
    except:
        pass
    
    return False


def _marcar_job_executado(job_nome: str):
    """
    Marca um job como executado hoje.
    
    Args:
        job_nome: Nome do job (ex: 'manha', 'tarde', 'sync', 'ferias')
    """
    controle_file = _get_controle_file()
    hoje_str = agora_formatado(FORMATO_ISO)
    
    # Lê jobs já executados hoje
    jobs_executados = set()
    if controle_file.exists():
        try:
            conteudo = controle_file.read_text().strip()
            if conteudo.startswith(hoje_str):
                partes = conteudo.split("|")
                if len(partes) > 1:
                    jobs_executados = set(partes[1].split(","))
        except:
            pass
    
    # Adiciona o novo job
    jobs_executados.add(job_nome)
    
    # Salva
    try:
        controle_file.write_text(f"{hoje_str}|{','.join(jobs_executados)}")
    except Exception as e:
        print(f"   ⚠️ Erro ao salvar controle de jobs: {e}")


def _notificar_kanbanize(EvolutionAPI, mensagem: str):
    """
    Envia notificação WhatsApp sobre sincronização Kanbanize.
    
    Args:
        EvolutionAPI: Classe da API Evolution (passada para evitar import circular)
        mensagem: Mensagem a ser enviada
    """
    if not settings.EVOLUTION_ENABLED or not settings.EVOLUTION_NUMERO_SYNC:
        return
    
    try:
        api_evolution = EvolutionAPI(
            url=settings.EVOLUTION_API_URL,
            numero=settings.EVOLUTION_NUMERO_SYNC,
            api_key=settings.EVOLUTION_API_KEY
        )
        resultado = api_evolution.enviar_mensagem(mensagem)
        
        if resultado["sucesso"]:
            print(f"   📱 Notificação enviada para {api_evolution.numero}")
        else:
            print(f"   ⚠️ Falha ao notificar: {resultado.get('mensagem')}")
    except Exception as e:
        print(f"   ⚠️ Erro ao enviar notificação: {e}")

# Tenta importar APScheduler, senão usa fallback simples
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    print("⚠️ APScheduler não instalado. Use: pip install apscheduler")

# Instância global do scheduler
_scheduler = None


def job_sincronizacao():
    """
    Job de sincronização diária (apenas dias úteis).
    Também envia notificação do resultado via WhatsApp.
    """
    if not _eh_dia_util():
        print(f"\n🔄 [{agora_formatado(FORMATO_HORA)}] Sincronização pulada (fim de semana)")
        return
    
    print(f"\n🔄 [{agora_formatado(FORMATO_HORA)}] Iniciando sincronização agendada...")
    
    try:
        sync = SyncManager()
        resultado = sync.sincronizar()
        
        if resultado["status"] == "success":
            print(f"   ✅ Sincronização concluída: {resultado['registros']} registros")
        
        elif resultado["status"] == "skipped":
            print(f"   ⏭️ Pulado: {resultado['message']}")
        
        else:
            print(f"   ❌ Erro: {resultado['message']}")
        
        # Envia notificação se Evolution API estiver habilitada
        if settings.EVOLUTION_ENABLED and settings.EVOLUTION_NUMERO_SYNC:
            try:
                from integrations.evolution_api import EvolutionAPI
                
                api = EvolutionAPI(
                    url=settings.EVOLUTION_API_URL,
                    numero=settings.EVOLUTION_NUMERO_SYNC,
                    api_key=settings.EVOLUTION_API_KEY
                )
                
                resultado_notif = api.enviar_mensagem_sync(resultado, origem="automatica")
                
                if resultado_notif["sucesso"]:
                    print(f"   📱 Notificação enviada para: {api.numero}")
                else:
                    print(f"   ⚠️ Falha ao enviar notificação: {resultado_notif['mensagem']}")
                    
            except Exception as e:
                print(f"   ⚠️ Erro ao enviar notificação: {e}")
            
    except Exception as e:
        print(f"   ❌ Erro na sincronização: {e}")


def job_sincronizacao_com_notificacao():
    """
    Job de sincronização com notificação (13:00).
    Verifica se já foi executada hoje para evitar duplicação.
    Se a sincronização das 08:15 já rodou, apenas envia notificação.
    Caso contrário, executa sincronização completa.
    """
    if not _eh_dia_util():
        print(f"\n🔔 [{agora_formatado(FORMATO_HORA)}] Sincronização + Notificação pulada (fim de semana)")
        return
    
    # Verifica se já foi executado hoje
    if _verificar_job_executado("sync_notif"):
        print(f"\n🔔 [{agora_formatado(FORMATO_HORA)}] Sincronização + Notificação já executada hoje, pulando...")
        return
    
    print(f"\n🔔 [{agora_formatado(FORMATO_HORA)}] Sincronização + Notificação (13:00)...")
    
    # Se a sincronização das 08:15 já rodou hoje, não precisa sincronizar de novo
    # Apenas verifica e envia notificação do status atual
    if _verificar_job_executado("sync"):
        print("   ℹ️ Sincronização das 08:15 já executada, enviando apenas notificação...")
        try:
            from integrations.evolution_api import EvolutionAPI
            from core.database import Database
            
            # Busca última sincronização
            db = Database()
            last_sync = db.buscar_ultimo_sync()
            
            if last_sync and settings.EVOLUTION_ENABLED and settings.EVOLUTION_NUMERO_SYNC:
                api = EvolutionAPI(
                    url=settings.EVOLUTION_API_URL,
                    numero=settings.EVOLUTION_NUMERO_SYNC,
                    api_key=settings.EVOLUTION_API_KEY
                )
                
                # Monta resultado para notificação
                resultado = {
                    "status": "success",
                    "registros": last_sync.get('total_registros', 0),
                    "message": f"Última sincronização: {last_sync.get('sync_at', 'N/A')}"
                }
                
                resultado_notif = api.enviar_mensagem_sync(resultado, origem="automatica_13h")
                
                if resultado_notif["sucesso"]:
                    print(f"   📱 Notificação enviada para: {api.numero}")
                else:
                    print(f"   ⚠️ Falha ao enviar notificação: {resultado_notif['mensagem']}")
            
            _marcar_job_executado("sync_notif")
        except Exception as e:
            print(f"   ❌ Erro ao enviar notificação: {e}")
    else:
        # Se não executou às 08:15, executa sincronização completa agora
        print("   ℹ️ Sincronização das 08:15 não foi executada, executando agora...")
        job_sincronizacao()
        _marcar_job_executado("sync_notif")


def job_verificar_ferias_proximas():
    """
    Verifica funcionários que vão sair de férias em breve.
    Apenas registra no log, NÃO envia mensagens (a mensagem matutina já cobre isso).
    """
    if not _eh_dia_util():
        print(f"\n📅 [{agora_formatado(FORMATO_HORA)}] Verificação de férias pulada (fim de semana)")
        return
    
    print(f"\n📅 [{agora_formatado(FORMATO_HORA)}] Verificando férias próximas...")
    
    try:
        from core.database import Database
        db = Database()
        
        dias = settings.NOTIFY_FERIAS_DIAS_ANTES
        proximos = db.buscar_proximos_a_sair(dias=dias)
        
        if not proximos:
            print(f"   ✅ Nenhum funcionário saindo nos próximos {dias} dia(s)")
            return
        
        print(f"   ⚠️ {len(proximos)} funcionário(s) saindo nos próximos {dias} dia(s)")
        for func in proximos:
            print(f"      - {func.get('nome', 'N/A')} (saída: {func.get('data_saida', 'N/A')})")
        
        # NÃO envia mensagens aqui - a mensagem matutina já cobre essa informação
        # Apenas registra no log de atividades
        db.registrar_log(
            tipo="verificacao",
            categoria="Férias",
            status="info",
            mensagem=f"{len(proximos)} funcionário(s) saindo nos próximos {dias} dia(s)",
            detalhes=", ".join([f.get('nome', 'N/A') for f in proximos]),
            origem="scheduler"
        )
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar férias: {e}")


def job_mensagem_manha():
    """Job para enviar mensagem matutina (apenas dias úteis)."""
    if not settings.EVOLUTION_ENABLED or not settings.MENSAGEM_MANHA_ENABLED:
        return
    
    if not _eh_dia_util():
        print(f"\n🌅 [{agora_formatado(FORMATO_HORA)}] Mensagem matutina pulada (fim de semana)")
        return
    
    # Verifica se já foi executado hoje (evita duplicação)
    if _verificar_job_executado("manha"):
        print(f"\n🌅 [{agora_formatado(FORMATO_HORA)}] Mensagem matutina já enviada hoje, pulando...")
        return
    
    print(f"\n🌅 [{agora_formatado(FORMATO_HORA)}] Enviando mensagem matutina...")
    
    try:
        from integrations.evolution_api import MensagensAutomaticas, EvolutionAPI
        api = EvolutionAPI(
            url=settings.EVOLUTION_API_URL,
            numero=settings.EVOLUTION_NUMERO,
            api_key=settings.EVOLUTION_API_KEY
        )
        mensagens = MensagensAutomaticas(api)
        resultado = mensagens.enviar_mensagem_manha()
        
        if resultado["sucesso"]:
            print("   ✅ Mensagem matutina enviada com sucesso")
            _marcar_job_executado("manha")
        else:
            print(f"   ❌ Erro ao enviar: {resultado['mensagem']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


def job_mensagem_tarde():
    """Job para enviar mensagem vespertina (apenas dias úteis)."""
    if not settings.EVOLUTION_ENABLED or not settings.MENSAGEM_TARDE_ENABLED:
        return
    
    if not _eh_dia_util():
        print(f"\n🌆 [{agora_formatado(FORMATO_HORA)}] Mensagem vespertina pulada (fim de semana)")
        return
    
    # Verifica se já foi executado hoje (evita duplicação)
    if _verificar_job_executado("tarde"):
        print(f"\n🌆 [{agora_formatado(FORMATO_HORA)}] Mensagem vespertina já enviada hoje, pulando...")
        return
    
    print(f"\n🌆 [{agora_formatado(FORMATO_HORA)}] Enviando mensagem vespertina...")
    
    try:
        from integrations.evolution_api import MensagensAutomaticas, EvolutionAPI
        api = EvolutionAPI(
            url=settings.EVOLUTION_API_URL,
            numero=settings.EVOLUTION_NUMERO,
            api_key=settings.EVOLUTION_API_KEY
        )
        mensagens = MensagensAutomaticas(api)
        resultado = mensagens.enviar_mensagem_tarde()
        
        if resultado["sucesso"]:
            print("   ✅ Mensagem vespertina enviada com sucesso")
            _marcar_job_executado("tarde")
        else:
            print(f"   ❌ Erro ao enviar: {resultado['mensagem']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


def job_kanbanize_sync_09h30():
    """Job para sincronizar cards do Kanbanize às 09:30 e enviar notificação."""
    if not settings.KANBANIZE_SYNC_ENABLED or not settings.KANBANIZE_SYNC_09H30_ENABLED:
        return
    
    if not _eh_dia_util():
        print(f"\n📋 [{agora_formatado(FORMATO_HORA)}] Sync Kanbanize 09:30 pulada (fim de semana)")
        return
    
    print(f"\n📋 [{agora_formatado(FORMATO_HORA)}] Sincronizando Kanbanize (09:30)...")
    
    from integrations.kanbanize import KanbanizeAPI
    from integrations.evolution_api import EvolutionAPI
    from core.database import Database
    
    db = Database()
    
    try:
        # Conecta na API e busca cards
        api = KanbanizeAPI(settings.KANBANIZE_BASE_URL, settings.KANBANIZE_API_KEY)
        board_id = int(settings.KANBANIZE_DEFAULT_BOARD_ID)
        
        resultado = api.buscar_cards_completos_paralelo(
            board_ids=[board_id],
            sem_detalhes=False  # Garante que os campos personalizados sejam buscados
        )
        
        if not resultado.get("sucesso"):
            erro_msg = resultado.get('mensagem', 'Erro desconhecido')
            print(f"   ❌ Erro na API Kanbanize: {erro_msg}")
            
            # Notifica erro via WhatsApp
            _notificar_kanbanize(EvolutionAPI, f"❌ Erro Kanbanize (09:30): {erro_msg}")
            
            db.registrar_log(
                tipo="kanbanize",
                categoria="Sincronização",
                status="erro",
                mensagem="Erro na API Kanbanize 09:30",
                detalhes=erro_msg,
                origem="scheduler"
            )
            return
        
        cards = resultado.get("dados", [])
        
        # Salva no banco
        cards_salvos = db.salvar_cards_kanbanize(cards, board_id=board_id)
        
        print(f"   ✅ {cards_salvos} cards sincronizados")
        
        # Envia mensagem de sucesso
        _notificar_kanbanize(EvolutionAPI, f"✅ Kanbanize sincronizado (09:30): {cards_salvos} cards atualizados")
        
        # Registra log
        db.registrar_log(
            tipo="kanbanize",
            categoria="Sincronização",
            status="sucesso",
            mensagem=f"Sincronização Kanbanize 09:30: {cards_salvos} cards",
            detalhes=f"Board ID: {board_id}",
            origem="scheduler"
        )
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        
        # Notifica erro via WhatsApp
        _notificar_kanbanize(EvolutionAPI, f"❌ Erro Kanbanize (09:30): {str(e)[:100]}")
        
        db.registrar_log(
            tipo="kanbanize",
            categoria="Sincronização",
            status="erro",
            mensagem="Erro na sincronização Kanbanize 09:30",
            detalhes=str(e),
            origem="scheduler"
        )


def job_kanbanize_sync_18h00():
    """Job para sincronizar cards do Kanbanize às 18:00 e enviar notificação."""
    if not settings.KANBANIZE_SYNC_ENABLED or not settings.KANBANIZE_SYNC_18H00_ENABLED:
        return
    
    if not _eh_dia_util():
        print(f"\n📋 [{agora_formatado(FORMATO_HORA)}] Sync Kanbanize 18:00 pulada (fim de semana)")
        return
    
    print(f"\n📋 [{agora_formatado(FORMATO_HORA)}] Sincronizando Kanbanize (18:00)...")
    
    from integrations.kanbanize import KanbanizeAPI
    from integrations.evolution_api import EvolutionAPI
    from core.database import Database
    
    db = Database()
    
    try:
        # Conecta na API e busca cards
        api = KanbanizeAPI(settings.KANBANIZE_BASE_URL, settings.KANBANIZE_API_KEY)
        board_id = int(settings.KANBANIZE_DEFAULT_BOARD_ID)
        
        resultado = api.buscar_cards_completos_paralelo(
            board_ids=[board_id],
            sem_detalhes=False  # Garante que os campos personalizados sejam buscados
        )
        
        if not resultado.get("sucesso"):
            erro_msg = resultado.get('mensagem', 'Erro desconhecido')
            print(f"   ❌ Erro na API Kanbanize: {erro_msg}")
            
            # Notifica erro via WhatsApp
            _notificar_kanbanize(EvolutionAPI, f"❌ Erro Kanbanize (18:00): {erro_msg}")
            
            db.registrar_log(
                tipo="kanbanize",
                categoria="Sincronização",
                status="erro",
                mensagem="Erro na API Kanbanize 18:00",
                detalhes=erro_msg,
                origem="scheduler"
            )
            return
        
        cards = resultado.get("dados", [])
        
        # Salva no banco
        cards_salvos = db.salvar_cards_kanbanize(cards, board_id=board_id)
        
        print(f"   ✅ {cards_salvos} cards sincronizados")
        
        # Envia mensagem de sucesso
        _notificar_kanbanize(EvolutionAPI, f"✅ Kanbanize sincronizado (18:00): {cards_salvos} cards atualizados")
        
        # Registra log
        db.registrar_log(
            tipo="kanbanize",
            categoria="Sincronização",
            status="sucesso",
            mensagem=f"Sincronização Kanbanize 18:00: {cards_salvos} cards",
            detalhes=f"Board ID: {board_id}",
            origem="scheduler"
        )
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        
        # Notifica erro via WhatsApp
        _notificar_kanbanize(EvolutionAPI, f"❌ Erro Kanbanize (18:00): {str(e)[:100]}")
        
        db.registrar_log(
            tipo="kanbanize",
            categoria="Sincronização",
            status="erro",
            mensagem="Erro na sincronização Kanbanize 18:00",
            detalhes=str(e),
            origem="scheduler"
        )


def _verificar_e_executar_jobs_perdidos():
    """
    Verifica se há jobs que deveriam ter sido executados hoje mas foram perdidos
    (por exemplo, se o scheduler iniciou depois do horário agendado).
    
    Usa arquivo de controle para evitar execução duplicada (funções _verificar_job_executado
    e _marcar_job_executado nos próprios jobs já fazem esse controle).
    """
    agora = datetime.now()
    hora_atual = agora.hour
    minuto_atual = agora.minute
    
    # Só executa em dias úteis
    if not _eh_dia_util():
        return
    
    print("\n🔍 Verificando jobs perdidos...")
    jobs_executados = []
    
    # Verifica sincronização (não tem controle de duplicação no job_sincronizacao, então verificamos aqui)
    if settings.SYNC_ENABLED and not _verificar_job_executado("sync"):
        hora_sync = settings.SYNC_HOUR
        min_sync = settings.SYNC_MINUTE
        if hora_atual > hora_sync or (hora_atual == hora_sync and minuto_atual > min_sync):
            print(f"   ⏰ Sincronização das {hora_sync:02d}:{min_sync:02d} foi perdida, executando agora...")
            job_sincronizacao()
            _marcar_job_executado("sync")
            jobs_executados.append("sync")
    
    # Verifica sincronização com notificação (13:00)
    if settings.SYNC_NOTIF_ENABLED and not _verificar_job_executado("sync_notif"):
        hora_sync_notif = settings.SYNC_NOTIF_HOUR
        min_sync_notif = settings.SYNC_NOTIF_MINUTE
        if hora_atual > hora_sync_notif or (hora_atual == hora_sync_notif and minuto_atual > min_sync_notif):
            print(f"   ⏰ Sincronização + Notificação das {hora_sync_notif:02d}:{min_sync_notif:02d} foi perdida, executando agora...")
            job_sincronizacao_com_notificacao()
            _marcar_job_executado("sync_notif")
            jobs_executados.append("sync_notif")
    
    # Verifica verificação de férias (09:00) - não envia mensagem, apenas verifica
    # NOTA: Removido desta verificação pois é apenas informativo e não crítico
    # if settings.EVOLUTION_ENABLED and not _verificar_job_executado("ferias"):
    #     if hora_atual > 9 or (hora_atual == 9 and minuto_atual > 0):
    #         print(f"   ⏰ Verificação de férias das 09:00 foi perdida, executando agora...")
    #         job_verificar_ferias_proximas()
    #         _marcar_job_executado("ferias")
    #         jobs_executados.append("ferias")
    
    # Verifica mensagem matutina (o job já tem controle de duplicação interno)
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_MANHA_ENABLED and not _verificar_job_executado("manha"):
        hora_manha = settings.MENSAGEM_MANHA_HOUR
        min_manha = settings.MENSAGEM_MANHA_MINUTE
        if hora_atual > hora_manha or (hora_atual == hora_manha and minuto_atual > min_manha):
            print(f"   ⏰ Mensagem matutina das {hora_manha:02d}:{min_manha:02d} foi perdida, executando agora...")
            job_mensagem_manha()  # O job já marca como executado se for bem-sucedido
            jobs_executados.append("manha")
    
    # Verifica mensagem vespertina (o job já tem controle de duplicação interno)
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_TARDE_ENABLED and not _verificar_job_executado("tarde"):
        hora_tarde = settings.MENSAGEM_TARDE_HOUR
        min_tarde = settings.MENSAGEM_TARDE_MINUTE
        if hora_atual > hora_tarde or (hora_atual == hora_tarde and minuto_atual > min_tarde):
            print(f"   ⏰ Mensagem vespertina das {hora_tarde:02d}:{min_tarde:02d} foi perdida, executando agora...")
            job_mensagem_tarde()  # O job já marca como executado se for bem-sucedido
            jobs_executados.append("tarde")
    
    if jobs_executados:
        print(f"   ✅ {len(jobs_executados)} job(s) perdido(s) processado(s): {', '.join(jobs_executados)}")
    else:
        print("   ✅ Nenhum job perdido")


def iniciar_scheduler(executar_perdidos: bool = True):
    """
    Inicia o agendador de tarefas.
    
    Args:
        executar_perdidos: Se True, executa jobs que foram perdidos (horário já passou hoje)
    
    Agenda:
        - Sincronização: diária no horário configurado (SYNC_HOUR:SYNC_MINUTE)
        - Verificação de Férias Próximas: diária às 09:00
        - Mensagem Matutina: no horário configurado (MENSAGEM_MANHA_HOUR:MINUTE)
        - Mensagem Vespertina: no horário configurado (MENSAGEM_TARDE_HOUR:MINUTE)
    """
    global _scheduler
    
    if not HAS_APSCHEDULER:
        print("❌ APScheduler não disponível. Instale com: pip install apscheduler")
        return False
    
    # Cria arquivo de lock para indicar que o scheduler está rodando
    try:
        lock_file = Path(settings.DATA_DIR) / ".scheduler.lock"
        lock_file.write_text(f"{datetime.now().isoformat()}\n")
    except:
        pass
    
    _scheduler = BackgroundScheduler()
    
    # Job 1: Sincronização diária (segunda a sexta)
    if settings.SYNC_ENABLED:
        _scheduler.add_job(
            job_sincronizacao,
            CronTrigger(hour=settings.SYNC_HOUR, minute=settings.SYNC_MINUTE, day_of_week='mon-fri'),
            id='sync_diaria',
            name='Sincronização Diária',
            replace_existing=True
        )
    
    # Job 1.5: Sincronização com notificação (segunda a sexta, 13:00)
    if settings.SYNC_NOTIF_ENABLED:
        _scheduler.add_job(
            job_sincronizacao_com_notificacao,
            CronTrigger(hour=settings.SYNC_NOTIF_HOUR, minute=settings.SYNC_NOTIF_MINUTE, day_of_week='mon-fri'),
            id='sync_notif',
            name='Sincronização + Notificação',
            replace_existing=True
        )
    
    # Job 2: Mensagem matutina (segunda a sexta)
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_MANHA_ENABLED:
        _scheduler.add_job(
            job_mensagem_manha,
            CronTrigger(hour=settings.MENSAGEM_MANHA_HOUR, minute=settings.MENSAGEM_MANHA_MINUTE, day_of_week='mon-fri'),
            id='mensagem_manha',
            name='Mensagem Matutina',
            replace_existing=True
        )
    
    # Job 3: Mensagem vespertina (segunda a sexta)
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_TARDE_ENABLED:
        _scheduler.add_job(
            job_mensagem_tarde,
            CronTrigger(hour=settings.MENSAGEM_TARDE_HOUR, minute=settings.MENSAGEM_TARDE_MINUTE, day_of_week='mon-fri'),
            id='mensagem_tarde',
            name='Mensagem Vespertina',
            replace_existing=True
        )
    
    # Job 4: Sincronização Kanbanize 09:30 (segunda a sexta)
    if settings.KANBANIZE_SYNC_ENABLED and settings.KANBANIZE_SYNC_09H30_ENABLED:
        _scheduler.add_job(
            job_kanbanize_sync_09h30,
            CronTrigger(hour=9, minute=30, day_of_week='mon-fri'),
            id='kanbanize_sync_09h30',
            name='Kanbanize Sync 09:30',
            replace_existing=True
        )
    
    # Job 5: Sincronização Kanbanize 18:00 (segunda a sexta)
    if settings.KANBANIZE_SYNC_ENABLED and settings.KANBANIZE_SYNC_18H00_ENABLED:
        _scheduler.add_job(
            job_kanbanize_sync_18h00,
            CronTrigger(hour=18, minute=0, day_of_week='mon-fri'),
            id='kanbanize_sync_18h00',
            name='Kanbanize Sync 18:00',
            replace_existing=True
        )
    
    _scheduler.start()
    
    print("=" * 60)
    print("📆 SCHEDULER INICIADO")
    print("=" * 60)
    if settings.SYNC_ENABLED:
        print(f"   🔄 Sincronização: seg-sex às {settings.SYNC_HOUR:02d}:{settings.SYNC_MINUTE:02d}")
    if settings.SYNC_NOTIF_ENABLED:
        print(f"   🔔 Sincronização + Notificação: seg-sex às {settings.SYNC_NOTIF_HOUR:02d}:{settings.SYNC_NOTIF_MINUTE:02d}")
    if settings.KANBANIZE_SYNC_ENABLED:
        if settings.KANBANIZE_SYNC_09H30_ENABLED:
            print(f"   📋 Kanbanize Sync 09:30: seg-sex às 09:30")
        if settings.KANBANIZE_SYNC_18H00_ENABLED:
            print(f"   📋 Kanbanize Sync 18:00: seg-sex às 18:00")
    if settings.EVOLUTION_ENABLED:
        if settings.MENSAGEM_MANHA_ENABLED:
            print(f"   🌅 Mensagem Matutina: seg-sex às {settings.MENSAGEM_MANHA_HOUR:02d}:{settings.MENSAGEM_MANHA_MINUTE:02d}")
        if settings.MENSAGEM_TARDE_ENABLED:
            print(f"   🌆 Mensagem Vespertina: seg-sex às {settings.MENSAGEM_TARDE_HOUR:02d}:{settings.MENSAGEM_TARDE_MINUTE:02d}")
    print("=" * 60)
    
    # Executa jobs perdidos se o scheduler iniciou depois do horário
    if executar_perdidos:
        _verificar_e_executar_jobs_perdidos()
    
    return True


def parar_scheduler():
    """Para o agendador."""
    global _scheduler
    
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        
        # Remove arquivo de lock
        try:
            lock_file = Path(settings.DATA_DIR) / ".scheduler.lock"
            if lock_file.exists():
                lock_file.unlink()
        except:
            pass
        
        print("⏹️ Scheduler parado")


def executar_agora():
    """Executa todos os jobs imediatamente (para testes)."""
    print("\n🚀 Executando jobs manualmente...")
    if settings.SYNC_ENABLED:
        job_sincronizacao()
    if settings.EVOLUTION_ENABLED:
        job_verificar_ferias_proximas()
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_MANHA_ENABLED:
        job_mensagem_manha()
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_TARDE_ENABLED:
        job_mensagem_tarde()


# ==================== CLI ====================

def main():
    """Execução via linha de comando."""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description='Scheduler de Tarefas')
    parser.add_argument('--once', action='store_true', 
                       help='Executa uma vez e sai')
    parser.add_argument('--sync', action='store_true',
                       help='Executa apenas sincronização')
    
    args = parser.parse_args()
    
    if args.sync:
        job_sincronizacao()
        return
    
    if args.once:
        executar_agora()
        return
    
    # Modo daemon
    if not iniciar_scheduler():
        return
    
    print("\n💡 Pressione Ctrl+C para parar\n")
    
    # Verifica periodicamente se há arquivo de reload
    reload_flag = Path(settings.DATA_DIR) / ".scheduler.reload"
    
    try:
        while True:
            time.sleep(60)
            
            # Verifica se foi criado arquivo de reload
            if reload_flag.exists():
                print("\n🔄 Detectado arquivo de reload, reiniciando scheduler...")
                
                try:
                    # Remove o arquivo de flag
                    reload_flag.unlink()
                    
                    # Para o scheduler atual
                    parar_scheduler()
                    
                    # Recarrega configurações
                    settings.carregar_env()
                    
                    # Reinicia o scheduler
                    time.sleep(1)
                    if iniciar_scheduler(executar_perdidos=False):
                        print("✅ Scheduler reiniciado com novas configurações!")
                    else:
                        print("❌ Falha ao reiniciar scheduler")
                        break
                except Exception as e:
                    print(f"❌ Erro ao reiniciar scheduler: {e}")
                    break
                    
    except KeyboardInterrupt:
        parar_scheduler()
        print("\n👋 Scheduler encerrado")


if __name__ == "__main__":
    main()

