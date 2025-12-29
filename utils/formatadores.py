# ============================================
# UTILITÁRIOS: FORMATADORES
# Responsabilidade: Formatação de datas e textos
# ============================================

from datetime import datetime
from typing import Optional


def formatar_data(data: datetime, formato: str = "%d/%m/%Y") -> str:
    """Formata datetime para string."""
    if data is None:
        return ""
    return data.strftime(formato)


def parse_data(texto: str, formatos: list = None) -> Optional[datetime]:
    """Converte string para datetime tentando múltiplos formatos."""
    if not texto or texto.strip() == "":
        return None
    
    if formatos is None:
        formatos = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]
    
    for fmt in formatos:
        try:
            return datetime.strptime(texto.strip(), fmt)
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
