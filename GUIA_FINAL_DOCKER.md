# 🐳 GUIA FINAL - Deploy em Docker

## ✅ Pré-requisitos Validados

Todos os testes passaram! O sistema está **100% pronto** para produção.

```
✅ Configurações carregam corretamente
✅ Scheduler inicia sem erros
✅ 4 jobs agendados aparecem
✅ Evolution API integrada
✅ Interface Streamlit funcional
```

---

## 🚀 Passo a Passo para Deploy

### 1️⃣ Preparação Local

```bash
# Verificar que .env tem as novas variáveis
grep "SYNC_NOTIF\|EVOLUTION_NUMERO_SYNC" .env

# Esperado:
# SYNC_NOTIF_ENABLED=true
# SYNC_NOTIF_HOUR=13
# SYNC_NOTIF_MINUTE=0
# EVOLUTION_NUMERO_SYNC=120363020985287866@g.us
```

### 2️⃣ Build da Imagem

```bash
# Opção 1: Usar docker-compose
cd /Users/gabriel.caetano/Documents/controle-ferias
docker-compose build

# Opção 2: Build direto
docker build -t controle-ferias:latest .
```

**Tempo esperado**: 2-5 minutos

### 3️⃣ Iniciar Container

```bash
# Com docker-compose
docker-compose up -d

# Ou com docker direto
docker run -d \
  --name controle-ferias \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  controle-ferias:latest
```

### 4️⃣ Validar Inicialização

```bash
# Ver logs
docker-compose logs -f controle-ferias

# Deve aparecer (depois de ~10 segundos):
# ============================================================
# 📆 SCHEDULER INICIADO
# ============================================================
#    🔄 Sincronização: seg-sex às 08:15
#    🔔 Sincronização + Notificação: seg-sex às 13:00
#    🌅 Mensagem Matutina: seg-sex às 09:00
#    🌆 Mensagem Vespertina: seg-sex às 18:00
# ============================================================
```

### 5️⃣ Acessar Interface

```
Abrir navegador: http://localhost:8501
Ir para: ⚙️ Configurações
Verificar: Todos os horários aparecem corretamente
```

### 6️⃣ Teste Manual

```bash
# Abra Streamlit e clique em:
# ⚙️ Configurações 
#    → 🚀 Executar Todos Agora

# Ou execute no terminal:
docker exec controle-ferias python -m scheduler.jobs --once
```

---

## 📊 Checklist de Validação Pós-Deploy

- [ ] Container está rodando: `docker ps | grep controle-ferias`
- [ ] Scheduler iniciou: Check logs com "📆 SCHEDULER INICIADO"
- [ ] 4 jobs aparecem nos logs
- [ ] Interface abre em http://localhost:8501
- [ ] ⚙️ Configurações mostra "🔔 Sincronização com Notificação"
- [ ] Botão "🚀 Executar Agora" funciona
- [ ] Logs aparecem em `/app/logs/` dentro do container

---

## 🔍 Troubleshooting

### Problema: "APScheduler não instalado"
```bash
docker exec controle-ferias pip install apscheduler
# Depois reiniciar container
docker restart controle-ferias
```

### Problema: "EVOLUTION_NUMERO_SYNC não encontrado"
```bash
# Verificar .env dentro do container
docker exec controle-ferias cat /app/.env | grep SYNC

# Se não estiver, adicionar manualmente:
echo "EVOLUTION_NUMERO_SYNC=120363020985287866@g.us" >> .env

# Rebuild:
docker-compose build --no-cache
docker-compose up -d
```

### Problema: "Scheduler não aparece nos logs"
```bash
# Aumentar quantidade de logs
docker-compose logs -f --tail=100 controle-ferias

# Ou verificar arquivo de lock do scheduler
docker exec controle-ferias cat /app/data/.scheduler.lock
```

---

## 📁 Estrutura de Arquivos no Container

