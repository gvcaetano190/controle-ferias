# 📊 Mapa Visual das Mudanças - Agendamento

## 🎯 Timeline Diária de Execução

```
SEGUNDA À SEXTA (seg-fri)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

08:15 ─────► 🔄 SINCRONIZAÇÃO
              • Sincroniza planilha Google Sheets
              • Envia para: EVOLUTION_NUMERO (principal)
              • Se falhar: tenta novamente no próximo ciclo

09:00 ─────► 📨 MENSAGEM MATUTINA
              • Quem sai de férias hoje
              • Quem voltaria mas está bloqueado
              • Envia para: EVOLUTION_NUMERO (principal)

13:00 ─────► 🔔 SINCRONIZAÇÃO + NOTIFICAÇÃO
              • Sincroniza planilha Google Sheets
              • Envia resultado via WhatsApp:
                ✅ Se sucesso: "Sincronização realizada - X registros"
                ⏭️ Se pulado: "Arquivo não foi alterado"
                ❌ Se erro: "Erro: [motivo]"
              • Envia para: EVOLUTION_NUMERO_SYNC (pode ser alternativo)

18:00 ─────► 🌆 MENSAGEM VESPERTINA
              • Quem volta amanhã (ou segunda se for sexta)
              • Quem está de férias com acessos pendentes
              • Envia para: EVOLUTION_NUMERO (principal)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SÁBADO E DOMINGO: Todos os jobs são pulados ⏭️
```

---

## 🔗 Fluxo de Números WhatsApp

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVOLUTION API - NÚMEROS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EVOLUTION_NUMERO (Principal)          EVOLUTION_NUMERO_SYNC    │
│  120363020985287866@g.us     ←────────→ [Configurável]         │
│                                                                 │
│  ├─ 09:00 Mensagem Matutina               ├─ 13:00 Notif Sync  │
│  ├─ 18:00 Mensagem Vespertina             │                   │
│  └─ [outros]                              └─ [futuras notif]   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Sincronização

```
EVOLUÇÃO DOS JOBS
┌──────────────────────────────────────────────────────────────┐
│ ANTES (08:15 e 13:00 iguais)        │ DEPOIS (implementado)│
├─────────────────────────────────────┼──────────────────────┤
│ 08:15 Sincronização                 │ 08:15 Sincronização  │
│  └─ Silenciosa                      │  └─ Silenciosa       │
│     (apenas DB atualizado)          │     (apenas DB)      │
│                                     │                      │
│ 13:00 ANTES: Nada                   │ 13:00 Sincronização  │
│                                     │       + Notificação  │
│                                     │  └─ Com mensagem     │
│                                     │     WhatsApp         │
└─────────────────────────────────────┴──────────────────────┘
```

---

## 📁 Arquivos Afetados

### Arquivos Modificados:
```
config/
  └─ settings.py          ← Adicionadas 4 novas variáveis
.env                      ← Atualizadas configurações
scheduler/
  └─ jobs.py             ← Novo job: job_sincronizacao_com_notificacao()
frontend/modules/
  └─ configuracoes.py     ← Nova seção de configuração para 13:00
```

### Arquivos NÃO Alterados (mas usados):
```
integrations/
  └─ evolution_api.py     ✓ Já suporta enviar_mensagem_sync()
core/
  └─ sync_manager.py      ✓ Retorna resultado com status
```

---

## 🎛️ Variáveis de Configuração

### Nova no .env:
```env
SYNC_NOTIF_ENABLED=true          # Habilita job das 13:00
SYNC_NOTIF_HOUR=13               # Hora do job
SYNC_NOTIF_MINUTE=0              # Minuto do job
EVOLUTION_NUMERO_SYNC=...         # Número alternativo
```

### Alteradas no .env:
```env
MENSAGEM_MANHA_HOUR=9             # Antes: 8  (Após: 9)
MENSAGEM_MANHA_MINUTE=0           # Antes: 15 (Após: 0)
MENSAGEM_TARDE_HOUR=18            # Antes: 17 (Após: 18)
```

### Adicionadas em settings.py:
```python
bool_keys: "SYNC_NOTIF_ENABLED"
int_keys: "SYNC_NOTIF_HOUR", "SYNC_NOTIF_MINUTE"
```

---

## 📱 Fluxo de Notificação (13:00)

```
┌─────────────────────────────────────┐
│  13:00 - Job Sincronizacao Notif    │
└──────────────┬──────────────────────┘
               │
               ▼
     ┌─────────────────────┐
     │ Sincronizar dados   │
     └────────┬────────────┘
              │
              ├─ Sucesso ──────┐
              ├─ Pulado ───────┤
              └─ Erro ─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Evolution API     │
                    │ enviar_mensagem   │
                    │ _sync()           │
                    └────────┬──────────┘
                             │
                    ┌────────▼─────────┐
                    │ WhatsApp         │
                    │ EVOLUTION_NUMERO │
                    │ _SYNC (13:00)    │
                    └──────────────────┘
```

---

## 🔧 Integração com Frontend

### Seção nova em ⚙️ Configurações:

```
┌─────────────────────────────────────────────────┐
│ 🔔 Sincronização com Notificação (13:00)       │
├─────────────────────────────────────────────────┤
│                                                 │
│ ☑️  Habilitar  [Hora: 13] [Min: 00]             │
│                                                 │
│ Número alternativo: [120363020985287866@g.us]  │
│                                                 │
│ [🚀 Executar Agora]                             │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Resumo atualizado:

```
┌────────────────────────────────────────────────────────┐
│ 📋 Resumo do Agendamento                             │
├────────────────────────────────────────────────────────┤
│                                                        │
│ 🔄 Sincronização  │ 🔔 Sync+Notif │ 📨 Mensagens    │
│ ✅ 08:15          │ ✅ 13:00      │ ✅ 09:00|18:00  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 🧪 Testes Validados

✅ **Carregamento de Configurações**
   - Settings lê todos os valores do .env
   - Conversões de tipo (bool, int) funcionam

✅ **Scheduler**
   - Inicia com sucesso
   - Registra 4 jobs (não 3)
   - Mostra corretamente no log

✅ **Funcionalidades**
   - `job_sincronizacao_com_notificacao()` existe e é chamável
   - Usa número alternativo se configurado

✅ **Interface**
   - Sem erros de syntax
   - Novos campos aparecem corretamente

---

## 🚀 Próximas Ações para Docker

1. **Build**: `docker-compose build`
2. **Iniciar**: `docker-compose up -d`
3. **Verificar logs**: `docker-compose logs -f`
4. **Acessar**: http://localhost:8501
5. **Testar**: ⚙️ Configurações → "🚀 Executar Agora"

---

## 💡 Diferenças com Deployment Anterior

| Aspecto | Antes | Agora |
|---------|-------|-------|
| Jobs agendados | 3 | **4** |
| Sincronizações/dia | 1 | **2** |
| Horários fixes | Sim | **Sim** (customizáveis via UI) |
| Notificação de sync | Não | **Sim (13:00)** |
| Números alternativos | Não | **Sim (para 13:00)** |

---

**Status**: ✅ **Pronto para Production**  
**Data**: 13 de janeiro de 2026  
**Versão**: 2.0 (com Sincronização Dupla + Notificação)
