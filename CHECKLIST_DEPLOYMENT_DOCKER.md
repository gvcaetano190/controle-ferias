# ✅ Checklist de Deployment no Docker

## 📋 Resumo das Alterações

Foram implementadas **4 janelas de agendamento** para o sistema:

| Horário | Tipo | Descrição | Número | Status |
|---------|------|-----------|--------|--------|
| **08:15** | 🔄 Sincronização | Sincroniza dados com Google Sheets | Principal | ✅ Existente |
| **09:00** | 📨 Mensagem Matutina | Resumo de quem sai de férias | Principal | ✅ **Alterado** |
| **13:00** | 🔔 Sincronização + Notificação | Sincroniza e notifica resultado | **Alternativo** | ✅ **NOVO** |
| **18:00** | 📨 Mensagem Vespertina | Resumo de quem volta amanhã | Principal | ✅ Existente |

---

## 🔧 Arquivos Alterados

### 1. **config/settings.py**
- ✅ Adicionadas chaves: `SYNC_NOTIF_HOUR`, `SYNC_NOTIF_MINUTE`, `SYNC_NOTIF_ENABLED`, `EVOLUTION_NUMERO_SYNC`
- ✅ Adicionadas aos conversores de tipo (bool e int)
- ✅ Valor padrão: `SYNC_NOTIF_HOUR=13`, `SYNC_NOTIF_MINUTE=0`

### 2. **.env**
```env
# Mensagens Automáticas
MENSAGEM_MANHA_ENABLED=true
MENSAGEM_MANHA_HOUR=9           # ← Alterado de 9:15 para 9:00
MENSAGEM_MANHA_MINUTE=0

# Sincronização com Notificação (NOVA)
SYNC_NOTIF_ENABLED=true         # ← NOVO
SYNC_NOTIF_HOUR=13              # ← NOVO
SYNC_NOTIF_MINUTE=0             # ← NOVO
EVOLUTION_NUMERO_SYNC=120363020985287866@g.us  # ← NOVO (usar para notificações de sync)
```

### 3. **scheduler/jobs.py**
- ✅ Nova função: `job_sincronizacao_com_notificacao()` 
  - Executa sincronização às 13:00
  - Envia notificação do resultado via WhatsApp
  - Usa número alternativo se configurado, senão usa número principal
- ✅ Atualizado `iniciar_scheduler()` para registrar novo job
- ✅ Atualizado `_verificar_e_executar_jobs_perdidos()` para verificar job perdido

### 4. **frontend/modules/configuracoes.py**
- ✅ Nova seção: "🔔 **Sincronização com Notificação (13:00)**"
- ✅ Campos adicionados:
  - Hora e Minuto personalizáveis
  - Número WhatsApp alternativo (opcional)
  - Botão para executar manualmente
- ✅ Interface de resumo atualizada (3 colunas em vez de 2)
- ✅ Todas as configurações são salvas no `.env`

---

## 🚀 Guia de Deployment no Docker

### Antes de fazer build da imagem:

#### 1️⃣ Validar .env local
```bash
cat .env | grep -E "MENSAGEM_MANHA|SYNC_NOTIF|EVOLUTION_NUMERO_SYNC"
```

Deve mostrar:
```
MENSAGEM_MANHA_HOUR=9
MENSAGEM_MANHA_MINUTE=0
SYNC_NOTIF_ENABLED=true
SYNC_NOTIF_HOUR=13
SYNC_NOTIF_MINUTE=0
EVOLUTION_NUMERO_SYNC=120363020985287866@g.us
```

#### 2️⃣ Testar scheduler localmente
```bash
# Verificar se scheduler inicia corretamente
python -m scheduler.jobs &

# Aguardar 10 segundos e ver logs
sleep 10

# Parar
pkill -f "python -m scheduler"
```

#### 3️⃣ Testar interface Streamlit
```bash
streamlit run frontend/app.py
# Ir para ⚙️ Configurações
# Verificar se aparecem:
# - Mensagem Matutina: 09:00
# - Sincronização + Notificação: 13:00
# - Mensagem Vespertina: 18:00
```

