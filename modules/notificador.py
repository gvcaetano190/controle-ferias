# ============================================
# MÓDULO: NOTIFICADOR
# Responsabilidade: Formatar e preparar mensagens
# (Futuro: integração com Evolution API)
# ============================================

from typing import List
from datetime import datetime
from .processador import Funcionario


class Notificador:
    """Classe responsável por formatar e exibir notificações."""
    
    def __init__(self):
        self.mensagens: List[str] = []
    
    def formatar_data(self, data: datetime) -> str:
        """Formata data para exibição."""
        return data.strftime("%d/%m/%Y")
    
    def gerar_mensagem_saida_hoje(self, funcionarios: List[Funcionario]) -> str:
        """Gera mensagem para quem sai hoje."""
        if not funcionarios:
            return "✅ Nenhum funcionário saindo de férias hoje."
        
        hoje = datetime.now().strftime("%d/%m/%Y")
        linhas = [
            f"🏖️ *SAINDO DE FÉRIAS HOJE ({hoje})*",
            f"Total: {len(funcionarios)} pessoa(s)",
            "-" * 40
        ]
        
        for i, f in enumerate(funcionarios, 1):
            linhas.append(
                f"{i}. *{f.nome}*\n"
                f"   📅 Retorno: {self.formatar_data(f.data_retorno)}\n"
                f"   👤 Gestor: {f.gestor}\n"
                f"   📋 Motivo: {f.motivo}"
            )
        
        return "\n".join(linhas)
    
    def gerar_mensagem_retorno_amanha(self, funcionarios: List[Funcionario]) -> str:
        """Gera mensagem para quem volta amanhã."""
        if not funcionarios:
            return "✅ Nenhum funcionário retornando amanhã."
        
        from datetime import timedelta
        amanha = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        
        linhas = [
            f"🔙 *RETORNANDO AMANHÃ ({amanha})*",
            f"Total: {len(funcionarios)} pessoa(s)",
            "-" * 40
        ]
        
        for i, f in enumerate(funcionarios, 1):
            dias = f.dias_ausencia()
            linhas.append(
                f"{i}. *{f.nome}*\n"
                f"   📅 Saiu em: {self.formatar_data(f.data_saida)}\n"
                f"   ⏱️ Dias ausente: {dias}\n"
                f"   👤 Gestor: {f.gestor}"
            )
        
        return "\n".join(linhas)
    
    def gerar_resumo_diario(self, saindo: List[Funcionario], voltando: List[Funcionario]) -> str:
        """Gera resumo diário completo."""
        hoje = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        linhas = [
            "=" * 50,
            f"📊 RESUMO DIÁRIO - {hoje}",
            "=" * 50,
            "",
            self.gerar_mensagem_saida_hoje(saindo),
            "",
            "-" * 50,
            "",
            self.gerar_mensagem_retorno_amanha(voltando),
            "",
            "=" * 50
        ]
        
        return "\n".join(linhas)
    
    def exibir_terminal(self, mensagem: str):
        """Exibe mensagem no terminal."""
        print(mensagem)
    
    # ==========================================
    # MÉTODOS PARA FUTURA INTEGRAÇÃO EVOLUTION API
    # ==========================================
    
    def preparar_para_whatsapp(self, mensagem: str) -> dict:
        """
        Prepara payload para envio via Evolution API.
        (Implementar quando integrar)
        """
        return {
            "number": "",  # Número do destinatário
            "text": mensagem,
            "delay": 1200
        }
    
    async def enviar_whatsapp(self, numero: str, mensagem: str):
        """
        Envia mensagem via Evolution API.
        (Implementar quando integrar)
        """
        # TODO: Implementar integração com Evolution API
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "http://localhost:8080/message/sendText/instance",
        #         json=self.preparar_para_whatsapp(mensagem)
        #     )
        pass
