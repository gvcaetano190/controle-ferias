#!/usr/bin/env python3
# Script para gerar planilha de exemplo para testes

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Data de hoje e amanhã para testes
hoje = datetime.now()
amanha = hoje + timedelta(days=1)
ontem = hoje - timedelta(days=1)

# Formata datas
def fmt(data):
    return data.strftime("%d/%m/%Y")

# Dados de exemplo - DEZEMBRO 2024
dados_dezembro = {
    "F": ["TIFFANY"] * 10,
    "Nome": [
        "THIAGO DA SILVA MOREIRA",
        "ADRIANO PIRES FRANCISCO DE ALM",
        "ANDERSON DINIZ PEDROSO",
        "ADALBERTO DA SILVA FARIA",
        "VLADIMIR CICERO DA SILVA DOS S",
        "MARIA TESTE SAINDO HOJE",      # Sai hoje
        "JOAO TESTE VOLTA AMANHA",      # Volta amanhã
        "CARLOS TESTE AUSENTE",         # Ausente (saiu antes, volta depois)
        "ANA TESTE SAINDO HOJE 2",      # Sai hoje
        "PEDRO TESTE VOLTA AMANHA 2"    # Volta amanhã
    ],
    "Motivo": ["FÉRIAS"] * 10,
    "Saída": [
        "02/12/2024",
        "02/12/2024",
        "02/12/2024",
        "02/12/2024",
        "02/12/2024",
        fmt(hoje),           # Sai HOJE
        fmt(ontem - timedelta(days=10)),  # Saiu há 10 dias
        fmt(ontem - timedelta(days=5)),   # Saiu há 5 dias
        fmt(hoje),           # Sai HOJE
        fmt(ontem - timedelta(days=15))   # Saiu há 15 dias
    ],
    "Retorno/Liberação": [
        "21/12/2024",
        "21/12/2024",
        "31/12/2024",
        "02/12/2024",
        "21/12/2024",
        fmt(hoje + timedelta(days=15)),   # Volta em 15 dias
        fmt(amanha),                       # Volta AMANHÃ
        fmt(amanha + timedelta(days=5)),   # Volta em 5 dias
        fmt(hoje + timedelta(days=20)),   # Volta em 20 dias
        fmt(amanha)                        # Volta AMANHÃ
    ],
    "Gestor": [
        "PEDRO RODRIGUES DE ALBUQUERQUE",
        "EDGARD DE LUNA",
        "ELTON TAVARES DE LIMA",
        "CLAYTON MANFRIN DE LIMA",
        "EDSON PASSARELLI VALDOMIRO",
        "GESTOR TESTE 1",
        "GESTOR TESTE 2",
        "GESTOR TESTE 3",
        "GESTOR TESTE 4",
        "GESTOR TESTE 5"
    ]
}

# Dados de exemplo - JANEIRO 2025
dados_janeiro = {
    "F": ["TIFFANY"] * 5,
    "Nome": [
        "THAIS RAMOS MAGALHAES",
        "HANS ULRICH LENK",
        "ANDRESSA DE FREITAS SILVA",
        "VITORIA SINFRONIO DANTAS",
        "RUAN CARLO PEREIRA DO ESPIRITO"
    ],
    "Motivo": ["FÉRIAS"] * 5,
    "Saída": [
        "16/12/2024",
        "16/12/2024",
        "16/12/2024",
        "16/12/2024",
        "16/12/2024"
    ],
    "Retorno/Liberação": [
        "04/01/2025",
        "30/12/2024",
        "09/01/2025",
        "14/01/2025",
        "20/12/2024"
    ],
    "Gestor": [
        "ANA PAULA DE MELO",
        "HANS ULRICH LENK",
        "TAIS SANTOS SOUZA",
        "VINICIUS BEZERRA DA SILVA",
        "KATE KARLA FREGONESI RAMOS"
    ]
}

# Cria DataFrames
df_dezembro = pd.DataFrame(dados_dezembro)
df_janeiro = pd.DataFrame(dados_janeiro)

# Salva planilha com múltiplas abas
caminho = Path("data/planilha.xlsx")
with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
    df_dezembro.to_excel(writer, sheet_name='DEZEMBRO 2024', index=False)
    df_janeiro.to_excel(writer, sheet_name='JANEIRO 2025', index=False)

print(f"✅ Planilha criada em: {caminho}")
print(f"📅 Data de hoje: {fmt(hoje)}")
print(f"📅 Data de amanhã: {fmt(amanha)}")
print(f"\n📊 Dados inseridos para teste:")
print(f"   - 2 pessoas saindo HOJE")
print(f"   - 2 pessoas voltando AMANHÃ")
