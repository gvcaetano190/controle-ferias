# 🧪 Scripts de Teste e Validação

Esta pasta contém scripts para testar e validar o sistema.

## Scripts Disponíveis

### `testar_planilha.py`
Script completo de teste que:
- Baixa planilha do Google Sheets
- Processa todas as abas
- Testa processamento do mês atual
- Mostra funcionários e filtros

**Uso:**
```bash
cd /Users/gabriel.caetano/Documents/controle-ferias
source venv/bin/activate
python tests/testar_planilha.py
```

### `validar_dados.py`
Script de validação que:
- Extrai dados completos de funcionários
- Valida formato de datas
- Verifica estrutura de acessos
- Mostra dados brutos para conferência

**Uso:**
```bash
cd /Users/gabriel.caetano/Documents/controle-ferias
source venv/bin/activate
python tests/validar_dados.py
```

## Notas

- Todos os scripts estão configurados para acessar o diretório raiz do projeto
- Certifique-se de ter ativado o ambiente virtual (`venv`) antes de executar
- Os scripts usam a URL do Google Sheets configurada internamente








