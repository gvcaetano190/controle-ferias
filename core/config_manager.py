"""
Gerenciador de configurações.

Permite ler e salvar configurações no arquivo .env
de forma segura e persistente.
"""

from pathlib import Path
from typing import Dict, Optional
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Não importa settings diretamente para evitar dependência circular
# Os valores padrão são definidos inline


class ConfigManager:
    """Gerencia leitura e escrita de configurações no .env"""
    
    def __init__(self, env_file: Path = None):
        if env_file is None:
            # Usa o caminho do arquivo para encontrar o root
            root_dir = Path(__file__).parent.parent
            env_file = root_dir / ".env"
        self.env_file = env_file
        if not self.env_file.exists():
            self._criar_env_padrao()
    
    def _criar_env_padrao(self):
        """Cria arquivo .env com valores padrão se não existir."""
        conteudo = """# Configurações do Sistema de Controle de Férias

# Google Sheets
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/1oIgONGE3W7E1sFFNWun3bUY6Ys3JVSK1/edit

# Sincronização
SYNC_HOUR=6
SYNC_MINUTE=0
SYNC_ENABLED=true
CACHE_MINUTES=60

# Evolution API (desabilitado por padrão)
EVOLUTION_ENABLED=false
"""
        self.env_file.write_text(conteudo)
    
    def ler_config(self) -> Dict[str, str]:
        """Lê todas as configurações do .env."""
        config = {}
        
        if not self.env_file.exists():
            return config
        
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                # Ignora comentários e linhas vazias
                if linha and not linha.startswith('#') and '=' in linha:
                    partes = linha.split('=', 1)
                    chave = partes[0].strip()
                    valor = partes[1].strip().strip('"').strip("'")
                    config[chave] = valor
        
        return config
    
    def salvar_config(self, novas_config: Dict[str, str]) -> bool:
        """
        Salva configurações no .env.
        
        Args:
            novas_config: Dicionário com chave=valor das novas configurações
            
        Returns:
            True se salvou com sucesso
        """
        try:
            # Lê configurações existentes
            config_atual = self.ler_config()
            
            # Atualiza com novas configurações
            config_atual.update(novas_config)
            
            # Valores padrão
            defaults = {
                'GOOGLE_SHEETS_URL': config_atual.get('GOOGLE_SHEETS_URL', 'https://docs.google.com/spreadsheets/d/1oIgONGE3W7E1sFFNWun3bUY6Ys3JVSK1/edit'),
                'SYNC_HOUR': config_atual.get('SYNC_HOUR', '6'),
                'SYNC_MINUTE': config_atual.get('SYNC_MINUTE', '0'),
                'SYNC_ENABLED': config_atual.get('SYNC_ENABLED', 'true'),
                'CACHE_MINUTES': config_atual.get('CACHE_MINUTES', '60'),
                'EVOLUTION_ENABLED': config_atual.get('EVOLUTION_ENABLED', 'false'),
                'NOTIFY_ON_SYNC': config_atual.get('NOTIFY_ON_SYNC', 'false'),
                'NOTIFY_FERIAS_DIAS_ANTES': config_atual.get('NOTIFY_FERIAS_DIAS_ANTES', '1'),
                
                # OneTimeSecret
                'ONETIMESECRET_EMAIL': config_atual.get('ONETIMESECRET_EMAIL', 'gvcaetano190@gmail.com'),
                'ONETIMESECRET_API_KEY': config_atual.get('ONETIMESECRET_API_KEY', '5a19ff2da5a9dac1391971611b9a021d6c3aade8'),
                'ONETIMESECRET_ENABLED': config_atual.get('ONETIMESECRET_ENABLED', 'true'),
                'API_HOST': config_atual.get('API_HOST', '0.0.0.0'),
                'API_PORT': config_atual.get('API_PORT', '8000'),
            }
            
            # Preenche valores padrão para chaves conhecidas
            for key, default_value in defaults.items():
                if key not in config_atual:
                    config_atual[key] = default_value
            
            # Reescreve o arquivo de forma organizada
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write("# Configurações do Sistema de Controle de Férias\n\n")
                
                # Google Sheets
                f.write("# Google Sheets\n")
                f.write(f"GOOGLE_SHEETS_URL={config_atual.get('GOOGLE_SHEETS_URL', defaults['GOOGLE_SHEETS_URL'])}\n")
                f.write("\n")
                
                # Sincronização
                f.write("# Sincronização\n")
                f.write(f"SYNC_HOUR={config_atual.get('SYNC_HOUR', defaults['SYNC_HOUR'])}\n")
                f.write(f"SYNC_MINUTE={config_atual.get('SYNC_MINUTE', defaults['SYNC_MINUTE'])}\n")
                f.write(f"SYNC_ENABLED={config_atual.get('SYNC_ENABLED', defaults['SYNC_ENABLED'])}\n")
                f.write(f"CACHE_MINUTES={config_atual.get('CACHE_MINUTES', defaults['CACHE_MINUTES'])}\n")
                f.write("\n")
                
                # Evolution API
                f.write("# Evolution API (desabilitado por padrão)\n")
                f.write(f"EVOLUTION_ENABLED={config_atual.get('EVOLUTION_ENABLED', defaults['EVOLUTION_ENABLED'])}\n")
                if config_atual.get('EVOLUTION_API_URL'):
                    f.write(f"EVOLUTION_API_URL={config_atual.get('EVOLUTION_API_URL')}\n")
                if config_atual.get('EVOLUTION_NUMERO'):
                    f.write(f"EVOLUTION_NUMERO={config_atual.get('EVOLUTION_NUMERO')}\n")
                if config_atual.get('EVOLUTION_API_KEY'):
                    f.write(f"EVOLUTION_API_KEY={config_atual.get('EVOLUTION_API_KEY')}\n")
                f.write("\n")
                
                # Mensagens Automáticas
                if config_atual.get('MENSAGEM_MANHA_ENABLED') or config_atual.get('MENSAGEM_TARDE_ENABLED'):
                    f.write("# Mensagens Automáticas\n")
                    if config_atual.get('MENSAGEM_MANHA_ENABLED'):
                        f.write(f"MENSAGEM_MANHA_ENABLED={config_atual.get('MENSAGEM_MANHA_ENABLED', 'false')}\n")
                        f.write(f"MENSAGEM_MANHA_HOUR={config_atual.get('MENSAGEM_MANHA_HOUR', '8')}\n")
                        f.write(f"MENSAGEM_MANHA_MINUTE={config_atual.get('MENSAGEM_MANHA_MINUTE', '0')}\n")
                    if config_atual.get('MENSAGEM_TARDE_ENABLED'):
                        f.write(f"MENSAGEM_TARDE_ENABLED={config_atual.get('MENSAGEM_TARDE_ENABLED', 'false')}\n")
                        f.write(f"MENSAGEM_TARDE_HOUR={config_atual.get('MENSAGEM_TARDE_HOUR', '17')}\n")
                        f.write(f"MENSAGEM_TARDE_MINUTE={config_atual.get('MENSAGEM_TARDE_MINUTE', '0')}\n")
                    f.write("\n")
                
                # Sincronização com Notificação
                if config_atual.get('SYNC_NOTIF_ENABLED'):
                    f.write("# Sincronização com Notificação\n")
                    f.write(f"SYNC_NOTIF_ENABLED={config_atual.get('SYNC_NOTIF_ENABLED', 'false')}\n")
                    f.write(f"SYNC_NOTIF_HOUR={config_atual.get('SYNC_NOTIF_HOUR', '13')}\n")
                    f.write(f"SYNC_NOTIF_MINUTE={config_atual.get('SYNC_NOTIF_MINUTE', '0')}\n")
                    if config_atual.get('EVOLUTION_NUMERO_SYNC'):
                        f.write(f"EVOLUTION_NUMERO_SYNC={config_atual.get('EVOLUTION_NUMERO_SYNC')}\n")
                    f.write("\n")
                
                # Notificações
                f.write("# Notificações\n")
                f.write(f"NOTIFY_ON_SYNC={config_atual.get('NOTIFY_ON_SYNC', defaults['NOTIFY_ON_SYNC'])}\n")
                f.write(f"NOTIFY_FERIAS_DIAS_ANTES={config_atual.get('NOTIFY_FERIAS_DIAS_ANTES', defaults['NOTIFY_FERIAS_DIAS_ANTES'])}\n")
                f.write("\n")
                
                # OneTimeSecret
                f.write("# OneTimeSecret API\n")
                f.write(f"ONETIMESECRET_ENABLED={config_atual.get('ONETIMESECRET_ENABLED', defaults['ONETIMESECRET_ENABLED'])}\n")
                f.write(f"ONETIMESECRET_EMAIL={config_atual.get('ONETIMESECRET_EMAIL', defaults['ONETIMESECRET_EMAIL'])}\n")
                f.write(f"ONETIMESECRET_API_KEY={config_atual.get('ONETIMESECRET_API_KEY', defaults['ONETIMESECRET_API_KEY'])}\n")
                f.write("\n")
                
                # Kanbanize
                f.write("# Kanbanize API\n")
                f.write(f"KANBANIZE_ENABLED={config_atual.get('KANBANIZE_ENABLED', 'false')}\n")
                if config_atual.get('KANBANIZE_BASE_URL'):
                    f.write(f"KANBANIZE_BASE_URL={config_atual.get('KANBANIZE_BASE_URL')}\n")
                if config_atual.get('KANBANIZE_API_KEY'):
                    f.write(f"KANBANIZE_API_KEY={config_atual.get('KANBANIZE_API_KEY')}\n")
                if config_atual.get('KANBANIZE_DEFAULT_BOARD_ID'):
                    f.write(f"KANBANIZE_DEFAULT_BOARD_ID={config_atual.get('KANBANIZE_DEFAULT_BOARD_ID', '0')}\n")
                
                # Kanbanize Sync
                if 'KANBANIZE_SYNC_ENABLED' in config_atual:
                    f.write(f"KANBANIZE_SYNC_ENABLED={config_atual.get('KANBANIZE_SYNC_ENABLED', 'false')}\n")
                    f.write(f"KANBANIZE_SYNC_09H30_ENABLED={config_atual.get('KANBANIZE_SYNC_09H30_ENABLED', 'false')}\n")
                    f.write(f"KANBANIZE_SYNC_18H00_ENABLED={config_atual.get('KANBANIZE_SYNC_18H00_ENABLED', 'false')}\n")

                f.write("\n")
                
                # FastAPI (futuro) - só escreve se diferentes do padrão
                if config_atual.get('API_HOST') != defaults['API_HOST'] or config_atual.get('API_PORT') != defaults['API_PORT']:
                    f.write("# FastAPI (Futuro)\n")
                    f.write(f"API_HOST={config_atual.get('API_HOST', defaults['API_HOST'])}\n")
                    f.write(f"API_PORT={config_atual.get('API_PORT', defaults['API_PORT'])}\n")
            
            return True
            
        except Exception as e:
            # Loga o erro
            import traceback
            traceback.print_exc()
            # Re-raise para que o frontend possa capturar e mostrar a mensagem
            raise
    
    def atualizar_config(self, chave: str, valor: str) -> bool:
        """Atualiza uma única configuração."""
        return self.salvar_config({chave: valor})
    
    def obter_config(self, chave: str, valor_padrao: str = "") -> str:
        """Obtém valor de uma configuração."""
        config = self.ler_config()
        return config.get(chave, valor_padrao)


def salvar_configuracoes_sync(horario_hora: int, horario_minuto: int, 
                              habilitado: bool, cache_minutos: int) -> bool:
    """
    Função auxiliar para salvar configurações de sincronização.
    
    Returns:
        True se salvou com sucesso
    """
    manager = ConfigManager()
    
    config = {
        "SYNC_HOUR": str(horario_hora),
        "SYNC_MINUTE": str(horario_minuto),
        "SYNC_ENABLED": "true" if habilitado else "false",
        "CACHE_MINUTES": str(cache_minutos),
    }
    
    return manager.salvar_config(config)

