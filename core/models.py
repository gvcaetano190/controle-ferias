"""
Modelos de dados do sistema.

Define as estruturas de dados usadas em todo o sistema.
Preparado para uso com SQLAlchemy (futuro FastAPI).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Funcionario:
    """Representa um funcionário com período de férias."""
    
    id: Optional[int] = None
    nome: str = ""
    unidade: str = ""
    motivo: str = ""
    data_saida: Optional[datetime] = None
    data_retorno: Optional[datetime] = None
    gestor: str = ""
    aba_origem: str = ""
    mes: int = 0
    ano: int = 0
    acessos: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "nome": self.nome,
            "unidade": self.unidade,
            "motivo": self.motivo,
            "data_saida": self.data_saida.strftime('%Y-%m-%d') if self.data_saida else None,
            "data_retorno": self.data_retorno.strftime('%Y-%m-%d') if self.data_retorno else None,
            "gestor": self.gestor,
            "aba_origem": self.aba_origem,
            "mes": self.mes,
            "ano": self.ano,
            "acessos": self.acessos,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Funcionario":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id"),
            nome=data.get("nome", ""),
            unidade=data.get("unidade", ""),
            motivo=data.get("motivo", ""),
            data_saida=datetime.strptime(data["data_saida"], '%Y-%m-%d') if data.get("data_saida") else None,
            data_retorno=datetime.strptime(data["data_retorno"], '%Y-%m-%d') if data.get("data_retorno") else None,
            gestor=data.get("gestor", ""),
            aba_origem=data.get("aba_origem", ""),
            mes=data.get("mes", 0),
            ano=data.get("ano", 0),
            acessos=data.get("acessos", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )
    
    def em_ferias(self, data_ref: datetime = None) -> bool:
        """Verifica se está em férias na data de referência."""
        if not self.data_saida or not self.data_retorno:
            return False
        
        ref = data_ref or datetime.now()
        ref_date = ref.date() if hasattr(ref, 'date') else ref
        
        return self.data_saida.date() <= ref_date <= self.data_retorno.date()


@dataclass
class Aba:
    """Representa uma aba (mês) da planilha."""
    
    id: Optional[int] = None
    nome: str = ""
    mes: int = 0
    ano: int = 0
    total_funcionarios: int = 0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "mes": self.mes,
            "ano": self.ano,
            "total_funcionarios": self.total_funcionarios,
        }


@dataclass
class SyncLog:
    """Log de sincronização."""
    
    id: Optional[int] = None
    sync_at: Optional[datetime] = None
    total_registros: int = 0
    total_abas: int = 0
    status: str = ""
    mensagem: str = ""
    arquivo_hash: str = ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sync_at": self.sync_at.isoformat() if self.sync_at else None,
            "total_registros": self.total_registros,
            "total_abas": self.total_abas,
            "status": self.status,
            "mensagem": self.mensagem,
            "arquivo_hash": self.arquivo_hash,
        }


@dataclass
class PasswordLink:
    """Representa um link de senha gerado."""

    id: Optional[int] = None
    senha_usada: str = ""  # Senha que foi compartilhada (mascarada no banco)
    link_url: str = ""     # URL completa do OneTimeSecret
    secret_key: str = ""   # Chave secreta do OneTimeSecret
    ttl_seconds: int = 3600  # Tempo de vida em segundos
    criado_em: Optional[datetime] = None
    expirado_em: Optional[datetime] = None
    visualizado: bool = False  # Se foi visualizado/acessado
    finalidade: str = ""      # Propósito (ex: "acesso_AD", "vpn_temp", etc.)
    usuario_criador: str = "" # Quem criou o link

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "senha_usada": self.senha_usada,
            "link_url": self.link_url,
            "secret_key": self.secret_key,
            "ttl_seconds": self.ttl_seconds,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "expirado_em": self.expirado_em.isoformat() if self.expirado_em else None,
            "visualizado": self.visualizado,
            "finalidade": self.finalidade,
            "usuario_criador": self.usuario_criador,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PasswordLink":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id"),
            senha_usada=data.get("senha_usada", ""),
            link_url=data.get("link_url", ""),
            secret_key=data.get("secret_key", ""),
            ttl_seconds=data.get("ttl_seconds", 3600),
            criado_em=datetime.fromisoformat(data["criado_em"]) if data.get("criado_em") else None,
            expirado_em=datetime.fromisoformat(data["expirado_em"]) if data.get("expirado_em") else None,
            visualizado=data.get("visualizado", False),
            finalidade=data.get("finalidade", ""),
            usuario_criador=data.get("usuario_criador", ""),
        )

    def esta_expirado(self) -> bool:
        """Verifica se o link já expirou."""
        if not self.criado_em:
            return False

        tempo_decorrido = datetime.now() - self.criado_em
        return tempo_decorrido.total_seconds() > self.ttl_seconds

    def tempo_restante_horas(self) -> float:
        """Retorna tempo restante em horas."""
        if not self.criado_em or self.esta_expirado():
            return 0.0

        tempo_decorrido = datetime.now() - self.criado_em
        restante_segundos = self.ttl_seconds - tempo_decorrido.total_seconds()
        return max(0, restante_segundos / 3600)


# ==================== SQLALCHEMY MODELS (FUTURO FASTAPI) ====================
#
# Para migrar para FastAPI, descomente e use estes models:
#
# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship
#
# Base = declarative_base()
#
# class FuncionarioDB(Base):
#     __tablename__ = "funcionarios"
#
#     id = Column(Integer, primary_key=True, index=True)
#     nome = Column(String, index=True)
#     unidade = Column(String)
#     motivo = Column(String)
#     data_saida = Column(DateTime)
#     data_retorno = Column(DateTime)
#     gestor = Column(String)
#     aba_origem = Column(String)
#     mes = Column(Integer)
#     ano = Column(Integer)
#     created_at = Column(DateTime, default=datetime.now)
#
#     acessos = relationship("AcessoDB", back_populates="funcionario")
#
# class AcessoDB(Base):
#     __tablename__ = "acessos"
#
#     id = Column(Integer, primary_key=True, index=True)
#     funcionario_id = Column(Integer, ForeignKey("funcionarios.id"))
#     sistema = Column(String)
#     status = Column(String)
#
#     funcionario = relationship("FuncionarioDB", back_populates="acessos")
#
# class PasswordLinkDB(Base):
#     __tablename__ = "password_links"
#
#     id = Column(Integer, primary_key=True, index=True)
#     senha_usada = Column(String)  # Hash/mascarada por segurança
#     link_url = Column(String, unique=True)
#     secret_key = Column(String)
#     ttl_seconds = Column(Integer)
#     criado_em = Column(DateTime, default=datetime.now)
#     expirado_em = Column(DateTime, nullable=True)
#     visualizado = Column(Boolean, default=False)
#     finalidade = Column(String)
#     usuario_criador = Column(String)