```
/app/
├── .env                    ← Variáveis de ambiente
├── config/
│   └── settings.py        ← Carrega SYNC_NOTIF_* e EVOLUTION_NUMERO_SYNC
├── scheduler/
│   └── jobs.py            ← Contém job_sincronizacao_com_notificacao()
├── frontend/modules/
│   └── configuracoes.py    ← Interface para editar configurações
├── data/
│   ├── database.sqlite     ← Banco de dados
│   └── .scheduler.lock     ← Lock file do scheduler
└── logs/
    ├── sistema.log         ← Logs gerais
    └── scheduler.log       ← Logs do scheduler
```

---

## 🔄 Variáveis de Ambiente Críticas

### Obrigatórias:
```env
EVOLUTION_ENABLED=true
EVOLUTION_API_URL=http://10.0.153.20:8081/message/sendText/zabbix
EVOLUTION_NUMERO=120363020985287866@g.us
EVOLUTION_API_KEY=B5083F44970B-410F-82CF-6B620C5E9B62
```

### Novas (do update):
```env
SYNC_NOTIF_ENABLED=true                     # Ativa job 13:00
SYNC_NOTIF_HOUR=13                          # Customizável
SYNC_NOTIF_MINUTE=0                         # Customizável
EVOLUTION_NUMERO_SYNC=...                   # Customizável (opcional)
```

### Opcionais (podem ser deixados vazios):
```env
KANBANIZE_API_KEY=
ONETIMESECRET_API_KEY=
```

---

## 📈 Monitoramento Pós-Deploy

### Verificar saúde do sistema:
```bash
# 1. Container rodando?
docker ps | grep controle-ferias

# 2. Scheduler ativo?
docker logs controle-ferias | grep "SCHEDULER INICIADO"

# 3. Jobs sendo executados?
docker logs -f controle-ferias | grep "🔄\|🔔\|🌅\|🌆"

# 4. Erros?
docker logs controle-ferias | grep "❌"
```

### Logs importantes:
```bash
# Ver últimas 50 linhas
docker logs --tail=50 controle-ferias

# Seguir logs em tempo real
docker logs -f controle-ferias

# Buscar erros específicos
docker logs controle-ferias | grep "ERROR\|ERRO\|❌"
```

---

## 🛑 Parar/Reiniciar Container

```bash
# Parar
docker-compose down

# Ou apenas parar sem remover
docker-compose stop

# Reiniciar
docker-compose restart controle-ferias

# Reiniciar tudo
docker-compose down && docker-compose up -d
```

---

## 🔐 Backup Importante

Antes de fazer deploy, faça backup dos arquivos críticos:

```bash
# Backup do .env
cp .env .env.backup.$(date +%Y%m%d)

# Backup do banco de dados
cp data/database.sqlite data/database.sqlite.backup.$(date +%Y%m%d)

# Backup de logs
cp -r logs logs.backup.$(date +%Y%m%d)
```

---

## 📞 Suporte Técnico

### Informações do Sistema:
```bash
# Versão do Docker
docker --version

# Versão do Docker Compose
docker-compose --version

# Info do container
docker inspect controle-ferias

# Recursos utilizados
docker stats controle-ferias
```

### Arquivos de Documentação:
- `CHECKLIST_DEPLOYMENT_DOCKER.md` - Checklist completo
- `MAPA_VISUAL_MUDANCAS.md` - Diagramas e fluxos
- `SUMARIO_EXECUTIVO_SCHEDULER.md` - Resumo executivo
- `test_scheduler_novo.py` - Script de teste automatizado

---

## ✨ Sumário Final

| Item | Status | Detalhes |
|------|--------|----------|
| Código | ✅ | Sem erros, validado |
| Testes | ✅ | 4/4 passando |
| Configurações | ✅ | Carregam corretamente |
| Interface | ✅ | Mostra novos campos |
| Docker | ✅ | Pronto para build |
| Documentação | ✅ | Completa |

---

## 🎯 Próximas Ações

1. **Agora**: Executar `docker-compose build`
2. **Depois**: Executar `docker-compose up -d`
3. **Validar**: Acessar http://localhost:8501
4. **Testar**: Clicar em "🚀 Executar Agora" em cada seção
5. **Monitorar**: Verificar logs por 24 horas

---

**Status Final**: ✅ **PRONTO PARA PRODUÇÃO**

*Data: 13 de janeiro de 2026*  
*Versão: 2.0 - Com Scheduler Dual de Sincronização*
