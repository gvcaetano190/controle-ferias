#!/usr/bin/env python3
# ============================================
# MAIN.PY - CÉREBRO DO SISTEMA
# Controle de Férias - Saídas e Retornos
# ============================================

import sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from config import PLANILHA_PATH, COLUNAS, SEPARADOR
from modules.leitor_excel import LeitorExcel
from modules.processador import Processador
from modules.notificador import Notificador


def main():
    """Função principal do sistema."""
    
    print(SEPARADOR)
    print("🗓️  SISTEMA DE CONTROLE DE FÉRIAS")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    print(SEPARADOR)
    print()
    
    # 1. Carregar planilha
    print("📂 Carregando planilha...")
    leitor = LeitorExcel(PLANILHA_PATH)
    
    if not leitor.carregar():
        print("❌ Falha ao carregar planilha. Encerrando.")
        return
    
    # Mostra abas disponíveis
    abas = leitor.listar_abas()
    print(f"📑 Abas encontradas: {', '.join(abas)}")
    print()
    
    # 2. Ler todas as abas
    print("📖 Lendo dados...")
    dados = leitor.ler_todas_abas()
    
    if not dados:
        print("❌ Nenhum dado encontrado. Encerrando.")
        return
    
    # 3. Processar dados
    print("⚙️  Processando dados...")
    processador = Processador(dados, COLUNAS)
    processador.processar_todas_abas()
    print()
    
    # 4. Filtrar resultados
    saindo_hoje = processador.filtrar_saida_hoje()
    voltando_amanha = processador.filtrar_retorno_amanha()
    
    # 5. Gerar e exibir notificações
    notificador = Notificador()
    
    resumo = notificador.gerar_resumo_diario(saindo_hoje, voltando_amanha)
    notificador.exibir_terminal(resumo)
    
    # Estatísticas adicionais
    print()
    ausentes_hoje = processador.filtrar_ausentes_hoje()
    print(f"📊 Total de ausentes hoje: {len(ausentes_hoje)}")
    
    print()
    print(SEPARADOR)
    print("✅ Processamento concluído!")
    print(SEPARADOR)


if __name__ == "__main__":
    main()
