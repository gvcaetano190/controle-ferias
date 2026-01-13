"""
Integração Profissional com Kanbanize/Businessmap API v2.
Backend Seguro: Estrutura Sequencial + Busca de Cards Paralela.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import concurrent.futures

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class KanbanizeAPI:
    """Cliente API Businessmap/Kanbanize V2."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url_original = base_url.strip().rstrip('/').split('/api')[0]
        self.api_key = api_key.strip()
        
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        # Retry conservador e pool maior para concorrência
        retries = Retry(total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
        # Monta para http e https
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, timeout: int = 10) -> Dict:
        if not HAS_REQUESTS:
            return {"sucesso": False, "mensagem": "Instale 'requests'."}
        
        endpoint_clean = endpoint.lstrip('/')
        if not endpoint_clean.startswith('api/v2'):
            endpoint_clean = f"api/v2/{endpoint_clean}"
            
        url = f"{self.base_url_original}/{endpoint_clean}"
        
        try:
            response = self.session.request(method, url, params=params, timeout=timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    final_data = data.get('data', data)
                    
                    # Extract pagination from nested structure (API v2 format)
                    pagination = None
                    if isinstance(final_data, dict):
                        pagination = final_data.get('pagination')
                        if 'data' in final_data:
                            final_data = final_data['data']
                    
                    # Also check top-level pagination
                    if not pagination:
                        pagination = data.get('pagination')

                    return {"sucesso": True, "dados": final_data, "paginacao": pagination}
                except ValueError:
                    return {"sucesso": False, "mensagem": "Erro JSON", "dados": response.text}
            
            return {"sucesso": False, "mensagem": f"Erro {response.status_code}: {response.text}"}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro Conexão: {e}"}

    # --- ESTRUTURA (Sequencial e Rápida) ---
    def listar_workflows(self, board_id: int) -> Dict:
        # Timeout curto (4s)
        return self._make_request(f"boards/{board_id}/workflows", timeout=4)

    def listar_colunas(self, board_id: int) -> Dict:
        return self._make_request(f"boards/{board_id}/columns", timeout=4)

    # --- BUSCA DE CARDS ---
    def buscar_detalhe_unico(self, card_id: int):
        return self._make_request(f"cards/{card_id}", timeout=20)

    def buscar_historico_card(self, card_id: int) -> Dict:
        """Busca histórico de movimentação do card (quando entrou em cada coluna)."""
        return self._make_request(f"cards/{card_id}/history", timeout=20)

    def buscar_cards_simples(self, board_ids=None, workflow_ids=None, column_ids=None, page=1, per_page=100, fields=None):
        """Busca cards resumidos do board.
        
        Args:
            fields: campo(s) adicionais a incluir na resposta (ex: 'in_current_position_since')
        """
        params = {"page": page, "per_page": per_page}
        if board_ids: params["board_ids"] = ','.join(map(str, board_ids)) if isinstance(board_ids, list) else board_ids
        if workflow_ids: params["workflow_ids"] = ','.join(map(str, workflow_ids)) if isinstance(workflow_ids, list) else workflow_ids
        if column_ids: params["column_ids"] = ','.join(map(str, column_ids)) if isinstance(column_ids, list) else column_ids
        if fields: params["fields"] = fields

        return self._make_request("cards", params=params, timeout=15)

    def buscar_cards_completos_paralelo(self, board_ids: List[int], workflow_ids=None, column_ids=None, page=1, per_page=200, max_workers: int = 20, sem_detalhes: bool = False):
        """Busca cards com ou sem detalhes completos.

        Args:
            per_page: itens por página (padrão 200)
            max_workers: número máximo de threads para buscar detalhes (padrão 20)
            sem_detalhes: se True, pula detail calls e retorna apenas resumo com in_current_position_since
        """
        # Fast mode: pede campos essenciais + in_current_position_since
        if sem_detalhes:
            # Campos disponíveis no list endpoint: card_id, title, workflow_id, column_id, board_id, in_current_position_since, etc
            fields_param = "card_id,title,description,owner_user_id,color,board_id,workflow_id,column_id,position,created_at,last_modified,in_current_position_since"
        else:
            fields_param = None
            
        res_lista = self.buscar_cards_simples(board_ids, workflow_ids, column_ids, page, per_page, fields=fields_param)
        
        if not res_lista.get("sucesso"):
            return res_lista
            
        cards_resumo = res_lista.get("dados", [])
        if not cards_resumo or sem_detalhes:
            # Se sem_detalhes, retorna as summaries como estão
            return res_lista
            
        cards_detalhados = []
        # Max workers configurável
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.buscar_detalhe_unico, c['card_id']): c for c in cards_resumo}
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    if res.get("sucesso"):
                        cards_detalhados.append(res.get("dados"))
                    else:
                        cards_detalhados.append(futures[future])
                except Exception:
                    cards_detalhados.append(futures[future])
                    
        return {
            "sucesso": True,
            "dados": cards_detalhados,
            "paginacao": res_lista.get("paginacao")
        }