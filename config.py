# ============================================
# CONFIGURAÇÕES DO SISTEMA DE CONTROLE DE FÉRIAS
# ============================================

from pathlib import Path

# Caminho da planilha (para uso local)
PLANILHA_PATH = Path("data/planilha.xlsx")

# URL do Google Sheets (opcional - para usar Google Sheets)
GOOGLE_SHEETS_URL = ""  # Cole aqui a URL da sua planilha do Google Sheets

# Colunas da planilha (baseado na estrutura real)
COLUNAS = {
    "unidade": "F",           # Coluna A - Unidade (TIFFANY)
    "nome": "Nome",           # Coluna B - Nome do funcionário
    "motivo": "Motivo",       # Coluna C - Motivo (FÉRIAS)
    "saida": "Saída",         # Coluna D - Data de saída
    "retorno": "Retorno/Liberação",  # Coluna E - Data de retorno
    "gestor": "Gestor"        # Coluna F - Nome do gestor
}

# Formato de data na planilha
FORMATO_DATA_PLANILHA = "%d/%m/%Y"

# Configurações de exibição
SEPARADOR = "=" * 60
