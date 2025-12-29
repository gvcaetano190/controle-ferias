# 🐳 Guia Docker - Sistema de Controle de Férias

Guia completo para executar o sistema usando Docker e Docker Compose.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter:

- **Docker** 20.10+ instalado
- **Docker Compose** 2.0+ instalado
- **Git** (para clonar o repositório)

### Verificar instalação:

```bash
docker --version
docker-compose --version
git --version
```

### Instalar Docker (se ainda não tiver):

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Faça logout e login novamente
```

**macOS:**
```bash
# Baixe e instale o Docker Desktop:
# https://www.docker.com/products/docker-desktop/
```

---

## 🚀 Início Rápido - Passo a Passo

### 📥 Passo 1: Clonar o Projeto

```bash
# Clone o repositório
git clone git@github.com:gvcaetano190/controle-ferias.git
cd controle-ferias
```

### ⚙️ Passo 2: Configurar o Ambiente

```bash
# 1. Copie o arquivo de exemplo (se existir)
cp .env.example .env  # ou crie um novo

# 2. Edite o arquivo .env com suas configurações
nano .env  # ou use seu editor favorito
```

**Configurações importantes no .env:**
```env
# Google Sheets
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/SEU_ID/edit

# Horário da sincronização automática
SYNC_HOUR=8
SYNC_MINUTE=15
SYNC_ENABLED=true

# Evolution API (opcional)
EVOLUTION_ENABLED=false
EVOLUTION_API_URL=
EVOLUTION_API_KEY=

