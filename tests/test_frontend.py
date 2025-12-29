
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Mock para o Streamlit antes de importar o app
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

from frontend.app import pagina_gerar_senhas
from config.settings import Settings

class TestFrontendApp(unittest.TestCase):

    def setUp(self):
        # Limpa o cache de módulos para garantir re-importação limpa
        if 'frontend.app' in sys.modules:
            del sys.modules['frontend.app']
        if 'config.settings' in sys.modules:
            del sys.modules['config.settings']
        
        # Garante que as variáveis de ambiente não persistam entre testes
        self.original_env = os.environ.copy()

    def tearDown(self):
        # Restaura as variáveis de ambiente originais
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('frontend.app.settings')
    def test_pagina_gerar_senhas_attribute_error_fallback(self, mock_settings):
        # Simula o AttributeError fazendo o atributo não existir
        del mock_settings.ONETIMESECRET_ENABLED

        # Define uma variável de ambiente para o fallback
        os.environ['ONETIMESECRET_ENABLED'] = 'false'
        
        # Importa novamente para pegar o mock
        from frontend.app import pagina_gerar_senhas
        
        # Chama a função
        pagina_gerar_senhas()

        # Verifica se o st.warning foi chamado, indicando que o fallback funcionou
        mock_st.warning.assert_called_with("⚠️ OneTimeSecret está desabilitado. Habilite nas configurações.")

    def test_settings_reloading_with_new_attribute(self):
        # 1. Cria um .env de teste sem o atributo
        with open(ROOT_DIR / ".env_test", "w") as f:
            f.write("SYNC_HOUR=8\n")
        
        # Força o carregamento do .env_test
        os.environ['ONETIMESECRET_ENABLED'] = 'true' # Simula uma var de ambiente
        
        from config.settings import Settings
        settings = Settings()
        settings.carregar_env(ROOT_DIR / ".env_test")
        
        self.assertTrue(hasattr(settings, 'ONETIMESECRET_ENABLED'))
        self.assertEqual(settings.SYNC_HOUR, 8)
        
        # 2. Salva uma nova config no .env_test que desabilita o onetimesecret
        from core.config_manager import ConfigManager
        config_manager = ConfigManager(env_file=ROOT_DIR / ".env_test")
        config_manager.salvar_config({"ONETIMESECRET_ENABLED": "false", "SYNC_HOUR": "10"})
        
        # 3. Recarrega as configurações e verifica
        settings.carregar_env(ROOT_DIR / ".env_test")
        
        self.assertFalse(settings.ONETIMESECRET_ENABLED)
        self.assertEqual(settings.SYNC_HOUR, 10)

        # Limpa o arquivo de teste
        (ROOT_DIR / ".env_test").unlink()

if __name__ == '__main__':
    unittest.main()
