# ============================================
# MÓDULO: LEITOR DE EXCEL
# Responsabilidade: Ler planilha e suas abas
# ============================================

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re


class LeitorExcel:
    """Classe responsável por ler a planilha Excel com múltiplas abas."""
    
    def __init__(self, caminho: Path):
        self.caminho = caminho
        self._excel_file: Optional[pd.ExcelFile] = None
        self._dados: Dict[str, pd.DataFrame] = {}
    
    def carregar(self) -> bool:
        """Carrega o arquivo Excel."""
        try:
            if not self.caminho.exists():
                print(f"❌ Arquivo não encontrado: {self.caminho}")
                return False
            
            self._excel_file = pd.ExcelFile(self.caminho)
            print(f"✅ Planilha carregada: {self.caminho.name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar planilha: {e}")
            return False
    
    def listar_abas(self) -> List[str]:
        """Retorna lista de abas disponíveis."""
        if self._excel_file is None:
            return []
        return self._excel_file.sheet_names
    
    def ler_aba(self, nome_aba: str) -> Optional[pd.DataFrame]:
        """Lê uma aba específica e retorna DataFrame."""
        if self._excel_file is None:
            print("❌ Planilha não carregada. Execute carregar() primeiro.")
            return None
        
        try:
            df = pd.read_excel(
                self._excel_file,
                sheet_name=nome_aba,
                dtype=str  # Lê tudo como string inicialmente
            )
            self._dados[nome_aba] = df
            return df
        except Exception as e:
            print(f"❌ Erro ao ler aba '{nome_aba}': {e}")
            return None
    
    def ler_todas_abas(self) -> Dict[str, pd.DataFrame]:
        """Lê todas as abas e retorna dicionário de DataFrames."""
        if self._excel_file is None:
            print("❌ Planilha não carregada. Execute carregar() primeiro.")
            return {}
        
        for aba in self.listar_abas():
            self.ler_aba(aba)
        
        print(f"📊 {len(self._dados)} aba(s) carregada(s)")
        return self._dados
    
    def obter_dados(self) -> Dict[str, pd.DataFrame]:
        """Retorna os dados já carregados."""
        return self._dados
    
    def _parse_nome_mes_ano(self, nome_aba: str) -> Optional[tuple]:
        """
        Tenta extrair mês e ano do nome da aba.
        Exemplos: "DEZEMBRO 2024", "JANEIRO 2025", "DEZEMBRO.2024"
        
        Returns:
            Tupla (mês, ano) ou None se não conseguir parsear
        """
        # Mapeamento de meses em português
        meses_pt = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
            'abril': 4, 'maio': 5, 'junho': 6,
            'julho': 7, 'agosto': 8, 'setembro': 9,
            'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        nome_normalizado = nome_aba.lower().strip()
        
        # Remove pontos e converte para espaço
        nome_normalizado = nome_normalizado.replace('.', ' ')
        
        # Tenta encontrar mês no nome
        for mes_nome, mes_num in meses_pt.items():
            if mes_nome in nome_normalizado:
                # Tenta encontrar ano (4 dígitos)
                ano_match = re.search(r'\b(20\d{2})\b', nome_aba)
                if ano_match:
                    ano = int(ano_match.group(1))
                    return (mes_num, ano)
                # Se não encontrou ano, assume ano atual
                return (mes_num, datetime.now().year)
        
        return None
    
    def encontrar_aba_mes_atual(self) -> Optional[str]:
        """
        Encontra a aba que corresponde ao mês e ano atual.
        
        Returns:
            Nome da aba do mês atual ou None se não encontrar
        """
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        for nome_aba in self.listar_abas():
            parsed = self._parse_nome_mes_ano(nome_aba)
            if parsed:
                mes, ano = parsed
                if mes == mes_atual and ano == ano_atual:
                    return nome_aba
        
        return None