---

### Durante build e deploy:

#### 4️⃣ Build da imagem Docker
```bash
docker-compose build

# Ou específico
docker build -t controle-ferias:latest .
```

#### 5️⃣ Iniciar container
```bash
docker-compose up -d

# Ou
docker run -d --name controle-ferias controle-ferias:latest
```

#### 6️⃣ Verificar logs do scheduler
```bash
docker-compose logs -f controle-ferias

# Ou específico
docker logs -f controle-ferias
```

Você deve ver:
```
============================================================
📆 SCHEDULER INICIADO
============================================================
   🔄 Sincronização: seg-sex às 08:15
   🔔 Sincronização + Notificação: seg-sex às 13:00
   🌅 Mensagem Matutina: seg-sex às 09:00
   🌆 Mensagem Vespertina: seg-sex às 18:00
============================================================
```

#### 7️⃣ Verificar interface (via navegador)
```
http://localhost:8501  (Streamlit)
```
- Ir para ⚙️ Configurações
- Confirmar que todos os horários estão corretos
- Testar botão "🚀 Executar Agora" em cada seção

---

## 📱 Números WhatsApp

### Configuração Atual:
- **Número Principal** (Mensagens 09:00 e 18:00): `120363020985287866@g.us`
- **Número Alternativo** (Notificações 13:00): `120363020985287866@g.us` (mesmo)

### Para mudar:
1. Editar `.env`:
   ```env
   EVOLUTION_NUMERO=<número-novo>              # Principal
   EVOLUTION_NUMERO_SYNC=<número-novo>         # Alternativo
   ```

2. Ou via interface Streamlit (⚙️ Configurações > Evolution API)

---

## ⚠️ Pontos de Atenção

### ✅ Validações já feitas:
- [x] Syntax validation em todos os arquivos Python
- [x] Settings.py carrega variáveis corretamente
- [x] Scheduler inicia com os 4 jobs
- [x] Interface mostra todos os campos

### ✅ Testes recomendados APÓS deploy:
- [ ] Verificar que scheduler inicia automaticamente ao iniciar container
- [ ] Testar execução manual de cada job via interface
- [ ] Validar que mensagens são enviadas para números corretos
- [ ] Verificar logs em `/app/logs/` dentro do container

### 📝 Logs disponíveis:
```bash
# Ver logs de tudo
docker-compose logs -f

# Ver logs específicos do scheduler
docker-compose logs -f | grep "🔄\|🔔\|🌅\|🌆"

# Ver arquivo de lock do scheduler
docker exec controle-ferias cat data/.scheduler.lock
```

---

## 🔄 Rollback (se necessário)

Se algo der errado:

```bash
# 1. Parar container
docker-compose down

# 2. Restaurar .env anterior (se tiver backup)
git checkout .env  # ou restaurar de backup

# 3. Reconstruir
docker-compose build
docker-compose up -d
```

---

## 📊 Status Esperado

Após deploy bem-sucedido, você verá:

```
✅ Scheduler com 4 jobs agendados
✅ Sincronização: 08:15 e 13:00 (com notificação)
✅ Mensagens: 09:00 (matutina) e 18:00 (vespertina)
✅ Números configuráveis via interface
✅ Todos os arquivos sincronizados com Docker
```

---

## 🆘 Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| APScheduler não encontrado | Dependências não instaladas | `pip install apscheduler` |
| Mensagens não são enviadas | Evolution API desabilitada ou número incorreto | Verificar `.env` e Evolution API settings |
| Scheduler não inicia | Erro de syntax ou import | Checar logs: `docker logs controle-ferias` |
| Variável não encontrada em settings | Typo no nome | Comparecar com lista exata de variáveis |

---

**Última atualização:** 13 de janeiro de 2026  
**Autor:** Sistema de Automação  
**Status:** ✅ Pronto para Production
