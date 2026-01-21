# 📊 Análise Completa do Projeto - Sistema de Controle de Férias

> **Data da Análise:** 17 de Janeiro de 2026  
> **Objetivo:** Documentar tecnologias, identificar melhorias e código duplicado

---

## 📋 Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Tecnologias Utilizadas](#2-tecnologias-utilizadas)
3. [Documentação Oficial das Tecnologias](#3-documentação-oficial-das-tecnologias)
4. [Estrutura de Arquivos](#4-estrutura-de-arquivos)
5. [Análise de Código Duplicado](#5-análise-de-código-duplicado)
6. [Padrões de Projeto Recomendados](#6-padrões-de-projeto-recomendados)
7. [Oportunidades de Melhoria](#7-oportunidades-de-melhoria)
8. [Referências e Links Úteis](#8-referências-e-links-úteis)

---

## 1. Visão Geral do Projeto

### Descrição
Sistema de controle de férias de funcionários com:
- Dashboard web interativo (Streamlit)
- Sincronização automática com Google Sheets
- Integração com WhatsApp via Evolution API
- Integração com Kanbanize para gestão de tarefas
- Geração de senhas seguras via OneTimeSecret
- Agendamento de tarefas (APScheduler)
- Armazenamento em SQLite

### Arquitetura
```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                      │
│  Dashboard, Relatórios, Configurações, Gerenciamento         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       CORE                                   │
│  Database, SyncManager, ConfigManager, Models                │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────▼────┐        ┌─────▼─────┐       ┌─────▼─────┐
    │ Google  │        │ Evolution │       │ Kanbanize │
    │ Sheets  │        │    API    │       │    API    │
    └─────────┘        └───────────┘       └───────────┘
```

---

## 2. Tecnologias Utilizadas

### 2.1 Backend / Core

| Tecnologia | Versão | Função | Arquivo Principal |
|------------|--------|--------|-------------------|
| **Python** | 3.11+ | Linguagem principal | Dockerfile |
| **SQLite3** | Built-in | Banco de dados local | `core/database.py` |
| **pandas** | ≥2.0.0 | Manipulação de dados | `modules/leitor_excel.py` |
| **openpyxl** | ≥3.1.0 | Leitura/escrita Excel | `modules/leitor_excel.py`, `core/sync_manager.py` |
| **APScheduler** | ≥3.10.0 | Agendamento de tarefas | `scheduler/jobs.py` |
| **requests** | ≥2.31.0 | Cliente HTTP | `integrations/*.py` |
| **python-dateutil** | ≥2.8.0 | Manipulação de datas | `modules/processador.py` |

### 2.2 Frontend

| Tecnologia | Versão | Função | Arquivo Principal |
|------------|--------|--------|-------------------|
| **Streamlit** | ≥1.28.0 | Framework web | `frontend/app.py` |

### 2.3 Infraestrutura / DevOps

| Tecnologia | Versão | Função | Arquivo Principal |
|------------|--------|--------|-------------------|
| **Docker** | 3.8 (compose) | Containerização | `Dockerfile`, `docker-compose.yml` |
| **Shell (Bash/Zsh)** | - | Scripts de automação | `scripts/*.sh` |

### 2.4 Integrações Externas

| API | Função | Arquivo |
|-----|--------|---------|
| **Google Sheets** | Fonte de dados das planilhas | `core/sync_manager.py`, `modules/leitor_google_sheets.py` |
| **Evolution API** | Envio de mensagens WhatsApp | `integrations/evolution_api.py` |
| **Kanbanize/Businessmap API v2** | Gestão de cards/tarefas | `integrations/kanbanize.py` |
| **OneTimeSecret API** | Compartilhamento seguro de senhas | `integrations/onetimesecret.py` |

### 2.5 Bibliotecas Python Padrão Utilizadas

| Biblioteca | Uso |
|------------|-----|
| `sqlite3` | Banco de dados |
| `datetime` | Manipulação de datas |
| `pathlib` | Caminhos de arquivos |
| `hashlib` | Hash MD5 para verificação de arquivos |
| `typing` | Type hints |
| `dataclasses` | Modelos de dados |
| `re` | Expressões regulares |
| `urllib.request` | Download de planilhas |
| `tempfile` | Arquivos temporários |
| `string` | Geração de senhas |
| `random` | Geração de senhas |
| `concurrent.futures` | Paralelismo (Kanbanize) |
| `json` | Serialização |

---

## 3. Documentação Oficial das Tecnologias

### Python & Bibliotecas Core

| Tecnologia | Documentação | Última Versão Estável |
|------------|--------------|----------------------|
| **Python 3.11** | https://docs.python.org/3/ | 3.11.x |
| **SQLite3** | https://docs.python.org/3/library/sqlite3.html | Built-in |
| **pandas** | https://pandas.pydata.org/docs/ | 2.3.3 (Jan 2026) |
| **openpyxl** | https://openpyxl.readthedocs.io/en/stable/ | 3.1.3 |
| **APScheduler** | https://apscheduler.readthedocs.io/en/stable/ | 3.x |
| **Requests** | https://requests.readthedocs.io/en/latest/ | 2.32.5 |
| **python-dateutil** | https://dateutil.readthedocs.io/ | 2.8.x |

### Frontend

| Tecnologia | Documentação | Novidades |
|------------|--------------|-----------|
| **Streamlit** | https://docs.streamlit.io/ | Cache por sessão, largura sidebar configurável, tokens OIDC |

### DevOps

| Tecnologia | Documentação |
|------------|--------------|
| **Docker** | https://docs.docker.com/ |
| **Docker Compose** | https://docs.docker.com/compose/ |

### Destaques de Atualizações Importantes

#### Streamlit (Novidades 2025-2026)
- ✨ **ASGI Entry Point & Starlette**: Suporte experimental para rotas HTTP customizadas e FastAPI
- ✨ **Session-scoped caching**: `st.cache_data` e `st.cache_resource` agora podem ser escopados por sessão
- ✨ **Sidebar configurável**: Definir largura padrão via `st.set_page_config`
- ✨ **OIDC Tokens**: Acesso a tokens em `st.user.tokens`

#### pandas 3.0 (Release Candidate)
- ⚠️ Mudanças significativas de API em desenvolvimento
- Verificar compatibilidade antes de atualizar

#### SQLite3 (Python 3.12+)
- ✨ Novo parâmetro `autocommit` em `sqlite3.connect()`
- ⚠️ Adaptadores e conversores padrão estão **deprecados** desde Python 3.12
- 📝 Recomendado usar conversores customizados (ver documentação)

---

## 4. Estrutura de Arquivos

### 4.1 Mapeamento Completo

```
controle-ferias/
├── main.py                      # Entry point CLI
├── config.py                    # Configurações básicas (legado)
├── Dockerfile                   # Imagem Docker
├── docker-compose.yml           # Orquestração de containers
├── requirements.txt             # Dependências Python
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Configurações centralizadas (Settings class)
│
├── core/                        # Lógica de negócio principal
│   ├── __init__.py
│   ├── database.py              # Acesso SQLite (1718 linhas)
│   ├── sync_manager.py          # Sincronização Google Sheets (659 linhas)
│   ├── models.py                # Dataclasses (Funcionario, Aba, SyncLog, PasswordLink)
│   ├── config_manager.py        # Gerenciamento de .env
│   └── validar_planilha.py      # Validação de planilhas
│
├── modules/                     # Módulos de processamento
│   ├── __init__.py
│   ├── leitor_excel.py          # Leitura de planilhas Excel locais
│   ├── leitor_google_sheets.py  # Leitura de Google Sheets
│   ├── processador.py           # Processamento/filtragem de dados
│   └── notificador.py           # Formatação de mensagens
│
├── integrations/                # Integrações externas
│   ├── __init__.py
│   ├── evolution_api.py         # WhatsApp via Evolution API
│   ├── kanbanize.py             # Kanbanize/Businessmap API v2
│   └── onetimesecret.py         # Geração de links de senha
│
├── frontend/                    # Interface Streamlit
│   ├── __init__.py
│   ├── app.py                   # App principal
│   ├── components.py            # Componentes reutilizáveis
│   └── modules/                 # Páginas do dashboard
│       ├── dashboard.py
│       ├── acessos.py
│       ├── configuracoes.py
│       ├── gerar_senhas.py
│       ├── kanbanize.py
│       ├── relatorio_kanbanize.py
│       ├── logs.py
│       ├── relatorios.py
│       └── sincronizacao.py
│
├── scheduler/                   # Agendamento de tarefas
│   ├── __init__.py
│   └── jobs.py                  # Jobs agendados (690 linhas)
│
├── utils/                       # Utilitários
│   ├── __init__.py
│   ├── formatadores.py          # Formatação de datas
│   └── password_generator.py    # Gerador de senhas seguras
│
├── scripts/                     # Scripts de automação
│   ├── iniciar.sh               # Iniciar aplicação
│   ├── parar.sh                 # Parar aplicação
│   ├── scheduler.sh             # Iniciar scheduler
│   ├── sync.sh                  # Executar sync manual
│   ├── docker-boot.sh
│   ├── docker-manager.sh
│   ├── docker-update.sh
│   └── deploy-ubuntu.sh
│
├── tests/                       # Testes
│   ├── __init__.py
│   ├── test_frontend.py
│   ├── testar_planilha.py
│   ├── validar_dados.py
│   └── gerar_planilha_teste.py
│
├── data/                        # Dados persistentes
│   ├── dados_sync.json
│   └── cache/
│
├── docs/                        # Documentação
│   ├── DOCUMENTACAO.md
│   ├── DOCUMENTACAO_COMPLETA.md
│   ├── GUIA_API_GOOGLE.md
│   └── ...
│
├── documentation/               # Documentação técnica
│   ├── DOCKER.md
│   ├── README.md
│   └── ...
│
└── logs/                        # Logs da aplicação
```

---

## 5. Análise de Código Duplicado

### 5.1 Código Duplicado Identificado

#### ❌ Função `_extrair_sheet_id()` - DUPLICADA

**Arquivos afetados:**
- `modules/leitor_google_sheets.py` (linha 28)
- `core/sync_manager.py` (linha 39)

**Código duplicado:**
```python
def _extrair_sheet_id(self, url: str) -> Optional[str]:
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
```

**Recomendação:** Mover para `utils/google_sheets.py` e importar em ambos os módulos.

---

#### ❌ Manipulação de `sys.path.insert()` - REPETIDA 20+ VEZES

**Arquivos afetados (parcial):**
- `main.py`
- `core/sync_manager.py`
- `core/config_manager.py`
- `integrations/*.py` (todos)
- `frontend/app.py`
- `frontend/modules/*.py` (todos)
- `scheduler/jobs.py`
- `tests/*.py`

**Código repetido:**
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
# ou
sys.path.insert(0, str(ROOT_DIR))
```

**Recomendação:** Configurar `PYTHONPATH` no ambiente ou criar um `__init__.py` na raiz que configure os paths automaticamente. Alternativa: usar pacotes instaláveis com `pyproject.toml`.

---

#### ❌ Função `formatar_data()` - 3 IMPLEMENTAÇÕES DIFERENTES

**Arquivos afetados:**
| Arquivo | Assinatura |
|---------|------------|
| `utils/formatadores.py` | `formatar_data(data: datetime, formato: str = "%d/%m/%Y")` |
| `frontend/components.py` | `formatar_data(data_str: str) -> str` |
| `modules/notificador.py` | `def formatar_data(self, data: datetime)` |
| `tests/validar_dados.py` | `formatar_data(valor, data_saida_ref=None)` |

**Recomendação:** Consolidar em `utils/formatadores.py` com sobrecarga ou função única que aceite múltiplos tipos de entrada.

---

#### ⚠️ Formatação de `datetime.now().strftime()` - REPETIDA 20+ VEZES

**Padrões encontrados:**
- `'%d/%m/%Y às %H:%M'` (4 ocorrências)
- `'%d/%m/%Y às %H:%M:%S'` (3 ocorrências)
- `'%Y%m%d_%H%M%S'` (2 ocorrências)
- `'%H:%M:%S'` (10+ ocorrências)
- `'%Y-%m-%d'` (2 ocorrências)

**Recomendação:** Criar constantes em `utils/formatadores.py`:
```python
FORMATO_DATA_BR = "%d/%m/%Y"
FORMATO_DATA_HORA_BR = "%d/%m/%Y às %H:%M"
FORMATO_DATA_HORA_COMPLETO = "%d/%m/%Y às %H:%M:%S"
FORMATO_TIMESTAMP_ARQUIVO = "%Y%m%d_%H%M%S"
FORMATO_HORA = "%H:%M:%S"
FORMATO_ISO = "%Y-%m-%d"

def agora_formatado(formato: str = FORMATO_DATA_HORA_BR) -> str:
    return datetime.now().strftime(formato)
```

---

### 5.2 Resumo de Código Duplicado

| Tipo | Quantidade | Severidade | Impacto |
|------|------------|------------|---------|
| `_extrair_sheet_id()` | 2 | 🔴 Alta | Manutenção duplicada |
| `sys.path.insert()` | 20+ | 🟡 Média | Boilerplate excessivo |
| `formatar_data()` | 4 | 🔴 Alta | Inconsistência de comportamento |
| Formatação de datas | 20+ | 🟡 Média | Código espalhado |

---

## 6. Padrões de Projeto Recomendados

### 6.1 Estrutura de Projeto (Baseado em Netflix Dispatch / FastAPI Best Practices)

Referência: [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)

**Estrutura recomendada por domínio:**
```
src/
├── {domain}/           # ex: auth/, posts/, funcionarios/
│   ├── router.py       # Endpoints da API (se usar FastAPI)
│   ├── schemas.py      # Modelos Pydantic
│   ├── models.py       # Modelos de banco de dados
│   ├── service.py      # Lógica de negócio
│   ├── dependencies.py # Dependências de rota
│   ├── config.py       # Variáveis de ambiente do módulo
│   ├── constants.py    # Constantes e códigos de erro
│   ├── exceptions.py   # Exceções específicas do domínio
│   └── utils.py        # Funções auxiliares
├── config.py           # Configuração global
├── models.py           # Modelos globais
├── exceptions.py       # Exceções globais
├── database.py         # Conexão com banco
└── main.py             # Inicialização da aplicação
```

### 6.2 Padrões Recomendados para Este Projeto

#### 1. **Repository Pattern** para `database.py`
Separar a lógica de acesso a dados em classes específicas:
```python
# repositories/funcionario_repository.py
class FuncionarioRepository:
    def buscar_por_id(self, id: int) -> Optional[Funcionario]: ...
    def buscar_em_ferias(self) -> List[Funcionario]: ...
    def salvar(self, funcionario: Funcionario) -> int: ...
```

#### 2. **Service Layer** para Lógica de Negócio
Mover lógica de negócio complexa para classes de serviço:
```python
# services/sync_service.py
class SyncService:
    def __init__(self, repository: FuncionarioRepository, downloader: SheetDownloader):
        self.repository = repository
        self.downloader = downloader
    
    def sincronizar(self) -> SyncResult: ...
```

#### 3. **Factory Pattern** para Integrações
```python
# integrations/factory.py
class IntegrationFactory:
    @staticmethod
    def criar_notificador() -> Notificador:
        if settings.EVOLUTION_ENABLED:
            return EvolutionNotificador()
        return ConsoleNotificador()
```

#### 4. **Strategy Pattern** para Processamento de Dados
```python
# processors/base.py
class ProcessadorStrategy(Protocol):
    def processar(self, dados: pd.DataFrame) -> List[Funcionario]: ...

class ProcessadorFerias(ProcessadorStrategy): ...
class ProcessadorLicencas(ProcessadorStrategy): ...
```

#### 5. **Singleton** para Settings (já implementado)
A classe `Settings` em `config/settings.py` já segue este padrão com `settings = Settings()`.

### 6.3 Convenções de Nomenclatura (FastAPI Best Practices)

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Tabelas | singular, snake_case | `funcionario`, `sync_log` |
| Colunas datetime | sufixo `_at` | `created_at`, `synced_at` |
| Colunas date | sufixo `_date` | `birth_date`, `data_saida` |
| Índices | `{coluna}_idx` | `data_saida_idx` |
| Foreign keys | `{tabela}_{coluna}_fkey` | `funcionario_id_fkey` |

---

## 7. Oportunidades de Melhoria

### 7.1 Prioridade Alta 🔴

| # | Melhoria | Benefício | Esforço |
|---|----------|-----------|---------|
| 1 | Eliminar código duplicado `_extrair_sheet_id()` | Manutenção simplificada | Baixo |
| 2 | Consolidar `formatar_data()` | Consistência | Baixo |
| 3 | Configurar `PYTHONPATH` adequadamente | Eliminar `sys.path.insert()` | Médio |
| 4 | Criar `pyproject.toml` para gerenciamento de pacote | Instalação moderna | Médio |
| 5 | Adicionar type hints completos | Melhor IDE support | Médio |

### 7.2 Prioridade Média 🟡

| # | Melhoria | Benefício | Esforço |
|---|----------|-----------|---------|
| 6 | Implementar logging estruturado | Debugging | Médio |
| 7 | Adicionar testes unitários | Confiabilidade | Alto |
| 8 | Usar Pydantic para validação | Validação robusta | Médio |
| 9 | Migrar para SQLAlchemy ORM | Queries tipadas | Alto |
| 10 | Adicionar Health Checks | Monitoramento | Baixo |

### 7.3 Prioridade Baixa 🟢

| # | Melhoria | Benefício | Esforço |
|---|----------|-----------|---------|
| 11 | Migrar para FastAPI | API REST moderna | Alto |
| 12 | Implementar cache com Redis | Performance | Alto |
| 13 | Adicionar Alembic para migrações | Versionamento de schema | Médio |
| 14 | Configurar ruff/black | Formatação consistente | Baixo |
| 15 | Adicionar CI/CD | Automação de deploy | Médio |

### 7.4 Sugestões Específicas por Arquivo

#### `core/database.py` (1718 linhas)
- ⚠️ Arquivo muito grande, considerar dividir em:
  - `repositories/funcionario.py`
  - `repositories/sync_log.py`
  - `repositories/kanbanize.py`
  - `repositories/acessos.py`

#### `scheduler/jobs.py` (690 linhas)
- Extrair lógica de mensagens para `services/notification_service.py`
- Usar decorators para controle de jobs executados

#### `config/settings.py`
- Migrar para `pydantic-settings` para validação automática:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_sheets_url: str
    sync_hour: int = 6
    sync_enabled: bool = True
    
    class Config:
        env_file = ".env"
```

#### Integrações
- Implementar retry com backoff exponencial para APIs externas
- Adicionar circuit breaker pattern para resiliência

---

## 8. Referências e Links Úteis

### Documentação Oficial

| Recurso | Link |
|---------|------|
| Python Docs | https://docs.python.org/3/ |
| Streamlit Docs | https://docs.streamlit.io/ |
| pandas Docs | https://pandas.pydata.org/docs/ |
| SQLite3 Python | https://docs.python.org/3/library/sqlite3.html |
| APScheduler | https://apscheduler.readthedocs.io/ |
| Docker Docs | https://docs.docker.com/ |
| openpyxl | https://openpyxl.readthedocs.io/ |
| Requests | https://requests.readthedocs.io/ |

### Padrões e Best Practices

| Recurso | Link |
|---------|------|
| FastAPI Best Practices | https://github.com/zhanymkanov/fastapi-best-practices |
| Python Project Structure | https://docs.python-guide.org/writing/structure/ |
| Twelve-Factor App | https://12factor.net/ |
| Clean Architecture Python | https://github.com/pcah/python-clean-architecture |

### Ferramentas Recomendadas

| Ferramenta | Função | Link |
|------------|--------|------|
| **ruff** | Linter + Formatter ultra-rápido | https://github.com/astral-sh/ruff |
| **pytest** | Framework de testes | https://docs.pytest.org/ |
| **Pydantic** | Validação de dados | https://docs.pydantic.dev/ |
| **SQLAlchemy** | ORM | https://www.sqlalchemy.org/ |
| **Alembic** | Migrações de banco | https://alembic.sqlalchemy.org/ |

---

## 📝 Checklist de Ações Recomendadas

### Imediatas (1-2 dias)
- [ ] Extrair `_extrair_sheet_id()` para `utils/google_sheets.py`
- [ ] Consolidar funções `formatar_data()`
- [ ] Criar constantes para formatos de data
- [ ] Configurar `PYTHONPATH` no `docker-compose.yml`

### Curto Prazo (1-2 semanas)
- [ ] Criar `pyproject.toml`
- [ ] Adicionar type hints em módulos principais
- [ ] Implementar logging estruturado
- [ ] Adicionar testes para `core/database.py`

### Médio Prazo (1 mês)
- [ ] Refatorar `core/database.py` em repositories
- [ ] Migrar Settings para pydantic-settings
- [ ] Configurar ruff e pre-commit hooks
- [ ] Adicionar documentação de API (se aplicável)

---

> **Nota:** Este documento deve ser atualizado conforme o projeto evolui. Use-o como referência para decisões técnicas e onboarding de novos desenvolvedores.
