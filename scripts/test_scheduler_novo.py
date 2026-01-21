#!/usr/bin/env python3
"""
Teste completo do novo sistema de scheduler com notificação.

Executa validações de:
1. Carregamento de configurações
2. Inicialização do scheduler
3. Jobs agendados
4. Integração com Evolution API
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from scheduler.jobs import iniciar_scheduler, parar_scheduler
import time

def test_config_loading():
    """Testa se as configurações carregam corretamente."""
    print("\n" + "="*70)
    print("📋 TESTE 1: Carregamento de Configurações")
    print("="*70)
    
    try:
        # Configurações gerais
        assert settings.SYNC_ENABLED == True, "SYNC_ENABLED deve estar True"
        assert settings.SYNC_HOUR == 8, "SYNC_HOUR deve ser 8"
        assert settings.SYNC_MINUTE == 15, "SYNC_MINUTE deve ser 15"
        print("   ✅ Sincronização: 08:15")
        
        # Configurações novas
        assert settings.SYNC_NOTIF_ENABLED == True, "SYNC_NOTIF_ENABLED deve estar True"
        assert settings.SYNC_NOTIF_HOUR == 13, "SYNC_NOTIF_HOUR deve ser 13"
        assert settings.SYNC_NOTIF_MINUTE == 0, "SYNC_NOTIF_MINUTE deve ser 0"
        print("   ✅ Sincronização + Notificação: 13:00")
        
        # Mensagens
        assert settings.MENSAGEM_MANHA_ENABLED == True, "Mensagem matutina deve estar habilitada"
        assert settings.MENSAGEM_MANHA_HOUR == 9, "MENSAGEM_MANHA_HOUR deve ser 9"
        assert settings.MENSAGEM_MANHA_MINUTE == 0, "MENSAGEM_MANHA_MINUTE deve ser 0"
        print("   ✅ Mensagem Matutina: 09:00")
        
        assert settings.MENSAGEM_TARDE_ENABLED == True, "Mensagem vespertina deve estar habilitada"
        assert settings.MENSAGEM_TARDE_HOUR == 18, "MENSAGEM_TARDE_HOUR deve ser 18"
        assert settings.MENSAGEM_TARDE_MINUTE == 0, "MENSAGEM_TARDE_MINUTE deve ser 0"
        print("   ✅ Mensagem Vespertina: 18:00")
        
        # Evolution API
        assert settings.EVOLUTION_ENABLED == True, "Evolution API deve estar habilitada"
        assert settings.EVOLUTION_NUMERO_SYNC != "", "EVOLUTION_NUMERO_SYNC deve estar configurado"
        print(f"   ✅ Evolution API: Número principal + alternativo")
        
        print("\n✅ TESTE 1 PASSOU: Todas as configurações carregadas corretamente!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TESTE 1 FALHOU: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TESTE 1 ERRO: {e}")
        return False

def test_scheduler_startup():
    """Testa se o scheduler inicia corretamente."""
    print("\n" + "="*70)
    print("📋 TESTE 2: Inicialização do Scheduler")
    print("="*70)
    
    try:
        # Inicia scheduler
        resultado = iniciar_scheduler(executar_perdidos=False)
        
        if not resultado:
            print("\n❌ TESTE 2 FALHOU: Scheduler não iniciou")
            return False
        
        print("   ✅ Scheduler iniciou com sucesso")
        
        # Aguarda um pouco
        time.sleep(1)
        
        # Para scheduler
        parar_scheduler()
        print("   ✅ Scheduler parou corretamente")
        
        print("\n✅ TESTE 2 PASSOU: Scheduler funciona corretamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ TESTE 2 ERRO: {e}")
        try:
            parar_scheduler()
        except:
            pass
        return False

def test_job_functions():
    """Testa se as funções dos jobs existem."""
    print("\n" + "="*70)
    print("📋 TESTE 3: Disponibilidade de Funções dos Jobs")
    print("="*70)
    
    try:
        from scheduler.jobs import (
            job_sincronizacao,
            job_sincronizacao_com_notificacao,
            job_mensagem_manha,
            job_mensagem_tarde
        )
        
        print("   ✅ job_sincronizacao")
        print("   ✅ job_sincronizacao_com_notificacao (NOVO)")
        print("   ✅ job_mensagem_manha")
        print("   ✅ job_mensagem_tarde")
        
        print("\n✅ TESTE 3 PASSOU: Todos os jobs disponíveis!")
        return True
        
    except ImportError as e:
        print(f"\n❌ TESTE 3 FALHOU: Função não encontrada - {e}")
        return False
    except Exception as e:
        print(f"\n❌ TESTE 3 ERRO: {e}")
        return False

def test_evolution_api():
    """Testa integração com Evolution API."""
    print("\n" + "="*70)
    print("📋 TESTE 4: Integração com Evolution API")
    print("="*70)
    
    try:
        from integrations.evolution_api import EvolutionAPI
        
        api = EvolutionAPI(
            url=settings.EVOLUTION_API_URL,
            numero=settings.EVOLUTION_NUMERO,
            api_key=settings.EVOLUTION_API_KEY
        )
        
        print(f"   ✅ API URL: {api.url}")
        print(f"   ✅ Número principal: {api.numero}")
        
        # Testa com número alternativo
        api_alt = EvolutionAPI(
            url=settings.EVOLUTION_API_URL,
            numero=settings.EVOLUTION_NUMERO_SYNC,
            api_key=settings.EVOLUTION_API_KEY
        )
        print(f"   ✅ Número alternativo: {api_alt.numero}")
        
        # Verifica método de enviar mensagem sync
        assert hasattr(api, 'enviar_mensagem_sync'), "Método enviar_mensagem_sync não encontrado"
        print("   ✅ Método enviar_mensagem_sync disponível")
        
        print("\n✅ TESTE 4 PASSOU: Evolution API funciona corretamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ TESTE 4 ERRO: {e}")
        return False

def run_all_tests():
    """Executa todos os testes."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "SUITE DE TESTES - SCHEDULER DUAL" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    
    resultados = {
        "Config": test_config_loading(),
        "Scheduler": test_scheduler_startup(),
        "Jobs": test_job_functions(),
        "Evolution": test_evolution_api(),
    }
    
    print("\n" + "="*70)
    print("📊 RESULTADO FINAL")
    print("="*70)
    
    for teste, resultado in resultados.items():
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"   {teste}: {status}")
    
    total = len(resultados)
    passou = sum(1 for r in resultados.values() if r)
    falhou = total - passou
    
    print("\n" + "-"*70)
    print(f"Total: {total} | Passou: {passou} ✅ | Falhou: {falhou} ❌")
    
    if falhou == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para Docker!")
        return True
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    sucesso = run_all_tests()
    sys.exit(0 if sucesso else 1)
