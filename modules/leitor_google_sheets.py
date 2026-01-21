# ============================================
# MÓDULO: LEITOR DE GOOGLE SHEETS
# Responsabilidade: Ler planilhas do Google Sheets
# ============================================

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import tempfile
from pathlib import Path
import urllib.request
import re
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.google_sheets import extrair_sheet_id, construir_url_exportacao


class LeitorGoogleSheets:
    """Classe responsável por ler planilhas do Google Sheets."""
    
    def __init__(self, url: str):
        """
        Inicializa o leitor com URL do Google Sheets.
        
        Args:
            url: URL do Google Sheets (formato: https://docs.google.com/spreadsheets/d/ID/edit)
        """
        self.url = url
        self._dados: Dict[str, pd.DataFrame] = {}
    
    def _converter_url_para_csv(self, url: str, gid: Optional[str] = None) -> str:
        """
        Converte URL do Google Sheets para URL de exportação CSV.
        
        Args:
            url: URL original do Google Sheets
            gid: ID numérico da aba (opcional). Se None, usa a primeira aba.
        
        Returns:
            URL para baixar como CSV
        """
        sheet_id = extrair_sheet_id(url)
        if not sheet_id:
            raise ValueError(f"URL inválida do Google Sheets: {url}")
        
        return construir_url_exportacao(sheet_id, formato="csv", gid=gid)
    
    def _converter_url_para_excel(self, url: str) -> str:
        """
        Converte URL do Google Sheets para URL de exportação Excel (.xlsx).
        
        Args:
            url: URL original do Google Sheets
        
        Returns:
            URL para baixar como Excel
        """
        sheet_id = extrair_sheet_id(url)
        if not sheet_id:
            raise ValueError(f"URL inválida do Google Sheets: {url}")
        
        return construir_url_exportacao(sheet_id, formato="xlsx")
    
    def baixar_como_excel(self, salvar_em_pasta: Optional[Path] = None) -> Optional[Path]:
        """
        Baixa a planilha do Google Sheets como arquivo Excel (.xlsx).
        
        Args:
            salvar_em_pasta: Pasta onde salvar o arquivo (opcional). 
                           Se None, usa pasta download do projeto.
        
        Returns:
            Caminho para o arquivo Excel baixado ou None em caso de erro
        """
        try:
            excel_url = self._converter_url_para_excel(self.url)
            
            # Define pasta de download
            if salvar_em_pasta:
                pasta_download = salvar_em_pasta
            else:
                # Usa pasta download no projeto
                pasta_download = Path(__file__).parent.parent / "download"
            
            # Cria pasta se não existir
            pasta_download.mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo com timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sheet_id = self._extrair_sheet_id(self.url) or "planilha"
            nome_arquivo = f"planilha_{timestamp}.xlsx"
            
            excel_path = pasta_download / nome_arquivo
            
            # Baixa o arquivo
            urllib.request.urlretrieve(excel_url, excel_path)
            
            print(f"✅ Planilha baixada em: {excel_path}")
            
            return excel_path
            
        except Exception as e:
            raise Exception(f"Erro ao baixar planilha como Excel: {str(e)}")
    
    def ler_todas_abas_via_excel(self, manter_arquivo: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Baixa a planilha como Excel e lê todas as abas usando LeitorExcel.
        Método recomendado para planilhas públicas com múltiplas abas.
        
        Args:
            manter_arquivo: Se True (padrão), mantém o arquivo baixado na pasta download
        
        Returns:
            Dicionário com DataFrames por aba
        """
        try:
            # Baixa como Excel (salva na pasta download)
            excel_path = self.baixar_como_excel()
            
            if not excel_path or not excel_path.exists():
                raise Exception("Falha ao baixar planilha")
            
            print(f"📂 Arquivo Excel baixado: {excel_path}")
            
            # Usa LeitorExcel para ler todas as abas
            from .leitor_excel import LeitorExcel
            
            leitor_excel = LeitorExcel(excel_path)
            if not leitor_excel.carregar():
                raise Exception("Falha ao carregar arquivo Excel baixado")
            
            # Lista abas disponíveis
            abas = leitor_excel.listar_abas()
            print(f"📑 Abas encontradas no Excel: {abas}")
            
            # Lê todas as abas
            self._dados = leitor_excel.ler_todas_abas()
            
            print(f"📊 Total de abas lidas: {len(self._dados)}")
            for nome_aba, df in self._dados.items():
                print(f"   - {nome_aba}: {len(df)} linhas, colunas: {list(df.columns)[:5]}...")
            
            # NÃO deleta o arquivo para poder analisar
            if not manter_arquivo:
                try:
                    excel_path.unlink()
                except:
                    pass
            
            return self._dados
            
        except Exception as e:
            raise Exception(f"Erro ao ler planilha via Excel: {str(e)}")
    
    def ler_aba_por_nome(self, nome_aba: str) -> Optional[pd.DataFrame]:
        """
        Lê uma aba específica pelo nome usando método CSV público.
        Nota: Funciona apenas se a planilha estiver pública.
        """
        try:
            sheet_id = self._extrair_sheet_id(self.url)
            if not sheet_id:
                return None
            
            # Para ler aba específica, precisamos listar todas primeiro
            # Ou usar API do Google (implementação futura)
            # Por enquanto, usa gspread se disponível, senão usa CSV da primeira aba
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                
                # Se tiver gspread configurado, usa API
                # TODO: Implementar autenticação
                pass
            except ImportError:
                # Método CSV público (funciona apenas com planilha pública)
                csv_url = self._converter_url_para_csv(self.url)
                df = pd.read_csv(csv_url, dtype=str)
                self._dados[nome_aba] = df
                return df
                
        except Exception as e:
            print(f"❌ Erro ao ler aba '{nome_aba}': {e}")
            return None
    
    def ler_todas_abas_csv_publico(self) -> Dict[str, pd.DataFrame]:
        """
        Lê planilha usando método CSV público.
        Nota: Funciona apenas se a planilha estiver pública.
        Por limitação do método CSV, lê apenas a primeira aba (gid=0).
        Para múltiplas abas, use ler_via_api() ou leia abas individuais.
        """
        try:
            # Tenta sem gid primeiro (primeira aba padrão)
            csv_url = self._converter_url_para_csv(self.url)
            
            # Lê CSV com encoding UTF-8 e trata possíveis problemas
            try:
                df = pd.read_csv(
                    csv_url,
                    dtype=str,
                    encoding='utf-8'
                )
            except UnicodeDecodeError:
                # Tenta com latin-1 se UTF-8 falhar
                df = pd.read_csv(
                    csv_url,
                    dtype=str,
                    encoding='latin-1'
                )
            except Exception as e1:
                # Tenta sem especificar encoding
                try:
                    df = pd.read_csv(csv_url, dtype=str)
                except Exception as e2:
                    raise Exception(f"Erro ao ler CSV: {str(e1)} / {str(e2)}")
            
            # Remove linhas completamente vazias
            df = df.dropna(how='all')
            
            # Remove colunas completamente vazias
            df = df.dropna(axis=1, how='all')
            
            # Se DataFrame não estiver vazio, adiciona
            if not df.empty:
                self._dados["Sheet1"] = df
            
            return self._dados
            
        except Exception as e:
            error_msg = str(e)
            # Re-raise com mais contexto
            csv_url_info = csv_url if 'csv_url' in locals() else 'N/A'
            raise Exception(f"Erro ao ler planilha CSV: {error_msg} (URL: {csv_url_info})")
    
    def ler_via_api(self, credenciais_json: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Lê todas as abas usando Google Sheets API.
        Requer biblioteca gspread e credenciais do Google.
        
        Args:
            credenciais_json: Caminho para arquivo JSON de credenciais do Google
                            Se None, tenta usar variável de ambiente ou default
        
        Returns:
            Dicionário com DataFrames por aba
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            # Autenticação
            if credenciais_json:
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_file(credenciais_json, scopes=scope)
                gc = gspread.authorize(creds)
            else:
                # Tenta autenticação padrão ou variável de ambiente
                try:
                    gc = gspread.service_account()
                except Exception:
                    # Se não conseguir autenticar, levanta exceção
                    raise Exception("Autenticação necessária. Forneça credenciais JSON ou configure autenticação padrão.")
            
            # Abre a planilha
            sheet_id = self._extrair_sheet_id(self.url)
            if not sheet_id:
                raise Exception("Não foi possível extrair ID da planilha da URL")
            
            spreadsheet = gc.open_by_key(sheet_id)
            
            # Lê todas as abas
            self._dados = {}  # Limpa dados anteriores
            for worksheet in spreadsheet.worksheets():
                try:
                    # Lê dados e converte para DataFrame
                    records = worksheet.get_all_records()
                    if records:  # Se tem dados
                        df = pd.DataFrame(records)
                        # Converte tudo para string inicialmente (mesmo padrão do CSV)
                        df = df.astype(str)
                        # Remove linhas completamente vazias
                        df = df.dropna(how='all')
                        if not df.empty:
                            self._dados[worksheet.title] = df
                except Exception as e:
                    # Se falhar ao ler uma aba específica, continua com as outras
                    continue
            
            return self._dados
            
        except ImportError:
            raise Exception("Biblioteca gspread não instalada. Use: pip install gspread google-auth")
        except Exception as e:
            # Re-raise para que o chamador saiba que falhou
            raise
    
    def ler_todas_abas(self, usar_api: bool = False, credenciais_json: Optional[str] = None, usar_excel: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Lê todas as abas. Por padrão baixa como Excel (todas as abas), ou pode usar API/CSV.
        
        Args:
            usar_api: Se True, força uso da API (requer gspread)
            credenciais_json: Caminho para credenciais JSON (se usar API)
            usar_excel: Se True (padrão), baixa como Excel para ler todas as abas (recomendado)
        
        Returns:
            Dicionário com DataFrames por aba
        """
        if usar_api:
            return self.ler_via_api(credenciais_json)
        elif usar_excel:
            # Método recomendado: baixa como Excel (lê todas as abas)
            return self.ler_todas_abas_via_excel()
        else:
            # Método CSV (limitação: só primeira aba)
            return self.ler_todas_abas_csv_publico()
    
    def listar_abas(self) -> List[str]:
        """Retorna lista de abas disponíveis."""
        return list(self._dados.keys())
    
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
    
    def obter_dados_aba(self, nome_aba: str) -> Optional[pd.DataFrame]:
        """Retorna DataFrame de uma aba específica."""
        return self._dados.get(nome_aba)

