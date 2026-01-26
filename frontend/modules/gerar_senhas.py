"""
Página de Gerar Senhas via OneTimeSecret.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import traceback

from config.settings import settings
from integrations.onetimesecret import OneTimeSecretAPI
from frontend.components import formatar_data


def render(database):
    """Renderiza a página de gerar senhas."""
    st.header("🔑 Gerar Senhas - OneTimeSecret")
    
    # Verifica se está habilitado
    if not settings.ONETIMESECRET_ENABLED:
        st.warning("⚠️ OneTimeSecret está desabilitado. Habilite nas configurações.")
        return
    
    # Tabs
    tab_gerar, tab_historico, tab_templates = st.tabs(["🔑 Gerar Senhas", "📋 Histórico", "🎯 Templates"])
    
    # ==================== ABA: GERAR SENHAS ====================
    with tab_gerar:
        # Busca pessoas voltando para usar na lógica
        voltando_proximo_dia = database.buscar_retornos_proximo_dia_util()
        
        # Determina texto "Amanhã" ou "Segunda"
        hoje = datetime.now()
        dia_semana = hoje.weekday()
        texto_voltando = "Segunda-feira" if dia_semana >= 4 else "Amanhã"
        
        # --- SELETOR DE MODO (Fora do form para atualizar a UI) ---
        col_modo_1, col_modo_2 = st.columns([1, 2])
        with col_modo_1:
            modo_geracao = st.radio(
                "Modo de Geração:",
                ["Individual", f"Em Lote (Voltando {texto_voltando})"],
                help="Individual cria links genéricos. Em Lote cria um link específico para cada pessoa voltando de férias."
            )
            is_lote = "Em Lote" in modo_geracao
        
        if is_lote and not voltando_proximo_dia:
            st.info(f"ℹ️ Ninguém voltando de férias {texto_voltando.lower()}. Mudando para modo Individual.")
            is_lote = False
        
        st.divider()
        
        # --- GERAÇÃO AUTOMÁTICA DE SENHA ---
        with st.expander("⚡ Gerador de Senha Forte (Opcional)", expanded=False):
            # Modo de geração
            modo_geracao_senha = st.radio(
                "Modo:",
                ["Senha Aleatória", "Palavra Fortalecida"],
                horizontal=True,
                key="modo_geracao_senha"
            )
            
            # Campo para palavra base (só aparece em modo Palavra Fortalecida)
            palavra_base = ""
            if modo_geracao_senha == "Palavra Fortalecida":
                palavra_base = st.text_input(
                    "🔤 Palavra base (opcional):",
                    placeholder="Ex: gabriel",
                    help="Digite uma palavra e ela será transformada em senha forte com maiúsculas, números e símbolos",
                    key="palavra_base_input"
                )
            
            if modo_geracao_senha == "Palavra Fortalecida":
                # Opções para fortalecer palavra
                col_p1, col_p2, col_p3 = st.columns([2, 2, 2])
                with col_p1:
                    comprimento_palavra = st.slider("Comprimento:", 8, 32, 16, key="comp_palavra")
                with col_p2:
                    incluir_maiusculas_palavra = st.checkbox("Maiúsculas (ABC)", value=True, key="add_maiusc_palavra")
                    incluir_numeros = st.checkbox("Números (123)", value=True, key="add_nums_palavra")
                with col_p3:
                    incluir_minusculas_palavra = st.checkbox("Minúsculas (abc)", value=True, key="add_minusc_palavra")
                    adicionar_simbolos = st.checkbox("Símbolos (!@#)", value=True, key="add_simbs_palavra")
                
                if st.button("🎲 Fortalecer Palavra", type="secondary", width="stretch"):
                    if palavra_base:
                        from utils.password_generator import password_generator
                        # Verifica se o método existe (para evitar erros de cache)
                        if hasattr(password_generator, 'fortalecer_palavra'):
                            senha = password_generator.fortalecer_palavra(
                                palavra=palavra_base,
                                adicionar_numeros=incluir_numeros,
                                adicionar_simbolos=adicionar_simbolos
                            )
                            st.session_state["senha_gerada"] = senha
                        else:
                            # Fallback: implementação inline se o método não estiver disponível
                            import random
                            palavra = palavra_base.strip().lower()
                            palavra_fortalecida = ""
                            
                            # Processa a palavra com as opções selecionadas
                            for i, char in enumerate(palavra):
                                if char.isalpha():
                                    if incluir_maiusculas_palavra and i == 0:
                                        palavra_fortalecida += char.upper()
                                    elif incluir_maiusculas_palavra and i % 2 == 0:
                                        palavra_fortalecida += char.upper()
                                    elif incluir_minusculas_palavra:
                                        palavra_fortalecida += char.lower()
                                    else:
                                        palavra_fortalecida += char
                                else:
                                    palavra_fortalecida += char
                            
                            if incluir_numeros:
                                numeros = ''.join(random.choices('0123456789', k=random.randint(2, 3)))
                                palavra_fortalecida += numeros
                            
                            if adicionar_simbolos:
                                simbolos = ''.join(random.choices('!@#$%^&*()_+-=[]{}|;:,.<>?', k=random.randint(1, 2)))
                                palavra_fortalecida += simbolos
                            
                            # Limita ao comprimento escolhido
                            if len(palavra_fortalecida) > comprimento_palavra:
                                palavra_fortalecida = palavra_fortalecida[:comprimento_palavra]
                            elif len(palavra_fortalecida) < comprimento_palavra:
                                chars_faltantes = comprimento_palavra - len(palavra_fortalecida)
                                chars_disponiveis = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'
                                palavra_fortalecida += ''.join(random.choices(chars_disponiveis, k=chars_faltantes))
                            
                            st.session_state["senha_gerada"] = palavra_fortalecida
                            st.warning("⚠️ Usando implementação alternativa (recarregue a página para usar a versão completa)")
                    else:
                        st.warning("⚠️ Digite uma palavra para fortalecer")
            else:
                # Modo senha aleatória (original)
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    comprimento = st.slider("Comprimento:", 8, 32, 16)
                with col2:
                    incluir_maiusculas = st.checkbox("Maiúsculas (ABC)", value=True)
                    incluir_numeros = st.checkbox("Números (123)", value=True)
                with col3:
                    incluir_simbolos = st.checkbox("Símbolos (!@#)", value=True)
                
                if st.button("🎲 Gerar Senha", type="secondary", width="stretch"):
                    from utils.password_generator import password_generator
                    senha = password_generator.gerar_senha_forte(
                        length=comprimento,
                        include_uppercase=incluir_maiusculas,
                        include_digits=incluir_numeros,
                        include_symbols=incluir_simbolos
                    )
                    st.session_state["senha_gerada"] = senha
            
            # Exibe senha gerada
            if "senha_gerada" in st.session_state:
                st.markdown("**Senha gerada:**")
                st.code(st.session_state["senha_gerada"], language=None)
                if st.button("📋 Copiar para Formulário", width="stretch"):
                    st.session_state["senha_base_input"] = st.session_state["senha_gerada"]
                    st.success("✅ Copiada para o campo de senha!")
        
        # --- FORMULÁRIO ---
        st.markdown(f"### 🔗 Configurar Links ({'Múltiplos Usuários' if is_lote else 'Link Único/Genérico'})")
        
        with st.form("form_gerar_senhas", clear_on_submit=True):
            # Inicializa input de senha
            if "senha_base_input" not in st.session_state:
                st.session_state["senha_base_input"] = ""
            
            col1, col2 = st.columns([2, 1])
            with col1:
                senha_base = st.text_input(
                    "🔐 Senha Base:",
                    type="password",
                    key="senha_base_input",
                    help="Senha inicial. Se 'Incrementar' estiver marcado, adicionará números ao final."
                )
            with col2:
                incrementar = st.checkbox(
                    "➕ Incrementar Senha",
                    value=is_lote,  # Padrão True se for lote
                    help="Ex: Senha1, Senha2, Senha3..."
                )
            
            # Lógica de exibição baseada no modo
            pessoas_alvo = []  # Lista de (Nome, ID/Ref)
            
            if is_lote:
                st.info(f"👥 Serão gerados **{len(voltando_proximo_dia)} links**, um para cada funcionário abaixo:")
                # Mostra quem vai receber
                cols_nomes = st.columns(3)
                for i, p in enumerate(voltando_proximo_dia):
                    with cols_nomes[i % 3]:
                        st.markdown(f"• **{p['nome']}**")
                
                pessoas_alvo = [{"nome": p['nome'], "gestor": p.get('gestor', ''), "referencia": f"Retorno Férias - {p['nome']}"} for p in voltando_proximo_dia]
                quantidade = len(voltando_proximo_dia)
                descricao_geral = f"Acesso Retorno Férias ({texto_voltando})"
            else:
                # Modo Individual
                col_qtd, col_desc = st.columns([1, 2])
                with col_qtd:
                    quantidade = st.number_input("Quantidade:", 1, 20, 1)
                with col_desc:
                    descricao_geral = st.text_input("Descrição (Opcional):", placeholder="Ex: VPN Temporária")
                
                # Cria lista genérica
                for i in range(quantidade):
                    pessoas_alvo.append({"nome": "Genérico", "referencia": descricao_geral})
            
            # Seleção de pessoa (referência)
            if not is_lote:
                # No modo individual, permite selecionar qualquer funcionário como referência
                # Busca todos os funcionários únicos
                todos_funcionarios = database.buscar_funcionarios()
                nomes_unicos = sorted(set(p['nome'] for p in todos_funcionarios if p.get('nome')))
                nomes_disponiveis = ["Nenhuma"] + nomes_unicos
                pessoa_selecionada = st.selectbox(
                    "👤 Funcionário (Referência):",
                    nomes_disponiveis,
                    help="Selecione um funcionário como referência (opcional)"
                )
                if pessoa_selecionada != "Nenhuma":
                    # Busca o gestor do funcionário selecionado
                    gestor_selecionado = ""
                    for func in todos_funcionarios:
                        if func.get('nome') == pessoa_selecionada:
                            gestor_selecionado = func.get('gestor', '')
                            break
                    pessoas_alvo = [{"nome": pessoa_selecionada, "gestor": gestor_selecionado, "referencia": f"Retorno Férias - {pessoa_selecionada}"} for _ in range(quantidade)]
            
            st.markdown("#### ⚙️ Configurações do Link")
            col_ttl, col_fin = st.columns(2)
            with col_ttl:
                ttl = st.number_input("⏰ Validade (horas):", 1, 168, 24)
            with col_fin:
                finalidade = st.selectbox("🎯 Finalidade:", ["Acesso Temporário", "VPN", "Email", "Admin", "Outro"])
            
            submitted = st.form_submit_button(
                f"🚀 Gerar {quantidade} Link(s)",
                type="primary",
                width="stretch"
            )
        
        # --- LÓGICA DE EXECUÇÃO (FORA DO FORM) ---
        if submitted:
            # Recupera senha do state se o form limpar
            if not senha_base:
                senha_base = st.session_state.get("senha_base_input", "")
            
            if not senha_base:
                st.error("❌ Digite uma senha base.")
            else:
                # Preparação API
                ots_email = settings.ONETIMESECRET_EMAIL
                ots_api_key = settings.ONETIMESECRET_API_KEY
                
                if not ots_email or not ots_api_key:
                    st.error("❌ Credenciais API não configuradas.")
                else:
                    api = OneTimeSecretAPI(email=ots_email, api_key=ots_api_key)
                    ttl_segundos = ttl * 3600
                    sucessos = []
                    erros = []
                    
                    with st.spinner(f"Gerando links para {len(pessoas_alvo)} usuários..."):
                        # Loop manual para ter controle total sobre quem é quem
                        for i, alvo in enumerate(pessoas_alvo):
                            # Calcula senha
                            if incrementar and (i > 0 or is_lote):
                                suffix = i + 1
                                senha_atual = f"{senha_base}{suffix}"
                            else:
                                senha_atual = senha_base
                            
                            # Chama API
                            res = api.criar_senha(senha_atual, ttl=ttl_segundos)
                            
                            if res.get("sucesso"):
                                # Adiciona dados extras ao resultado para exibição
                                res["nome_pessoa"] = alvo["nome"] if is_lote or alvo["nome"] != "Genérico" else ""
                                res["gestor_pessoa"] = alvo.get("gestor", "")
                                res["senha_usada"] = senha_atual
                                res["numero"] = i + 1
                                
                                # Salva no Banco
                                agora = datetime.now()
                                expirado_em = agora + timedelta(seconds=ttl_segundos)
                                link_data = {
                                    "senha_usada": senha_atual,  # Senha completa sem máscara
                                    "link_url": res.get("link", ""),
                                    "secret_key": res.get("secret_key", ""),
                                    "metadata_key": res.get("metadata_key", ""),
                                    "ttl_seconds": ttl_segundos,
                                    "expirado_em": expirado_em.strftime('%Y-%m-%d %H:%M:%S'),
                                    "finalidade": finalidade,
                                    "nome_pessoa": alvo["nome"] if is_lote or alvo["nome"] != "Genérico" else "",
                                    "gestor_pessoa": alvo.get("gestor", ""),
                                    "descricao": descricao_geral if not is_lote else "",
                                    "usuario_criador": "Sistema"
                                }
                                database.salvar_password_link(link_data)
                                sucessos.append(res)
                            else:
                                erros.append(f"Erro para {alvo['nome']}: {res.get('mensagem')}")
                            
                            # Pausa leve para API rate limit
                            time.sleep(0.3)
                    
                    # Armazena no session_state para persistir
                    st.session_state["links_gerados"] = sucessos
                    st.session_state["links_erros"] = erros
                    st.session_state["links_ttl"] = ttl
                    st.session_state["links_incrementar"] = incrementar
        
        # --- EXIBIÇÃO DOS RESULTADOS (USA SESSION STATE) ---
        if "links_gerados" in st.session_state and st.session_state["links_gerados"]:
            sucessos = st.session_state["links_gerados"]
            erros = st.session_state.get("links_erros", [])
            ttl_display = st.session_state.get("links_ttl", 24)
            incrementar_display = st.session_state.get("links_incrementar", False)
            
            st.success(f"✅ {len(sucessos)} Links gerados com sucesso!")
            
            # Registra log apenas uma vez
            if not st.session_state.get("links_logged", False):
                database.registrar_log(
                    tipo="senha",
                    categoria="OneTimeSecret",
                    status="sucesso",
                    mensagem=f"{len(sucessos)} link(s) de senha gerado(s)",
                    detalhes=f"TTL: {ttl_display}h, Incrementar: {incrementar_display}",
                    origem="gerar_senhas"
                )
                st.session_state["links_logged"] = True
            
            st.markdown("### 📋 Links Gerados (Copie as senhas abaixo)")
            st.info("💡 A senha usada em cada link está mostrada acima dele. Use essa senha para resetar no sistema.")
            
            # Botão para limpar resultados
            if st.button("🗑️ Limpar Resultados", type="secondary"):
                del st.session_state["links_gerados"]
                if "links_erros" in st.session_state:
                    del st.session_state["links_erros"]
                if "links_ttl" in st.session_state:
                    del st.session_state["links_ttl"]
                if "links_incrementar" in st.session_state:
                    del st.session_state["links_incrementar"]
                if "links_logged" in st.session_state:
                    del st.session_state["links_logged"]
                st.rerun()
            
            # Função para criar botão de copiar com JavaScript
            def botao_copiar(texto: str, key: str, label: str = "📋"):
                """Cria um botão que copia texto para o clipboard usando JavaScript."""
                import streamlit.components.v1 as components
                
                # Escapa aspas e caracteres especiais
                texto_escaped = texto.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
                
                html_code = f"""
                <button onclick="navigator.clipboard.writeText('{texto_escaped}').then(() => {{
                    this.innerHTML = '✅';
                    setTimeout(() => {{ this.innerHTML = '{label}'; }}, 1500);
                }}).catch(err => {{
                    this.innerHTML = '❌';
                    setTimeout(() => {{ this.innerHTML = '{label}'; }}, 1500);
                }});" 
                style="background-color: #262730; color: white; border: 1px solid #4a4a5a; 
                       padding: 5px 15px; border-radius: 5px; cursor: pointer; font-size: 14px;
                       transition: all 0.2s ease;">
                    {label}
                </button>
                """
                components.html(html_code, height=40)
            
            # Exibição em Cartões
            for idx, item in enumerate(sucessos):
                # Define cor e ícone base
                bg_color = "#f0f2f6"
                icon = "👤" if is_lote or item.get('nome_pessoa') else "🔑"
                titulo = item['nome_pessoa'] if (is_lote or item.get('nome_pessoa')) else f"Link #{item['numero']}"
                
                # Layout do Cartão
                with st.container():
                    # Constrói HTML do gestor se disponível
                    gestor_html = ""
                    if item.get('gestor_pessoa'):
                        gestor_html = f"""<p style="margin: 5px 0 0 0; color: #555; font-size: 0.9em;">👔 Gestor: {item['gestor_pessoa']}</p>"""

                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid #1e3a5f; margin-bottom: 10px;">
                        <h4 style="margin:0; color: #1e3a5f;">{icon} {titulo}</h4>
                        {gestor_html}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.caption("🔐 Senha definida neste link:")
                        st.code(item['senha_usada'], language=None)
                        botao_copiar(item['senha_usada'], f"senha_{idx}", "📋 Copiar Senha")
                    with c2:
                        st.caption("🔗 Link OneTimeSecret:")
                        st.code(item['link'], language=None)
                        botao_copiar(item['link'], f"link_{idx}", "📋 Copiar Link")
                    st.markdown("---")
            
            # Exportação em bloco
            with st.expander("📥 Copiar lista para WhatsApp/Email"):
                texto_export = ""
                for item in sucessos:
                    ident = item['nome_pessoa'] if (is_lote or item.get('nome_pessoa')) else f"Link {item['numero']}"
                    texto_export += f"👤 *{ident}*\n🔗 {item['link']}\n\n"
                st.text_area("Lista completa:", value=texto_export, height=200)
            
            if erros:
                for e in erros:
                    st.error(e)
                
                # Registra log de erro apenas uma vez
                if not st.session_state.get("links_erros_logged", False):
                    database.registrar_log(
                        tipo="senha",
                        categoria="OneTimeSecret",
                        status="erro",
                        mensagem=f"{len(erros)} erro(s) ao gerar links",
                        detalhes="; ".join(erros),
                        origem="gerar_senhas"
                    )
                    st.session_state["links_erros_logged"] = True
    
    # ==================== ABA: HISTÓRICO ====================
    with tab_historico:
        st.markdown("### 📋 Histórico Recente")
        
        # Filtros
        col1, col2 = st.columns([1, 1])
        with col1:
            apenas_ativos = st.checkbox("Apenas links ativos", value=True, key="filtro_ativos")
        with col2:
            limite_historico = st.number_input("Limite:", 10, 100, 20, key="limite_historico")
        
        links = database.buscar_password_links(limite=limite_historico, apenas_ativos=apenas_ativos)
        
        if links:
            for link in links:
                # Determina se expirou
                try:
                    criado_em = datetime.strptime(link['criado_em'], '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        criado_em = datetime.fromisoformat(link['criado_em'].replace('Z', '+00:00'))
                    except:
                        criado_em = datetime.now()
                
                tempo_restante = (criado_em + timedelta(seconds=link['ttl_seconds'])) - datetime.now()
                
                # Busca gestor se não estiver salvo no link
                gestor_pessoa = link.get('gestor_pessoa', '')
                if not gestor_pessoa and link.get('nome_pessoa'):
                    # Tenta buscar o gestor do funcionário no banco
                    try:
                        funcionarios = database.buscar_funcionarios()
                        for func in funcionarios:
                            if func.get('nome') == link.get('nome_pessoa'):
                                gestor_pessoa = func.get('gestor', '')
                                break
                    except:
                        pass
                
                # Título do expander
                titulo = f"{link.get('nome_pessoa', 'Link') or 'Link'} - {formatar_data(link['criado_em'])}"
                if link.get('visualizado'):
                    titulo += " ✅ Visualizado"
                elif tempo_restante.total_seconds() <= 0:
                    titulo += " ⏰ Expirado"
                
                with st.expander(titulo):
                    # Função para criar botão de copiar (definida localmente também para o histórico)
                    def botao_copiar_hist(texto: str, key: str, label: str = "📋"):
                        """Cria um botão que copia texto para o clipboard usando JavaScript."""
                        import streamlit.components.v1 as components
                        
                        # Escapa aspas e caracteres especiais
                        texto_escaped = texto.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
                        
                        html_code = f"""
                        <button onclick="navigator.clipboard.writeText('{texto_escaped}').then(() => {{
                            this.innerHTML = '✅';
                            setTimeout(() => {{ this.innerHTML = '{label}'; }}, 1500);
                        }}).catch(err => {{
                            this.innerHTML = '❌';
                            setTimeout(() => {{ this.innerHTML = '{label}'; }}, 1500);
                        }});" 
                        style="background-color: #262730; color: white; border: 1px solid #4a4a5a; 
                               padding: 5px 15px; border-radius: 5px; cursor: pointer; font-size: 14px;
                               transition: all 0.2s ease;">
                            {label}
                        </button>
                        """
                        components.html(html_code, height=40)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**URL:** {link['link_url']}")
                        botao_copiar_hist(link['link_url'], f"hist_link_{link['id']}", "📋 Copiar Link")
                        st.write(f"**Senha:** {link['senha_usada']}")
                        botao_copiar_hist(link['senha_usada'], f"hist_senha_{link['id']}", "📋 Copiar Senha")
                        if link.get('nome_pessoa'):
                            st.write(f"**👤 Pessoa:** {link['nome_pessoa']}")
                        if gestor_pessoa:
                            st.write(f"**👔 Gestor:** {gestor_pessoa}")
                        elif link.get('nome_pessoa'):
                            st.write(f"**👔 Gestor:** *Não informado*")
                        if link.get('descricao'):
                            st.write(f"**📝 Descrição:** {link['descricao']}")
                        st.write(f"**🎯 Finalidade:** {link.get('finalidade', 'N/A')}")
                        st.write(f"**⏰ Validade:** {link['ttl_seconds'] // 3600}h")
                        
                        if tempo_restante.total_seconds() > 0:
                            st.info(f"⏳ Tempo restante: {int(tempo_restante.total_seconds() / 3600)}h {int((tempo_restante.total_seconds() % 3600) / 60)}m")
                        else:
                            st.warning("⏰ Link expirado")
                    
                    with col2:
                        # Botão Status
                        if st.button("🔄 Checar Status", key=f"chk_{link['id']}", width="stretch"):
                            api = OneTimeSecretAPI(
                                email=settings.ONETIMESECRET_EMAIL,
                                api_key=settings.ONETIMESECRET_API_KEY
                            )
                            
                            resultado = api.verificar_status(link.get('metadata_key', ''), link.get('link_url', ''))
                            
                            if resultado.get("sucesso"):
                                state = (resultado.get("status") or "").lower()
                                
                                if state in ('viewed', 'received'):
                                    st.error("❌ **O link JÁ FOI ABERTO!**")
                                    if resultado.get('visualizado_em'):
                                        st.caption(f"Visto em: {formatar_data(resultado['visualizado_em'])}")
                                    if not link.get('visualizado'):
                                        database.marcar_link_visualizado(link['id'])
                                        st.toast("Status atualizado para Visualizado!")
                                        time.sleep(1)
                                        st.rerun()
                                elif state == 'expired':
                                    st.warning("⏳ **O link EXPIROU!**")
                                    st.caption("O tempo limite (TTL) acabou e o segredo foi destruído sem ser lido.")
                                elif state == 'burned':
                                    st.warning("🔥 **O link foi QUEIMADO manualmente!**")
                                    st.caption("Alguém deletou este segredo antes do tempo.")
                                elif state == 'new':
                                    if tempo_restante.total_seconds() <= 0:
                                        st.info("🗑️ **Link expirou (cálculo local).**")
                                    else:
                                        st.success("✅ **O link AINDA NÃO foi aberto.**")
                                else:
                                    st.info(f"ℹ️ Status: {state}")
                            else:
                                st.error(f"❌ Erro: {resultado.get('mensagem', 'Erro desconhecido')}")
                        
                        # Botão Excluir
                        if st.button("🗑️ Excluir", key=f"del_{link['id']}", width="stretch", type="secondary"):
                            if database.excluir_link(link['id']):
                                st.success("✅ Link excluído com sucesso!")
                                
                                # Registra log
                                database.registrar_log(
                                    tipo="senha",
                                    categoria="OneTimeSecret",
                                    status="info",
                                    mensagem=f"Link excluído do histórico",
                                    detalhes=f"ID: {link['id']}, Pessoa: {link.get('nome_pessoa', 'N/A')}",
                                    origem="gerar_senhas"
                                )
                                
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao excluir link")
        else:
            st.info("📭 Histórico vazio.")
    
    # ==================== ABA: TEMPLATES ====================
    with tab_templates:
        st.info("Templates disponíveis na versão completa.")
        st.markdown("""
        **Templates de Senha:**
        - Básica: 8 caracteres (letras e números)
        - Segura: 12 caracteres (letras, números e símbolos)
        - Muito Segura: 16 caracteres (todos os caracteres)
        - WiFi: 10 caracteres (otimizado para redes)
        - Banco: 20 caracteres (máxima segurança)
        """)
