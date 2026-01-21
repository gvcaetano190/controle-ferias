# ============================================
# UTILITÁRIOS: FORMATADORES
# Responsabilidade: Formatação de datas e textos
# ============================================

from datetime import datetime
from typing import Optional, Union
import re

# ============================================
# CONSTANTES DE FORMATOS DE DATA
# ============================================

FORMATO_DATA_BR = "%d/%m/%Y"
FORMATO_DATA_HORA_BR = "%d/%m/%Y às %H:%M"
FORMATO_DATA_HORA_COMPLETO = "%d/%m/%Y às %H:%M:%S"
FORMATO_TIMESTAMP_ARQUIVO = "%Y%m%d_%H%M%S"
FORMATO_HORA = "%H:%M:%S"
FORMATO_ISO = "%Y-%m-%d"
FORMATO_ISO_DATETIME = "%Y-%m-%d %H:%M:%S"

# Formatos suportados para parse automático
FORMATOS_PARSE = [
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
]


def agora_formatado(formato: str = FORMATO_DATA_HORA_BR) -> str:
    """
    Retorna a data/hora atual formatada.
    
    Args:
        formato: Formato de saída (padrão: DD/MM/YYYY às HH:MM)
        
    Returns:
        String com data/hora formatada
    """
    return datetime.now().strftime(formato)


def formatar_data(
    data: Union[datetime, str, None], 
    formato: str = FORMATO_DATA_BR,
    formato_entrada: Optional[str] = None
) -> str:
    """
    Formata data para string - versão unificada.
    
    Aceita múltiplos tipos de entrada:
    - datetime: converte diretamente
    - str: tenta parsear automaticamente ou usa formato_entrada
    - None/vazio: retorna string vazia
    
    Args:
        data: Data a formatar (datetime, string ou None)
        formato: Formato de saída (padrão: DD/MM/YYYY)
        formato_entrada: Formato específico para parse de string (opcional)
        
    Returns:
        String formatada ou vazia se data inválida
        
    Examples:
        >>> formatar_data(datetime(2026, 1, 17))
        '17/01/2026'
        >>> formatar_data("2026-01-17")
        '17/01/2026'
        >>> formatar_data("17/01/2026")
        '17/01/2026'
    """
    if data is None:
        return ""
    
    # Se já é datetime, formata diretamente
    if isinstance(data, datetime):
        return data.strftime(formato)
    
    # Se é string, tenta converter
    if isinstance(data, str):
        data_str = str(data).strip()
        
        if not data_str or data_str == "-":
            return ""
        
        # Se já está no formato desejado DD/MM/YYYY, retorna
        if formato == FORMATO_DATA_BR and re.match(r'^\d{2}/\d{2}/\d{4}$', data_str):
            return data_str
        
        # Tenta parsear
        dt = parse_data(data_str, [formato_entrada] if formato_entrada else None)
        if dt:
            return dt.strftime(formato)
        
        # Fallback: retorna original
        return data_str
    
    # Tenta converter outros tipos (ex: pandas Timestamp)
    try:
        if hasattr(data, 'strftime'):
            return data.strftime(formato)
    except Exception:
        pass
    
    return str(data) if data else ""


def formatar_data_iso(data_str: str) -> str:
    """
    Formata data ISO (usada em APIs) para formato brasileiro.
    
    Útil para dados vindos de APIs que retornam formato ISO.
    
    Args:
        data_str: Data em formato ISO (ex: 2026-01-17T10:30:00Z)
        
    Returns:
        Data em formato DD/MM/YYYY
    """
    if not data_str:
        return ""
    
    try:
        # Remove timezone suffix e parseia
        if 'T' in str(data_str):
            dt = datetime.fromisoformat(data_str.replace('Z', '+00:00').replace('+00:00', ''))
        else:
            dt = datetime.strptime(str(data_str).split()[0], FORMATO_ISO)
        return dt.strftime(FORMATO_DATA_BR)
    except Exception:
        return str(data_str)


def parse_data(texto: str, formatos: Optional[list] = None) -> Optional[datetime]:
    """
    Converte string para datetime tentando múltiplos formatos.
    
    Args:
        texto: String com a data
        formatos: Lista de formatos a tentar (opcional, usa padrões)
        
    Returns:
        datetime ou None se não conseguir converter
    """
    if not texto or str(texto).strip() == "":
        return None
    
    texto = str(texto).strip()
    
    if formatos is None:
        formatos = FORMATOS_PARSE
    
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    
    return None


def formatar_nome(nome: str) -> str:
    """Formata nome para exibição (Title Case)."""
    if not nome:
        return ""
    return nome.strip().title()


def dias_entre_datas(data_inicio: datetime, data_fim: datetime) -> int:
    """Calcula dias entre duas datas."""
    if data_inicio is None or data_fim is None:
        return 0
    return (data_fim - data_inicio).days
