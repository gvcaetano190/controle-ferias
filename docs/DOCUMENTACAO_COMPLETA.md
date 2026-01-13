# 📚 Documentação Completa - Sistema de Controle de Férias

**Última atualização:** 25/12/2025  
**Versão:** 2.0 (Python-only com Streamlit)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Estrutura de Diretórios](#estrutura-de-diretórios)
4. [Instalação e Configuração](#instalação-e-configuração)
5. [Uso do Sistema](#uso-do-sistema)
6. [Funcionalidades](#funcionalidades)
7. [Integrações](#integrações)
8. [Agendamento (Scheduler)](#agendamento-scheduler)
9. [Banco de Dados](#banco-de-dados)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O **Sistema de Controle de Férias** é uma solução completa para gerenciamento e acompanhamento de férias de funcionários, com sincronização automática de dados do Google Sheets e notificações via WhatsApp.

### Principais Características

- ✅ **Interface Web Moderna** (Streamlit)
- ✅ **Sincronização Automática** com Google Sheets
- ✅ **Banco de Dados SQLite** para persistência
- ✅ **Agendamento Automático** de tarefas (APScheduler)
- ✅ **Notificações WhatsApp** via Evolution API
- ✅ **Controle de Acessos** por sistema (AD, VPN, Gmail, etc)
- ✅ **Dashboard Interativo** com múltiplas visualizações

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Dashboard   │  │ Configurações│  │ Sincronização│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                     CORE LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Database   │  │Sync Manager  │  │Config Manager│  │
│  │   (SQLite)   │  │(Google Sheets)│ │   (.env)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────┬──────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐            ┌──────────────────┐
│   SCHEDULER   │            │  INTEGRATIONS    │
│  (APScheduler)│            │  Evolution API   │
│               │            │   (WhatsApp)     │
└───────────────┘            └──────────────────┘
```

### Fluxo de Dados

1. **Scheduler** → Executa jobs em horários configurados
2. **Sync Manager** → Baixa Google Sheets → Processa → Salva no banco
3. **Database** → Armazena funcionários, acessos, logs
4. **Streamlit** → Lê do banco → Exibe no dashboard
5. **Evolution API** → Envia notificações quando configurado

---

## 📁 Estrutura de Diretórios

```
controle-ferias/
├── 📂 config/                    # Configurações centralizadas
│   ├── __init__.py
│   └── settings.py              # Todas as configurações (via .env)
│
├── 📂 core/                      # Núcleo do sistema
│   ├── __init__.py
│   ├── database.py              # Conexão e operações SQLite
│   ├── models.py                # Modelos de dados (SQLAlchemy)
│   ├── sync_manager.py          # Sincronização Google Sheets
│   ├── config_manager.py        # Gerenciamento de .env
│   └── validar_planilha.py      # Validação de planilhas
│
├── 📂 frontend/                  # Interface web
│   └── app.py                   # Dashboard Streamlit principal
│
├── 📂 integrations/              # Integrações externas
│   ├── __init__.py
│   └── evolution_api.py         # Cliente Evolution API (WhatsApp)
│
├── 📂 modules/                   # Módulos de negócio (legado/CLI)
│   ├── leitor_excel.py          # Leitor de arquivos Excel
│   ├── leitor_google_sheets.py  # Leitor Google Sheets
│   ├── processador.py           # Processamento de dados
│   └── notificador.py           # Notificações (CLI)
│
├── 📂 scheduler/                 # Agendamento de tarefas
│   ├── __init__.py
│   └── jobs.py                  # Jobs automáticos (sync, mensagens)
│
├── 📂 scripts/                   # Scripts de execução
│   ├── iniciar.sh               # Inicia Streamlit
│   ├── scheduler.sh             # Inicia scheduler daemon
│   ├── sync.sh                  # Sincronização manual
│   └── parar.sh                 # Para todos os processos
│
├── 📂 data/                      # Dados persistentes
│   ├── database.sqlite          # Banco de dados principal
│   └── cache/                   # Cache de arquivos e hash
│
├── 📂 download/                  # Arquivos baixados
│   └── planilha_*.xlsx          # Planilhas baixadas do Google Sheets
│
├── 📂 tests/                     # Testes e validações
│   ├── testar_planilha.py       # Teste de planilhas
│   ├── validar_dados.py         # Validação de dados
│   └── gerar_planilha_teste.py  # Gerador de planilhas de teste
│
├── 📂 docs/                      # Documentação
│   ├── DOCUMENTACAO_COMPLETA.md # Este arquivo
│   ├── ANALISE_ESTRUTURA.md     # Análise da estrutura
│   ├── COMO_FUNCIONA_SCHEDULER.md # Guia do scheduler
│   ├── GUIA_API_GOOGLE.md       # Guia Google Sheets API
│   └── README_STREAMLIT.md      # Guia Streamlit
│
├── 📂 utils/                     # Utilitários
│   └── formatadores.py          # Funções de formatação
│
├── 📄 .env                       # Configurações locais (não versionado)
├── 📄 .env.example               # Exemplo de configuração
├── 📄 requirements.txt           # Dependências Python
├── 📄 README.md                  # README principal
├── 📄 config.py                  # Config antigo (legado - CLI)
└── 📄 main.py                    # CLI antigo (legado)
```

---

## 🚀 Instalação e Configuração

### 1. Pré-requisitos

- Python 3.8+
- pip
- Git (opcional)

### 2. Instalação

```bash
# Clone o repositório (ou baixe o código)
cd controle-ferias

# Crie e ative o virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração Inicial

#### 3.1. Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto (ou copie de `.env.example`):

```env
# ============================================
# GOOGLE SHEETS
# ============================================
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/SEU_ID/edit

# ============================================
# SINCRONIZAÇÃO
# ============================================
SYNC_HOUR=8                    # Hora da sincronização diária (0-23)
SYNC_MINUTE=15                 # Minuto da sincronização (0-59)
SYNC_ENABLED=true              # Habilitar sincronização automática
CACHE_MINUTES=60               # Tempo de cache em minutos

# ============================================
# EVOLUTION API (WhatsApp) - Opcional
# ============================================
EVOLUTION_ENABLED=false        # Habilitar integração WhatsApp
EVOLUTION_API_URL=http://10.0.153.28:8081/message/sendText/zabbix
EVOLUTION_NUMERO=120363020985287866@g.us
EVOLUTION_API_KEY=sua_chave_aqui

# ============================================
# MENSAGENS AUTOMÁTICAS - Opcional
# ============================================
MENSAGEM_MANHA_ENABLED=true    # Mensagem matutina
MENSAGEM_MANHA_HOUR=8          # Hora da mensagem matutina
MENSAGEM_MANHA_MINUTE=0        # Minuto da mensagem matutina

MENSAGEM_TARDE_ENABLED=true    # Mensagem vespertina
MENSAGEM_TARDE_HOUR=17         # Hora da mensagem vespertina
MENSAGEM_TARDE_MINUTE=0        # Minuto da mensagem vespertina

# ============================================
# NOTIFICAÇÕES - Opcional
# ============================================
NOTIFY_ON_SYNC=true            # Notificar após sincronização
NOTIFY_FERIAS_DIAS_ANTES=1     # Dias antes para avisar férias

# ============================================
# FASTAPI (Futuro)
# ============================================
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 💻 Uso do Sistema

### Iniciar o Dashboard

```bash
# Opção 1: Script
./scripts/iniciar.sh

# Opção 2: Direto
streamlit run frontend/app.py
```

Acesse: **http://localhost:8501**

### Sincronização Manual

```bash
# Sincronização normal (usa cache se disponível)
./scripts/sync.sh

# Forçar download e processamento
./scripts/sync.sh --forcar
```

### Iniciar Scheduler (Agendamento Automático)

```bash
# Inicia daemon em background
./scripts/scheduler.sh

# Para parar: Ctrl+C ou
pkill -f scheduler.jobs
```

---

## 🎨 Funcionalidades

### 1. Dashboard Principal

#### Páginas Disponíveis:

- **🏠 Início**: Visão geral do sistema
- **📊 Funcionários**: Lista todos os funcionários
- **🏖️ Saindo Hoje**: Funcionários que saem hoje de férias
- **📅 Voltando Amanhã**: Funcionários que retornam amanhã
- **🌴 Em Férias**: Funcionários atualmente em férias
- **⏰ Próximos a Sair**: Funcionários que vão sair nos próximos dias
- **⚠️ Acessos Pendentes**: Funcionários com acessos não bloqueados
- **⚙️ Configurações**: Configurações do sistema

### 2. Controle de Acessos

O sistema rastreia o status de acesso de cada funcionário para os seguintes sistemas:

- **AD PRIN** (Active Directory)
- **VPN**
- **Gmail**
- **Admin**
- **Metrics**
- **TOTVS**

**Status possíveis:**
- 🟢 **LIBERADO**: Acesso liberado
- 🔴 **BLOQUEADO**: Acesso bloqueado
- 🟡 **NP** (Não Possui): Não tem acesso ao sistema
- ⚪ **NB** (Não Bloqueado): Pendente - ainda não foi feito nada

### 3. Sincronização

#### Características:

- ✅ **Download Automático** do Google Sheets
- ✅ **Verificação de Mudanças** via hash MD5
- ✅ **Cache Inteligente** (não reprocessa se não mudou)
- ✅ **Processamento de Múltiplas Abas** (uma por mês)
- ✅ **Correção Automática** de datas invertidas
- ✅ **Validação de Dados** antes de salvar

#### Processo de Sincronização:

1. Baixa planilha do Google Sheets (formato Excel)
2. Calcula hash MD5 do arquivo
3. Compara com hash anterior
4. Se mudou → Processa dados
5. Extrai funcionários e acessos
6. Salva no banco SQLite
7. Atualiza hash para próxima verificação

---

## 🔌 Integrações

### Evolution API (WhatsApp)

Integração opcional para envio de notificações via WhatsApp.

#### Configuração:

1. Configure no `.env`:
   ```env
   EVOLUTION_ENABLED=true
   EVOLUTION_API_URL=http://seu_servidor:porta/message/sendText/instancia
   EVOLUTION_NUMERO=numero_ou_grupo@g.us
   EVOLUTION_API_KEY=sua_chave
   ```

2. Teste a conexão na página de Configurações

#### Funcionalidades:

- ✅ **Mensagem de Teste**: Testa a conexão
- ✅ **Mensagem Matutina**: Envia relatório pela manhã
  - Quem sai hoje de férias
  - Quem voltaria hoje mas ainda está bloqueado
- ✅ **Mensagem Vespertina**: Envia relatório à tarde
  - Quem volta amanhã
  - Quem está em férias com acessos pendentes (NB)
- ✅ **Notificação de Sync**: Notifica após sincronização
- ✅ **Aviso de Férias**: Avisa X dias antes das férias

---

## ⏰ Agendamento (Scheduler)

O sistema usa **APScheduler** para executar tarefas automaticamente.

### Jobs Agendados:

| Job | Horário | Condição | Descrição |
|-----|---------|----------|-----------|
| 🔄 **Sincronização** | Configurável | `SYNC_ENABLED=true` | Baixa e processa planilha |
| 📅 **Férias Próximas** | 09:00 (fixo) | `EVOLUTION_ENABLED=true` | Verifica e avisa funcionários |
| 🌅 **Mensagem Manhã** | Configurável | `MENSAGEM_MANHA_ENABLED=true` | Envia relatório matutino |
| 🌆 **Mensagem Tarde** | Configurável | `MENSAGEM_TARDE_ENABLED=true` | Envia relatório vespertino |

### Como Funciona:

Ver documentação completa em: `docs/COMO_FUNCIONA_SCHEDULER.md`

**Resumo:**
- O scheduler roda como daemon em background
- Lê configurações do `.env` ao iniciar
- Executa jobs nos horários agendados
- Precisa estar rodando para funcionar

---

## 🗄️ Banco de Dados

### Estrutura SQLite

#### Tabelas:

1. **`funcionarios`**
   - `id`, `nome`, `unidade`, `motivo`
   - `data_saida`, `data_retorno`
   - `gestor`, `aba_origem`, `mes`, `ano`

2. **`acessos`**
   - `id`, `funcionario_id`, `sistema`, `status`

3. **`abas`**
   - `id`, `nome`, `mes`, `ano`, `total_funcionarios`

4. **`sync_logs`**
   - `id`, `sync_at`, `total_registros`, `total_abas`
   - `status`, `mensagem`, `arquivo_hash`

### Acesso ao Banco:

```python
from core.database import Database

db = Database()

# Buscar funcionários
funcionarios = db.buscar_funcionarios()

# Buscar por aba
funcionarios_jan = db.buscar_funcionarios(aba="Janeiro 2025")

# Buscar saindo hoje
saindo = db.buscar_saindo_hoje()

# Buscar acessos pendentes
pendentes = db.buscar_acessos_pendentes()
```

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Scheduler não inicia

**Erro:** `APScheduler não instalado`

**Solução:**
```bash
pip install apscheduler
```

#### 2. Erro ao baixar planilha

**Erro:** `Erro ao baixar planilha`

**Verificações:**
- URL está correta no `.env`
- Planilha é pública (ou tem permissões)
- Internet está funcionando

#### 3. Banco de dados com erro

**Erro:** `table sync_logs has no column named arquivo_hash`

**Solução:**
```bash
sqlite3 data/database.sqlite "ALTER TABLE sync_logs ADD COLUMN arquivo_hash TEXT;"
```

#### 4. Streamlit não inicia

**Erro:** Porta já em uso

**Solução:**
```bash
pkill -f "streamlit run"
# ou
streamlit run frontend/app.py --server.port 8502
```

#### 5. Evolution API retorna 401/400

**Verificações:**
- API Key está correta
- Número está formatado corretamente (com @g.us para grupos)
- URL do endpoint está completa

---

## 📝 Notas Importantes

1. **Primeira Sincronização**: Pode demorar mais (baixa e processa tudo)
2. **Cache**: Arquivos baixados ficam em `download/` (últimos 3 são mantidos)
3. **Logs**: Logs do scheduler ficam em `scheduler.log`
4. **Banco de Dados**: Fica em `data/database.sqlite`
5. **Configurações**: Sempre edite o `.env`, não o código
6. **Reiniciar Scheduler**: Sempre reinicie após mudar configurações

---

## 🚀 Futuro

### Planejado:

- [ ] Migração para FastAPI (opcional)
- [ ] API REST completa
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Gráficos e estatísticas avançadas
- [ ] Multi-tenant (múltiplas empresas)

---

## 📞 Suporte

Para mais informações, consulte:
- `docs/COMO_FUNCIONA_SCHEDULER.md` - Detalhes do scheduler
- `docs/ANALISE_ESTRUTURA.md` - Análise técnica
- `README.md` - Guia rápido

---

**Desenvolvido com ❤️ para facilitar o controle de férias**









