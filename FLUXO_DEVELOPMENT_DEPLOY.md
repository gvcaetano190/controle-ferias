# 🚀 Fluxo Completo: Mac → GitHub → Ubuntu → Docker

Guia passo a passo completo para desenvolver no Mac, publicar no GitHub e fazer deploy em um servidor Ubuntu com Docker.

---

## 📋 Visão Geral do Fluxo

```
Mac (Desenvolvimento)
    ↓
GitHub (Repositório)
    ↓
Ubuntu Server (Produção)
    ↓
Docker Containers (Execução)
```

---

## 🍎 PARTE 1: Desenvolvimento no Mac

### 1.1. Setup Inicial

```bash
# 1. Clone ou navegue até o projeto
cd ~/Documents/controle-ferias

# 2. Ative o ambiente virtual
source venv/bin/activate

# 3. Configure o .env local (não versionar!)
cp .env.example .env
nano .env
```

### 1.2. Desenvolvimento Local

```bash
# Desenvolva normalmente no Mac
# Teste localmente:

# Terminal 1: Frontend
./scripts/iniciar.sh

# Terminal 2: Scheduler (opcional para testes)
./scripts/scheduler.sh
```

### 1.3. Testar Mudanças

```bash
# Execute testes
./scripts/sync.sh

# Verifique se está funcionando
# Acesse: http://localhost:8501
```

---

## 📤 PARTE 2: Publicar no GitHub

### 2.1. Configurar Git (Primeira Vez)

```bash
# Se ainda não inicializou o repositório
cd ~/Documents/controle-ferias

git init
git branch -M main
```

### 2.2. Criar .gitignore (se não existir)

Verifique se o `.gitignore` inclui:

```gitignore
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Dados sensíveis
.env
.env.local
*.log

# Dados
data/database.sqlite
data/*.sqlite
download/*.xlsx
logs/*.log

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Docker (opcional)
# Mantenha Dockerfile e docker-compose.yml no git
```

### 2.3. Criar Repositório no GitHub

1. Acesse: https://github.com/new
2. Crie um novo repositório (ex: `controle-ferias`)
3. **NÃO** inicialize com README, .gitignore ou license

### 2.4. Fazer Commit e Push

```bash
# Adiciona todos os arquivos
git add .

# Primeiro commit
git commit -m "Initial commit: Sistema de Controle de Férias"

# Adiciona remote do GitHub
git remote add origin https://github.com/SEU_USUARIO/controle-ferias.git

# Push inicial
git push -u origin main
```

### 2.5. Workflow de Desenvolvimento

```bash
# 1. Faça suas alterações no código

# 2. Teste localmente
./scripts/iniciar.sh

# 3. Commit e push
git add .
git commit -m "Descrição das mudanças"
git push origin main
```

---

## 🐧 PARTE 3: Deploy no Ubuntu Server

### 3.1. Conectar ao Servidor Ubuntu

```bash
# SSH para o servidor
ssh usuario@seu-servidor-ubuntu

# Navegue até onde quer instalar (ex: /opt ou /home/usuario)
cd /opt
# ou
cd ~/docker-projects
```

### 3.2. Clonar do GitHub

```bash
# Clona o repositório
git clone https://github.com/SEU_USUARIO/controle-ferias.git
cd controle-ferias

# Verifica se clonou corretamente
ls -la
```

### 3.3. Configurar .env no Servidor

```bash
# Copia o exemplo
cp .env.example .env

# Edita com as configurações de PRODUÇÃO
nano .env
```

**Configurações importantes para produção:**

