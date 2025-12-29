#!/usr/bin/env python3
"""
Script de VALIDAÇÃO - Extrai dados completos de funcionários para conferência.
"""

import sys
from pathlib import Path
import pandas as pd
import re

# Adiciona o diretório raiz ao path (subir um nível de tests/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.leitor_google_sheets import LeitorGoogleSheets
from datetime import datetime

# URL da planilha
URL = "https://docs.google.com/spreadsheets/d/1oIgONGE3W7E1sFFNWun3bUY6Ys3JVSK1/edit"

# Sistemas de acesso (colunas)
SISTEMAS = ["AD PRIN", "VPN", "Gmail", "Admin", "Metrics", "TOTVS"]


def corrigir_inversao_dia_mes(dt, data_saida=None):
    """
    Corrige datas que foram interpretadas com dia/mês invertidos.
    
    Detecta quando o Google Sheets interpretou DD/MM como MM/DD.
    Ex: 03/01/2026 (3 jan) foi lido como 01/03/2026 (1 mar)
    
    Critérios para inversão:
    1. O dia atual é <= 12 (poderia ser um mês válido)
    2. Se temos data_saida, o retorno deveria ser DEPOIS da saída
    3. Se dia=01 e mês>1, provavelmente está invertido
    """
    if not isinstance(dt, datetime):
        return dt
    
    dia = dt.day
    mes = dt.month
    ano = dt.year
    
    # Se o dia é > 12, não pode estar invertido (mês não pode ser > 12)
    if dia > 12:
        return dt
    
    # Cria a versão invertida (troca dia <-> mês)
    try:
        dt_invertido = datetime(ano, dia, mes)
    except ValueError:
        # Data inválida após inversão
        return dt
    
    # Heurística 1: Se temos data de saída, verifica qual faz mais sentido
    if data_saida:
        # Converte data_saida para datetime se for string
        if isinstance(data_saida, str):
            try:
                # Tenta formato DD/MM/YYYY
                data_saida = datetime.strptime(data_saida, '%d/%m/%Y')
            except:
                try:
                    data_saida = pd.to_datetime(data_saida)
                except:
                    data_saida = None
        
        if data_saida:
            # Se a data original é ANTES da saída, está errado
            # Se a data invertida é DEPOIS da saída, provavelmente está certo
            if dt < data_saida and dt_invertido > data_saida:
                return dt_invertido
            # Se ambas estão depois, usa a mais próxima (mais provável para férias)
            if dt > data_saida and dt_invertido > data_saida:
                # Férias geralmente duram de 10 a 30 dias
                diff_original = (dt - data_saida).days
                diff_invertido = (dt_invertido - data_saida).days
                # Se a original dá mais de 60 dias e a invertida dá menos de 45, inverte
                if diff_original > 60 and diff_invertido < 45:
                    return dt_invertido
    
    # Heurística 2: Se dia=01 e mês > 1, provavelmente está invertido
    # Porque é mais comum retornar no dia X do mês 01 (janeiro)
    if dia == 1 and mes > 1 and mes <= 12:
        return dt_invertido
    
    return dt


def formatar_data(valor, data_saida_ref=None):
    """
    Formata data para DD/MM/YYYY (formato brasileiro).
    Lida com diferentes formatos de entrada.
    Corrige inversão dia/mês quando detectada.
    
    Args:
        valor: Valor da data (string, datetime, etc)
        data_saida_ref: Data de saída para referência (ajuda a detectar inversão)
    """
    if pd.isna(valor) or str(valor).strip() == "" or str(valor).strip() == "-":
        return ""
    
    # Se já é datetime, aplica correção de inversão
    if isinstance(valor, datetime):
        valor_corrigido = corrigir_inversao_dia_mes(valor, data_saida_ref)
        return valor_corrigido.strftime('%d/%m/%Y')
    
    valor_str = str(valor).strip()
    
    # Se já está no formato DD/MM/YYYY, retorna como está
    if re.match(r'^\d{2}/\d{2}/\d{4}$', valor_str):
        return valor_str
    
    # Se está no formato datetime do pandas (YYYY-MM-DD HH:MM:SS)
    if re.match(r'^\d{4}-\d{2}-\d{2}', valor_str):
        try:
            # Parse como YYYY-MM-DD
            dt = pd.to_datetime(valor_str)
            # Aplica correção de inversão
            dt_corrigido = corrigir_inversao_dia_mes(dt, data_saida_ref)
            return dt_corrigido.strftime('%d/%m/%Y')
        except:
            pass
    
    # Tenta outros formatos
    formatos = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
    ]
    
    for fmt in formatos:
        try:
            dt = datetime.strptime(valor_str.split()[0], fmt.split()[0])
            return dt.strftime('%d/%m/%Y')
        except:
            continue
    
    # Se não conseguiu parsear, retorna o original
    return valor_str


def mapear_status(valor):
    """Mapeia valor da célula para status padronizado."""
    if pd.isna(valor) or str(valor).strip() == "":
        return "⬜ PENDENTE"
    
    valor = str(valor).upper().strip()
    
    if valor in ["BLOQUEADO", "BLOQ"]:
        return "🔴 BLOQUEADO"
    if valor in ["LIBERADO", "LIB"]:
        return "🟢 LIBERADO"
    if valor in ["N/P", "N\\A", "NA", "N/A", "NP", "-"]:
        return "⚪ N/A"
    
    # Se não reconheceu, mostra o valor original
    return f"❓ {valor}"


