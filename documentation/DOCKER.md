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

#### Linux (Ubuntu/Debian):
```bash
# 1. Configure o Docker para iniciar no boot
sudo systemctl enable docker
sudo systemctl enable containerd

# 2. Verifique se está ativado
sudo systemctl is-enabled docker

# 3. Os containers com restart: always iniciam automaticamente!
```

#### macOS:
```bash
# O Docker Desktop já inicia automaticamente se configurado nas Preferências
# 1. Abra Docker Desktop
# 2. Vá em Preferences → General
# 3. Marque "Start Docker Desktop when you log in"
```

---

## 🔧 Operações Comuns

---

## 🔧 Operações Comuns

### 📊 Monitorar o Sistema

```bash
# Ver status e uso de recursos
./scripts/docker-manager.sh status

# Ver logs em tempo real
./scripts/docker-manager.sh logs

# Ver logs apenas do frontend
docker-compose logs -f frontend

# Ver logs apenas do scheduler
docker-compose logs -f scheduler

# Ver últimas 100 linhas de log
docker-compose logs --tail=100
```

### 🔄 Executar Sincronização Manual

```bash
# Dentro do container via script
./scripts/docker-manager.sh sync

# OU diretamente
docker-compose exec frontend python -m modules.leitor_google_sheets
```

### 🐚 Acessar o Shell do Container

```bash
# Via script
./scripts/docker-manager.sh shell

# OU diretamente
docker-compose exec frontend bash

# Dentro do container, você pode:
# - Ver arquivos: ls -la
# - Ver banco: sqlite3 data/database.sqlite ".tables"
# - Ver logs: cat logs/app.log
```

### ⚙️ Modificar Configurações

```bash
# 1. Edite o .env
nano .env

# 2. Reinicie os containers para aplicar
./scripts/docker-manager.sh restart

# OU reinicie apenas o scheduler
docker-compose restart scheduler
```

---

## 🐛 Solução de Problemas

---

## 🐛 Solução de Problemas

### ❌ Container não inicia

```bash
# 1. Ver logs detalhados
docker-compose logs frontend
docker-compose logs scheduler

# 2. Verificar se a porta 8501 está livre
lsof -i :8501
# Se estiver ocupada, mate o processo ou use outra porta

# 3. Verificar configuração do docker-compose
docker-compose config

# 4. Tentar reconstruir
./scripts/docker-manager.sh rebuild
```

### ⏰ Scheduler não executa jobs

```bash
# 1. Verificar se o scheduler está rodando
docker-compose ps scheduler

# 2. Ver logs do scheduler
docker-compose logs scheduler

# 3. Verificar variáveis do .env
cat .env | grep SYNC

# 4. Executar sincronização manual para testar
./scripts/docker-manager.sh sync

# 5. Reiniciar scheduler
docker-compose restart scheduler
```

### 💾 Banco de dados com erro

```bash
# 1. Fazer backup primeiro!
cp data/database.sqlite data/database.sqlite.backup

# 2. Acessar container e verificar
docker-compose exec frontend bash
sqlite3 data/database.sqlite ".tables"
sqlite3 data/database.sqlite "PRAGMA integrity_check;"

# 3. Se necessário, resetar banco (CUIDADO: perde dados!)
rm data/database.sqlite
docker-compose restart frontend
```

### 🌐 Erro "Port 8501 already in use"

```bash
# 1. Verificar o que está usando a porta
lsof -i :8501

# 2. Matar o processo
kill -9 <PID>

# 3. OU mudar a porta no docker-compose.yml
# ports:
#   - "8502:8501"  # Use porta 8502 no host
```

### 🔄 Container fica reiniciando constantemente

```bash
# 1. Ver logs para identificar o erro
docker-compose logs --tail=50 frontend

# 2. Verificar se o .env está correto
cat .env

# 3. Verificar se todas as dependências estão instaladas
docker-compose exec frontend pip list

# 4. Reconstruir do zero
./scripts/docker-manager.sh rebuild
```

### 🧹 Limpar tudo e recomeçar

```bash
# CUIDADO: Isso remove TUDO (containers, volumes, imagens, dados)!
./scripts/docker-manager.sh clean

# Depois reconstrua
./scripts/docker-manager.sh start
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

---

## 🚀 Deploy em Produção (Servidor/VPS)

### 📝 Passo a Passo para Servidor Ubuntu

```bash
# === 1. PREPARAR O SERVIDOR ===

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Git
sudo apt install git -y

# === 2. CLONAR O PROJETO ===

# Clone o repositório
cd /home/$USER
git clone git@github.com:gvcaetano190/controle-ferias.git
cd controle-ferias