```env
# Google Sheets
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/SEU_ID/edit

# Sincronização
SYNC_HOUR=8
SYNC_MINUTE=15
SYNC_ENABLED=true

# Evolution API (se estiver no mesmo host, use o nome do container ou IP interno)
EVOLUTION_ENABLED=true
EVOLUTION_API_URL=http://evolution-api:8081/message/sendText/zabbix
# OU se estiver em outro container na mesma rede:
# EVOLUTION_API_URL=http://IP_INTERNO_DO_CONTAINER:8081/message/sendText/zabbix
EVOLUTION_NUMERO=120363020985287866@g.us
EVOLUTION_API_KEY=sua_chave_aqui

# Mensagens
MENSAGEM_MANHA_ENABLED=true
MENSAGEM_MANHA_HOUR=8
MENSAGEM_MANHA_MINUTE=0

MENSAGEM_TARDE_ENABLED=true
MENSAGEM_TARDE_HOUR=17
MENSAGEM_TARDE_MINUTE=0
```

### 3.4. Verificar Docker no Servidor

```bash
# Verifica se Docker está instalado
docker --version
docker-compose --version

# Se não estiver instalado:
# sudo apt update
# sudo apt install docker.io docker-compose
# sudo systemctl enable docker
# sudo systemctl start docker
```

---

## 🐳 PARTE 4: Deploy com Docker

### 4.1. Opção A: Docker Compose Separado (Recomendado)

**Cenário:** Você já tem outros containers rodando e quer adicionar este como mais um serviço.

#### 4.1.1. Iniciar os Containers

```bash
# No diretório do projeto
cd /opt/controle-ferias

# Inicia os containers
docker-compose up -d

# Verifica se estão rodando
docker-compose ps
docker-compose logs -f
```

#### 4.1.2. Verificar Comunicação com Evolution API

Se sua Evolution API está em outro container, você precisa:

**Opção 1: Usar nome do container (se estiver na mesma rede Docker)**
```env
EVOLUTION_API_URL=http://nome-container-evolution:8081/message/sendText/zabbix
```

**Opção 2: Usar IP interno do container**
```bash
# Descobrir IP do container da Evolution API
docker inspect nome-container-evolution | grep IPAddress

# Usar o IP no .env
EVOLUTION_API_URL=http://172.17.0.X:8081/message/sendText/zabbix
```

**Opção 3: Criar uma rede compartilhada**
```bash
# Cria uma rede compartilhada
docker network create controle-ferias-network

# Adiciona containers existentes à rede
docker network connect controle-ferias-network nome-container-evolution

# Atualiza docker-compose.yml para usar essa rede (veja seção 4.2)
```

---

### 4.2. Opção B: Integrar ao Docker Compose Existente

**Cenário:** Você quer adicionar este serviço ao seu `docker-compose.yml` principal que já tem outros serviços.

#### 4.2.1. Adicionar ao docker-compose.yml Principal

No seu `docker-compose.yml` principal (que já tem outros serviços), adicione:

```yaml
version: '3.8'

services:
  # ... seus serviços existentes (evolution-api, etc) ...
  
  # ============================================
  # CONTROLE DE FÉRIAS - Frontend
  # ============================================
  controle-ferias-frontend:
    build: ./controle-ferias  # Caminho para o projeto clonado
    container_name: controle-ferias-frontend
    ports:
      - "8501:8501"
    volumes:
      - ./controle-ferias/data:/app/data
      - ./controle-ferias/download:/app/download
      - ./controle-ferias/logs:/app/logs
      - ./controle-ferias/.env:/app/.env
    environment:
      - PYTHONUNBUFFERED=1
    command: ["./scripts/iniciar.sh"]
    restart: always
    networks:
      - sua-rede-compartilhada  # Mesma rede dos outros containers
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ============================================
  # CONTROLE DE FÉRIAS - Scheduler
  # ============================================
  controle-ferias-scheduler:
    build: ./controle-ferias
    container_name: controle-ferias-scheduler
    volumes:
      - ./controle-ferias/data:/app/data
      - ./controle-ferias/download:/app/download
      - ./controle-ferias/logs:/app/logs
      - ./controle-ferias/.env:/app/.env
    environment:
      - PYTHONUNBUFFERED=1
    command: ["./scripts/scheduler.sh"]
    restart: always
    networks:
      - sua-rede-compartilhada
    depends_on:
      - controle-ferias-frontend
      - evolution-api  # Se quiser garantir ordem de inicialização
    healthcheck:
      test: ["CMD", "pgrep", "-f", "scheduler.jobs"]
      interval: 60s
      timeout: 10s
      retries: 3

networks:
  sua-rede-compartilhada:
    external: true  # Se a rede já existe
    # OU
    # driver: bridge  # Se for criar nova rede
```

