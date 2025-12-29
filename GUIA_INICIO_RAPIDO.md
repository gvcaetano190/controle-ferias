# 🚀 Guia de Início Rápido - macOS

Guia passo a passo para executar o Sistema de Controle de Férias no macOS.

---

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
   ```bash
   python3 --version
   ```

2. **Git** (opcional, para clonar o repositório)

---

## ⚡ Instalação Rápida

### 1. Clone ou baixe o projeto

```bash
cd ~/Documents  # ou onde preferir
git clone <seu-repositorio> controle-ferias
cd controle-ferias
```

### 2. Crie e ative o ambiente virtual

```bash
# Cria o ambiente virtual
python3 -m venv venv

# Ativa o ambiente virtual
source venv/bin/activate

# Você verá (venv) no início do prompt
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o arquivo .env

```bash
# Se não existir, crie a partir do exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações
nano .env
# ou use qualquer editor de texto
```

**Configurações mínimas necessárias:**
```env
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/SEU_ID/edit
SYNC_HOUR=8
SYNC_MINUTE=15
SYNC_ENABLED=true
```

---

## 🎯 Como Executar

### Opção 1: Usando os Scripts (Recomendado)

#### Iniciar o Dashboard (Interface Web)

```bash
# Certifique-se de estar no diretório do projeto
cd ~/Documents/controle-ferias

# Ative o ambiente virtual (se não estiver ativo)
source venv/bin/activate

# Execute o script
./scripts/iniciar.sh
```

O dashboard abrirá em: **http://localhost:8501**

#### Iniciar o Scheduler (Agendamento Automático)

Em um **novo terminal**, execute:

```bash
cd ~/Documents/controle-ferias
source venv/bin/activate
./scripts/scheduler.sh
```

**Importante:** O scheduler precisa estar rodando para executar os jobs automáticos!

#### Executar Sincronização Manual

```bash
cd ~/Documents/controle-ferias
source venv/bin/activate

# Sincronização normal
./scripts/sync.sh

# Forçar sincronização (ignora cache)
./scripts/sync.sh --forcar
```

#### Parar Todos os Processos

```bash
./scripts/parar.sh
```

---

### Opção 2: Executar Diretamente (Sem Scripts)

#### Dashboard

```bash
source venv/bin/activate
streamlit run frontend/app.py
```

#### Scheduler

```bash
source venv/bin/activate
python -m scheduler.jobs
```

#### Sincronização

```bash
source venv/bin/activate
python -m core.sync_manager
```

---

## 🔧 Resolução de Problemas

### Erro: "Permission denied"

Os scripts não têm permissão de execução. Execute:

```bash
chmod +x scripts/*.sh
```

### Erro: "command not found: python"

Use `python3` ao invés de `python`:

```bash
python3 -m venv venv
python3 -m pip install -r requirements.txt
```

### Erro: "port already in use"

A porta 8501 está ocupada. Pare processos anteriores:

```bash
./scripts/parar.sh
# ou
pkill -f "streamlit run"
```

### Virtual Environment não ativa

Certifique-se de usar `source` (não `./venv/bin/activate`):

```bash
source venv/bin/activate
```

Você deve ver `(venv)` no início do prompt.

---

## 📱 Executar em Background (Opcional)

### Terminal 1: Dashboard

```bash
cd ~/Documents/controle-ferias
source venv/bin/activate
./scripts/iniciar.sh
```

### Terminal 2: Scheduler

```bash
cd ~/Documents/controle-ferias
source venv/bin/activate
./scripts/scheduler.sh
```

### Usando nohup (para rodar em background)

```bash
# Dashboard em background
nohup ./scripts/iniciar.sh > logs/frontend.log 2>&1 &

# Scheduler em background
nohup ./scripts/scheduler.sh > logs/scheduler.log 2>&1 &
```

Para parar:

```bash
./scripts/parar.sh
```

---

## ✅ Verificar se está Funcionando

### 1. Dashboard

Acesse: http://localhost:8501

Você deve ver a interface do sistema.

### 2. Scheduler

Verifique se o scheduler está rodando:

```bash
ps aux | grep scheduler.jobs
```

Deve mostrar um processo Python executando o scheduler.

### 3. Teste Manual

Execute uma sincronização manual:

```bash
./scripts/sync.sh
```

Se funcionar, você verá mensagens de sucesso.

---

## 🔄 Fluxo de Trabalho Recomendado

### Primeira Execução

1. ✅ Instale as dependências
2. ✅ Configure o `.env`
3. ✅ Execute sincronização manual: `./scripts/sync.sh`
4. ✅ Inicie o dashboard: `./scripts/iniciar.sh`
5. ✅ Verifique se os dados aparecem

### Uso Diário

1. ✅ Inicie o scheduler: `./scripts/scheduler.sh` (deixa rodando)
2. ✅ Inicie o dashboard quando precisar: `./scripts/iniciar.sh`
3. ✅ O scheduler executa tudo automaticamente nos horários configurados

---

## 💡 Dicas

### Atalho para Ativar o Ambiente Virtual

Adicione ao seu `~/.zshrc` ou `~/.bash_profile`:

```bash
alias ativar-ferias="cd ~/Documents/controle-ferias && source venv/bin/activate"
```

Depois, use: `ativar-ferias`

### Abrir Automaticamente no Navegador

```bash
./scripts/iniciar.sh &
sleep 3
open http://localhost:8501
```

---

## 📞 Precisa de Ajuda?

1. Verifique os logs em `scheduler.log`
2. Confira se o `.env` está configurado corretamente
3. Certifique-se de que o ambiente virtual está ativo
4. Verifique se todas as dependências foram instaladas

---

**Pronto! Agora você pode usar o sistema no seu Mac! 🎉**

