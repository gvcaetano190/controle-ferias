"""
Integração com Evolution API.

Envia mensagens via WhatsApp usando Evolution API.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# Tenta importar requests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class EvolutionAPI:
    """Cliente para Evolution API (WhatsApp)."""
    
    def __init__(self, url: str = None, numero: str = None, api_key: str = None):
        """
        Inicializa Evolution API.
        
        Args:
            url: URL completa do endpoint (ex: http://10.0.153.28:8081/message/sendText/zabbix)
            numero: Número/grupo do WhatsApp (ex: 120363020985287866@g.us)
            api_key: Chave da API (opcional)
        """
        self.url = url or settings.EVOLUTION_API_URL
        self.numero = numero or settings.EVOLUTION_NUMERO
        self.api_key = api_key or settings.EVOLUTION_API_KEY
        self.enabled = settings.EVOLUTION_ENABLED
    
    def enviar_mensagem(self, texto: str, numero: str = None) -> Dict:
        """
        Envia mensagem de texto via WhatsApp.
        
        Args:
            texto: Texto da mensagem
            numero: Número/grupo (opcional, usa o configurado se não fornecido)
            
        Returns:
            Dict com resultado: {"sucesso": bool, "mensagem": str}
        """
        if not self.enabled:
            return {
                "sucesso": False,
                "mensagem": "Evolution API desabilitada"
            }
        
        if not HAS_REQUESTS:
            return {
                "sucesso": False,
                "mensagem": "requests não instalado. Use: pip install requests"
            }
        
        if not self.url:
            return {
                "sucesso": False,
                "mensagem": "URL da Evolution API não configurada"
            }
        
        numero_final = numero or self.numero
        if not numero_final:
            return {
                "sucesso": False,
                "mensagem": "Número/grupo do WhatsApp não configurado"
            }
        
        # Formata o número: se não começar com código do país e não for grupo, adiciona 55 (Brasil)
        numero_formatado = str(numero_final).strip()
        
        # Se já termina com @g.us ou @s.whatsapp.net, é grupo/contato já formatado
        if "@" in numero_formatado:
            numero_final = numero_formatado
        else:
            # Remove caracteres não numéricos
            numero_limpo = ''.join(filter(str.isdigit, numero_formatado))
            
            # Se não começa com 55 (Brasil) e tem 10 ou 11 dígitos, adiciona 55
            if not numero_limpo.startswith("55") and len(numero_limpo) >= 10:
                numero_limpo = "55" + numero_limpo
            
            numero_final = numero_limpo
        
        try:
            payload = {
                "number": numero_final,
                "text": texto
            }
            
            # Headers (sempre inclui Content-Type)
            headers = {
                "Content-Type": "application/json"
            }
            
            # Adiciona API Key no header se configurado (não vazio)
            if self.api_key and self.api_key.strip():
                headers["apikey"] = self.api_key.strip()
            
            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Aceita 200 (OK) e 201 (Created) como sucesso
            if response.status_code in [200, 201]:
                return {
                    "sucesso": True,
                    "mensagem": "Mensagem enviada com sucesso",
                    "status_code": response.status_code
                }
            else:
                return {
                    "sucesso": False,
                    "mensagem": f"Erro HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "sucesso": False,
                "mensagem": "Erro de conexão: não foi possível conectar ao servidor"
            }
        except requests.exceptions.Timeout:
            return {
                "sucesso": False,
                "mensagem": "Timeout: servidor não respondeu a tempo"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro inesperado: {str(e)}"
            }
    
    def enviar_mensagem_teste(self) -> Dict:
        """Envia mensagem de teste."""
        texto = f"""
🧪 *Teste de Integração*

Este é um teste do sistema de Controle de Férias.

*Data/Hora:* {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}

Se você recebeu esta mensagem, a integração está funcionando! ✅
        """.strip()
        
        return self.enviar_mensagem(texto)
    
    def enviar_mensagem_sync(self, resultado: Dict) -> Dict:
        """
        Envia notificação após sincronização.
        
        Args:
            resultado: Dict com resultado da sincronização:
                - status: "success" | "skipped" | "error"
                - registros: int (número de registros processados)
                - message: str (mensagem descritiva)
        """
        hoje = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
        
        if resultado.get("status") == "success":
            registros = resultado.get("registros", 0)
            texto = f"""
🔄 *Sincronização Concluída*

*Data/Hora:* {hoje}

✅ Sincronização realizada com sucesso!
📊 *Registros processados:* {registros}

_Sistema de Controle de Férias_
            """.strip()
        elif resultado.get("status") == "skipped":
            motivo = resultado.get("message", "Arquivo não foi alterado")
            texto = f"""
⏭️ *Sincronização Pulada*

*Data/Hora:* {hoje}

{motivo}

_Sistema de Controle de Férias_
            """.strip()
        else:
            erro = resultado.get("message", "Erro desconhecido")
            texto = f"""
❌ *Erro na Sincronização*

*Data/Hora:* {hoje}

Erro: {erro}

_Sistema de Controle de Férias_
            """.strip()
        
        return self.enviar_mensagem(texto)
    
    def enviar_aviso_ferias(self, funcionario: Dict) -> Dict:
        """
        Envia aviso de férias próximas para um funcionário.
        
        Args:
            funcionario: Dict com dados do funcionário:
                - nome: str
                - data_saida: str (formato YYYY-MM-DD)
                - unidade: str (opcional)
        """
        nome = funcionario.get("nome", "Funcionário")
        data_saida_str = funcionario.get("data_saida", "")
        unidade = funcionario.get("unidade", "")
        
        # Formata data de saída
        try:
            data_obj = datetime.strptime(data_saida_str, '%Y-%m-%d')
            data_formatada = data_obj.strftime('%d/%m/%Y')
            
            # Calcula dias até a saída
            dias_restantes = (data_obj - datetime.now()).days
            if dias_restantes == 0:
                dias_texto = "hoje"
            elif dias_restantes == 1:
                dias_texto = "amanhã"
            else:
                dias_texto = f"em {dias_restantes} dias"
        except:
            data_formatada = data_saida_str
            dias_texto = "em breve"
        
        # Evita backslashes dentro de expressão em f-string
        unidade_block = f"*Unidade:* {unidade}\n" if unidade else ""
        
        texto = f"""
📅 *Aviso de Férias Próximas*

*Funcionário:* {nome}
{unidade_block}🏖️ *Data de Saída:* {data_formatada} ({dias_texto})

⚠️ Prepare os acessos para bloqueio.

_Sistema de Controle de Férias_
        """.strip()
        
        return self.enviar_mensagem(texto)


class MensagensAutomaticas:
    """Gera mensagens automáticas do sistema."""
    
    def __init__(self, evolution_api: EvolutionAPI = None):
        self.evolution_api = evolution_api or EvolutionAPI()
        self.db = None  # Será inicializado quando necessário
    
    def _get_db(self):
        """Lazy load do database."""
        if self.db is None:
            from core.database import Database
            self.db = Database()
        return self.db
    
    def gerar_mensagem_manha(self) -> str:
        """
        Gera mensagem para enviar de manhã:
        - Quem sai hoje de férias
        - Quem voltaria hoje mas não foi alterado para liberado
        """
        db = self._get_db()
        
        hoje = datetime.now().strftime('%d/%m/%Y')
        
        # Funcionários saindo hoje
        saindo_hoje = db.buscar_saindo_hoje()
        
        # Funcionários que voltariam hoje mas ainda estão bloqueados
        voltando_hoje_com_bloqueios = []
        funcionarios_voltando = db.buscar_funcionarios()
        
        for func in funcionarios_voltando:
            if func.get("data_retorno") == datetime.now().strftime('%Y-%m-%d'):
                acessos = func.get("acessos", {})
                # Verifica se tem algum bloqueado
                tem_bloqueado = any(
                    status == "BLOQUEADO" 
                    for sistema, status in acessos.items()
                )
                if tem_bloqueado:
                    voltando_hoje_com_bloqueios.append(func)
        
        # Monta mensagem
        mensagem = f"🌅 *Relatório Matutino - {hoje}*\n\n"
        
        # Seção: Saindo hoje
        if saindo_hoje:
            mensagem += f"🏖️ *Saindo de Férias Hoje ({len(saindo_hoje)}):*\n"
            for func in saindo_hoje:
                mensagem += f"• {func.get('nome', 'N/A')}\n"
            mensagem += "\n"
        else:
            mensagem += "✅ Nenhum funcionário saindo de férias hoje.\n\n"
        
        # Seção: Voltariam hoje mas ainda bloqueados
        if voltando_hoje_com_bloqueios:
            mensagem += f"⚠️ *Atenção - Voltariam Hoje mas Ainda Bloqueados ({len(voltando_hoje_com_bloqueios)}):*\n"
            for func in voltando_hoje_com_bloqueios:
                nome = func.get('nome', 'N/A')
                acessos_bloqueados = [
                    sistema for sistema, status in func.get('acessos', {}).items()
                    if status == "BLOQUEADO"
                ]
                mensagem += f"• {nome} - Bloqueados: {', '.join(acessos_bloqueados)}\n"
            mensagem += "\n"
        else:
            mensagem += "✅ Todos que voltam hoje têm acessos liberados.\n\n"
        
        mensagem += "_Sistema de Controle de Férias_"
        
        return mensagem
    
    def gerar_mensagem_tarde(self) -> str:
        """
        Gera mensagem para enviar no final da tarde:
        - Quem volta amanhã (ou segunda-feira se for sexta)
        - Quem está de férias com acessos NB (não bloqueado/pendente)
        """
        db = self._get_db()
        
        hoje = datetime.now()
        hoje_str = hoje.strftime('%d/%m/%Y')
        dia_semana = hoje.weekday()  # 0=segunda, 4=sexta
        
        # Funcionários voltando amanhã (ou segunda se for sexta)
        voltando_amanha = db.buscar_voltando_amanha()
        
        # Determina texto da data de retorno
        if dia_semana == 4:  # Sexta-feira
            proxima_segunda = (hoje + timedelta(days=3)).strftime('%d/%m/%Y')
            texto_data = f"Segunda-feira ({proxima_segunda})"
        else:
            amanha = (hoje + timedelta(days=1)).strftime('%d/%m/%Y')
            texto_data = f"Amanhã ({amanha})"
        
        # Funcionários em férias com acessos pendentes (NB)
        em_ferias_com_pendentes = db.buscar_acessos_pendentes()
        
        # Monta mensagem
        mensagem = f"🌆 *Relatório Vespertino - {hoje_str}*\n\n"
        
        # Seção: Voltando amanhã/segunda
        if voltando_amanha:
            mensagem += f"📅 *Voltando {texto_data} - {len(voltando_amanha)} funcionário(s):*\n"
            for func in voltando_amanha:
                nome = func.get('nome', 'N/A')
                acessos = func.get('acessos', {})
                
                # Verifica status dos acessos
                tem_bloqueado = any(
                    status == "BLOQUEADO" 
                    for sistema, status in acessos.items()
                )
                
                tem_pendente = any(
                    status == "PENDENTE" 
                    for sistema, status in acessos.items()
                )
                
                # Conta acessos por status
                total_acessos = len(acessos) if acessos else 0
                acessos_liberados = sum(
                    1 for status in acessos.values() 
                    if status == "LIBERADO"
                )
                
                # Define status
                if tem_bloqueado:
                    acessos_bloqueados = [
                        sistema for sistema, status in acessos.items()
                        if status == "BLOQUEADO"
                    ]
                    mensagem += f"• {nome} - ⚠️ Bloqueados: {', '.join(acessos_bloqueados)}\n"
                elif tem_pendente:
                    acessos_pendentes = [
                        sistema for sistema, status in acessos.items()
                        if status == "PENDENTE"
                    ]
                    mensagem += f"• {nome} - ⏳ Pendentes: {', '.join(acessos_pendentes)}\n"
                elif total_acessos > 0 and acessos_liberados == total_acessos:
                    mensagem += f"• {nome} - ✅ Todos os acessos liberados\n"
                else:
                    # Caso não tenha acessos configurados ou status misto
                    mensagem += f"• {nome}\n"
            mensagem += "\n"
        else:
            mensagem += f"✅ Nenhum funcionário voltando {texto_data.lower()}.\n\n"
        
        # Seção: Em férias com acessos NB
        if em_ferias_com_pendentes:
            mensagem += f"⚠️ *Atenção - Em Férias com Acessos Pendentes (NB) ({len(em_ferias_com_pendentes)}):*\n"
            for func in em_ferias_com_pendentes:
                nome = func.get('nome', 'N/A')
                acessos_pendentes = [
                    sistema for sistema, status in func.get('acessos', {}).items()
                    if status == "PENDENTE"
                ]
                if acessos_pendentes:
                    mensagem += f"• {nome} - Pendentes: {', '.join(acessos_pendentes)}\n"
            mensagem += "\n"
        else:
            mensagem += "✅ Todos em férias têm acessos configurados.\n\n"
        
        mensagem += "_Sistema de Controle de Férias_"
        
        return mensagem
    
    def enviar_mensagem_manha(self) -> Dict:
        """Envia mensagem matutina."""
        texto = self.gerar_mensagem_manha()
        return self.evolution_api.enviar_mensagem(texto)
    
    def enviar_mensagem_tarde(self) -> Dict:
        """Envia mensagem vespertina."""
        texto = self.gerar_mensagem_tarde()
        return self.evolution_api.enviar_mensagem(texto)
