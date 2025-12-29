"""
Integração com OneTimeSecret API.

Gera links de senha únicos que expiram após serem visualizados uma vez.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

# Tenta importar requests
try:
    import requests
    from requests.auth import HTTPBasicAuth
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    # Cria mock para evitar erros
    class HTTPBasicAuth:
        def __init__(self, *args, **kwargs):
            pass


class OneTimeSecretAPI:
    """Cliente para OneTimeSecret API."""
    
    # Alterado para EU (Europa)
    BASE_URL = "https://eu.onetimesecret.com/api/v1"
    SECRET_URL_PREFIX = "https://eu.onetimesecret.com/secret/"
    
    def __init__(self, email: str, api_key: str):
        """
        Inicializa OneTimeSecret API.
        
        Args:
            email: Email cadastrado no OneTimeSecret
            api_key: Chave da API
        """
        self.email = email
        self.api_key = api_key
        self.auth = HTTPBasicAuth(email, api_key)
    
    def criar_senha(self, senha: str, ttl: int = 3600) -> Dict:
        """
        Cria um link de senha única.
        
        Args:
            senha: A senha a ser compartilhada
            ttl: Tempo de vida em segundos (padrão: 3600 = 1 hora)
            
        Returns:
            Dict com resultado: {
                "sucesso": bool,
                "link": str (URL completa),
                "secret_key": str,
                "mensagem": str
            }
        """
        if not HAS_REQUESTS:
            return {
                "sucesso": False,
                "mensagem": "requests não instalado. Use: pip install requests"
            }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/share",
                auth=self.auth,
                data={
                    "secret": senha,
                    "ttl": ttl
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                secret_key = data.get("secret_key", "")
                metadata_key = data.get("metadata_key", "")
                # Sempre usa nosso SECRET_URL_PREFIX (EU) ao invés do share_url da API
                link_completo = f"{self.SECRET_URL_PREFIX}{secret_key}"
                
                return {
                    "sucesso": True,
                    "link": link_completo,
                    "secret_key": secret_key,
                    "metadata_key": metadata_key,
                    "ttl": ttl,
                    "mensagem": "Senha criada com sucesso"
                }
            else:
                return {
                    "sucesso": False,
                    "mensagem": f"Erro HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "sucesso": False,
                "mensagem": "Erro de conexão: não foi possível conectar ao servidor"
            }
        except requests.exceptions.Timeout:
            return {
                "sucesso": False,
                "mensagem": "Timeout: servidor não respondeu a tempo"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro inesperado: {str(e)}"
            }
    
    def verificar_status(self, metadata_key: str, link_url: str = "") -> Dict:
        """
        Verifica o status do segredo sem queimá-lo (usa API v2).
        Detecta automaticamente se deve usar servidor EU ou Global baseado no link.
        """
        if not HAS_REQUESTS:
            return {"sucesso": False, "mensagem": "requests não instalado"}
            
        if not metadata_key:
            return {"sucesso": False, "mensagem": "metadata_key não fornecido"}
            
        # 1. Determina a Base URL correta (Global ou Europa)
        base_api = "https://onetimesecret.com/api/v2"
        if "eu.onetimesecret.com" in link_url:
            base_api = "https://eu.onetimesecret.com/api/v2"
            
        # 2. Monta a URL de metadados segura (v2)
        url_v2 = f"{base_api}/private/{metadata_key}"
        
        try:
            # 3. Usa GET (Seguro)
            response = requests.get(
                url_v2,
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                record = data.get("record", data) 
                
                # Obtém o estado do record
                state = record.get("state", "unknown")
                
                # Se o estado for 'received' ou houver campo 'received' (data), significa que foi visualizado
                # A API pode retornar 'received' como estado ou 'viewed' com data em 'received'
                if state == "received" or record.get("received"):
                    state = "viewed"
                
                return {
                    "sucesso": True,
                    "status": state, # 'new' ou 'viewed'
                    "visualizado_em": record.get("received", None),
                    "detalhes": record
                }
            elif response.status_code == 404:
                return {"sucesso": False, "mensagem": "Segredo não encontrado (pode ter expirado ou região errada)"}
            elif response.status_code == 401:
                return {"sucesso": False, "mensagem": "Não autorizado - verifique email e API key"}
            else:
                # Tenta obter mais informações do erro
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                except:
                    error_msg = response.text
                    
                return {
                    "sucesso": False, 
                    "mensagem": f"Erro API {response.status_code}: {error_msg}"
                }
        except requests.exceptions.ConnectionError:
            return {"sucesso": False, "mensagem": "Erro de conexão: não foi possível conectar ao servidor"}
        except requests.exceptions.Timeout:
            return {"sucesso": False, "mensagem": "Timeout: servidor não respondeu a tempo"}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro inesperado: {str(e)}"}
    
    def criar_multiplas_senhas(self, senha_base: str, quantidade: int, 
                               incrementar: bool = False, ttl: int = 3600) -> List[Dict]:
        """
        Cria múltiplas senhas.
        
        Args:
            senha_base: Senha base (ex: "123@teste")
            quantidade: Número de senhas para criar
            incrementar: Se True, incrementa número (123@teste, 123@teste1, etc)
            ttl: Tempo de vida em segundos
            
        Returns:
            Lista de resultados, cada um com:
            {
                "sucesso": bool,
                "senha": str,
                "link": str,
                "secret_key": str,
                "mensagem": str
            }
        """
        resultados = []
        
        for i in range(quantidade):
            # Determina a senha a ser usada
            if incrementar and i > 0:
                # Adiciona número ao final
                senha = f"{senha_base}{i}"
            else:
                senha = senha_base
            
            # Cria a senha
            resultado = self.criar_senha(senha, ttl)
            resultado["senha"] = senha
            resultado["numero"] = i + 1
            
            resultados.append(resultado)
            
            # Pequena pausa para não sobrecarregar a API
            import time
            time.sleep(0.5)
        
        return resultados
