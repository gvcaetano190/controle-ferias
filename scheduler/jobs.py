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


def _eh_dia_util():
    """Verifica se hoje é dia útil (segunda a sexta)."""
    return datetime.now().weekday() < 5  # 0=segunda, 4=sexta, 5=sábado, 6=domingo

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
    """Job de sincronização diária (apenas dias úteis)."""
    if not _eh_dia_util():
        print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Sincronização pulada (fim de semana)")
        return
    
    print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Iniciando sincronização agendada...")
    
    try:
        sync = SyncManager()
        resultado = sync.sincronizar()
        
        if resultado["status"] == "success":
            print(f"   ✅ Sincronização concluída: {resultado['registros']} registros")
            
            # Notifica se configurado
            if settings.NOTIFY_ON_SYNC and settings.EVOLUTION_ENABLED:
                from integrations.evolution_api import EvolutionAPI
                api = EvolutionAPI(
                    url=settings.EVOLUTION_API_URL,
                    numero=settings.EVOLUTION_NUMERO,
                    api_key=settings.EVOLUTION_API_KEY
                )
                resultado_notificacao = api.enviar_mensagem_sync(resultado)
                if resultado_notificacao["sucesso"]:
                    print("   📨 Notificação de sincronização enviada")
                else:
                    print(f"   ⚠️ Erro ao enviar notificação: {resultado_notificacao['mensagem']}")
        
        elif resultado["status"] == "skipped":
            print(f"   ⏭️ Pulado: {resultado['message']}")
            
            # Notifica mesmo quando pulado, se configurado
            if settings.NOTIFY_ON_SYNC and settings.EVOLUTION_ENABLED:
                from integrations.evolution_api import EvolutionAPI
                api = EvolutionAPI(
                    url=settings.EVOLUTION_API_URL,
                    numero=settings.EVOLUTION_NUMERO,
                    api_key=settings.EVOLUTION_API_KEY
                )
                api.enviar_mensagem_sync(resultado)
        
        else:
            print(f"   ❌ Erro: {resultado['message']}")
            
            # Notifica erro também, se configurado
            if settings.NOTIFY_ON_SYNC and settings.EVOLUTION_ENABLED:
                from integrations.evolution_api import EvolutionAPI
                api = EvolutionAPI(
                    url=settings.EVOLUTION_API_URL,
                    numero=settings.EVOLUTION_NUMERO,
                    api_key=settings.EVOLUTION_API_KEY
                )
                api.enviar_mensagem_sync(resultado)
            
    except Exception as e:
        print(f"   ❌ Erro na sincronização: {e}")


def job_verificar_ferias_proximas():
    """
    Verifica funcionários que vão sair de férias em breve.
    Envia notificações se configurado (apenas dias úteis).
    """
    if not _eh_dia_util():
        print(f"\n📅 [{datetime.now().strftime('%H:%M:%S')}] Verificação de férias pulada (fim de semana)")
        return
    
    print(f"\n📅 [{datetime.now().strftime('%H:%M:%S')}] Verificando férias próximas...")
    
    try:
        from core.database import Database
        db = Database()
        
        dias = settings.NOTIFY_FERIAS_DIAS_ANTES
        proximos = db.buscar_proximos_a_sair(dias=dias)
        
        if not proximos:
            print(f"   ✅ Nenhum funcionário saindo nos próximos {dias} dia(s)")
            return
        
        print(f"   ⚠️ {len(proximos)} funcionário(s) saindo nos próximos {dias} dia(s)")
        
        # Envia notificações se Evolution API estiver configurada
        if settings.EVOLUTION_ENABLED:
            from integrations.evolution_api import EvolutionAPI
            api = EvolutionAPI(
                url=settings.EVOLUTION_API_URL,
                numero=settings.EVOLUTION_NUMERO,
                api_key=settings.EVOLUTION_API_KEY
            )
            
            enviados = 0
            erros = 0
            for func in proximos:
                resultado = api.enviar_aviso_ferias(func)
                if resultado["sucesso"]:
                    enviados += 1
                else:
                    erros += 1
                    print(f"   ⚠️ Erro ao enviar aviso para {func.get('nome', 'N/A')}: {resultado['mensagem']}")
            
            if enviados > 0:
                print(f"   📨 {enviados} aviso(s) de férias enviado(s)")
            if erros > 0:
                print(f"   ❌ {erros} erro(s) ao enviar avisos")
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar férias: {e}")