# === 3. CONFIGURAR ===

# Crie o arquivo .env
nano .env

# Cole suas configurações:
# GOOGLE_SHEETS_URL=...
# SYNC_HOUR=8
# etc...

# === 4. INICIAR ===

# Dê permissão aos scripts
chmod +x scripts/*.sh

# Inicie os containers
./scripts/docker-manager.sh start

# === 5. CONFIGURAR AUTOSTART ===

# Configure Docker para iniciar no boot
sudo systemctl enable docker

# === 6. (OPCIONAL) CONFIGURAR NGINX ===

# Instale nginx
sudo apt install nginx -y

# Crie configuração
sudo nano /etc/nginx/sites-available/controle-ferias

# Cole:
server {
    listen 80;
    server_name seu-dominio.com;

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

# Ative o site
sudo ln -s /etc/nginx/sites-available/controle-ferias /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 🔒 Segurança em Produção

**Recomendações importantes:**

1. **Firewall:**
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

2. **SSL/HTTPS com Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

3. **Limites de recursos no docker-compose.yml:**
```yaml
services:
  frontend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

4. **Backup automático:**
```bash
# Adicione ao crontab
crontab -e

# Backup diário às 3h
0 3 * * * tar -czf /backup/controle-ferias-$(date +\%Y\%m\%d).tar.gz /home/$USER/controle-ferias/data
```

```

---

## 📝 Resumo dos Scripts Disponíveis

O projeto inclui vários scripts na pasta `scripts/` para facilitar a operação:

| Script | Descrição | Quando usar |
|--------|-----------|-------------|
| `docker-manager.sh` | **Script principal** - Gerencia tudo | Use sempre! |
| `iniciar.sh` | Inicia o Streamlit (frontend) | Automático pelo Docker |
| `scheduler.sh` | Inicia o scheduler | Automático pelo Docker |
| `sync.sh` | Executa sincronização manual | Quando quiser forçar sync |
| `deploy-ubuntu.sh` | Deploy completo em servidor Ubuntu | Setup inicial no servidor |
| `docker-update.sh` | Atualiza containers | `./scripts/docker-manager.sh update` |
| `parar.sh` | Para o sistema local (sem Docker) | Desenvolvimento local |

**Comando mais importante:**
```bash
./scripts/docker-manager.sh help  # Ver todos os comandos disponíveis
```

---

## ✅ Checklist Pós-Instalação

Após iniciar os containers, verifique:

- [ ] Containers estão rodando: `./scripts/docker-manager.sh status`
- [ ] Frontend está acessível em http://localhost:8501
- [ ] Não há erros nos logs: `./scripts/docker-manager.sh logs`
- [ ] Banco de dados foi criado: `ls -la data/database.sqlite`
- [ ] Scheduler está ativo: `docker-compose logs scheduler | grep "Started"`
- [ ] Sincronização funciona: `./scripts/docker-manager.sh sync`
- [ ] Volumes estão montados: `docker-compose ps`

---

## 🆘 Comandos de Debug

### Comandos úteis para solução de problemas:

```bash
# Ver versões
docker --version
docker-compose --version

# Ver o que está usando as portas
lsof -i :8501

# Ver todos os containers (incluindo parados)
docker ps -a

# Ver uso de disco Docker
docker system df

# Limpar cache Docker (libera espaço)
docker system prune -a

# Ver redes Docker
docker network ls

# Inspecionar container detalhadamente
docker inspect controle-ferias-frontend
```

### Estrutura de Logs:

- **Logs do Docker:** `./scripts/docker-manager.sh logs`
- **Logs da aplicação:** `./logs/app.log`
- **Logs do scheduler:** `docker-compose logs scheduler`

---

## 📚 Recursos Adicionais

- **Documentação Docker:** https://docs.docker.com/
- **Docker Compose:** https://docs.docker.com/compose/
- **Streamlit:** https://docs.streamlit.io/
- **Repositório:** https://github.com/gvcaetano190/controle-ferias

---

**🎉 Pronto! Seu sistema está rodando em Docker!**

### 💡 Dica Final:

Para operação diária, você só precisa de 3 comandos:

```bash
./scripts/docker-manager.sh start    # Iniciar
./scripts/docker-manager.sh logs     # Monitorar
./scripts/docker-manager.sh stop     # Parar
```

Se tiver problemas, sempre comece verificando os logs!

---

## 📞 Suporte

Em caso de dúvidas ou problemas:
1. Verifique os logs: `./scripts/docker-manager.sh logs`
2. Verifique o status: `./scripts/docker-manager.sh status`
3. Consulte a seção de Solução de Problemas acima
4. Abra uma issue no GitHub do projeto