#### 4.2.2. Configurar Rede Compartilhada

```bash
# Criar rede compartilhada (se ainda não existe)
docker network create controle-ferias-network

# Adicionar containers existentes à rede
docker network connect controle-ferias-network nome-container-evolution

# OU atualizar docker-compose.yml principal para usar essa rede
```

#### 4.2.3. Atualizar .env para Usar Nome do Container

```env
# Se Evolution API está na mesma rede Docker
EVOLUTION_API_URL=http://evolution-api:8081/message/sendText/zabbix
# ou o nome que você deu ao container da Evolution API
```

#### 4.2.4. Iniciar Todos os Serviços

```bash
# No diretório do docker-compose.yml principal
docker-compose up -d

# Verificar todos os containers
docker-compose ps

# Ver logs de todos
docker-compose logs -f
```

---

## 🔄 PARTE 5: Atualizações Futuras

### 5.1. Fluxo de Atualização

**No Mac (desenvolvimento):**
```bash
# 1. Faça suas alterações
# 2. Teste localmente
./scripts/iniciar.sh

# 3. Commit e push
git add .
git commit -m "Atualização: descrição"
git push origin main
```

**No Ubuntu (produção):**
```bash
# 1. SSH para o servidor
ssh usuario@seu-servidor

# 2. Vá até o diretório do projeto
cd /opt/controle-ferias

# 3. Puxa as atualizações
git pull origin main

# 4. Atualiza os containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# OU use o script helper
./scripts/docker-manager.sh rebuild
```

### 5.2. Script de Atualização Automatizado

Crie um script no servidor Ubuntu para facilitar:

```bash
# Cria script de atualização
nano /opt/controle-ferias/atualizar.sh
```

```bash
#!/bin/bash
cd /opt/controle-ferias
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "✅ Sistema atualizado!"
docker-compose ps
```

```bash
chmod +x /opt/controle-ferias/atualizar.sh

# Usar:
./atualizar.sh
```

---

## 🔗 PARTE 6: Integração com Evolution API

### 6.1. Descobrir Informações do Container Existente

```bash
# Lista todos os containers
docker ps

# Inspeciona o container da Evolution API
docker inspect nome-container-evolution

# Descobre o IP interno
docker inspect nome-container-evolution | grep IPAddress

# Descobre a rede
docker inspect nome-container-evolution | grep Networks
```

### 6.2. Opções de Comunicação

#### Opção 1: Mesma Rede Docker (Recomendado)

```bash
# Lista redes existentes
docker network ls

# Cria rede compartilhada (se não existe)
docker network create controle-ferias-network

# Adiciona Evolution API à rede
docker network connect controle-ferias-network nome-container-evolution

# Adiciona Controle de Férias à mesma rede (no docker-compose.yml)
networks:
  - controle-ferias-network
```

**No .env:**
```env
EVOLUTION_API_URL=http://nome-container-evolution:8081/message/sendText/zabbix
```

#### Opção 2: Host Network

Se os containers compartilham a rede do host:

```env
EVOLUTION_API_URL=http://localhost:8081/message/sendText/zabbix
# OU
EVOLUTION_API_URL=http://127.0.0.1:8081/message/sendText/zabbix
```

#### Opção 3: IP do Container

```env
EVOLUTION_API_URL=http://172.17.0.X:8081/message/sendText/zabbix
```

**⚠️ Atenção:** IPs de containers podem mudar quando reiniciados. Use nome do container quando possível.

---

## 🔧 PARTE 7: Configuração de Rede Docker

### 7.1. Criar e Gerenciar Rede Compartilhada

