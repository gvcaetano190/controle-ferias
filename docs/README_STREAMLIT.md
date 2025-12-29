# 🚀 Guia de Uso - Interface Web com Streamlit

Este guia explica como usar a interface web do Sistema de Controle de Férias.

---

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Dependências instaladas** (veja abaixo)

---

## 🔧 Instalação

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

Isso instalará:
- `streamlit` - Framework web
- `pandas` - Manipulação de dados
- `openpyxl` - Leitura de Excel
- `gspread` - Integração com Google Sheets API (opcional)
- `google-auth` - Autenticação Google (opcional)

---

## 🚀 Como Executar

### Executar interface web:

```bash
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`

---

## 📊 Como Usar com Google Sheets

### Opção 1: Planilha Pública (Mais Simples) ⭐ RECOMENDADO

**Passo a passo:**

1. **Tornar a planilha pública:**
   - Abra sua planilha no Google Sheets
   - Clique em "Compartilhar" (botão no canto superior direito)
   - Clique em "Alterar para qualquer pessoa com o link"
   - Selecione "Visualizador"
   - Clique em "Concluído"
   - Copie o link da planilha

2. **No Streamlit:**
   - Selecione "Google Sheets (URL)" na sidebar
   - Cole o link completo da planilha
   - **NÃO** marque "Usar Google Sheets API"
   - Clique em "🔄 Carregar Planilha"

**⚠️ Limitação:** Com CSV público, apenas a **primeira aba** será lida.

---

### Opção 2: Google Sheets API (Múltiplas Abas)

Para ler múltiplas abas ou planilhas privadas, você precisa configurar a API do Google:

**Passo a passo:**

1. **Criar projeto no Google Cloud:**
   - Acesse [Google Cloud Console](https://console.cloud.google.com/)
   - Crie um novo projeto (ou use existente)
   - Ative a **Google Sheets API**

2. **Criar credenciais:**
   - Vá em "APIs e Serviços" > "Credenciais"
   - Clique em "Criar credenciais" > "Conta de serviço"
   - Dê um nome (ex: "controle-ferias")
   - Clique em "Concluído"

3. **Baixar chave JSON:**
   - Clique na conta de serviço criada
   - Vá na aba "Chaves"
   - Clique em "Adicionar chave" > "Criar nova chave"
   - Escolha "JSON"
   - Baixe o arquivo JSON

4. **Compartilhar planilha com a conta de serviço:**
   - Abra sua planilha no Google Sheets
   - Clique em "Compartilhar"
   - Cole o email da conta de serviço (está no JSON: `client_email`)
   - Dê permissão de "Visualizador"
   - Clique em "Concluído"

5. **No Streamlit:**
   - Selecione "Google Sheets (URL)"
   - Cole o link da planilha
   - **MARQUE** "Usar Google Sheets API"
   - Faça upload do arquivo JSON baixado
   - Clique em "🔄 Carregar Planilha"

**✅ Vantagem:** Lê **todas as abas** da planilha!

---

## 📁 Como Usar com Arquivo Excel Local

1. **No Streamlit:**
   - Selecione "Arquivo Excel Local" na sidebar
   - Clique em "Browse files" e selecione seu arquivo `.xlsx` ou `.xls`
   - Clique em "🔄 Processar Planilha"

**✅ Vantagem:** Funciona offline e lê todas as abas!

---

## 🎯 Formatos de URL Aceitos

O sistema aceita URLs do Google Sheets nos formatos:

- `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
- `https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0`
- Qualquer variação da URL acima

O sistema extrai automaticamente o ID da planilha.

---

## 🔍 Estrutura da Planilha Esperada

A planilha deve ter as seguintes colunas:

| Coluna | Nome Esperado | Exemplo |
|--------|---------------|---------|
| F | unidade | TIFFANY |
| Nome | nome | MARIA SILVA |
| Motivo | motivo | FÉRIAS |
| Saída | saida | 15/12/2024 |
| Retorno/Liberação | retorno | 30/12/2024 |
| Gestor | gestor | PEDRO RODRIGUES |

**Formatos de data aceitos:**
- `DD/MM/YYYY` (ex: 15/12/2024)
- `YYYY-MM-DD` (ex: 2024-12-15)
- `DD-MM-YYYY` (ex: 15-12-2024)

---

## 📊 Funcionalidades da Interface

A interface web exibe:

1. **Métricas principais:**
   - Funcionários saindo hoje
   - Funcionários voltando amanhã
   - Funcionários ausentes hoje
   - Total de registros

2. **Tabelas interativas:**
   - Lista completa de funcionários saindo hoje
   - Lista completa de funcionários voltando amanhã
   - Lista de ausentes (com expand/collapse)

3. **Informações exibidas:**
   - Nome do funcionário
   - Datas de saída e retorno
   - Dias de ausência
   - Nome do gestor
   - Unidade
   - Motivo

---

## 🐛 Solução de Problemas

### Erro: "Falha ao carregar planilha do Google Sheets"

**Possíveis causas:**
1. URL incorreta ou inválida
2. Planilha não está pública (se usando CSV)
3. Conexão com internet falhou

**Solução:**
- Verifique se a URL está correta
- Se usando CSV público, certifique-se que a planilha está compartilhada publicamente
- Teste abrir a URL no navegador

---

### Erro: "Biblioteca gspread não instalada"

**Solução:**
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

### Erro ao usar API: "Permission denied"

**Possíveis causas:**
1. Conta de serviço não tem acesso à planilha
2. Arquivo JSON de credenciais incorreto

**Solução:**
- Certifique-se de compartilhar a planilha com o email da conta de serviço
- Verifique se o arquivo JSON está correto

---

### Planilha não carrega múltiplas abas

**Causa:** Usando método CSV público (que só lê primeira aba)

**Solução:**
- Use Google Sheets API para ler múltiplas abas
- Ou consolide todas as abas em uma única aba
- Ou use arquivo Excel local

---

## 💡 Dicas

1. **Para produção:** Considere hospedar no Streamlit Cloud (gratuito)
2. **Performance:** API do Google é mais rápida que CSV público
3. **Segurança:** Use API para planilhas com dados sensíveis
4. **Múltiplas abas:** Use API do Google ou Excel local

---

## 🔗 Links Úteis

- [Documentação do Streamlit](https://docs.streamlit.io/)
- [Documentação do gspread](https://docs.gspread.org/)
- [Google Sheets API](https://developers.google.com/sheets/api)

---

**Última atualização:** Dezembro 2024

