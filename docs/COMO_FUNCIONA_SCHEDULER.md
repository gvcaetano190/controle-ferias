# 📆 Como Funciona o Agendador (Scheduler)

## Visão Geral

O agendador é um **daemon** (processo que roda em background) que executa tarefas automaticamente em horários específicos. Ele usa a biblioteca **APScheduler** (Advanced Python Scheduler) para gerenciar os agendamentos.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────┐
│         APScheduler (Biblioteca)        │
│  - Gerencia múltiplos jobs              │
│  - Executa em threads separadas         │
│  - Não bloqueia o programa principal    │
└─────────────────────────────────────────┘
              │
              │ Agenda
              ▼
┌─────────────────────────────────────────┐
│         scheduler/jobs.py               │
│  - job_sincronizacao()                  │
│  - job_verificar_ferias_proximas()      │
│  - job_mensagem_manha()                 │
│  - job_mensagem_tarde()                 │
└─────────────────────────────────────────┘
```

---

## 🚀 Como Iniciar

### Opção 1: Script Bash (Recomendado)
```bash
./scripts/scheduler.sh
```

### Opção 2: Python Direto
```bash
python -m scheduler.jobs
```

---

## ⚙️ Modos de Execução

### 1. Modo Daemon (Padrão)
Executa continuamente e aguarda os horários configurados:
```bash
./scripts/scheduler.sh
# ou
python -m scheduler.jobs
```

**Comportamento:**
- Fica rodando em background
- Executa jobs nos horários agendados
- Continua rodando até você parar (Ctrl+C)

### 2. Modo "Once" (Executar uma vez)
Executa todos os jobs imediatamente e encerra:
```bash
python -m scheduler.jobs --once
```

**Uso:** Testes ou execução manual

### 3. Modo Sync (Apenas sincronização)
Executa apenas a sincronização:
```bash
python -m scheduler.jobs --sync
```

---

## 📅 Jobs Agendados

O scheduler agenda 4 tipos de tarefas:

### 1. 🔄 Sincronização Diária
- **Horário:** Configurável (`.env`: `SYNC_HOUR` e `SYNC_MINUTE`)
- **Padrão:** 08:15
- **Condição:** `SYNC_ENABLED=true`
- **O que faz:**
  - Baixa a planilha do Google Sheets
  - Verifica se houve mudanças (MD5 hash)
  - Processa e salva no banco SQLite
  - Envia notificação (se `NOTIFY_ON_SYNC=true`)

### 2. 📅 Verificação de Férias Próximas
- **Horário:** 09:00 (fixo)
- **Condição:** `EVOLUTION_ENABLED=true`
- **O que faz:**
  - Busca funcionários que vão sair nos próximos X dias
  - X = valor de `NOTIFY_FERIAS_DIAS_ANTES` (padrão: 1)
  - Envia mensagem individual para cada funcionário

### 3. 🌅 Mensagem Matutina
- **Horário:** Configurável (`.env`: `MENSAGEM_MANHA_HOUR` e `MENSAGEM_MANHA_MINUTE`)
- **Padrão:** 08:00
- **Condições:** `EVOLUTION_ENABLED=true` E `MENSAGEM_MANHA_ENABLED=true`
- **O que faz:**
  - Gera relatório: quem sai hoje + quem voltaria hoje mas está bloqueado
  - Envia via WhatsApp

### 4. 🌆 Mensagem Vespertina
- **Horário:** Configurável (`.env`: `MENSAGEM_TARDE_HOUR` e `MENSAGEM_TARDE_MINUTE`)
- **Padrão:** 17:00
- **Condições:** `EVOLUTION_ENABLED=true` E `MENSAGEM_TARDE_ENABLED=true`
- **O que faz:**
  - Gera relatório: quem volta amanhã + quem está em férias com acessos pendentes
  - Envia via WhatsApp

---

## 🔄 Fluxo de Execução

```
1. Inicia scheduler
   │
   ├─► Lê configurações do .env
   │
   ├─► Cria BackgroundScheduler
   │
   ├─► Adiciona jobs (se habilitados):
   │   ├─► Sync (CronTrigger: hora:minuto)
   │   ├─► Férias Próximas (CronTrigger: 09:00)
   │   ├─► Mensagem Manhã (CronTrigger: hora:minuto)
   │   └─► Mensagem Tarde (CronTrigger: hora:minuto)
   │
   ├─► _scheduler.start() → Inicia threads
   │
   └─► Loop infinito (time.sleep(60))
       │
       └─► Aguarda horários → Executa jobs automaticamente
```

---

## 🛑 Como Parar

### Terminal onde está rodando:
```bash
Ctrl + C
```

### Se estiver rodando em background:
```bash
# Encontrar processo
ps aux | grep "scheduler.jobs"

# Matar processo (substitua PID)
kill <PID>
```

---

## 🔧 Como Funciona Internamente

### APScheduler
- Usa threads separadas para cada job
- Não bloqueia o programa principal
- Gerencia múltiplos agendamentos simultaneamente
- Usa `CronTrigger` (similar ao cron do Linux)

### Exemplo de CronTrigger:
```python
CronTrigger(hour=8, minute=15)
# Executa todos os dias às 08:15
```

### Jobs são Funções Python
Cada job é uma função Python simples:
```python
def job_sincronizacao():
    sync = SyncManager()
    resultado = sync.sincronizar()
    # ...
```

---

## 📊 Exemplo de Saída

Quando você inicia o scheduler, ele mostra:

```
============================================================
📆 SCHEDULER INICIADO
============================================================
   🔄 Sincronização: diariamente às 08:15
   📅 Verificação de Férias Próximas: diariamente às 09:00
   🌅 Mensagem Matutina: diariamente às 08:00
   🌆 Mensagem Vespertina: diariamente às 17:00
============================================================

💡 Pressione Ctrl+C para parar
```

E quando um job executa:
```
🔄 [08:15:00] Iniciando sincronização agendada...
   ✅ Sincronização concluída: 45 registros
   📨 Notificação de sincronização enviada
```

---

## ⚠️ Importante

1. **O scheduler precisa estar rodando** para executar os jobs agendados
2. **Após mudar configurações** no `.env`, você precisa **reiniciar o scheduler**
3. **Não há persistência** - se o processo morrer, os agendamentos param
4. **Para produção**, considere usar `systemd` ou `supervisor` para manter o processo rodando

---

## 🐳 Exemplo de Uso em Produção

### Com systemd (Linux):
```ini
[Unit]
Description=Controle de Férias - Scheduler
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/caminho/do/projeto
ExecStart=/caminho/do/projeto/venv/bin/python -m scheduler.jobs
Restart=always

[Install]
WantedBy=multi-user.target
```

### Com nohup (temporário):
```bash
nohup ./scripts/scheduler.sh > scheduler.log 2>&1 &
```

---

## 🔍 Debugging

### Ver logs:
Se rodando com nohup:
```bash
tail -f scheduler.log
```

### Executar manualmente para testar:
```bash
python -m scheduler.jobs --once
```

### Verificar se está rodando:
```bash
ps aux | grep scheduler.jobs
```