```bash
# Criar rede
docker network create controle-ferias-network

# Listar redes
docker network ls

# Inspecionar rede
docker network inspect controle-ferias-network

# Conectar container existente à rede
docker network connect controle-ferias-network nome-container-evolution

# Desconectar (se necessário)
docker network disconnect controle-ferias-network nome-container-evolution

# Remover rede (cuidado!)
docker network rm controle-ferias-network
```

### 7.2. Verificar Conectividade

```bash
# Testa se o container consegue acessar outro
docker exec controle-ferias-frontend ping nome-container-evolution

# OU testa via curl (se curl estiver instalado)
docker exec controle-ferias-frontend curl http://nome-container-evolution:8081
```

---

## 📝 PARTE 8: Checklist de Deploy

### Antes do Deploy

- [ ] Código testado localmente no Mac
- [ ] Código commitado e pushado para GitHub
- [ ] `.env.example` atualizado com todas as variáveis
- [ ] `.gitignore` configurado (não versionar .env, database, etc)

### No Servidor Ubuntu

- [ ] Docker e Docker Compose instalados
- [ ] Repositório clonado do GitHub
- [ ] Arquivo `.env` criado e configurado
- [ ] Rede Docker configurada (se necessário)
- [ ] Containers iniciados e funcionando
- [ ] Teste de sincronização manual funcionou
- [ ] Evolution API acessível (se configurada)
- [ ] Dashboard acessível na porta 8501

### Pós-Deploy

- [ ] Verificar logs: `docker-compose logs -f`
- [ ] Testar sincronização: `docker-compose exec frontend ./scripts/sync.sh`
- [ ] Testar mensagem: Usar botão de teste na interface
- [ ] Verificar scheduler: `docker-compose logs scheduler`
- [ ] Configurar restart automático no boot (opcional)

---

## 🔐 PARTE 9: Segurança

### 9.1. Arquivo .env

**NUNCA** faça commit do `.env`:

```bash
# Verifica se .env está no .gitignore
cat .gitignore | grep .env

# Se não estiver, adicione:
echo ".env" >> .gitignore
```

### 9.2. Backup de Dados

```bash
# Backup do banco de dados
docker exec controle-ferias-frontend cp /app/data/database.sqlite /app/data/database.sqlite.backup

# Backup completo dos dados
tar -czf backup-ferias-$(date +%Y%m%d).tar.gz data/ download/ .env
```

### 9.3. Permissões

```bash
# Ajusta permissões dos diretórios
sudo chown -R $USER:$USER /opt/controle-ferias
chmod 600 .env  # Protege arquivo .env
```

---

## 🚨 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs frontend
docker-compose logs scheduler

# Verificar configuração
docker-compose config

# Verificar se porta está livre
sudo netstat -tulpn | grep 8501
```

### Evolution API não conecta

```bash
# Verifica se está na mesma rede
docker network inspect controle-ferias-network

# Testa conectividade
docker exec controle-ferias-frontend ping nome-container-evolution

# Verifica URL no .env
cat .env | grep EVOLUTION_API_URL
```

### Scheduler não executa

```bash
# Ver logs
docker-compose logs scheduler

# Verifica se está rodando
docker-compose exec scheduler ps aux | grep scheduler

# Reinicia scheduler
docker-compose restart scheduler
```

---

## 📚 Comandos Rápidos - Referência

### No Mac (Desenvolvimento)
```bash
# Iniciar local
./scripts/iniciar.sh

# Commit e push
git add . && git commit -m "mensagem" && git push
```

### No Ubuntu (Produção)
```bash
# Atualizar código
cd /opt/controle-ferias && git pull && docker-compose up -d --build

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart

# Parar tudo
docker-compose down
```

---

## ✅ Resumo do Fluxo Completo

```
1. Mac: Desenvolve e testa
   ↓
2. Mac: git add, commit, push
   ↓
3. GitHub: Código atualizado
   ↓
4. Ubuntu: git pull
   ↓
5. Ubuntu: docker-compose up -d --build
   ↓
6. Pronto! Sistema rodando em produção
```

---

**Agora você tem um fluxo completo de desenvolvimento e deploy! 🎉**