def extrair_funcionario_completo(row, colunas):
    """Extrai todos os dados de uma linha."""
    
    # Primeiro extrai a data de saída (como referência para corrigir retorno)
    data_saida_raw = row.iloc[3] if len(row) > 3 else None
    data_saida_str = formatar_data(data_saida_raw)
    
    # Agora extrai retorno usando saída como referência para correção
    data_retorno_raw = row.iloc[4] if len(row) > 4 else None
    data_retorno_str = formatar_data(data_retorno_raw, data_saida_ref=data_saida_str)
    
    # Dados básicos
    dados = {
        "unidade": str(row.iloc[0]).strip() if len(row) > 0 else "",
        "nome": str(row.iloc[1]).strip() if len(row) > 1 else "",
        "motivo": str(row.iloc[2]).strip() if len(row) > 2 else "",
        "saida": data_saida_str,
        "retorno": data_retorno_str,
        "gestor": "",
        "acessos": {}
    }
    
    # Limpa "nan" de strings
    for key in ["unidade", "nome", "motivo", "gestor"]:
        if dados[key].lower() == "nan":
            dados[key] = ""
    
    # Encontra coluna Gestor
    for i, col in enumerate(colunas):
        col_upper = str(col).upper()
        if "GESTOR" in col_upper:
            dados["gestor"] = str(row.iloc[i]) if len(row) > i else ""
            break
    
    # Encontra colunas de sistemas
    for sistema in SISTEMAS:
        for i, col in enumerate(colunas):
            col_upper = str(col).upper().strip()
            sistema_upper = sistema.upper().strip()
            
            if col_upper == sistema_upper or sistema_upper in col_upper:
                valor = row.iloc[i] if len(row) > i else ""
                dados["acessos"][sistema] = mapear_status(valor)
                break
        
        # Se não encontrou a coluna, marca como não encontrada
        if sistema not in dados["acessos"]:
            dados["acessos"][sistema] = "❌ COLUNA NÃO ENCONTRADA"
    
    return dados


def main():
    print("=" * 70)
    print("🔍 VALIDAÇÃO DE EXTRAÇÃO DE DADOS")
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    print("=" * 70)
    print()
    
    # 1. Baixar planilha
    print("📥 Baixando planilha do Google Sheets...")
    leitor = LeitorGoogleSheets(URL)
    
    try:
        dados = leitor.ler_todas_abas_via_excel(manter_arquivo=True)
    except Exception as e:
        print(f"❌ Erro ao baixar: {e}")
        return
    
    # 2. Encontrar aba DEZEMBRO 2025
    aba_dezembro = None
    for nome_aba in dados.keys():
        if "DEZEMBRO" in nome_aba.upper() and "2025" in nome_aba:
            aba_dezembro = nome_aba
            break
    
    if not aba_dezembro:
        print("❌ Aba DEZEMBRO 2025 não encontrada!")
        print(f"Abas disponíveis: {list(dados.keys())}")
        return
    
    print(f"✅ Aba encontrada: {aba_dezembro}")
    print()
    
    # 3. Pegar DataFrame da aba
    df = dados[aba_dezembro]
    colunas = list(df.columns)
    
    print("=" * 70)
    print("📋 ESTRUTURA DA ABA")
    print("=" * 70)
    print(f"Total de linhas: {len(df)}")
    print(f"Colunas encontradas ({len(colunas)}):")
    for i, col in enumerate(colunas):
        print(f"   [{i}] {col}")
    print()
    
    # 4. Mostrar primeiros 5 funcionários com dados completos
    print("=" * 70)
    print("👥 PRIMEIROS 5 FUNCIONÁRIOS - DADOS COMPLETOS")
    print("=" * 70)
    
    for idx in range(min(5, len(df))):
        row = df.iloc[idx]
        func = extrair_funcionario_completo(row, colunas)
        
        print()
        print(f"{'─' * 70}")
        print(f"📌 FUNCIONÁRIO #{idx + 1}")
        print(f"{'─' * 70}")
        print(f"   Nome:     {func['nome']}")
        print(f"   Unidade:  {func['unidade']}")
        print(f"   Motivo:   {func['motivo']}")
        print(f"   Saída:    {func['saida']}")
        print(f"   Retorno:  {func['retorno']}")
        print(f"   Gestor:   {func['gestor']}")
        print()
        print(f"   📊 STATUS DOS ACESSOS:")
        for sistema, status in func['acessos'].items():
            print(f"      • {sistema:12} → {status}")
    
    # 5. Mostrar dados brutos da primeira linha para conferência
    print()
    print("=" * 70)
    print("🔎 DADOS BRUTOS DA LINHA 1 (para conferência)")
    print("=" * 70)
    primeira_linha = df.iloc[0]
    for i, (col, valor) in enumerate(zip(colunas, primeira_linha)):
        print(f"   [{i:2}] {str(col):25} = '{valor}'")
    
    print()
    print("=" * 70)
    print("✅ VALIDAÇÃO CONCLUÍDA!")
    print("=" * 70)
    print()
    print("📝 CONFIRA OS DADOS ACIMA COM A PLANILHA ORIGINAL")
    print("   Se estiver correto, me avise para prosseguir!")
    print()


if __name__ == "__main__":
    main()

