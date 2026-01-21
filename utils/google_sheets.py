# ============================================
# UTILITÁRIOS: GOOGLE SHEETS
# Responsabilidade: Funções utilitárias para Google Sheets
# ============================================

import re
from typing import Optional


def extrair_sheet_id(url: str) -> Optional[str]:
    """
    Extrai o ID da planilha de uma URL do Google Sheets.
    
    Suporta múltiplos formatos de URL:
    - https://docs.google.com/spreadsheets/d/SHEET_ID/edit
    - https://docs.google.com/spreadsheets/d/SHEET_ID
    - URLs com parâmetro ?id=SHEET_ID
    
    Args:
        url: URL do Google Sheets
        
    Returns:
        ID da planilha ou None se não encontrado
        
    Example:
        >>> extrair_sheet_id("https://docs.google.com/spreadsheets/d/abc123/edit")
        'abc123'
    """
    if not url:
        return None
    
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def construir_url_exportacao(sheet_id: str, formato: str = "xlsx", gid: Optional[str] = None) -> str:
    """
    Constrói URL de exportação para Google Sheets.
    
    Args:
        sheet_id: ID da planilha
        formato: Formato de exportação (xlsx, csv, pdf, etc.)
        gid: ID numérico da aba (opcional)
        
    Returns:
        URL de exportação
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format={formato}"
    
    if gid:
        url += f"&gid={gid}"
    
    return url
