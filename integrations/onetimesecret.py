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
                
                # Verifica se foi visualizado
                # O estado pode ser 'received', 'viewed', ou 'new'
                # O campo 'received' contém a data/hora quando foi visualizado (se existir e não for None/vazio)
                received_value = record.get("received")
                
                # Verifica se received_value é uma data válida (não None, não vazio, não "None" como string)
                has_received_date = False
                if received_value:
                    received_str = str(received_value).strip()
                    if received_str and received_str.lower() not in ("none", "null", ""):
                        # Verifica se parece ser uma data (contém números e caracteres de data)
                        if any(c.isdigit() for c in received_str):
                            has_received_date = True
                
                # Considera como visualizado apenas se:
                # 1. O estado for explicitamente 'received' ou 'viewed' E houver data de recebimento válida, OU
                # 2. O estado for 'viewed' (mesmo sem data, pois a API pode não retornar a data)
                # IMPORTANTE: 'new' nunca deve ser considerado como visualizado
                if state == "new":
                    # Se o estado é 'new', sempre mantém como 'new', mesmo se houver campo 'received'
                    # (pode ser um bug da API ou campo preenchido incorretamente)
                    final_state = "new"
                elif state in ("received", "viewed"):
                    # Se o estado é 'received' ou 'viewed', confirma se há data válida
                    if has_received_date:
                        final_state = "viewed"
                    else:
                        # Estado diz 'received'/'viewed' mas sem data - pode ser inconsistente
                        # Por segurança, considera como 'new' se não houver data válida
                        final_state = "new"
                else:
                    # Estado desconhecido - mantém o original
                    final_state = state
                
                return {
                    "sucesso": True,
                    "status": final_state, # 'new' ou 'viewed'
                    "visualizado_em": received_value if has_received_date else None,
                    "detalhes": record,
                    "debug": {
                        "state_original": state,
                        "has_received_date": has_received_date,
                        "received_value": received_value
                    }
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
