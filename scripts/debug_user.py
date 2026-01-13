"""
Script de depuração para verificar os dados de um usuário específico
diretamente da planilha, como o sync_manager os vê.
"""
import sys
import os
from pathlib import Path
import argparse
import json

# Adiciona a raiz do projeto ao sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.sync_manager import SyncManager

def debug_user(user_name: str):
    """
    Carrega a planilha, processa os dados e imprime as informações
    de um usuário específico para depuração.
    """
    print("=" * 60)
    print(f"🕵️  Iniciando depuração para o usuário: {user_name}")
    print("=" * 60)

    sync = SyncManager()

    # 1. Baixar a planilha (usando o cache se disponível, mas podemos forçar)
    print("\n[PASSO 1] Baixando a planilha...")
    if not sync.baixar_planilha(forcar=True):
        print("❌ Falha no download. Abortando.")
        return
    print(f"✅ Planilha baixada: {sync.arquivo_excel.name}")

    # 2. Processar a planilha para extrair todos os dados
    print("\n[PASSO 2] Processando a planilha...")
    try:
        dados_processados = sync.processar_planilha()
        if not dados_processados:
            print("❌ Nenhum dado foi processado da planilha.")
            return
        print(f"✅ {len(dados_processados)} registros processados.")
    except Exception as e:
        print(f"❌ Erro ao processar a planilha: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Encontrar o usuário específico
    print(f"\n[PASSO 3] Procurando por '{user_name}'...")
    user_name_upper = user_name.upper()
    
    # Procura em todos os registros, incluindo duplicados de abas diferentes
    found_users = [
        p for p in dados_processados 
        if user_name_upper in p.get("nome", "").upper()
    ]

    if not found_users:
        print(f"❌ Usuário '{user_name}' não encontrado nos dados processados.")
        return

    print(f"✅ Encontrado(s) {len(found_users)} registro(s) para o usuário.")

    # 4. Imprimir os dados encontrados
    for i, user_data in enumerate(found_users, 1):
        print("-" * 60)
        print(f"Registro {i}/{len(found_users)}")
        print(f"  Nome: {user_data.get('nome')}")
        print(f"  Aba de Origem: {user_data.get('aba_origem')}")
        print(f"  Data Saída: {user_data.get('data_saida')}")
        print(f"  Data Retorno: {user_data.get('data_retorno')}")
        
        acessos = user_data.get('acessos', {})
        print("  Acessos:")
        # Usando json.dumps para uma visualização bonita
        print(json.dumps(acessos, indent=4))
        print("-" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Debuga a leitura de um usuário específico da planilha."
    )
    parser.add_argument(
        "nome",
        type=str,
        help="Nome do usuário a ser verificado (pode ser parcial, entre aspas)."
    )
    args = parser.parse_args()
    
    debug_user(args.nome)
