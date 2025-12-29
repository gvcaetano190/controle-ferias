# 📋 DOCUMENTAÇÃO DO SISTEMA DE CONTROLE DE FÉRIAS

## 📖 Visão Geral

Este sistema foi desenvolvido para controlar e monitorar férias de funcionários, processando dados de uma planilha Excel e gerando notificações sobre saídas e retornos de férias.

---

## 🏗️ Estrutura do Projeto

```
controle-ferias/
├── main.py                      # 🧠 Arquivo principal - executa todo o fluxo
├── config.py                    # ⚙️ Configurações do sistema
├── requirements.txt             # 📦 Dependências Python
├── gerar_planilha_teste.py      # 🧪 Script para gerar planilha de teste
├── DOCUMENTACAO.md              # 📚 Este arquivo
│
├── modules/                     # 📁 Módulos principais
│   ├── __init__.py
│   ├── leitor_excel.py          # 📖 Lê planilhas Excel
│   ├── processador.py           # 🔄 Processa e filtra dados
│   └── notificador.py           # 📨 Formata e exibe mensagens
│
├── utils/                       # 🔧 Utilitários
│   ├── __init__.py
│   └── formatadores.py          # Funções auxiliares de formatação
│
└── data/                        # 📊 Dados
    └── planilha.xlsx            # Planilha Excel com dados de férias
```

---

## 🔧 Configurações do Sistema

### Arquivo `config.py`

Este arquivo centraliza todas as configurações do sistema:

#### **Caminho da Planilha**
```python
PLANILHA_PATH = Path("data/planilha.xlsx")
```
- Localização do arquivo Excel que contém os dados de férias

#### **Mapeamento de Colunas**
```python
COLUNAS = {
    "unidade": "F",                      # Coluna F - Unidade (ex: TIFFANY)
    "nome": "Nome",                      # Coluna Nome - Nome do funcionário
    "motivo": "Motivo",                  # Coluna Motivo (ex: FÉRIAS)
    "saida": "Saída",                    # Coluna Saída - Data de saída
    "retorno": "Retorno/Liberação",      # Coluna Retorno - Data de retorno
    "gestor": "Gestor"                   # Coluna Gestor - Nome do gestor
}
```
- Define quais colunas da planilha contêm cada informação
- Essas colunas são usadas para mapear os dados do Excel

#### **Formato de Data**
```python
FORMATO_DATA_PLANILHA = "%d/%m/%Y"
```
- Formato esperado das datas na planilha (ex: 15/12/2024)

#### **Separador de Exibição**
```python
SEPARADOR = "=" * 60
```
- Usado para formatar a saída no terminal

---

## 📦 Dependências

### Arquivo `requirements.txt`

O sistema utiliza as seguintes bibliotecas Python:

- **pandas** (>=2.0.0): Manipulação e análise de dados
- **openpyxl** (>=3.1.0): Leitura e escrita de arquivos Excel (.xlsx)
- **python-dateutil** (>=2.8.0): Processamento avançado de datas

### Instalação
```bash
pip install -r requirements.txt
```

---

## 🔄 Fluxo de Execução

### Arquivo `main.py`

O arquivo principal executa o seguinte fluxo:

1. **Inicialização e Exibição de Cabeçalho**
   - Mostra data/hora atual
   - Exibe título do sistema

2. **Carregamento da Planilha** (`LeitorExcel`)
   - Verifica se o arquivo existe
   - Carrega o arquivo Excel
   - Lista todas as abas disponíveis

3. **Leitura dos Dados** (`LeitorExcel.ler_todas_abas()`)
   - Lê todas as abas da planilha
   - Retorna um dicionário com DataFrames por aba

4. **Processamento dos Dados** (`Processador`)
   - Converte dados brutos em objetos `Funcionario`
   - Processa todas as abas
   - Valida e parseia datas

5. **Filtragem** (`Processador`)
   - **Saindo Hoje**: Funcionários que começam férias hoje
   - **Voltando Amanhã**: Funcionários que retornam amanhã
   - **Ausentes Hoje**: Funcionários atualmente de férias

