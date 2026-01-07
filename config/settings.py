"""
Configurações centralizadas do sistema.

Esta nova versão lê as configurações diretamente do arquivo .env para um
dicionário interno, evitando problemas de cache de variáveis de ambiente
que podem ocorrer em ambientes como o Streamlit.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent.parent


class Settings:
    """
    Mantém todas as configurações do sistema, lendo diretamente do .env
    para evitar problemas com o ambiente de execução.
    """
    _data: Dict[str, Any]

    def __init__(self):
        """
        Inicializa o objeto de configurações, carregando os valores padrão
        e, em seguida, sobrescrevendo com os valores do arquivo .env.
        """
        self._data = {}
        self._load_defaults()
        self.carregar_env()

    def _load_defaults(self):
        """Carrega os valores padrão no dicionário de configurações."""
        self._data.update({
            "GOOGLE_SHEETS_URL": "https://docs.google.com/spreadsheets/d/1oIgONGE3W7E1sFFNWun3bUY6Ys3JVSK1/edit",
            "SYNC_HOUR": "6",
            "SYNC_MINUTE": "0",
            "SYNC_ENABLED": "true",
            "CACHE_MINUTES": "60",
            "EVOLUTION_API_URL": "",
            "EVOLUTION_NUMERO": "",
            "EVOLUTION_API_KEY": "",
            "EVOLUTION_ENABLED": "false",
            "ONETIMESECRET_EMAIL": "gvcaetano190@gmail.com",
            "ONETIMESECRET_API_KEY": "5a19ff2da5a9dac1391971611b9a021d6c3aade8",
            "ONETIMESECRET_ENABLED": "true",
            "MENSAGEM_MANHA_HOUR": "8",
            "MENSAGEM_MANHA_MINUTE": "0",
            "MENSAGEM_TARDE_HOUR": "17",
            "MENSAGEM_TARDE_MINUTE": "0",
            "MENSAGEM_MANHA_ENABLED": "false",
            "MENSAGEM_TARDE_ENABLED": "false",
            "NOTIFY_ON_SYNC": "false",
            "NOTIFY_FERIAS_DIAS_ANTES": "1",
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000",
            "SISTEMAS_ACESSO": ["AD PRIN", "VPN", "Gmail", "Admin", "Metrics", "TOTVS"],
            # Padrões que indicam que a pessoa NÃO TEM acesso à ferramenta (será mapeado para "NA")
            "PADROES_SEM_ACESSO": "N/P,N\\A,NA,N/A,NP,-,NB"
        })

    def carregar_env(self, env_file: Path = None):
        """
        Carrega/recarrega variáveis de um arquivo .env diretamente no dicionário interno.
        """
        if env_file is None:
            env_file = ROOT_DIR / ".env"
        
        # Não recarrega os padrões aqui para permitir que o .env seja a única fonte da verdade após a carga inicial
        if not env_file.exists():
            return
        
        with open(env_file, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith('#') and '=' in linha:
                    chave, valor = linha.split('=', 1)
                    self._data[chave.strip()] = valor.strip().strip('"').strip("'")

    def __getattr__(self, name: str) -> Any:
        """
        Permite acesso aos valores como atributos, com conversão de tipo no momento do acesso.
        Isso garante que os tipos corretos (bool, int) sejam retornados.
        """
        # Atributos de diretório são computados e não estão no .env
        if name == 'ROOT_DIR': return ROOT_DIR
        if name == 'DATA_DIR': return ROOT_DIR / "data"
        if name == 'DOWNLOAD_DIR': return ROOT_DIR / "download"
        if name == 'CACHE_DIR': return ROOT_DIR / "data" / "cache"
        if name == 'DATABASE_PATH': return (ROOT_DIR / "data" / "database.sqlite")
        if name == 'HASH_FILE': return (ROOT_DIR / "data" / "cache" / ".last_hash")

        if name not in self._data:
            raise AttributeError(f"'Settings' object has no attribute '{name}'")

        value = self._data[name]

        # Conversão de tipo "Just-In-Time"
        bool_keys = [
            "SYNC_ENABLED", "EVOLUTION_ENABLED", "ONETIMESECRET_ENABLED", 
            "MENSAGEM_MANHA_ENABLED", "MENSAGEM_TARDE_ENABLED", "NOTIFY_ON_SYNC"
        ]
        if name in bool_keys:
            return str(value).lower() == 'true'

        int_keys = [
            "SYNC_HOUR", "SYNC_MINUTE", "CACHE_MINUTES", "MENSAGEM_MANHA_HOUR", 
            "MENSAGEM_MANHA_MINUTE", "MENSAGEM_TARDE_HOUR", "MENSAGEM_TARDE_MINUTE", 
            "NOTIFY_FERIAS_DIAS_ANTES", "API_PORT"
        ]
        if name in int_keys:
            try:
                return int(value)
            except (ValueError, TypeError):
                # Retorna 0 ou um padrão razoável se a conversão falhar
                return 0

        return value

# Instância global única que será usada em toda a aplicação.
settings = Settings()
