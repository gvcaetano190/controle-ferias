#!/usr/bin/env python3
"""
Script de teste para baixar e analisar a planilha do Google Sheets.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path (subir um nível de tests/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.leitor_google_sheets import LeitorGoogleSheets
from modules.processador import Processador
from config import COLUNAS
from datetime import datetime

# URL da planilha
URL = "https://docs.google.com/spreadsheets/d/1oIgONGE3W7E1sFFNWun3bUY6Ys3JVSK1/edit?usp=sharing&ouid=118228570317015041234&rtpof=true&sd=true"

def main():
    print("=" * 60)
    print("TESTE DE DOWNLOAD E ANÁLISE DA PLANILHA")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    print("=" * 60)
    print()
    
    # 1. Baixar planilha
    print("📥 Baixando planilha do Google Sheets...")
    leitor = LeitorGoogleSheets(URL)
    
    try:
        dados = leitor.ler_todas_abas_via_excel(manter_arquivo=True)
    except Exception as e:
        print(f"❌ Erro ao baixar: {e}")
        return
    
    print()
    print("=" * 60)
    print("ANÁLISE DAS ABAS")
    print("=" * 60)
    
    # 2. Analisar cada aba
    for nome_aba, df in dados.items():
        print()
        print(f"📑 ABA: {nome_aba}")
        print(f"   Linhas: {len(df)}")
        print(f"   Colunas: {list(df.columns)}")
        
        # Mostra primeiras linhas
        if len(df) > 0:
            print(f"   Primeiras 3 linhas:")
            print(df.head(3).to_string())
        print()
    
    # 3. Testar processamento do mês atual
    print()
    print("=" * 60)
    print("TESTE DE PROCESSAMENTO - MÊS ATUAL (DEZEMBRO 2025)")
    print("=" * 60)
    
    # Encontrar aba do mês atual
    aba_dezembro = None
    for nome_aba in dados.keys():
        if "DEZEMBRO" in nome_aba.upper() and "2025" in nome_aba:
            aba_dezembro = nome_aba
            break
        # Tenta também DEZEMBRO.25 ou similar
        if "DEZEMBRO" in nome_aba.upper():
            aba_dezembro = nome_aba
    
    if aba_dezembro:
        print(f"✅ Aba encontrada: {aba_dezembro}")
        
        # Processar
        dados_aba = {aba_dezembro: dados[aba_dezembro]}
        processador = Processador(dados_aba, COLUNAS)
        processador.processar_aba_especifica(aba_dezembro)
        
        print(f"📊 Funcionários processados: {len(processador.funcionarios)}")
        
        # Mostrar alguns
        for i, f in enumerate(processador.funcionarios[:5]):
            print(f"   {i+1}. {f.nome}")
            print(f"      Saída: {f.data_saida.strftime('%d/%m/%Y')}")
            print(f"      Retorno: {f.data_retorno.strftime('%d/%m/%Y')}")
        
        # Testar filtros
        print()
        print("🔍 FILTROS:")
        
        saindo_hoje = processador.filtrar_saida_hoje()
        print(f"   Saindo hoje: {len(saindo_hoje)}")
        
        voltando_amanha = processador.filtrar_retorno_amanha()
        print(f"   Voltando amanhã: {len(voltando_amanha)}")
        
        ausentes_hoje = processador.filtrar_ausentes_hoje()
        print(f"   Em férias agora: {len(ausentes_hoje)}")
        
        if ausentes_hoje:
            print()
            print("🏖️ FUNCIONÁRIOS EM FÉRIAS AGORA:")
            for f in ausentes_hoje[:10]:
                print(f"   - {f.nome} (Saída: {f.data_saida.strftime('%d/%m/%Y')}, Retorno: {f.data_retorno.strftime('%d/%m/%Y')})")
    else:
        print("❌ Aba de dezembro não encontrada!")
        print(f"   Abas disponíveis: {list(dados.keys())}")
    
    print()
    print("=" * 60)
    print("VERIFICAÇÃO DAS COLUNAS")
    print("=" * 60)
    print(f"Configuração de colunas em config.py:")
    for chave, valor in COLUNAS.items():
        print(f"   {chave}: '{valor}'")
    
    print()
    print("✅ Teste concluído!")
    print(f"📂 Verifique o arquivo baixado na pasta: download/")

if __name__ == "__main__":
    main()