6. **Geração de Notificações** (`Notificador`)
   - Formata mensagens para exibição
   - Gera resumo diário completo
   - Exibe no terminal

7. **Estatísticas**
   - Mostra total de ausentes hoje

---

## 📚 Módulos Detalhados

### 1. `modules/leitor_excel.py` - Leitor de Excel

**Responsabilidade**: Ler planilhas Excel e suas múltiplas abas.

**Classe Principal**: `LeitorExcel`

**Métodos Principais**:
- `carregar()`: Carrega o arquivo Excel e valida existência
- `listar_abas()`: Retorna lista de todas as abas disponíveis
- `ler_aba(nome_aba)`: Lê uma aba específica e retorna DataFrame
- `ler_todas_abas()`: Lê todas as abas e retorna dicionário de DataFrames

**Características**:
- Suporta múltiplas abas (ex: "DEZEMBRO 2024", "JANEIRO 2025")
- Lê todas as colunas como string inicialmente
- Tratamento de erros robusto

---

### 2. `modules/processador.py` - Processador de Dados

**Responsabilidade**: Processar, validar e filtrar dados de férias.

**Classes**:
- `Funcionario`: Dataclass que representa um funcionário
  - Campos: nome, motivo, data_saida, data_retorno, gestor, unidade
  - Método: `dias_ausencia()` - calcula dias de ausência

**Classe Principal**: `Processador`

**Métodos Principais**:
- `processar_todas_abas()`: Processa todas as abas e extrai funcionários
- `filtrar_saida_hoje()`: Funcionários que saem hoje
- `filtrar_retorno_amanha()`: Funcionários que voltam amanhã
- `filtrar_ausentes_hoje()`: Funcionários atualmente de férias
- `filtrar_saida_data(data)`: Filtrar por data de saída específica
- `filtrar_retorno_data(data)`: Filtrar por data de retorno específica
- `_parse_data(valor)`: Converte string para datetime (suporta múltiplos formatos)

**Características**:
- Parse inteligente de datas (tenta múltiplos formatos)
- Ignora linhas inválidas (sem datas)
- Processa todas as abas automaticamente

---

### 3. `modules/notificador.py` - Notificador

**Responsabilidade**: Formatar e preparar mensagens de notificação.

**Classe Principal**: `Notificador`

**Métodos Principais**:
- `gerar_mensagem_saida_hoje(funcionarios)`: Mensagem para quem sai hoje
- `gerar_mensagem_retorno_amanha(funcionarios)`: Mensagem para quem volta amanhã
- `gerar_resumo_diario(saindo, voltando)`: Resumo completo do dia
- `exibir_terminal(mensagem)`: Exibe mensagem no terminal
- `formatar_data(data)`: Formata datetime para exibição

**Métodos Futuros (Preparados)**:
- `preparar_para_whatsapp(mensagem)`: Prepara payload para Evolution API
- `enviar_whatsapp(numero, mensagem)`: Envia via Evolution API (TODO)

**Características**:
- Formatação com emojis para melhor visualização
- Estrutura preparada para integração com WhatsApp (Evolution API)
- Mensagens formatadas em markdown para WhatsApp

---

### 4. `utils/formatadores.py` - Utilitários de Formatação

**Responsabilidade**: Funções auxiliares de formatação.

**Funções**:
- `formatar_data(data, formato)`: Converte datetime para string formatada
- `parse_data(texto, formatos)`: Converte string para datetime (múltiplos formatos)
- `formatar_nome(nome)`: Formata nome em Title Case
- `dias_entre_datas(data_inicio, data_fim)`: Calcula diferença em dias

---

## 📊 Estrutura da Planilha Excel

### Formato Esperado

A planilha deve ter as seguintes colunas:

| Coluna | Nome no Sistema | Exemplo |
|--------|----------------|---------|
| F | unidade | TIFFANY |
| Nome | nome | MARIA SILVA |
| Motivo | motivo | FÉRIAS |
| Saída | saida | 15/12/2024 |
| Retorno/Liberação | retorno | 30/12/2024 |
| Gestor | gestor | PEDRO RODRIGUES |

