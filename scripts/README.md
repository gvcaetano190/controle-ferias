# 📜 Scripts do Sistema

Scripts bash compatíveis com **Linux Ubuntu**, **macOS** e **Docker**.

## ✅ Compatibilidade

Todos os scripts são compatíveis com:
- ✅ Linux (Ubuntu, Debian, CentOS, etc)
- ✅ macOS
- ✅ Docker containers
- ✅ WSL (Windows Subsystem for Linux)

## 📋 Scripts Disponíveis

### `iniciar.sh`
Inicia o dashboard Streamlit.

```bash
./scripts/iniciar.sh
```

**O que faz:**
- Ativa o virtual environment (se existir)
- Verifica dependências
- Para processos anteriores do Streamlit
- Inicia o Streamlit na porta 8501

### `scheduler.sh`
Inicia o scheduler (daemon) para agendamento automático.

```bash
./scripts/scheduler.sh
```

**O que faz:**
- Ativa o virtual environment
- Inicia o scheduler em modo daemon
- Executa jobs nos horários configurados

**Modos:**
```bash
./scripts/scheduler.sh           # Modo daemon (roda continuamente)
./scripts/scheduler.sh --once    # Executa uma vez e sai
./scripts/scheduler.sh --sync    # Executa apenas sincronização
```

### `sync.sh`
Executa sincronização manual.

```bash
./scripts/sync.sh           # Sincronização normal (usa cache)
./scripts/sync.sh --forcar  # Força download e processamento
```

**O que faz:**
- Ativa o virtual environment
- Baixa planilha do Google Sheets
- Processa e salva no banco de dados

### `parar.sh`
Para todos os processos do sistema.

```bash
./scripts/parar.sh
```

**O que faz:**
- Para o Streamlit
- Para o scheduler
- Remove arquivos PID (se existirem)

## 🐳 Uso no Docker

### Exemplo de Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copia código
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Torna scripts executáveis
RUN chmod +x scripts/*.sh

# Comando padrão
CMD ["./scripts/iniciar.sh"]
```

### Docker Compose:

```yaml
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    command: ["./scripts/iniciar.sh"]
    
  scheduler:
    build: .
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    command: ["./scripts/scheduler.sh"]
    restart: unless-stopped
```

## 🐧 Uso no Linux Ubuntu

### Permissões:

```bash
# Torna scripts executáveis (se necessário)
chmod +x scripts/*.sh
```

### Executar como serviço (systemd):

Crie `/etc/systemd/system/controle-ferias-scheduler.service`:

```ini
[Unit]
Description=Controle de Férias - Scheduler
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/caminho/para/controle-ferias
ExecStart=/caminho/para/controle-ferias/scripts/scheduler.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ative o serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable controle-ferias-scheduler
sudo systemctl start controle-ferias-scheduler
```

## 📝 Notas

- Todos os scripts detectam automaticamente o diretório do projeto
- Funcionam com ou sem virtual environment
- Compatíveis com caminhos relativos e absolutos
- Usam apenas comandos padrão do bash (sem dependências especiais)

## ⚠️ Requisitos

- Bash 4.0+
- Python 3.8+
- Comandos padrão: `grep`, `cut`, `pkill` (disponíveis no Linux/macOS)







