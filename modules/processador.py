# ============================================
# MÓDULO: PROCESSADOR DE DADOS
# Responsabilidade: Filtrar e processar dados
# ============================================

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Funcionario:
    """Representa um funcionário com dados de férias."""
    nome: str
    motivo: str
    data_saida: datetime
    data_retorno: datetime
    gestor: str
    unidade: str
    
    def dias_ausencia(self) -> int:
        """Calcula dias de ausência."""
        return (self.data_retorno - self.data_saida).days


class Processador:
    """Classe responsável por processar e filtrar dados de férias."""
    
    def __init__(self, dados: Dict[str, pd.DataFrame], config_colunas: dict):
        self.dados = dados
        self.colunas = config_colunas
        self.funcionarios: List[Funcionario] = []
    
    def _parse_data(self, valor: str) -> Optional[datetime]:
        """Converte string para datetime."""
        if pd.isna(valor) or valor == "" or valor is None:
            return None
        
        # Tenta diferentes formatos
        formatos = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
        
        for fmt in formatos:
            try:
                return datetime.strptime(str(valor).strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def processar_todas_abas(self) -> List[Funcionario]:
        """Processa todas as abas e extrai funcionários."""
        self.funcionarios = []
        
        for nome_aba, df in self.dados.items():
            funcionarios_aba = self._processar_aba(df, nome_aba)
            self.funcionarios.extend(funcionarios_aba)
        
        print(f"👥 {len(self.funcionarios)} registro(s) processado(s)")
        return self.funcionarios
    
    def processar_aba_especifica(self, nome_aba: str) -> List[Funcionario]:
        """
        Processa apenas uma aba específica.
        
        Args:
            nome_aba: Nome da aba a processar
        
        Returns:
            Lista de funcionários da aba
        """
        if nome_aba not in self.dados:
            return []
        
        df = self.dados[nome_aba]
        funcionarios = self._processar_aba(df, nome_aba)
        self.funcionarios = funcionarios
        return funcionarios
    
    def _encontrar_coluna(self, df: pd.DataFrame, nome_coluna: str, indice_fallback: int = None) -> str:
        """
        Encontra uma coluna no DataFrame, usando fallback por índice se necessário.
        
        Args:
            df: DataFrame a analisar
            nome_coluna: Nome da coluna esperado
            indice_fallback: Índice da coluna se o nome não for encontrado
        
        Returns:
            Nome da coluna encontrada
        """
        colunas = list(df.columns)
        
        # Tenta encontrar pelo nome exato
        if nome_coluna in colunas:
            return nome_coluna
        
        # Tenta encontrar por nome similar (case-insensitive)
        for col in colunas:
            if str(col).upper().strip() == nome_coluna.upper().strip():
                return col
        
        # Tenta encontrar por nome parcial
        for col in colunas:
            col_str = str(col).upper().strip()
            nome_str = nome_coluna.upper().strip()
            if nome_str in col_str or col_str in nome_str:
                return col
        
        # Usa fallback por índice se o nome começa com "Unnamed" ou não foi encontrado
        if indice_fallback is not None and indice_fallback < len(colunas):
            return colunas[indice_fallback]
        
        return nome_coluna  # Retorna o nome original se nada funcionar
    
    def _processar_aba(self, df: pd.DataFrame, nome_aba: str) -> List[Funcionario]:
        """Processa uma aba específica."""
        funcionarios = []
        
        if df.empty:
            return funcionarios
        
        # Mapeia colunas com fallback por índice
        # Estrutura esperada: [Unidade, Nome, Motivo, Saída, Retorno, Gestor, ...]
        col_unidade = self._encontrar_coluna(df, self.colunas.get("unidade", "F"), 0)
        col_nome = self._encontrar_coluna(df, self.colunas.get("nome", "Nome"), 1)
        col_motivo = self._encontrar_coluna(df, self.colunas.get("motivo", "Motivo"), 2)
        col_saida = self._encontrar_coluna(df, self.colunas.get("saida", "Saída"), 3)
        col_retorno = self._encontrar_coluna(df, self.colunas.get("retorno", "Retorno/Liberação"), 4)
        col_gestor = self._encontrar_coluna(df, self.colunas.get("gestor", "Gestor"), 5)
        
        for _, row in df.iterrows():
            try:
                data_saida = self._parse_data(row.get(col_saida))
                data_retorno = self._parse_data(row.get(col_retorno))
                
                # Pula linhas sem datas válidas
                if data_saida is None or data_retorno is None:
                    continue
                
                nome = str(row.get(col_nome, "")).strip()
                if not nome or nome.lower() == "nan":
                    continue
                
                func = Funcionario(
                    nome=nome,
                    motivo=str(row.get(col_motivo, "")).strip(),
                    data_saida=data_saida,
                    data_retorno=data_retorno,
                    gestor=str(row.get(col_gestor, "")).strip(),
                    unidade=str(row.get(col_unidade, "")).strip()
                )
                funcionarios.append(func)
            except Exception as e:
                continue  # Pula linhas com erro
        
        return funcionarios
    
    def filtrar_saida_hoje(self) -> List[Funcionario]:
        """Retorna funcionários que saem HOJE."""
        hoje = datetime.now().date()
        
        return [
            f for f in self.funcionarios
            if f.data_saida.date() == hoje
        ]
    
    def filtrar_retorno_amanha(self) -> List[Funcionario]:
        """Retorna funcionários que voltam AMANHÃ."""
        amanha = (datetime.now() + timedelta(days=1)).date()
        
        return [
            f for f in self.funcionarios
            if f.data_retorno.date() == amanha
        ]
    
    def filtrar_saida_data(self, data: datetime) -> List[Funcionario]:
        """Retorna funcionários que saem em uma data específica."""
        return [
            f for f in self.funcionarios
            if f.data_saida.date() == data.date()
        ]
    
    def filtrar_retorno_data(self, data: datetime) -> List[Funcionario]:
        """Retorna funcionários que voltam em uma data específica."""
        return [
            f for f in self.funcionarios
            if f.data_retorno.date() == data.date()
        ]
    
    def filtrar_ausentes_hoje(self) -> List[Funcionario]:
        """Retorna funcionários ausentes HOJE."""
        hoje = datetime.now().date()
        
        return [
            f for f in self.funcionarios
            if f.data_saida.date() <= hoje <= f.data_retorno.date()
        ]