def job_mensagem_manha():
    """Job para enviar mensagem matutina (apenas dias úteis)."""
    if not settings.EVOLUTION_ENABLED or not settings.MENSAGEM_MANHA_ENABLED:
        return
    
    if not _eh_dia_util():
        print(f"\n🌅 [{datetime.now().strftime('%H:%M:%S')}] Mensagem matutina pulada (fim de semana)")
        return
    
    print(f"\n🌅 [{datetime.now().strftime('%H:%M:%S')}] Enviando mensagem matutina...")
    
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
        else:
            print(f"   ❌ Erro ao enviar: {resultado['mensagem']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


def job_mensagem_tarde():
    """Job para enviar mensagem vespertina (apenas dias úteis)."""
    if not settings.EVOLUTION_ENABLED or not settings.MENSAGEM_TARDE_ENABLED:
        return
    
    if not _eh_dia_util():
        print(f"\n🌆 [{datetime.now().strftime('%H:%M:%S')}] Mensagem vespertina pulada (fim de semana)")
        return
    
    print(f"\n🌆 [{datetime.now().strftime('%H:%M:%S')}] Enviando mensagem vespertina...")
    
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
        else:
            print(f"   ❌ Erro ao enviar: {resultado['mensagem']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


def iniciar_scheduler():
    """
    Inicia o agendador de tarefas.
    
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
    
    _scheduler = BackgroundScheduler()
    
    # Job de sincronização diária (segunda a sexta)
    if settings.SYNC_ENABLED:
        _scheduler.add_job(
            job_sincronizacao,
            CronTrigger(hour=settings.SYNC_HOUR, minute=settings.SYNC_MINUTE, day_of_week='mon-fri'),
            id='sync_diaria',
            name='Sincronização Diária',
            replace_existing=True
        )
    
    # Job de verificação de férias próximas (segunda a sexta às 09:00)
    if settings.EVOLUTION_ENABLED:
        _scheduler.add_job(
            job_verificar_ferias_proximas,
            CronTrigger(hour=9, minute=0, day_of_week='mon-fri'),
            id='verificar_ferias_proximas',
            name='Verificação de Férias Próximas',
            replace_existing=True
        )
    
    # Job de mensagem matutina (segunda a sexta)
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_MANHA_ENABLED:
        _scheduler.add_job(
            job_mensagem_manha,
            CronTrigger(hour=settings.MENSAGEM_MANHA_HOUR, minute=settings.MENSAGEM_MANHA_MINUTE, day_of_week='mon-fri'),
            id='mensagem_manha',
            name='Mensagem Matutina',
            replace_existing=True
        )
    
    # Job de mensagem vespertina (segunda a sexta)
    if settings.EVOLUTION_ENABLED and settings.MENSAGEM_TARDE_ENABLED:
        _scheduler.add_job(
            job_mensagem_tarde,
            CronTrigger(hour=settings.MENSAGEM_TARDE_HOUR, minute=settings.MENSAGEM_TARDE_MINUTE, day_of_week='mon-fri'),
            id='mensagem_tarde',
            name='Mensagem Vespertina',
            replace_existing=True
        )
    
    _scheduler.start()
    
    print("=" * 60)
    print("📆 SCHEDULER INICIADO")
    print("=" * 60)
    if settings.SYNC_ENABLED:
        print(f"   🔄 Sincronização: seg-sex às {settings.SYNC_HOUR:02d}:{settings.SYNC_MINUTE:02d}")
    if settings.EVOLUTION_ENABLED:
        print(f"   📅 Verificação de Férias Próximas: seg-sex às 09:00")
        if settings.MENSAGEM_MANHA_ENABLED:
            print(f"   🌅 Mensagem Matutina: seg-sex às {settings.MENSAGEM_MANHA_HOUR:02d}:{settings.MENSAGEM_MANHA_MINUTE:02d}")
        if settings.MENSAGEM_TARDE_ENABLED:
            print(f"   🌆 Mensagem Vespertina: seg-sex às {settings.MENSAGEM_TARDE_HOUR:02d}:{settings.MENSAGEM_TARDE_MINUTE:02d}")
    print("=" * 60)
    
    return True


def parar_scheduler():
    """Para o agendador."""
    global _scheduler
    
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
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
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        parar_scheduler()
        print("\n👋 Scheduler encerrado")


if __name__ == "__main__":
    main()

