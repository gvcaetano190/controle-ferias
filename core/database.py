"""
Módulo de acesso ao banco de dados SQLite.

Fornece interface unificada para todas as operações de banco.
Pronto para migração futura para SQLAlchemy/FastAPI.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import opcional do pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


class Database:
    """Gerenciador de banco de dados SQLite."""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._criar_tabelas()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Retorna conexão com o banco."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _criar_tabelas(self):
        """Cria tabelas se não existirem."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabela de funcionários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                unidade TEXT,
                motivo TEXT,
                data_saida DATE,
                data_retorno DATE,
                gestor TEXT,
                aba_origem TEXT,
                mes INTEGER,
                ano INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de acessos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acessos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER,
                sistema TEXT,
                status TEXT,
                FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
            )
        """)
        
        # Tabela de abas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS abas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                mes INTEGER,
                ano INTEGER,
                total_funcionarios INTEGER
            )
        """)
        
        # Tabela de logs de sincronização
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_registros INTEGER,
                total_abas INTEGER,
                status TEXT,
                mensagem TEXT,
                arquivo_hash TEXT
            )
        """)
        
        # Migração: adiciona coluna arquivo_hash se não existir
        try:
            cursor.execute("ALTER TABLE sync_logs ADD COLUMN arquivo_hash TEXT")
        except sqlite3.OperationalError:
            pass  # Coluna já existe, ignora
        
        # Tabela de logs de atividades gerais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                status TEXT NOT NULL,
                mensagem TEXT,
                detalhes TEXT,
                origem TEXT
            )
        """)
        
        # Tabela de cards do Kanbanize (Cache)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kanbanize_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER UNIQUE NOT NULL,
                board_id INTEGER,
                workflow_id INTEGER,
                workflow_name TEXT,
                column_id INTEGER,
                column_name TEXT,
                title TEXT NOT NULL,
                description TEXT,
                color TEXT,
                custom_fields TEXT,
                created_at TEXT,
                last_modified TEXT,
                in_current_position_since TEXT,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de filtros salvos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kanbanize_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filter_name TEXT UNIQUE NOT NULL,
                workflow_id INTEGER,
                column_id INTEGER,
                board_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_func_data_saida ON funcionarios(data_saida)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_func_data_retorno ON funcionarios(data_retorno)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_func_aba ON funcionarios(aba_origem)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_acessos_func ON acessos(funcionario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanbanize_card_id ON kanbanize_cards(card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanbanize_workflow ON kanbanize_cards(workflow_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanbanize_column ON kanbanize_cards(column_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanbanize_board ON kanbanize_cards(board_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanbanize_board_workflow ON kanbanize_cards(board_id, workflow_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanbanize_board_column ON kanbanize_cards(board_id, column_id)")
        
        # Migração: adiciona coluna in_current_position_since se não existir
        try:
            cursor.execute("ALTER TABLE kanbanize_cards ADD COLUMN in_current_position_since TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                # Log silencioso - coluna pode já existir
                pass
        
        conn.commit()
        conn.close()
    
    # ==================== OPERAÇÕES DE ESCRITA ====================
    
    def limpar_dados(self):
        """Limpa todas as tabelas (exceto logs)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM acessos")
        cursor.execute("DELETE FROM funcionarios")
        cursor.execute("DELETE FROM abas")
        conn.commit()
        conn.close()
    
    def salvar_funcionarios(self, funcionarios: List[Dict]) -> int:
        """
        Salva lista de funcionários no banco, atualizando se já existir.
        Usa o nome do funcionário e a data de saída como chave única.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        registros_atualizados = 0
        registros_inseridos = 0
        
        for f in funcionarios:
            nome = f.get("nome", "")
            data_saida = f.get("data_saida")
            
            # 1. Verifica se já existe um registro com o mesmo nome E data de saída
            cursor.execute("""
                SELECT id FROM funcionarios WHERE nome = ? AND data_saida = ?
            """, (nome, data_saida))
            existente = cursor.fetchone()
            
            if existente:
                # UPDATE - Atualiza o registro existente
                funcionario_id = existente[0]
                cursor.execute("""
                    UPDATE funcionarios 
                    SET unidade = ?, motivo = ?, data_retorno = ?, gestor = ?, 
                        aba_origem = ?, mes = ?, ano = ?
                    WHERE id = ?
                """, (
                    f.get("unidade", ""), f.get("motivo", ""), f.get("data_retorno"),
                    f.get("gestor", ""), f.get("aba_origem", ""), f.get("mes", 0),
                    f.get("ano", 0), funcionario_id
                ))
                
                # Deleta acessos antigos para reinserir
                cursor.execute("DELETE FROM acessos WHERE funcionario_id = ?", (funcionario_id,))
                registros_atualizados += 1
            else:
                # INSERT - Insere um novo registro
                cursor.execute("""
                    INSERT INTO funcionarios 
                    (nome, unidade, motivo, data_saida, data_retorno, gestor, aba_origem, mes, ano)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nome, f.get("unidade", ""), f.get("motivo", ""), data_saida,
                    f.get("data_retorno"), f.get("gestor", ""), f.get("aba_origem", ""),
                    f.get("mes", 0), f.get("ano", 0)
                ))
                funcionario_id = cursor.lastrowid
                registros_inseridos += 1

            # Insere/Reinsere os acessos
            acessos = f.get("acessos", {})
            for sistema, status in acessos.items():
                cursor.execute("""
                    INSERT INTO acessos (funcionario_id, sistema, status)
                    VALUES (?, ?, ?)
                """, (funcionario_id, sistema, status))
        
        conn.commit()
        conn.close()
        
        print(f"   -> Inseridos: {registros_inseridos}, Atualizados: {registros_atualizados}")
        return registros_inseridos + registros_atualizados
    
    def salvar_abas(self, abas: List[Dict]):
        """Salva lista de abas no banco."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for a in abas:
            cursor.execute("""
                INSERT INTO abas (nome, mes, ano, total_funcionarios)
                VALUES (?, ?, ?, ?)
            """, (
                a.get("nome", ""),
                a.get("mes", 0),
                a.get("ano", 0),
                a.get("total_funcionarios", 0)
            ))
        
        conn.commit()
        conn.close()
    
    def registrar_sync(self, total_registros: int, total_abas: int, 
                       status: str, mensagem: str, arquivo_hash: str = ""):
        """Registra log de sincronização."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Define explicitamente o sync_at com o timestamp atual
        sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO sync_logs (sync_at, total_registros, total_abas, status, mensagem, arquivo_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sync_at, total_registros, total_abas, status, mensagem, arquivo_hash))
        
        conn.commit()
        conn.close()
        
        # Também registra no log de atividades
        self.registrar_log(
            tipo="sync",
            categoria="Sincronização",
            status=status,
            mensagem=mensagem,
            detalhes=f"Registros: {total_registros}, Abas: {total_abas}",
            origem="sync_manager"
        )
    
    def registrar_log(self, tipo: str, categoria: str, status: str, 
                      mensagem: str, detalhes: str = "", origem: str = "sistema"):
        """
        Registra um log de atividade no banco.
        
        Args:
            tipo: Tipo do log (sync, mensagem, erro, acesso, senha, etc.)
            categoria: Categoria descritiva (Sincronização, WhatsApp, OneTimeSecret, etc.)
            status: Status (sucesso, erro, info, warning)
            mensagem: Mensagem principal do log
            detalhes: Detalhes adicionais (opcional)
            origem: Origem do log (módulo/função)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO activity_logs (created_at, tipo, categoria, status, mensagem, detalhes, origem)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (created_at, tipo, categoria, status, mensagem, detalhes, origem))
        
        conn.commit()
        conn.close()
    
    def buscar_logs(self, limite: int = 100, tipo: str = None, 
                    categoria: str = None, status: str = None) -> List[Dict]:
        """
        Busca logs de atividades com filtros opcionais.
        
        Args:
            limite: Número máximo de registros
            tipo: Filtrar por tipo (opcional)
            categoria: Filtrar por categoria (opcional)
            status: Filtrar por status (opcional)
            
        Returns:
            Lista de logs ordenados por data decrescente
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM activity_logs WHERE 1=1"
        params = []
        
        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)
        
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
            
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limite)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = [self._row_to_dict(row) for row in rows]
        conn.close()
        
        return result
    
    def buscar_sync_logs(self, limite: int = 50) -> List[Dict]:
        """Busca logs de sincronização."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sync_logs 
            ORDER BY id DESC 
            LIMIT ?
        """, (limite,))
        
        rows = cursor.fetchall()
        result = [self._row_to_dict(row) for row in rows]
        conn.close()
        
        return result
    
    def limpar_logs_antigos(self, dias: int = 30):
        """Remove logs com mais de X dias."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM activity_logs 
            WHERE created_at < datetime('now', ?)
        """, (f'-{dias} days',))
        
        conn.commit()
        conn.close()
    
    # ==================== OPERAÇÕES DE LEITURA ====================
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Converte Row para dicionário."""
        return dict(row)
    
    def _adicionar_acessos(self, funcionarios: List[Dict]) -> List[Dict]:
        """Adiciona acessos aos funcionários."""
        if not funcionarios:
            return funcionarios
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for f in funcionarios:
            cursor.execute(
                "SELECT sistema, status FROM acessos WHERE funcionario_id = ?",
                (f["id"],)
            )
            f["acessos"] = {row["sistema"]: row["status"] for row in cursor.fetchall()}
        
        conn.close()
        return funcionarios
    
    def buscar_funcionarios(self, aba: str = None, mes: int = None, 
                            ano: int = None) -> List[Dict]:
        """Busca funcionários com filtros opcionais."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM funcionarios WHERE 1=1"
        params = []
        
        if aba:
            query += " AND aba_origem = ?"
            params.append(aba)
        if mes:
            query += " AND mes = ?"
            params.append(mes)
        if ano:
            query += " AND ano = ?"
            params.append(ano)
        
        query += " ORDER BY data_saida DESC"
        
        cursor.execute(query, params)
        funcionarios = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return self._adicionar_acessos(funcionarios)
    
    def buscar_saindo_hoje(self) -> List[Dict]:
        """Busca funcionários saindo de férias hoje."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "SELECT * FROM funcionarios WHERE date(data_saida) = ?",
            (hoje,)
        )
        funcionarios = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return self._adicionar_acessos(funcionarios)
    
    def buscar_retornos_proximo_dia_util(self) -> List[Dict]:
        """
        Busca funcionários que retornam no próximo dia útil.
        - Em dias de semana (seg-qui), busca quem volta no dia seguinte.
        - Na sexta-feira, busca quem volta no sábado, domingo e segunda-feira.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        hoje = datetime.now()
        dia_semana = hoje.weekday()  # 0=segunda, 4=sexta

        datas_busca = []
        if dia_semana == 4:  # Sexta-feira
            # Adiciona sábado, domingo e segunda
            datas_busca.append((hoje + timedelta(days=1)).strftime('%Y-%m-%d'))
            datas_busca.append((hoje + timedelta(days=2)).strftime('%Y-%m-%d'))
            datas_busca.append((hoje + timedelta(days=3)).strftime('%Y-%m-%d'))
        else:
            # Para outros dias da semana, busca apenas o dia seguinte
            amanha = (hoje + timedelta(days=1)).strftime('%Y-%m-%d')
            datas_busca.append(amanha)

        # Cria a string de placeholders para a consulta IN
        placeholders = ','.join('?' for _ in datas_busca)

        query = f"SELECT * FROM funcionarios WHERE date(data_retorno) IN ({placeholders}) ORDER BY data_retorno ASC"
        
        cursor.execute(query, datas_busca)
        funcionarios = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        return self._adicionar_acessos(funcionarios)
    
    def buscar_em_ferias(self) -> List[Dict]:
        """Busca funcionários atualmente em férias."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT * FROM funcionarios 
            WHERE date(data_saida) <= ? AND date(data_retorno) >= ?
            ORDER BY data_retorno ASC
        """, (hoje, hoje))
        funcionarios = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return self._adicionar_acessos(funcionarios)
    
    def buscar_proximos_a_sair(self, dias: int = 7) -> List[Dict]:
        """Busca funcionários que vão sair nos próximos X dias."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        data_limite = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT * FROM funcionarios 
            WHERE date(data_saida) > ? AND date(data_saida) <= ?
            ORDER BY data_saida ASC
        """, (hoje, data_limite))
        funcionarios = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return self._adicionar_acessos(funcionarios)
    
    def buscar_retornados_com_acessos_bloqueados(self, mes_inicio: int = None, ano_inicio: int = None,
                                                     mes_fim: int = None, ano_fim: int = None) -> List[Dict]:
        """
        Busca funcionários que já retornaram de férias mas ainda têm acessos bloqueados.
        Esses funcionários deveriam ter seus acessos liberados.
        
        Args:
            mes_inicio: Mês inicial do filtro (opcional)
            ano_inicio: Ano inicial do filtro (opcional)
            mes_fim: Mês final do filtro (opcional)
            ano_fim: Ano final do filtro (opcional)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        # Busca IDs de funcionários com acessos BLOQUEADO
        cursor.execute("""
            SELECT DISTINCT funcionario_id 
            FROM acessos 
            WHERE status = 'BLOQUEADO'
        """)
        ids_bloqueados = [row["funcionario_id"] for row in cursor.fetchall()]
        
        if not ids_bloqueados:
            conn.close()
            return []
        
        # Monta query base
        placeholders = ','.join('?' * len(ids_bloqueados))
        query = f"""
            SELECT * FROM funcionarios 
            WHERE id IN ({placeholders})
            AND date(data_retorno) < ?
        """
        params = ids_bloqueados + [hoje]
        
        # Adiciona filtro de período se especificado
        if mes_inicio and ano_inicio:
            data_inicio = f"{ano_inicio}-{mes_inicio:02d}-01"
            query += " AND date(data_saida) >= ?"
            params.append(data_inicio)
        
        if mes_fim and ano_fim:
            # Último dia do mês
            if mes_fim == 12:
                prox_mes = 1
                prox_ano = ano_fim + 1
            else:
                prox_mes = mes_fim + 1
                prox_ano = ano_fim
            data_fim = f"{prox_ano}-{prox_mes:02d}-01"
            query += " AND date(data_saida) < ?"
            params.append(data_fim)
        
        query += " ORDER BY data_retorno DESC"
        
        cursor.execute(query, params)
        funcionarios = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return self._adicionar_acessos(funcionarios)
    
    def buscar_acessos_pendentes(self) -> List[Dict]:
        """Busca funcionários em férias com acessos pendentes (NB)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        # Busca IDs de funcionários com acessos PENDENTE
        cursor.execute("""
            SELECT DISTINCT funcionario_id 
            FROM acessos 
            WHERE status = 'PENDENTE'
        """)
        ids_pendentes = [row["funcionario_id"] for row in cursor.fetchall()]
        
        if not ids_pendentes:
            conn.close()
            return []
        
        # Busca funcionários em férias
        placeholders = ','.join('?' * len(ids_pendentes))
        cursor.execute(f"""
            SELECT * FROM funcionarios 
            WHERE id IN ({placeholders})
            AND date(data_saida) <= ? AND date(data_retorno) >= ?
        """, ids_pendentes + [hoje, hoje])
        
        funcionarios = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return self._adicionar_acessos(funcionarios)
    
    def buscar_abas(self) -> List[Dict]:
        """Busca todas as abas ordenadas por data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM abas ORDER BY ano DESC, mes DESC")
        abas = [self._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return abas
    
    def buscar_resumo_acessos(self) -> Dict[str, Dict[str, int]]:
        """Retorna resumo de acessos por sistema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        resumo = {}
        for sistema in settings.SISTEMAS_ACESSO:
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM acessos 
                WHERE sistema = ?
                GROUP BY status
            """, (sistema,))
            
            resumo[sistema] = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        conn.close()
        return resumo
    
    def buscar_ultimo_sync(self) -> Optional[Dict]:
        """Retorna dados da última sincronização."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sync_logs 
            ORDER BY id DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_dict(row) if row else None
    
    # ==================== PANDAS INTERFACE ====================
    
    def buscar_funcionarios_df(self, **filtros):
        """Retorna funcionários como DataFrame do Pandas."""
        if not HAS_PANDAS:
            raise ImportError("pandas não está instalado. Instale com: pip install pandas")

        funcionarios = self.buscar_funcionarios(**filtros)
        return pd.DataFrame(funcionarios)

    def buscar_em_ferias_df(self):
        """Retorna funcionários em férias como DataFrame."""
        if not HAS_PANDAS:
            raise ImportError("pandas não está instalado. Instale com: pip install pandas")

        funcionarios = self.buscar_em_ferias()
        return pd.DataFrame(funcionarios)

    # ==================== HISTÓRICO DE LINKS DE SENHA ====================

    def _criar_tabela_password_links(self):
        """Cria tabela de histórico de links de senha se não existir."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                senha_usada TEXT NOT NULL,
                link_url TEXT NOT NULL UNIQUE,
                secret_key TEXT NOT NULL,
                metadata_key TEXT,
                ttl_seconds INTEGER NOT NULL,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                expirado_em DATETIME,
                visualizado BOOLEAN DEFAULT 0,
                finalidade TEXT,
                nome_pessoa TEXT,
                descricao TEXT,
                usuario_criador TEXT
            )
        """)

        # Migração: garante que as colunas existem em bancos antigos
        try:
            cursor.execute("ALTER TABLE password_links ADD COLUMN metadata_key TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE password_links ADD COLUMN nome_pessoa TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE password_links ADD COLUMN descricao TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE password_links ADD COLUMN gestor_pessoa TEXT")
        except sqlite3.OperationalError:
            pass

        # Índice para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_criado ON password_links(criado_em)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_expirado ON password_links(expirado_em)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_visualizado ON password_links(visualizado)")

        conn.commit()
        conn.close()

    def salvar_password_link(self, link_data: Dict) -> int:
        """Salva um link de senha no histórico."""
        self._criar_tabela_password_links()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO password_links (
                senha_usada, link_url, secret_key, metadata_key, ttl_seconds,
                expirado_em, finalidade, nome_pessoa, gestor_pessoa, descricao, usuario_criador
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            link_data.get("senha_usada", ""),
            link_data.get("link_url", ""),
            link_data.get("secret_key", ""),
            link_data.get("metadata_key", ""),
            link_data.get("ttl_seconds", 3600),
            link_data.get("expirado_em"),
            link_data.get("finalidade", ""),
            link_data.get("nome_pessoa", ""),
            link_data.get("gestor_pessoa", ""),
            link_data.get("descricao", ""),
            link_data.get("usuario_criador", "")
        ))

        link_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return link_id

    def buscar_password_links(self, limite: int = 100, apenas_ativos: bool = False,
                            finalidade: str = None) -> List[Dict]:
        """Busca links de senha do histórico."""
        self._criar_tabela_password_links()

        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM password_links
            WHERE 1=1
        """
        params = []

        if apenas_ativos:
            query += " AND (expirado_em IS NULL OR expirado_em > datetime('now'))"
            query += " AND visualizado = 0"

        if finalidade:
            query += " AND finalidade = ?"
            params.append(finalidade)

        query += " ORDER BY criado_em DESC LIMIT ?"
        params.append(limite)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def marcar_link_visualizado(self, link_id: int):
        """Marca um link como visualizado."""
        self._criar_tabela_password_links()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE password_links
            SET visualizado = 1
            WHERE id = ?
        """, (link_id,))

        conn.commit()
        conn.close()

    def excluir_link(self, link_id: int) -> bool:
        """Exclui um link específico do histórico."""
        self._criar_tabela_password_links()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM password_links WHERE id = ?", (link_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def excluir_links_expirados(self, dias_antigos: int = 30):
        """Remove links expirados há mais de X dias."""
        self._criar_tabela_password_links()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM password_links
            WHERE expirado_em < datetime('now', '-{} days')
        """.format(dias_antigos))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def obter_estatisticas_links(self) -> Dict:
        """Retorna estatísticas dos links de senha."""
        self._criar_tabela_password_links()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_links,
                COUNT(CASE WHEN visualizado = 1 THEN 1 END) as visualizados,
                COUNT(CASE WHEN expirado_em > datetime('now') AND visualizado = 0 THEN 1 END) as ativos,
                COUNT(CASE WHEN expirado_em <= datetime('now') THEN 1 END) as expirados
            FROM password_links
        """)

        stats = dict(cursor.fetchone())
        conn.close()

        return stats

    # ==================== RELATÓRIOS ====================

    def buscar_historico_ferias_por_funcionario(self) -> Dict[str, Dict]:
        """
        Busca histórico completo de férias agrupado por funcionário.
        
        Returns:
            Dicionário com nome do funcionário como chave e dados como valor
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nome, unidade, motivo, data_saida, data_retorno, gestor, aba_origem, mes, ano
            FROM funcionarios
            WHERE nome IS NOT NULL AND nome != ''
            ORDER BY nome, data_saida DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        historico = {}
        for row in rows:
            row_dict = dict(row)
            nome = row_dict["nome"]
            
            if nome not in historico:
                historico[nome] = {"ferias": []}
            
            # Calcula dias de férias
            dias = 0
            data_saida_fmt = ""
            data_retorno_fmt = ""
            
            if row_dict["data_saida"] and row_dict["data_retorno"]:
                try:
                    saida = datetime.strptime(row_dict["data_saida"], '%Y-%m-%d')
                    retorno = datetime.strptime(row_dict["data_retorno"], '%Y-%m-%d')
                    dias = (retorno - saida).days + 1
                    data_saida_fmt = saida.strftime('%d/%m/%Y')
                    data_retorno_fmt = retorno.strftime('%d/%m/%Y')
                except:
                    pass
            
            historico[nome]["ferias"].append({
                "data_saida": row_dict["data_saida"],
                "data_retorno": row_dict["data_retorno"],
                "data_saida_fmt": data_saida_fmt,
                "data_retorno_fmt": data_retorno_fmt,
                "dias": dias,
                "motivo": row_dict["motivo"],
                "unidade": row_dict["unidade"],
                "gestor": row_dict["gestor"],
                "aba_origem": row_dict["aba_origem"],
                "mes": row_dict["mes"],
                "ano": row_dict["ano"]
            })
        
        return historico

    def buscar_ferias_por_periodo(self, data_inicio: str, data_fim: str) -> List[Dict]:
        """
        Busca férias em um período específico (quem estava em férias durante o período).
        
        Args:
            data_inicio: Data início no formato YYYY-MM-DD
            data_fim: Data fim no formato YYYY-MM-DD
            
        Returns:
            Lista de funcionários com férias no período
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM funcionarios
            WHERE (
                (date(data_saida) >= ? AND date(data_saida) <= ?)
                OR (date(data_retorno) >= ? AND date(data_retorno) <= ?)
                OR (date(data_saida) <= ? AND date(data_retorno) >= ?)
            )
            ORDER BY data_saida DESC
        """, (data_inicio, data_fim, data_inicio, data_fim, data_inicio, data_fim))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_ferias_por_data_saida(self, data_inicio: str, data_fim: str) -> List[Dict]:
        """
        Busca férias onde a DATA DE SAÍDA está dentro do período.
        
        Args:
            data_inicio: Data início no formato YYYY-MM-DD
            data_fim: Data fim no formato YYYY-MM-DD
            
        Returns:
            Lista de funcionários que saem de férias no período
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM funcionarios
            WHERE date(data_saida) >= ? AND date(data_saida) <= ?
            ORDER BY data_saida ASC
        """, (data_inicio, data_fim))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_ferias_por_data_retorno(self, data_inicio: str, data_fim: str) -> List[Dict]:
        """
        Busca férias onde a DATA DE RETORNO está dentro do período.
        
        Args:
            data_inicio: Data início no formato YYYY-MM-DD
            data_fim: Data fim no formato YYYY-MM-DD
            
        Returns:
            Lista de funcionários que retornam de férias no período
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM funcionarios
            WHERE date(data_retorno) >= ? AND date(data_retorno) <= ?
            ORDER BY data_retorno ASC
        """, (data_inicio, data_fim))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_estatisticas_por_unidade(self) -> List[Dict]:
        """
        Busca estatísticas de férias agrupadas por unidade.
        
        Returns:
            Lista com unidade e total de registros
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT unidade, COUNT(*) as total
            FROM funcionarios
            WHERE unidade IS NOT NULL AND unidade != ''
            GROUP BY unidade
            ORDER BY total DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_funcionarios_por_unidade(self, unidade: str) -> List[Dict]:
        """
        Busca todos os funcionários de uma unidade específica.
        
        Args:
            unidade: Nome da unidade
            
        Returns:
            Lista de funcionários
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM funcionarios
            WHERE unidade = ?
            ORDER BY data_saida DESC
        """, (unidade,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_estatisticas_gerais(self) -> Dict:
        """
        Busca estatísticas gerais do sistema.
        
        Returns:
            Dicionário com estatísticas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total de registros
        cursor.execute("SELECT COUNT(*) as total FROM funcionarios")
        total_registros = cursor.fetchone()["total"]
        
        # Funcionários únicos
        cursor.execute("SELECT COUNT(DISTINCT nome) as total FROM funcionarios WHERE nome IS NOT NULL AND nome != ''")
        funcionarios_unicos = cursor.fetchone()["total"]
        
        # Total de unidades
        cursor.execute("SELECT COUNT(DISTINCT unidade) as total FROM funcionarios WHERE unidade IS NOT NULL AND unidade != ''")
        total_unidades = cursor.fetchone()["total"]
        
        # Total de abas
        cursor.execute("SELECT COUNT(*) as total FROM abas")
        total_abas = cursor.fetchone()["total"]
        
        conn.close()
        
        return {
            "total_registros": total_registros,
            "funcionarios_unicos": funcionarios_unicos,
            "total_unidades": total_unidades,
            "total_abas": total_abas
        }

    def buscar_estatisticas_por_ano(self) -> List[Dict]:
        """
        Busca estatísticas de férias por ano.
        
        Returns:
            Lista com ano e total de registros
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ano, COUNT(*) as total
            FROM funcionarios
            WHERE ano IS NOT NULL AND ano > 0
            GROUP BY ano
            ORDER BY ano DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_ranking_ferias(self, limite: int = 10) -> List[Dict]:
        """
        Busca ranking de funcionários com mais períodos de férias.
        
        Args:
            limite: Número máximo de resultados
            
        Returns:
            Lista com nome e total de períodos
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nome, COUNT(*) as total
            FROM funcionarios
            WHERE nome IS NOT NULL AND nome != ''
            GROUP BY nome
            ORDER BY total DESC
            LIMIT ?
        """, (limite,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_estatisticas_por_gestor(self, limite: int = 10) -> List[Dict]:
        """
        Busca estatísticas de férias por gestor.
        
        Args:
            limite: Número máximo de resultados
            
        Returns:
            Lista com gestor e total de subordinados em férias
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gestor, COUNT(*) as total
            FROM funcionarios
            WHERE gestor IS NOT NULL AND gestor != ''
            GROUP BY gestor
            ORDER BY total DESC
            LIMIT ?
        """, (limite,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_funcionarios_por_gestor(self, gestor: str, ano: int = None, mes: int = None) -> List[Dict]:
        """
        Busca todos os funcionários de um gestor específico, com filtros opcionais.
        
        Args:
            gestor: Nome do gestor
            ano: Ano para filtrar (opcional)
            mes: Mês para filtrar (opcional)
            
        Returns:
            Lista de funcionários do gestor
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Monta a cláusula WHERE
        where_clauses = ["gestor = ?"]
        params = [gestor]
        
        if ano:
            where_clauses.append("ano = ?")
            params.append(ano)
        
        if mes:
            where_clauses.append("mes = ?")
            params.append(mes)
        
        where_sql = " AND ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT * FROM funcionarios
            WHERE {where_sql}
            ORDER BY data_saida DESC
        """, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_anos_disponiveis(self) -> List[int]:
        """
        Busca lista de anos disponíveis nos dados.
        
        Returns:
            Lista de anos ordenados
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT ano
            FROM funcionarios
            WHERE ano IS NOT NULL AND ano > 0
            ORDER BY ano DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row["ano"] for row in rows]

    def buscar_ferias_por_mes(self, ano: int) -> List[Dict]:
        """
        Busca total de férias por mês em um ano específico.
        
        Args:
            ano: Ano para buscar
            
        Returns:
            Lista com mês e total
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT mes, COUNT(*) as total
            FROM funcionarios
            WHERE ano = ? AND mes IS NOT NULL AND mes > 0
            GROUP BY mes
            ORDER BY mes
        """, (ano,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    # ==================== RELATÓRIOS FILTRADOS ====================

    def buscar_estatisticas_filtradas(self, ano: int = None, mes: int = None) -> Dict:
        """
        Busca estatísticas gerais filtradas por ano e/ou mês.
        
        Args:
            ano: Ano para filtrar (opcional)
            mes: Mês para filtrar (opcional)
            
        Returns:
            Dicionário com estatísticas filtradas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Monta a cláusula WHERE
        where_clauses = []
        params = []
        
        if ano:
            where_clauses.append("ano = ?")
            params.append(ano)
        
        if mes:
            where_clauses.append("mes = ?")
            params.append(mes)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Total de registros
        cursor.execute(f"SELECT COUNT(*) as total FROM funcionarios WHERE {where_sql}", params)
        total_registros = cursor.fetchone()["total"]
        
        # Funcionários únicos
        cursor.execute(f"""
            SELECT COUNT(DISTINCT nome) as total 
            FROM funcionarios 
            WHERE {where_sql} AND nome IS NOT NULL AND nome != ''
        """, params)
        funcionarios_unicos = cursor.fetchone()["total"]
        
        # Total de unidades
        cursor.execute(f"""
            SELECT COUNT(DISTINCT unidade) as total 
            FROM funcionarios 
            WHERE {where_sql} AND unidade IS NOT NULL AND unidade != ''
        """, params)
        total_unidades = cursor.fetchone()["total"]
        
        # Total de gestores
        cursor.execute(f"""
            SELECT COUNT(DISTINCT gestor) as total 
            FROM funcionarios 
            WHERE {where_sql} AND gestor IS NOT NULL AND gestor != ''
        """, params)
        total_gestores = cursor.fetchone()["total"]
        
        conn.close()
        
        return {
            "total_registros": total_registros,
            "funcionarios_unicos": funcionarios_unicos,
            "total_unidades": total_unidades,
            "total_gestores": total_gestores
        }

    def buscar_ranking_ferias_filtrado(self, limite: int = 10, ano: int = None, mes: int = None) -> List[Dict]:
        """
        Busca ranking de funcionários com mais períodos de férias, filtrado por ano/mês.
        
        Args:
            limite: Número máximo de resultados
            ano: Ano para filtrar (opcional)
            mes: Mês para filtrar (opcional)
            
        Returns:
            Lista com nome e total de períodos
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Monta a cláusula WHERE
        where_clauses = ["nome IS NOT NULL", "nome != ''"]
        params = []
        
        if ano:
            where_clauses.append("ano = ?")
            params.append(ano)
        
        if mes:
            where_clauses.append("mes = ?")
            params.append(mes)
        
        where_sql = " AND ".join(where_clauses)
        params.append(limite)
        
        cursor.execute(f"""
            SELECT nome, COUNT(*) as total
            FROM funcionarios
            WHERE {where_sql}
            GROUP BY nome
            ORDER BY total DESC
            LIMIT ?
        """, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_estatisticas_por_gestor_filtrado(self, limite: int = 10, ano: int = None, mes: int = None) -> List[Dict]:
        """
        Busca estatísticas de férias por gestor, filtrado por ano/mês.
        
        Args:
            limite: Número máximo de resultados
            ano: Ano para filtrar (opcional)
            mes: Mês para filtrar (opcional)
            
        Returns:
            Lista com gestor e total de subordinados em férias
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Monta a cláusula WHERE
        where_clauses = ["gestor IS NOT NULL", "gestor != ''"]
        params = []
        
        if ano:
            where_clauses.append("ano = ?")
            params.append(ano)
        
        if mes:
            where_clauses.append("mes = ?")
            params.append(mes)
        
        where_sql = " AND ".join(where_clauses)
        params.append(limite)
        
        cursor.execute(f"""
            SELECT gestor, COUNT(*) as total
            FROM funcionarios
            WHERE {where_sql}
            GROUP BY gestor
            ORDER BY total DESC
            LIMIT ?
        """, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def buscar_estatisticas_por_unidade_filtrado(self, limite: int = 10, ano: int = None, mes: int = None) -> List[Dict]:
        """
        Busca estatísticas de férias por unidade, filtrado por ano/mês.
        
        Args:
            limite: Número máximo de resultados
            ano: Ano para filtrar (opcional)
            mes: Mês para filtrar (opcional)
            
        Returns:
            Lista com unidade e total de férias
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Monta a cláusula WHERE
        where_clauses = ["unidade IS NOT NULL", "unidade != ''"]
        params = []
        
        if ano:
            where_clauses.append("ano = ?")
            params.append(ano)
        
        if mes:
            where_clauses.append("mes = ?")
            params.append(mes)
        
        where_sql = " AND ".join(where_clauses)
        params.append(limite)
        
        cursor.execute(f"""
            SELECT unidade, COUNT(*) as total
            FROM funcionarios
            WHERE {where_sql}
            GROUP BY unidade
            ORDER BY total DESC
            LIMIT ?
        """, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    # ==================== OPERAÇÕES KANBANIZE ====================
    
    def salvar_cards_kanbanize(self, cards: List[Dict], board_id: int = None) -> int:
        """
        Salva cards do Kanbanize no banco de dados (cache).
        
        Args:
            cards: Lista de dicionários com dados dos cards
            board_id: ID do board (para rastreabilidade)
            
        Returns:
            Número de cards salvos/atualizados
        """
        import json
        from datetime import datetime
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        salvos = 0
        synced_at = datetime.now().isoformat()

        rows = []
        for card in cards:
            card_id = card.get('card_id')
            if not card_id:
                continue

            custom_fields_json = json.dumps(card.get('custom_fields', []))

            rows.append((
                card_id,
                board_id or card.get('board_id'),
                card.get('workflow_id'),
                card.get('workflow_name'),
                card.get('column_id'),
                card.get('column_name'),
                card.get('title'),
                card.get('description'),
                card.get('color'),
                custom_fields_json,
                card.get('created_at'),
                card.get('last_modified'),
                card.get('in_current_position_since'),
                synced_at
            ))

        if rows:
            cursor.executemany("""
                INSERT OR REPLACE INTO kanbanize_cards 
                (card_id, board_id, workflow_id, workflow_name, column_id, column_name,
                 title, description, color, custom_fields, created_at, last_modified, 
                 in_current_position_since, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            salvos = len(rows)

        conn.commit()
        conn.close()

        return salvos
    
    def buscar_cards_kanbanize(self, workflow_id: int = None, column_id: int = None, 
                               board_id: int = None) -> List[Dict]:
        """
        Busca cards do Kanbanize do cache (banco de dados).
        
        Args:
            workflow_id: Filtrar por workflow (opcional)
            column_id: Filtrar por coluna (opcional)
            board_id: Filtrar por board (opcional)
            
        Returns:
            Lista de cards encontrados
        """
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM kanbanize_cards WHERE 1=1"
        params = []
        
        if board_id:
            query += " AND board_id = ?"
            params.append(board_id)
        
        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        
        if column_id:
            query += " AND column_id = ?"
            params.append(column_id)
        
        query += " ORDER BY synced_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        cards = []
        for row in rows:
            card = self._row_to_dict(row)
            # Reconverte custom_fields de JSON
            if card.get('custom_fields'):
                try:
                    card['custom_fields'] = json.loads(card['custom_fields'])
                except:
                    card['custom_fields'] = []
            cards.append(card)
        
        conn.close()
        
        return cards
    
    def limpar_cards_kanbanize(self, board_id: int = None):
        """
        Limpa cache de cards do Kanbanize.
        
        Args:
            board_id: Se fornecido, limpa apenas este board. Senão, limpa tudo.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if board_id:
            cursor.execute("DELETE FROM kanbanize_cards WHERE board_id = ?", (board_id,))
        else:
            cursor.execute("DELETE FROM kanbanize_cards")
        
        conn.commit()
        conn.close()
    
    def obter_ultima_sincronizacao_kanbanize(self, board_id: int) -> str:
        """Obtém timestamp da última sincronização dos cards."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(synced_at) as ultima_sync
            FROM kanbanize_cards
            WHERE board_id = ?
        """, (board_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return row['ultima_sync'] if row['ultima_sync'] else None
    
    def salvar_filtro_kanbanize(self, filter_name: str, workflow_id: int = None, 
                                column_id: int = None, board_id: int = None) -> bool:
        """
        Salva um filtro para reutilização futura.
        
        Args:
            filter_name: Nome do filtro
            workflow_id: ID do workflow para filtro
            column_id: ID da coluna para filtro
            board_id: ID do board
            
        Returns:
            True se salvo com sucesso
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO kanbanize_filters
                (filter_name, workflow_id, column_id, board_id, last_used)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (filter_name, workflow_id, column_id, board_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False
    
    def buscar_filtros_kanbanize(self, board_id: int = None) -> List[Dict]:
        """Busca filtros salvos."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM kanbanize_filters WHERE 1=1"
        params = []
        
        if board_id:
            query += " AND board_id = ?"
            params.append(board_id)
        
        query += " ORDER BY last_used DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def contar_cards_cache(self, board_id: int = None) -> int:
        """Conta quantos cards estão em cache."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if board_id:
            cursor.execute("SELECT COUNT(*) as total FROM kanbanize_cards WHERE board_id = ?", (board_id,))
        else:
            cursor.execute("SELECT COUNT(*) as total FROM kanbanize_cards")
        
        result = cursor.fetchone()
        conn.close()
        
        return result['total'] if result else 0

    def remover_cards_por_nome_coluna(self, board_id: int = None, names: List[str] = None, like_patterns: List[str] = None) -> int:
        """
        Remove cards do cache cujo `column_name` corresponde a nomes/expressiones fornecidas.

        Args:
            board_id: opcional, limita a remoção a um board específico
            names: lista de nomes exatos (comparação em lowercase)
            like_patterns: lista de substrings para comparar com LIKE (comparação em lowercase)

        Returns:
            Número de registros removidos
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "DELETE FROM kanbanize_cards WHERE 1=1"
        params = []

        if board_id:
            query += " AND board_id = ?"
            params.append(board_id)

        conds = []
        if names:
            placeholders = ','.join('?' for _ in names)
            conds.append(f"lower(column_name) IN ({placeholders})")
            params.extend([n.lower() for n in names])

        if like_patterns:
            for p in like_patterns:
                conds.append("lower(column_name) LIKE ?")
                params.append(f"%{p.lower()}%")

        if conds:
            query += " AND (" + " OR ".join(conds) + ")"

        cursor.execute(query, params)
        removed = cursor.rowcount

        conn.commit()
        conn.close()

        return removed

