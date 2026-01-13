"""
Validador de planilha do Google Sheets.

Testa se o link está acessível e se consegue baixar e processar a planilha.
"""

import re
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple
import tempfile

import openpyxl


def validar_url_google_sheets(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Valida se a URL do Google Sheets é válida e acessível.
    
    Args:
        url: URL do Google Sheets
        
    Returns:
        Tuple (sucesso, mensagem, sheet_id)
    """
    if not url or not url.strip():
        return False, "URL vazia", None
    
    # Extrai sheet ID
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
    ]
    
    sheet_id = None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            sheet_id = match.group(1)
            break
    
    if not sheet_id:
        return False, "URL inválida: não foi possível extrair o ID da planilha", None
    
    # Tenta baixar
    try:
        excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            urllib.request.urlretrieve(excel_url, tmp.name)
            tmp_path = Path(tmp.name)
            
            # Tenta abrir o arquivo
            try:
                wb = openpyxl.load_workbook(tmp_path, data_only=True)
                num_abas = len(wb.sheetnames)
                wb.close()
                
                # Remove arquivo temporário
                tmp_path.unlink()
                
                return True, f"✅ Link válido! Planilha acessível com {num_abas} aba(s)", sheet_id
                
            except Exception as e:
                tmp_path.unlink()
                return False, f"❌ Erro ao processar planilha: {str(e)}", sheet_id
                
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return False, "❌ Acesso negado: a planilha precisa ser pública (qualquer um com o link pode ver)", sheet_id
        elif e.code == 404:
            return False, "❌ Planilha não encontrada: verifique se o link está correto", sheet_id
        else:
            return False, f"❌ Erro HTTP {e.code}: {e.reason}", sheet_id
    except urllib.error.URLError as e:
        return False, f"❌ Erro de conexão: {str(e)}", sheet_id
    except Exception as e:
        return False, f"❌ Erro inesperado: {str(e)}", sheet_id


def testar_planilha_completa(url: str) -> Dict:
    """
    Testa a planilha completa: download, processamento e validação.
    
    Returns:
        Dicionário com resultado do teste
    """
    from core.sync_manager import SyncManager
    
    resultado = {
        "sucesso": False,
        "mensagem": "",
        "detalhes": {}
    }
    
    # Valida URL
    valido, msg, sheet_id = validar_url_google_sheets(url)
    if not valido:
        resultado["mensagem"] = msg
        return resultado
    
    resultado["detalhes"]["sheet_id"] = sheet_id
    resultado["detalhes"]["url_valida"] = True
    
    # Tenta baixar e processar
    try:
        sync = SyncManager()
        
        # Força download
        arquivo = sync.baixar_planilha(forcar=True)
        if not arquivo:
            resultado["mensagem"] = "❌ Erro ao baixar planilha"
            return resultado
        
        resultado["detalhes"]["arquivo_baixado"] = True
        resultado["detalhes"]["nome_arquivo"] = arquivo.name
        
        # Tenta processar
        dados = sync.processar_planilha()
        if not dados:
            resultado["mensagem"] = "⚠️ Planilha baixada, mas nenhum dado foi processado. Verifique o formato."
            return resultado
        
        resultado["sucesso"] = True
        resultado["mensagem"] = f"✅ Tudo OK! Planilha processada com sucesso: {len(dados)} funcionários em {len(sync.abas_processadas)} aba(s)"
        resultado["detalhes"]["total_funcionarios"] = len(dados)
        resultado["detalhes"]["total_abas"] = len(sync.abas_processadas)
        resultado["detalhes"]["abas"] = [a["nome"] for a in sync.abas_processadas[:10]]  # Primeiras 10
        
        return resultado
        
    except Exception as e:
        resultado["mensagem"] = f"❌ Erro ao processar: {str(e)}"
        return resultado









