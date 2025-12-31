# 🕐 Correção de Timezone e Agendamento

## Problemas Identificados

### 1. **Timezone Incorreto do Container**
- O container estava usando **UTC** em vez de **São Paulo (-3)**
- Isso causava desalinhamento entre o horário esperado e o real
- A sincronização e mensagens eram executadas em horários diferentes do esperado

### 2. **Duplicação de Mensagens**
- A verificação de férias próximas era disparada às **09:00**
- A mensagem matutina também era disparada às **09:00**
- Isso resultava em 2 mensagens no mesmo horário

### 3. **Falta de Sincronização entre Host e Container**
- Só o Dockerfile tinha timezone, mas o docker-compose não propagava para os containers
- Variáveis de ambiente não estavam sincronizadas

## ✅ Soluções Implementadas

### 1. Dockerfile - Configurar Timezone
```dockerfile
# Configura timezone para São Paulo (Brasil)
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
```

**O que faz:**
- Define variável `TZ` para America/Sao_Paulo
- Cria symlink do arquivo de timezone
- Adiciona `tzdata` às dependências do sistema

### 2. docker-compose.yml - Propagar Timezone
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - TZ=America/Sao_Paulo
```

**O que faz:**
- Garante que a variável `TZ` seja passada ao container em tempo de execução
- Sincroniza timezone do host com o container

### 3. .env - Ajustar Horários dos Agendamentos

**Antes:**
- Sincronização: 08:15
- Verificação de Férias: 09:00
- Mensagem Matutina: 09:00 ❌ (duplicada)
- Mensagem Vespertina: 17:00

**Depois:**
- Sincronização: 08:15
- Verificação de Férias: 09:00
- Mensagem Matutina: 09:15 ✅ (defasada por 15 min)
- Mensagem Vespertina: 18:00 ✅ (mudado de 17h para 18h)

## 📋 Fluxo de Agendamento (Revisado)

```
Seg-Sex (Dias Úteis)
├─ 08:15 - Sincronização de dados
├─ 09:00 - Verificação de férias próximas
├─ 09:15 - Mensagem matutina 🌅
└─ 18:00 - Mensagem vespertina 🌆
```

## 🧪 Como Verificar o Timezone

Use o novo script:
```bash
./scripts/verificar-timezone.sh
```

Ou manualmente:
```bash
# Verificar timezone do container frontend
docker-compose exec frontend date

# Verificar timezone do container scheduler
docker-compose exec scheduler date
```

**Saída esperada:**
```
Tue Dec 31 09:30:00 BRST 2025  ← Horário de Brasília (UTC-3)
```

## 🔄 Próximos Passos

1. **Reconstruir os containers:**
   ```bash
   ./scripts/docker-manager.sh rebuild
   ```

2. **Verificar os logs:**
   ```bash
   ./scripts/docker-manager.sh logs
   ```

3. **Monitorar mensagens:**
   - As mensagens devem agora ser disparadas nos horários corretos (09:15 e 18:00)
   - Não deve haver duplicação de mensagens no mesmo horário

## 📝 Notas Importantes

- O timezone é definido em **duas camadas**:
  1. No Dockerfile (imagem)
  2. No docker-compose.yml (container em execução)
  
- Isso garante que mesmo se a imagem for reconstruída, o timezone será mantido

- O horário interno do container agora está sincronizado com São Paulo (Brazil Standard Time - BRST)

- Se precisar alterar os horários, edite o arquivo `.env` e execute `rebuild`
