# 🎨 Guia de Melhoria da Interface Kanbanize

## Índice
1. [Resumo Executivo](#resumo-executivo)
2. [Tecnologias Recomendadas](#tecnologias-recomendadas)
3. [Análise do Docker-Compose](#análise-do-docker-compose)
4. [Plano de Implementação](#plano-de-implementação)
5. [Arquivos Afetados](#arquivos-afetados)
6. [Padrões de Projeto](#padrões-de-projeto)
7. [Código de Exemplo](#código-de-exemplo)
8. [Checklist de Implementação](#checklist-de-implementação)

---

## Resumo Executivo

Este documento detalha como transformar a interface do Kanbanize de simples cards HTML para uma experiência visual moderna, igual ao Kanbanize original, usando bibliotecas prontas para não reinventar a roda.

### Objetivo
- Interface de cards bonita e responsiva
- Dashboard arrastável e redimensionável
- Gráficos interativos para relatórios
- Performance otimizada
- Código organizado sem duplicação

---

## Tecnologias Recomendadas

### 1. **streamlit-elements** ⭐ RECOMENDADO PRINCIPAL
> Dashboard arrastável com Material UI + Nivo Charts

```bash
pip install streamlit-elements==0.1.*
```

**Por que usar:**
- ✅ Dashboard drag-and-drop nativo
- ✅ Material UI (mesmo visual do MUI/React)
- ✅ 45+ gráficos Nivo incluídos
- ✅ Monaco Editor (VS Code) integrado
- ✅ 906+ stars no GitHub

**Componentes disponíveis:**
| Componente | Descrição |
|------------|-----------|
| `dashboard` | Grid arrastável e redimensionável |
| `mui` | Material UI widgets e ícones |
| `nivo` | 45 tipos de gráficos interativos |
| `html` | Elementos HTML customizados |
| `sync` | Sincronização com session_state |

**Documentação:** https://github.com/okld/streamlit-elements

---

### 2. **streamlit-shadcn-ui** ⭐ ALTERNATIVA MODERNA
> Componentes shadcn/ui (Tailwind CSS) para Streamlit

```bash
pip install streamlit-shadcn-ui
```

**Por que usar:**
- ✅ Design moderno (shadcn/ui)
- ✅ Cards, badges, metric cards
- ✅ Componentes aninhados
- ✅ 1.1k stars no GitHub
- ✅ Ativamente mantido (última release: 3 meses)

**Componentes úteis para Kanbanize:**
- `ui.card()` - Cards estilizados
- `ui.metric_card()` - Métricas com ícones
- `ui.badges()` - Tags coloridas
- `ui.tabs()` - Navegação por abas
- `ui.table()` - Tabelas interativas
- `ui.avatar()` - Avatares de usuários

**Documentação:** https://shadcn.streamlit.app/

---

### 3. **streamlit-aggrid**
> Tabelas interativas de alta performance

```bash
pip install streamlit-aggrid
```

**Por que usar:**
- ✅ Tabelas com milhares de linhas sem lag
- ✅ Filtros, ordenação, agrupamento
- ✅ Células editáveis
- ✅ 841+ stars

---

### 4. **streamlit-echarts**
> Gráficos Apache ECharts (alternativa ao Nivo)

```bash
pip install streamlit-echarts
```

**Por que usar:**
- ✅ Gráficos altamente customizáveis
- ✅ Animações suaves
- ✅ Temas prontos

---

## Análise do Docker-Compose

### ✅ Status: **CONFIGURADO CORRETAMENTE**

Seu `docker-compose.yml` está bem configurado para persistência de dados:

```yaml
volumes:
  # Named volumes - dados persistem mesmo se container parar
  data-volume:
    driver: local
  download-volume:
    driver: local
  logs-volume:
    driver: local
```

### Pontos Positivos:
| Configuração | Status | Descrição |
|--------------|--------|-----------|
| Named Volumes | ✅ | `data-volume`, `download-volume`, `logs-volume` |
| Volume Sharing | ✅ | Frontend e Scheduler compartilham mesmos volumes |
| Restart Policy | ✅ | `restart: always` - reinicia automaticamente |
| Healthchecks | ✅ | Verificação de saúde configurada |
| Timezone | ✅ | `TZ=America/Sao_Paulo` |
| Network | ✅ | Rede isolada `controle-ferias-network` |

### Comandos Úteis para Verificar Dados:
```bash
# Ver volumes criados
docker volume ls

# Inspecionar volume de dados
docker volume inspect controle-ferias_data-volume

# Ver onde os dados estão no host
docker inspect controle-ferias-frontend | grep -A 10 Mounts
```

### ⚠️ Recomendação de Backup:
Adicione um script de backup periódico:

```bash
# backup-volumes.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker run --rm \
  -v controle-ferias_data-volume:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/data-$DATE.tar.gz /data
```

---

## Plano de Implementação

### Fase 1: Preparação (1 dia)

#### 1.1 Atualizar `requirements.txt`
```txt
# Interface Kanbanize Melhorada
streamlit-elements==0.1.*
streamlit-shadcn-ui>=0.1.19
streamlit-aggrid>=0.3.0
streamlit-echarts>=0.4.0
```

#### 1.2 Criar estrutura de diretórios
```
frontend/
├── modules/
│   ├── kanbanize.py           # Existente (será refatorado)
│   ├── relatorio_kanbanize.py # Existente (será refatorado)
│   └── components/            # NOVO - Componentes reutilizáveis
│       ├── __init__.py
│       ├── kanban_card.py     # Card individual
│       ├── kanban_board.py    # Board completo
│       ├── kanban_charts.py   # Gráficos
│       └── kanban_filters.py  # Filtros
```

### Fase 2: Componentes Base (2 dias)

#### 2.1 Criar `frontend/modules/components/kanban_card.py`
Componente reutilizável para renderizar cards.

#### 2.2 Criar `frontend/modules/components/kanban_board.py`
Board drag-and-drop com colunas.

#### 2.3 Criar `frontend/modules/components/kanban_charts.py`
Gráficos de análise (tempo parado, distribuição, etc).

### Fase 3: Integração (2 dias)

#### 3.1 Refatorar `kanbanize.py`
- Usar novos componentes
- Remover HTML inline
- Adicionar dashboard interativo

#### 3.2 Refatorar `relatorio_kanbanize.py`
- Adicionar gráficos Nivo
- Usar AgGrid para tabelas
- Cards de métricas shadcn

### Fase 4: Testes e Deploy (1 dia)

---

## Arquivos Afetados

### Arquivos a CRIAR:
| Arquivo | Descrição |
|---------|-----------|
| `frontend/modules/components/__init__.py` | Exporta componentes |
| `frontend/modules/components/kanban_card.py` | Card individual |
| `frontend/modules/components/kanban_board.py` | Board completo |
| `frontend/modules/components/kanban_charts.py` | Gráficos |
| `frontend/modules/components/kanban_filters.py` | Filtros |

### Arquivos a MODIFICAR:
| Arquivo | Mudanças |
|---------|----------|
| `requirements.txt` | Adicionar novas bibliotecas |
| `frontend/modules/kanbanize.py` | Usar novos componentes |
| `frontend/modules/relatorio_kanbanize.py` | Usar novos componentes |

### Arquivos que NÃO mudam:
- `docker-compose.yml` ✅
- `Dockerfile` (talvez precisar rebuild)
- `integrations/kanbanize.py` (API intacta)
- `core/database.py` (dados intactos)

---

## Padrões de Projeto

### 1. **Component Pattern** (Componentes Reutilizáveis)
```python
# frontend/modules/components/kanban_card.py
class KanbanCard:
    """Componente de card reutilizável."""
    
    def __init__(self, card_data: dict):
        self.data = card_data
    
    def render(self, style: str = "default"):
        """Renderiza o card no estilo especificado."""
        if style == "material":
            return self._render_material()
        elif style == "shadcn":
            return self._render_shadcn()
        return self._render_default()
```

### 2. **Factory Pattern** (Criação de Cards)
```python
# frontend/modules/components/__init__.py
def create_card(card_data: dict, style: str = "material") -> KanbanCard:
    """Factory para criar cards com estilo consistente."""
    return KanbanCard(card_data).render(style)
```

### 3. **Strategy Pattern** (Renderização Flexível)
```python
# Diferentes estratégias de renderização
RENDER_STRATEGIES = {
    "list": render_as_list,
    "grid": render_as_grid,
    "kanban": render_as_kanban_board,
}

def render_cards(cards: list, strategy: str = "kanban"):
    return RENDER_STRATEGIES[strategy](cards)
```

### 4. **Singleton para Cache** (Conexão API)
```python
# Já existe no código atual - manter!
@st.cache_resource(show_spinner=False)
def get_api_connection():
    # Singleton da conexão API
    pass
```

---

## Código de Exemplo

### Exemplo 1: Card Material UI com streamlit-elements

```python
# frontend/modules/components/kanban_card.py
from streamlit_elements import elements, mui, html

def render_card_material(card: dict):
    """Renderiza card estilo Material UI."""
    
    title = card.get('title', 'Sem Título')
    card_id = card.get('card_id')
    color = card.get('color', '#1976d2')
    column_name = card.get('column_name', '-')
    tempo_parado = calcular_tempo_parado(card)
    
    with elements(f"card_{card_id}"):
        with mui.Card(
            sx={
                "borderLeft": f"5px solid {color}",
                "marginBottom": "10px",
                "boxShadow": 2,
                "&:hover": {"boxShadow": 6}
            }
        ):
            mui.CardHeader(
                title=title,
                subheader=f"#{card_id}",
                avatar=mui.Avatar(
                    children=title[0].upper(),
                    sx={"bgcolor": color}
                )
            )
            
            with mui.CardContent():
                with mui.Box(sx={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": 2}):
                    # Chip para coluna
                    mui.Chip(
                        label=column_name,
                        icon=mui.icon.ViewColumn,
                        size="small"
                    )
                    
                    # Chip para tempo parado
                    mui.Chip(
                        label=tempo_parado,
                        icon=mui.icon.Schedule,
                        size="small",
                        color="warning" if "d" in tempo_parado else "default"
                    )
            
            with mui.CardActions():
                mui.IconButton(mui.icon.Visibility, size="small")
                mui.IconButton(mui.icon.Edit, size="small")
```

### Exemplo 2: Dashboard Kanban Arrastável

```python
# frontend/modules/components/kanban_board.py
from streamlit_elements import elements, dashboard, mui

def render_kanban_board(cards_by_column: dict, colunas: list):
    """
    Renderiza board Kanban com colunas arrastáveis.
    
    Args:
        cards_by_column: Dict {column_name: [cards]}
        colunas: Lista de colunas ordenadas
    """
    
    # Define layout do dashboard
    layout = []
    for i, col in enumerate(colunas):
        layout.append(
            dashboard.Item(
                f"col_{col['id']}", 
                x=i * 3,  # Posição X
                y=0,      # Posição Y
                w=3,      # Largura
                h=10,     # Altura
                isDraggable=True,
                isResizable=True
            )
        )
    
    with elements("kanban_board"):
        with dashboard.Grid(layout, draggableHandle=".drag-handle"):
            for col in colunas:
                col_cards = cards_by_column.get(col['name'], [])
                
                with mui.Paper(
                    key=f"col_{col['id']}",
                    sx={
                        "p": 2,
                        "height": "100%",
                        "bgcolor": "#f5f5f5",
                        "overflow": "auto"
                    }
                ):
                    # Header da coluna (drag handle)
                    mui.Typography(
                        col['name'],
                        variant="h6",
                        className="drag-handle",
                        sx={"cursor": "grab", "mb": 2}
                    )
                    
                    # Badge com contagem
                    mui.Badge(
                        badgeContent=len(col_cards),
                        color="primary",
                        sx={"mb": 2}
                    )
                    
                    # Cards da coluna
                    for card in col_cards:
                        render_mini_card(card)


def render_mini_card(card: dict):
    """Mini card dentro da coluna."""
    with mui.Card(
        sx={
            "mb": 1,
            "p": 1,
            "borderLeft": f"4px solid {card.get('color', '#ccc')}",
            "&:hover": {"bgcolor": "#e3f2fd"}
        }
    ):
        mui.Typography(
            card.get('title', '')[:40] + "...",
            variant="body2"
        )
        mui.Typography(
            f"#{card.get('card_id')}",
            variant="caption",
            color="text.secondary"
        )
```

### Exemplo 3: Gráficos com Nivo

```python
# frontend/modules/components/kanban_charts.py
from streamlit_elements import elements, mui, nivo

def render_cards_por_coluna_chart(dados: list):
    """
    Gráfico de barras: cards por coluna.
    
    Args:
        dados: [{"coluna": "Em Análise", "quantidade": 15}, ...]
    """
    
    with elements("chart_cards_coluna"):
        with mui.Box(sx={"height": 400}):
            nivo.Bar(
                data=dados,
                keys=["quantidade"],
                indexBy="coluna",
                margin={"top": 50, "right": 50, "bottom": 50, "left": 60},
                padding=0.3,
                colors={"scheme": "paired"},
                borderRadius=4,
                axisBottom={
                    "tickSize": 5,
                    "tickPadding": 5,
                    "tickRotation": -45
                },
                axisLeft={
                    "tickSize": 5,
                    "tickPadding": 5,
                    "legend": "Quantidade",
                    "legendPosition": "middle",
                    "legendOffset": -40
                },
                labelSkipWidth=12,
                labelSkipHeight=12,
                legends=[
                    {
                        "anchor": "bottom-right",
                        "direction": "column",
                        "translateX": 100,
                        "itemWidth": 80,
                        "itemHeight": 20
                    }
                ],
                animate=True,
                motionConfig="gentle"
            )


def render_tempo_parado_chart(dados: list):
    """
    Gráfico de pizza: distribuição por tempo parado.
    
    Args:
        dados: [{"id": "1-5 dias", "value": 10}, {"id": ">10 dias", "value": 5}]
    """
    
    with elements("chart_tempo_parado"):
        with mui.Box(sx={"height": 300}):
            nivo.Pie(
                data=dados,
                margin={"top": 40, "right": 80, "bottom": 40, "left": 80},
                innerRadius=0.5,  # Donut chart
                padAngle=0.7,
                cornerRadius=3,
                colors={"scheme": "red_yellow_green"},
                borderWidth=1,
                arcLinkLabelsTextColor="#333",
                arcLabelsSkipAngle=10,
                legends=[
                    {
                        "anchor": "bottom",
                        "direction": "row",
                        "translateY": 56,
                        "itemWidth": 100,
                        "itemHeight": 18
                    }
                ]
            )
```

### Exemplo 4: Metric Cards com shadcn-ui

```python
# frontend/modules/components/kanban_metrics.py
import streamlit_shadcn_ui as ui

def render_metrics_dashboard(stats: dict):
    """
    Dashboard de métricas usando shadcn-ui.
    
    Args:
        stats: {
            "total_cards": 150,
            "parados_5_dias": 23,
            "media_tempo_coluna": "3.5 dias",
            "cards_urgentes": 5
        }
    """
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ui.metric_card(
            title="Total de Cards",
            content=str(stats.get('total_cards', 0)),
            description="Todos os cards no board",
            key="metric_total"
        )
    
    with col2:
        ui.metric_card(
            title="Parados > 5 dias",
            content=str(stats.get('parados_5_dias', 0)),
            description="Atenção necessária",
            key="metric_parados"
        )
    
    with col3:
        ui.metric_card(
            title="Tempo Médio",
            content=stats.get('media_tempo_coluna', '-'),
            description="Na coluna atual",
            key="metric_tempo"
        )
    
    with col4:
        ui.metric_card(
            title="Urgentes",
            content=str(stats.get('cards_urgentes', 0)),
            description="> 10 dias parado",
            key="metric_urgentes"
        )


def render_card_shadcn(card: dict):
    """Renderiza card individual usando shadcn-ui."""
    
    with ui.card(key=f"card_{card.get('card_id')}"):
        # Header
        ui.element("div", key=f"header_{card.get('card_id')}", children=[
            ui.element("span", text=card.get('title', 'Sem título')),
            ui.badges(
                badge_list=[(card.get('column_name', '-'), "default")],
                key=f"badge_{card.get('card_id')}"
            )
        ])
        
        # Infos
        ui.element("p", 
            text=f"Criado: {card.get('created_at', '-')[:10]}",
            key=f"created_{card.get('card_id')}"
        )
```

### Exemplo 5: Tabela com AgGrid

```python
# frontend/modules/components/kanban_table.py
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

def render_cards_table(cards: list):
    """
    Tabela interativa de alta performance.
    
    Args:
        cards: Lista de dicionários de cards
    """
    import pandas as pd
    
    # Prepara dados
    df = pd.DataFrame([{
        "ID": c.get('card_id'),
        "Título": c.get('title'),
        "Coluna": c.get('column_name'),
        "Fluxo": c.get('workflow_name'),
        "Criado": c.get('created_at', '')[:10],
        "Dias Parado": calcular_dias_parado(c)
    } for c in cards])
    
    # Configura grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection('single')
    gb.configure_default_column(
        groupable=True,
        filterable=True,
        sortable=True,
        editable=False
    )
    
    # Destaca linhas com muitos dias parado
    gb.configure_column(
        "Dias Parado",
        cellStyle={
            "function": """
            params.value > 10 ? {'backgroundColor': '#ffcdd2'} :
            params.value > 5 ? {'backgroundColor': '#fff9c4'} :
            {'backgroundColor': 'white'}
            """
        }
    )
    
    grid_options = gb.build()
    
    # Renderiza
    response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        theme='streamlit'
    )
    
    return response


def calcular_dias_parado(card: dict) -> int:
    """Calcula dias parado na coluna atual."""
    from datetime import datetime
    
    in_position = card.get('in_current_position_since')
    if not in_position:
        return 0
    
    try:
        dt_position = datetime.fromisoformat(in_position.replace('Z', '+00:00'))
        dt_now = datetime.now(dt_position.tzinfo)
        return (dt_now - dt_position).days
    except:
        return 0
```

---

## Checklist de Implementação

### Preparação
- [ ] Backup do projeto atual
- [ ] Criar branch `feature/kanbanize-ui`
- [ ] Atualizar `requirements.txt`
- [ ] Testar instalação local das bibliotecas

### Estrutura
- [ ] Criar diretório `frontend/modules/components/`
- [ ] Criar `__init__.py`
- [ ] Criar `kanban_card.py`
- [ ] Criar `kanban_board.py`
- [ ] Criar `kanban_charts.py`
- [ ] Criar `kanban_metrics.py`
- [ ] Criar `kanban_table.py`

### Componentes
- [ ] Implementar `KanbanCard` com Material UI
- [ ] Implementar `KanbanBoard` drag-and-drop
- [ ] Implementar gráficos Nivo (barras, pizza, timeline)
- [ ] Implementar métricas shadcn-ui
- [ ] Implementar tabela AgGrid

### Integração
- [ ] Refatorar `kanbanize.py` para usar componentes
- [ ] Refatorar `relatorio_kanbanize.py` para usar componentes
- [ ] Remover HTML inline duplicado
- [ ] Testar filtros e cache

### Testes
- [ ] Testar em ambiente local
- [ ] Testar com Docker build
- [ ] Verificar persistência de dados
- [ ] Testar performance com muitos cards

### Deploy
- [ ] Rebuild imagem Docker
- [ ] Deploy para produção
- [ ] Verificar healthchecks
- [ ] Monitorar logs

---

## Recursos Adicionais

### Documentação Oficial
- [streamlit-elements](https://github.com/okld/streamlit-elements)
- [streamlit-shadcn-ui](https://shadcn.streamlit.app/)
- [Nivo Charts](https://nivo.rocks/)
- [Material UI](https://mui.com/material-ui/react-card/)
- [AgGrid](https://www.ag-grid.com/react-data-grid/)

### Demos Online
- [Streamlit Elements Demo](https://share.streamlit.io/okld/streamlit-gallery/main?p=elements)
- [Shadcn UI Demo](https://shadcn.streamlit.app/)
- [Nivo Storybook](https://nivo.rocks/storybook/)

---

## Conclusão

### Resumo das Vantagens

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Visual | HTML inline básico | Material UI / Shadcn moderno |
| Interatividade | Estático | Drag-and-drop, hover, animações |
| Gráficos | Nenhum | Nivo (45 tipos) |
| Tabelas | Básico | AgGrid (filtros, ordenação) |
| Código | Duplicado | Componentes reutilizáveis |
| Manutenção | Difícil | Fácil (padrões de projeto) |

### Próximos Passos Recomendados
1. **Instalar bibliotecas** e testar localmente
2. **Criar componente base** (KanbanCard)
3. **Refatorar uma página** como piloto
4. **Validar com usuários**
5. **Expandir para outras páginas**

---

*Documento criado em: 17/01/2026*
*Versão: 1.0*