### Formatos de Data Aceitos
- `%d/%m/%Y` (ex: 15/12/2024)
- `%Y-%m-%d` (ex: 2024-12-15)
- `%d-%m-%Y` (ex: 15-12-2024)

### Suporte a Múltiplas Abas
- O sistema processa todas as abas automaticamente
- Cada aba pode conter registros diferentes
- Exemplo: "DEZEMBRO 2024", "JANEIRO 2025"

---

## 🧪 Script de Teste

### Arquivo `gerar_planilha_teste.py`

Este script gera uma planilha de exemplo para testes com:
- Dados de exemplo de dezembro 2024
- Dados de exemplo de janeiro 2025
- Funcionários que saem hoje (data atual)
- Funcionários que voltam amanhã (data atual + 1 dia)
- Funcionários ausentes

**Uso**:
```bash
python gerar_planilha_teste.py
```

---

## 🚀 Como Executar

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Preparar Planilha
- Coloque sua planilha em `data/planilha.xlsx`
- Ou execute `python gerar_planilha_teste.py` para criar uma planilha de teste

### 3. Executar Sistema
```bash
python main.py
```

### Saída Esperada
```
============================================================
🗓️  SISTEMA DE CONTROLE DE FÉRIAS
📅 Data: 15/12/2024 às 14:30
============================================================

📂 Carregando planilha...
✅ Planilha carregada: planilha.xlsx
📑 Abas encontradas: DEZEMBRO 2024, JANEIRO 2025

📖 Lendo dados...
📊 2 aba(s) carregada(s)

⚙️  Processando dados...
👥 15 registro(s) processado(s)

==================================================
📊 RESUMO DIÁRIO - 15/12/2024 às 14:30
==================================================

🏖️ *SAINDO DE FÉRIAS HOJE (15/12/2024)*
Total: 2 pessoa(s)
----------------------------------------
1. *MARIA TESTE SAINDO HOJE*
   📅 Retorno: 30/12/2024
   👤 Gestor: GESTOR TESTE 1
   📋 Motivo: FÉRIAS

...

==================================================
✅ Processamento concluído!
============================================================
```

---

## 🔮 Funcionalidades Futuras

O sistema está preparado para:

1. **Integração com Evolution API (WhatsApp)**
   - Métodos já preparados em `notificador.py`
   - Estrutura de payload definida
   - Pendente: implementação do envio HTTP

2. **Expansão de Filtros**
   - Filtros por período
   - Filtros por unidade
   - Filtros por gestor

3. **Relatórios**
   - Exportação para PDF
   - Gráficos e estatísticas
   - Histórico de férias

---

## 📝 Notas Técnicas

### Tratamento de Erros
- O sistema ignora linhas inválidas (sem datas)
- Continua processamento mesmo com erros parciais
- Mensagens de erro claras no terminal

### Performance
- Processa todas as abas em uma única execução
- Usa pandas para eficiência com grandes volumes
- Leitura otimizada de Excel

### Manutenibilidade
- Código modular e bem organizado
- Separação clara de responsabilidades
- Configurações centralizadas
- Documentação inline nos códigos

---

## 🐛 Resolução de Problemas

### Erro: "Arquivo não encontrado"
- Verifique se `data/planilha.xlsx` existe
- Verifique o caminho em `config.py`

### Erro: "Nenhum dado encontrado"
- Verifique se as abas não estão vazias
- Verifique se as colunas estão corretas em `config.py`
- Verifique formato das datas

### Datas não sendo reconhecidas
- Verifique se as datas estão no formato esperado
- O sistema tenta múltiplos formatos automaticamente
- Formatos aceitos: `%d/%m/%Y`, `%Y-%m-%d`, `%d-%m-%Y`

---

## 👤 Autor

Sistema desenvolvido para controle de férias de funcionários.

---

**Última Atualização**: Dezembro 2024

