# 🏖️ Sistema de Controle de Férias

Sistema para gerenciamento e acompanhamento de férias de funcionários, com sincronização automática de dados do Google Sheets.

## 📁 Estrutura do Projeto

```
controle-ferias/
├── config/                    # Configurações centralizadas
│   ├── __init__.py
│   └── settings.py           # Todas as configurações (via .env)
│
├── core/                      # Núcleo do sistema
│   ├── __init__.py
│   ├── database.py           # Conexão SQLite
│   ├── models.py             # Modelos de dados
│   └── sync_manager.py       # Sincronização com Google Sheets
│
├── frontend/                  # Interface web
│   └── app.py                # Dashboard Streamlit
│
├── integrations/              # Integrações externas
│   ├── __init__.py
│   └── evolution_api.py      # WhatsApp (Evolution API)
│
├── modules/                   # Módulos de negócio
│   ├── leitor_excel.py
│   ├── leitor_google_sheets.py
│   └── processador.py
│
├── scheduler/                 # Agendamento de tarefas
│   ├── __init__.py
│   └── jobs.py               # Jobs automáticos
│
├── scripts/                   # Scripts de execução
│   ├── iniciar.sh            # Inicia o sistema
│   ├── sync.sh               # Sincronização manual
│   └── scheduler.sh          # Daemon de agendamento
│
├── data/                      # Dados persistentes
│   ├── database.sqlite       # Banco de dados
│   └── cache/                # Cache de arquivos
│
├── tests/                     # Testes e validações
│
├── .env                       # Configurações locais
├── .env.example              # Exemplo de configuração
└── requirements.txt          # Dependências Python
```

## 🚀 Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd controle-ferias

# Crie e ative o virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o .env
cp .env.example .env
# Edite o .env com suas configurações
```

## ⚙️ Configuração

Edite o arquivo `.env`:

```env
# URL da planilha do Google Sheets
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/SEU_ID/edit

# Horário da sincronização automática (24h)
SYNC_HOUR=6
SYNC_MINUTE=0

# Tempo de cache em minutos
CACHE_MINUTES=60
```

## 🎯 Uso

### Iniciar o Dashboard

```bash
./scripts/iniciar.sh
# ou
streamlit run frontend/app.py
```

Acesse: **http://localhost:8501**

### Sincronização Manual

```bash
./scripts/sync.sh           # Normal (usa cache)
./scripts/sync.sh --forcar  # Força download
```

### Agendamento Automático

```bash
./scripts/scheduler.sh      # Inicia daemon
```

O scheduler executará:
- **Sincronização diária** no horário configurado
- **Verificação de férias** às 8h

## 📊 Funcionalidades

### Dashboard
- 📋 Lista de funcionários por mês
- 🏖️ Funcionários saindo hoje
- 📆 Próximos a sair de férias
- 🌴 Funcionários em férias agora
- 📅 Voltando amanhã

### Controle de Acessos
- Status por sistema (AD, VPN, Gmail, etc)
- Alertas de acessos pendentes
- Resumo geral

### Sincronização
- Automática (diária)
- Manual (via botão ou script)
- Verificação de alterações (hash MD5)

## 🔌 Integrações (Opcionais)

### Evolution API (WhatsApp)
```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua_chave
EVOLUTION_INSTANCE=nome_instancia
EVOLUTION_ENABLED=true
```

## 🔧 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                         STREAMLIT                            │
│  (Dashboard - lê diretamente do SQLite)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       CORE/DATABASE                          │
│  (SQLite - dados persistentes)                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      SYNC MANAGER                            │
│  (Baixa Google Sheets → Processa → Salva no banco)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       SCHEDULER                              │
│  (APScheduler - executa sync diariamente)                   │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Futuro: FastAPI

O sistema está preparado para migrar para FastAPI se necessário:

1. Descomente as dependências em `requirements.txt`
2. Use os models SQLAlchemy em `core/models.py`
3. Crie os endpoints em `api/` (estrutura já planejada)

## 📝 Licença

MIT