# OneTimeSecret (opcional)
ONETIMESECRET_ENABLED=false
ONETIMESECRET_EMAIL=
ONETIMESECRET_API_KEY=
```

### 🐳 Passo 3: Subir os Containers

**Opção A - Usando o Script Helper (Recomendado):**
```bash
# Dê permissão de execução aos scripts (primeira vez)
chmod +x scripts/*.sh

# Inicie tudo com um comando
./scripts/docker-manager.sh start
```

**Opção B - Usando Docker Compose diretamente:**
```bash
# Construir e iniciar os containers
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f
```

### ✅ Passo 4: Verificar se está Funcionando

```bash
# Verificar status dos containers
./scripts/docker-manager.sh status

# OU
docker-compose ps
```

**Você deve ver algo como:**
```
NAME                           STATUS          PORTS
controle-ferias-frontend       Up (healthy)    0.0.0.0:8501->8501/tcp
controle-ferias-scheduler      Up (healthy)    
```

### 🌐 Passo 5: Acessar o Sistema

Abra seu navegador e acesse:
- **Dashboard:** http://localhost:8501
- **Scheduler:** Rodando em background automaticamente

---

## 🛠️ Comandos Principais

### ⚡ Script Helper (Mais Fácil)

O script `docker-manager.sh` facilita todas as operações:

```bash
# Ver todos os comandos disponíveis
./scripts/docker-manager.sh help

# Iniciar os containers
./scripts/docker-manager.sh start

# Parar os containers
./scripts/docker-manager.sh stop

# Reiniciar os containers
./scripts/docker-manager.sh restart

# Atualizar código (após git pull)
./scripts/docker-manager.sh update

# Reconstruir tudo do zero (após mudanças importantes)
./scripts/docker-manager.sh rebuild

# Ver logs em tempo real
./scripts/docker-manager.sh logs

# Ver status e uso de recursos
./scripts/docker-manager.sh status

# Executar sincronização manual
./scripts/docker-manager.sh sync

# Acessar o shell do container
./scripts/docker-manager.sh shell

# Limpar tudo (CUIDADO: remove dados!)
./scripts/docker-manager.sh clean
```

### 📝 Comandos Docker Compose Diretos

Se preferir usar o Docker Compose diretamente:

```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Reconstruir e iniciar
docker-compose up -d --build

# Reiniciar um serviço específico
docker-compose restart frontend
docker-compose restart scheduler
```

---

## 📦 Arquitetura dos Containers

### 🎯 Estrutura do Projeto

```
controle-ferias/
├── Dockerfile              # Define como construir a imagem Docker
├── docker-compose.yml      # Orquestra os containers
├── .env                    # Configurações (não commitar!)
├── requirements.txt        # Dependências Python
├── scripts/
│   ├── docker-manager.sh   # Script helper principal
│   ├── iniciar.sh          # Inicia o Streamlit
│   ├── scheduler.sh        # Inicia o scheduler
│   └── sync.sh             # Executa sincronização manual
├── data/                   # Banco de dados SQLite (persistente)
├── logs/                   # Logs do sistema (persistente)
└── download/               # Arquivos baixados (persistente)
```

### 🐳 Containers

O sistema utiliza 2 containers:

#### 1️⃣ **Frontend (Streamlit)**
- **Container:** `controle-ferias-frontend`
- **Porta:** 8501 (http://localhost:8501)
- **Função:** Interface web do dashboard
- **Restart:** `always` - reinicia automaticamente
- **Healthcheck:** Verifica se está respondendo

**O que ele faz:**
- Exibe o dashboard web
- Permite configurar o sistema
- Mostra relatórios e logs
- Executa operações manuais

#### 2️⃣ **Scheduler**
- **Container:** `controle-ferias-scheduler`
- **Função:** Executa tarefas agendadas
- **Restart:** `always` - reinicia automaticamente
- **Healthcheck:** Verifica se o processo está ativo

**O que ele faz:**
- Sincroniza dados do Google Sheets automaticamente
- Envia notificações via Evolution API
- Executa jobs nos horários configurados
- Roda em background 24/7

### 📁 Volumes Persistentes

Dados que **NÃO são perdidos** quando você para os containers:

```yaml
volumes:
  - ./data:/app/data          # Banco de dados SQLite
  - ./download:/app/download  # Planilhas baixadas
  - ./logs:/app/logs          # Logs do sistema
  - ./.env:/app/.env          # Configurações
```

**⚠️ Importante:** Esses dados ficam no seu computador, não dentro do container!

---

## 🔄 Fluxo de Trabalho Comum

### 📝 Cenário 1: Primeira Instalação

```bash
# 1. Clone o projeto
git clone git@github.com:gvcaetano190/controle-ferias.git
cd controle-ferias

# 2. Configure o .env
nano .env

# 3. Dê permissão aos scripts
chmod +x scripts/*.sh

# 4. Inicie tudo
./scripts/docker-manager.sh start

# 5. Acesse http://localhost:8501
```

### 🔃 Cenário 2: Atualizar o Código

```bash
# 1. Baixe as atualizações
git pull

# 2. Atualize e reinicie
./scripts/docker-manager.sh update

# Pronto! Os containers foram reconstruídos com o novo código
```

### 🔧 Cenário 3: Mudou Dependências (requirements.txt)

```bash
# 1. Baixe as atualizações
git pull

# 2. Reconstrua tudo do zero
./scripts/docker-manager.sh rebuild

# Isso garante que as novas dependências sejam instaladas
```

### 🛑 Cenário 4: Parar Tudo

```bash
# Parar os containers
./scripts/docker-manager.sh stop

# OU
docker-compose down

# Seus dados em ./data, ./logs e ./download continuam salvos!
```

### 🗑️ Cenário 5: Resetar Completamente

```bash
# CUIDADO: Isso apaga TODOS os dados!
./scripts/docker-manager.sh clean

# Vai perguntar confirmação antes de apagar
```

### 🔍 Cenário 6: Investigar Problemas

```bash
# Ver logs em tempo real
./scripts/docker-manager.sh logs

# Ver status e uso de recursos
./scripts/docker-manager.sh status

# Acessar o container para investigar
./scripts/docker-manager.sh shell
```

---

## 🤖 Restart Automático após Reboot

Os containers estão configurados com `restart: always`, o que significa:
- ✅ Reiniciam automaticamente se caírem
- ✅ Iniciam automaticamente quando o computador ligar
- ✅ Reiniciam após falhas

### Configuração Adicional

**Para garantir que funcionem após reboot:**
```bash
# Configure o Docker para iniciar no boot
sudo systemctl enable docker
sudo systemctl enable containerd

# Configure docker-compose para iniciar os containers no boot
# Adicione ao crontab (inicia 2 minutos após boot)
(crontab -l 2>/dev/null; echo "@reboot sleep 120 && cd /caminho/para/controle-ferias && docker-compose up -d") | crontab -
```

#### macOS:
O Docker Desktop já inicia automaticamente se configurado nas Preferências do Docker Desktop.

---

## 🔧 Comandos Úteis

### ⚡ Script Helper (Mais Fácil)

```bash
# Iniciar tudo
./scripts/docker-manager.sh start

# Atualizar código (rápido)
./scripts/docker-manager.sh update

# Reconstruir após mudanças no código
./scripts/docker-manager.sh rebuild

# Ver logs
./scripts/docker-manager.sh logs

# Ver status
./scripts/docker-manager.sh status

# Parar
./scripts/docker-manager.sh stop

# Executar sincronização manual
./scripts/docker-manager.sh sync

# Ver todos os comandos
./scripts/docker-manager.sh help
```

### Gerenciamento Básico

```bash
# Iniciar tudo
docker-compose up -d

# Parar tudo
docker-compose down

# Reiniciar tudo
docker-compose restart

# Ver status
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Ver logs dos últimos 100 linhas
docker-compose logs --tail=100
```

### Executar Comandos Dentro dos Containers

```bash
# Executar sincronização manual
docker-compose exec frontend ./scripts/sync.sh

# Executar sincronização forçada
docker-compose exec frontend ./scripts/sync.sh --forcar

# Acessar shell do container
docker-compose exec frontend bash
docker-compose exec scheduler bash

# Ver processos rodando
docker-compose exec scheduler ps aux
```

### Rebuild

```bash
# Reconstruir após mudanças no código
docker-compose build --no-cache

# Reconstruir e reiniciar
docker-compose up -d --build
```

---

## 📁 Persistência de Dados

Os seguintes diretórios são montados como volumes:

- `./data` → Banco de dados SQLite e cache
- `./download` → Arquivos baixados do Google Sheets
- `./logs` → Logs do sistema
- `./.env` → Configurações

**Importante:** Os dados persistem mesmo após parar os containers.

---

## 🔄 Atualizações

### Atualizar Código

```bash
# 1. Pare os containers
docker-compose down

# 2. Reconstrua as imagens
docker-compose build --no-cache

# 3. Inicie novamente
docker-compose up -d
```

### Atualizar Configurações (.env)

```bash
# 1. Edite o arquivo .env
nano .env

# 2. Reinicie os containers para aplicar mudanças
docker-compose restart

# OU reinicie apenas o scheduler (para aplicar novos horários)
docker-compose restart scheduler
```

---

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs frontend
docker-compose logs scheduler

# Verificar se a porta está livre
lsof -i :8501

# Verificar configuração
docker-compose config
```

### Scheduler não executa jobs

```bash
# Verificar se está rodando
docker-compose exec scheduler ps aux | grep scheduler

# Ver logs do scheduler
docker-compose logs scheduler

# Reiniciar scheduler
docker-compose restart scheduler
```

### Banco de dados com erro

```bash
# Acessar container e verificar banco
docker-compose exec frontend bash
sqlite3 data/database.sqlite ".tables"

# Fazer backup antes de reconstruir
docker-compose exec frontend cp data/database.sqlite data/database.sqlite.backup
```

### Limpar tudo e recomeçar

```bash
# Para e remove containers, networks
docker-compose down

# Remove também volumes (CUIDADO: apaga dados!)
docker-compose down -v

# Remove imagens também
docker-compose down --rmi all
```

---

## 🔒 Segurança

### Produção

Para ambiente de produção, considere:

1. **Variáveis de ambiente** ao invés de arquivo .env montado
2. **Usuário não-root** no container
3. **Secrets management** (Docker Secrets ou Vault)
4. **HTTPS** com reverse proxy (nginx/traefik)
5. **Limites de recursos** (CPU/Memória)

Exemplo com variáveis de ambiente:

```yaml
environment:
  - GOOGLE_SHEETS_URL=${GOOGLE_SHEETS_URL}
  - SYNC_HOUR=${SYNC_HOUR}
  # ... outras variáveis
```

---

## 📊 Monitoramento

### Verificar Status

```bash
# Status dos containers
docker-compose ps

# Uso de recursos
docker stats controle-ferias-frontend controle-ferias-scheduler

# Healthcheck
docker-compose ps
# Status "healthy" indica que está funcionando
```

### Logs

```bash
# Todos os logs
docker-compose logs

# Últimas 50 linhas de cada serviço
docker-compose logs --tail=50

# Seguir logs em tempo real
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f scheduler
```

---

## 🚀 Deploy em Produção

### Exemplo com Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name controle-ferias.exemplo.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Docker Compose com Limites

```yaml
services:
  frontend:
    # ... outras configurações
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 📝 Exemplo Completo de Uso

```bash
# 1. Clone o projeto
git clone <repo> controle-ferias
cd controle-ferias

# 2. Configure .env
cp .env.example .env
nano .env

# 3. Inicie tudo
docker-compose up -d

# 4. Verifique se está rodando
docker-compose ps

# 5. Acesse o dashboard
# http://localhost:8501

# 6. Verifique logs
docker-compose logs -f scheduler

# 7. Execute sincronização manual
docker-compose exec frontend ./scripts/sync.sh

# 8. Para parar
docker-compose down
```

---

## ✅ Checklist de Verificação

Após iniciar os containers, verifique:

- [ ] Frontend está acessível em http://localhost:8501
- [ ] Scheduler está rodando (`docker-compose logs scheduler`)
- [ ] Banco de dados está sendo criado em `./data/database.sqlite`
- [ ] Logs não mostram erros
- [ ] Jobs são executados nos horários configurados

---

**Pronto para rodar em Docker! 🐳**

