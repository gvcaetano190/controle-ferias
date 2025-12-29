"""
Componentes reutilizáveis do frontend.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List


def formatar_data(data_str: str) -> str:
    """Formata data para DD/MM/YYYY."""
    if not data_str:
        return ""
    try:
        if 'T' in str(data_str):
            dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(str(data_str).split()[0], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except:
        return str(data_str)


def status_emoji(status: str) -> str:
    """Retorna emoji/texto para status de acesso."""
    status = (status or "").upper()
    
    if status == "BLOQUEADO":
        return "🔴"
    elif status == "LIBERADO":
        return "🟢"
    elif status == "PENDENTE":
        return "NB"  # Não Bloqueado
    elif status in ["NA", "N/A", "NP", "N/P"]:
        return "NP"  # Não Possui
    return "NP"


def exibir_tabela_funcionarios(funcionarios: List[Dict], mostrar_acessos: bool = True):
    """Exibe tabela de funcionários."""
    if not funcionarios:
        st.info("Nenhum funcionário encontrado.")
        return
    
    dados_tabela = []
    for f in funcionarios:
        row = {
            "Nome": f.get("nome", ""),
            "Motivo": f.get("motivo", ""),
            "Saída": formatar_data(f.get("data_saida", "")),
            "Retorno": formatar_data(f.get("data_retorno", "")),
            "Gestor": f.get("gestor", ""),
            "Unidade": f.get("unidade", ""),
        }
        
        if mostrar_acessos and "acessos" in f:
            acessos = f.get("acessos", {})
            row["AD"] = status_emoji(acessos.get("AD PRIN", "NA"))
            row["VPN"] = status_emoji(acessos.get("VPN", "NA"))
            row["Gmail"] = status_emoji(acessos.get("Gmail", "NA"))
            row["Admin"] = status_emoji(acessos.get("Admin", "NA"))
            row["Metrics"] = status_emoji(acessos.get("Metrics", "NA"))
            row["TOTVS"] = status_emoji(acessos.get("TOTVS", "NA"))
        
        dados_tabela.append(row)
    
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, width='stretch', hide_index=True)


def exibir_resumo_acessos(resumo: Dict):
    """Exibe resumo dos acessos por sistema."""
    if not resumo:
        return
    
    st.subheader("📊 Resumo de Acessos")
    
    sistemas = ["AD PRIN", "VPN", "Gmail", "Admin", "Metrics", "TOTVS"]
    dados = []
    
    for sistema in sistemas:
        if sistema in resumo:
            dados.append({
                "Sistema": sistema,
                "🔴 Bloqueado": resumo[sistema].get("BLOQUEADO", 0),
                "🟢 Liberado": resumo[sistema].get("LIBERADO", 0),
                "⬜ Pendente": resumo[sistema].get("PENDENTE", 0),
                "⚪ N/A": resumo[sistema].get("NA", 0),
            })
    
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df, width='stretch', hide_index=True)

