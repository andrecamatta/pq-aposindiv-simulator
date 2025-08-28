# 🎯 Especificação Técnica: Simulador Atuarial Interativo Individual

## 📋 Visão Geral

O **Simulador Atuarial Interativo Individual** é uma aplicação web standalone para simulação determinística de reservas matemáticas e projeções previdenciárias personalizadas. O sistema é completamente autônomo, oferecendo uma interface web reativa moderna com engine atuarial próprio implementado from-scratch.

### 🎯 Objetivos Principais

- **Reatividade Total**: Alterações em parâmetros atualizam resultados instantaneamente
- **Interface Profissional**: Design moderno com terminologia atuarial técnica precisa
- **Visualizações Avançadas**: Gráficos interativos para projeções temporais e análise
- **Rigor Atuarial**: Implementação completa de funções atuariais com precisão profissional
- **Flexibilidade Paramétrica**: Controle granular sobre todas as hipóteses atuariais
- **Conformidade Regulatória**: Tábuas oficiais brasileiras e métodos aprovados

## 🏗️ Arquitetura do Sistema

O sistema é uma aplicação web moderna com separação clara entre frontend e backend, desenvolvida do zero como projeto independente.

### Estrutura do Projeto

```
simulador-atuarial-individual/
├── backend/                   # API e engine atuarial
│   ├── src/
│   │   ├── core/             # Core atuarial engine
│   │   ├── api/              # REST API e WebSocket
│   │   ├── models/           # Estruturas de dados
│   │   └── utils/            # Utilitários
│   ├── data/
│   │   └── mortality_tables/ # Tábuas de mortalidade
│   ├── tests/
│   └── requirements.txt
├── frontend/                  # Interface React
│   ├── src/
│   ├── public/
│   ├── tests/
│   └── package.json
├── docker/                    # Containerização
├── docs/                      # Documentação
└── README.md
```

### Backend (Python + FastAPI)

```python
# Backend estruturado em Python para máxima compatibilidade
backend/src/
├── core/
│   ├── actuarial_engine.py    # Engine principal de cálculos
│   ├── mortality_tables.py    # Gestão de tábuas de mortalidade
│   ├── financial_math.py      # Matemática financeira
│   └── projections.py         # Projeções atuariais
├── api/
│   ├── main.py               # FastAPI application
│   ├── websocket_handler.py  # Handlers WebSocket
│   ├── endpoints.py          # REST endpoints
│   └── middleware.py         # CORS, auth, etc.
├── models/
│   ├── participant.py        # Modelo do participante
│   ├── simulation.py         # Modelo da simulação
│   └── results.py            # Modelos de resultados
└── utils/
    ├── validators.py         # Validações
    ├── formatters.py         # Formatadores
    └── cache.py              # Sistema de cache
```

#### Modelos de Dados Python:

```python
# models/participant.py
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"

class CalculationMethod(str, Enum):
    PUC = "PUC"  # Projected Unit Credit
    EAN = "EAN"  # Entry Age Normal

class SimulatorState(BaseModel):
    """Estado reativo do simulador"""
    # Dados do participante (editáveis)
    age: int
    gender: Gender
    salary: float
    entry_age: int
    service_years: float
    
    # Parâmetros do plano (editáveis)
    accrual_rate: float        # Taxa de acumulação (%)
    retirement_age: int        # Idade de aposentadoria
    contribution_rate: float   # Taxa de contribuição (%)
    
    # Base atuarial (pré-definida + editável)
    mortality_table: str       # "BR_EMS_2021", "AT_2000", "SOA_2017", "CUSTOM"
    discount_rate: float       # Taxa de desconto atuarial (ex: 0.06 = 6% a.a.)
    inflation_rate: float      # Taxa de inflação (ex: 0.04 = 4% a.a.)
    salary_growth_real: float  # Crescimento salarial real (ex: 0.02 = 2% a.a.)
    
    # Hipóteses demográficas avançadas
    turnover_rates: Optional[Dict[int, float]] = None  # Taxa rotatividade por idade
    disability_rates: Optional[Dict[int, float]] = None  # Taxa invalidez por idade
    early_retirement_factors: Optional[Dict[int, float]] = None  # Fatores aposentadoria antecipada
    
    # Hipóteses econômicas avançadas
    salary_scale: Optional[Dict[int, float]] = None  # Escala salarial por idade
    benefit_indexation: str = "inflation"  # "inflation", "salary", "none", "custom"
    contribution_indexation: str = "salary"  # "salary", "inflation", "none"
    
    # Estrutura a termo de juros (ETTJ)
    use_ettj: bool = False
    ettj_curve: Optional[Dict[int, float]] = None  # {ano: taxa} para ETTJ ANBIMA/PREVIC
    
    # Configurações de cálculo
    projection_years: int      # Horizonte de projeção
    calculation_method: CalculationMethod
    
    # Metadados
    last_update: Optional[datetime] = None
    calculation_id: Optional[str] = None

class SimulatorResults(BaseModel):
    """Resultados calculados da simulação"""
    # Reservas Matemáticas
    rmba: float                # Reserva de Benefícios a Conceder
    rmbc: float                # Reserva de Benefícios Concedidos
    normal_cost: float         # Custo Normal anual
    
    # Projeções anuais (vetores para gráficos)
    projection_years: List[int]
    projected_salaries: List[float]
    projected_benefits: List[float]
    projected_contributions: List[float]
    survival_probabilities: List[float]
    accumulated_reserves: List[float]
    
    # Métricas-chave
    total_contributions: float  # Contribuições totais projetadas
    total_benefits: float      # Benefícios totais projetados
    replacement_ratio: float   # Taxa de reposição (%)
    funding_ratio: Optional[float] = None  # Cobertura patrimonial
    
    # Análise detalhada de sensibilidade
    sensitivity_discount_rate: Dict[float, float]  # Taxa → Impacto RMBA
    sensitivity_mortality: Dict[str, float]        # Tabela → Impacto RMBA  
    sensitivity_retirement_age: Dict[int, float]   # Idade → Impacto RMBA
    sensitivity_salary_growth: Dict[float, float]  # Taxa → Impacto RMBA
    sensitivity_inflation: Dict[float, float]      # Taxa → Impacto RMBA
    
    # Decomposição atuarial detalhada
    actuarial_present_value_benefits: float        # VPA dos benefícios futuros
    actuarial_present_value_salary: float          # VPA dos salários futuros
    service_cost_breakdown: Dict[str, float]       # Decomposição do custo normal
    liability_duration: float                      # Duration dos passivos
    convexity: float                              # Convexidade para análise de risco
    
    # Análise de cenários
    best_case_scenario: Dict[str, float]          # Cenário otimista (5%)
    worst_case_scenario: Dict[str, float]         # Cenário pessimista (95%)
    confidence_intervals: Dict[str, tuple]        # Intervalos de confiança
    
    # Metadados técnicos
    calculation_timestamp: datetime
    computation_time_ms: float
    actuarial_method_details: Dict[str, str]      # Detalhes dos métodos utilizados
    assumptions_validation: Dict[str, bool]       # Validação das premissas
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### Frontend (React/TypeScript)

```typescript
// Estrutura proposta: frontend/
frontend/
├── src/
│   ├── components/
│   │   ├── ParameterPanel.tsx      # Painel de parâmetros editáveis
│   │   ├── ResultsDashboard.tsx    # Dashboard de resultados
│   │   ├── ChartsContainer.tsx     # Container de gráficos
│   │   ├── SensitivityAnalysis.tsx # Análise de sensibilidade
│   │   └── MortalityTableSelector.tsx # Seletor de tábuas
│   ├── charts/
│   │   ├── ProjectionChart.tsx     # Gráfico de projeções temporais
│   │   ├── ReservesChart.tsx       # Gráfico de reservas acumuladas
│   │   ├── CashFlowChart.tsx       # Gráfico de fluxo de caixa
│   │   └── SensitivityChart.tsx    # Gráfico de sensibilidade
│   ├── services/
│   │   ├── api.ts                  # Cliente API/WebSocket
│   │   ├── calculator.ts           # Validações frontend
│   │   └── formatters.ts           # Formatadores de dados
│   └── types/
│       ├── simulator.types.ts      # Tipos TypeScript
│       └── charts.types.ts         # Tipos para gráficos
```

## 🎨 Interface de Usuário

### Layout Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  🧮 SIMULADOR ATUARIAL INDIVIDUAL                              │
├─────────────────┬───────────────────────────────────────────────┤
│                 │  📊 RESULTADOS PRINCIPAIS                    │
│  📝 PARÂMETROS  │  • RMBA: R$ 1.234.567,89                    │
│                 │  • RMBC: R$ 987.654,32                      │
│  👤 Participante │  • Custo Normal: R$ 12.345,67/ano           │
│  • Idade: [45]  │  • Taxa Reposição: 78,5%                    │
│  • Sexo: [M▼]   │                                              │
│  • Salário: R$  │  📈 GRÁFICOS INTERATIVOS                    │
│    [8000.00]    │  ┌─────────────────────────────────────────┐ │
│                 │  │ Projeção Salarial vs Benefício         │ │
│  💼 Plano       │  │                                         │ │
│  • Taxa Acum.:  │  │    /\     Salário                       │ │
│    [2.0]%       │  │   /  \   /\                             │ │
│  • Aposentad.:  │  │  /    \ /  \    Benefício               │ │
│    [65] anos    │  │ /      \    \  /                        │ │
│  • Contrib.:    │  │/        \____\/                         │ │
│    [8.0]%       │  └─────────────────────────────────────────┘ │
│                 │                                              │
│  📊 Base Atual. │  ┌─────────────────────────────────────────┐ │
│  • Mortalidade: │  │ Evolução das Reservas Matemáticas      │ │
│    [BR-EMS▼]    │  │                                         │ │
│  • Desc.: [6]%  │  │ RMBA ────                               │ │
│  • Infl.: [4]%  │  │      ╲                                  │ │
│                 │  │       ╲     RMBC ....                   │ │
│  🔍 Análise     │  │        ╲   ╱                            │ │
│  • Horizonte:   │  │         ╲ ╱                             │ │
│    [40] anos    │  │          ╲╱                              │ │
│  • Método:      │  │                                         │ │
│    [PUC▼]       │  └─────────────────────────────────────────┘ │
├─────────────────┼───────────────────────────────────────────────┤
│                 │  🎛️ ANÁLISE DE SENSIBILIDADE                │
│  📋 TÁBUAS      │  ┌─────────────────────────────────────────┐ │
│                 │  │ Taxa Desconto:  4% [▬▬█▬▬] 8%          │ │
│ ✓ BR-EMS 2021   │  │ RMBA: R$ 890K ← → R$ 1.5M               │ │
│ ○ BR-EMS 2015   │  │                                         │ │
│ ○ AT-2000       │  │ Idade Aposentadoria: 60 [▬█▬▬] 70      │ │
│ ○ SOA 2017      │  │ Benefício: R$ 6.2K ← → R$ 9.8K         │ │
│                 │  └─────────────────────────────────────────┘ │
└─────────────────┴───────────────────────────────────────────────┘
```

### Componentes Detalhados

#### 1. Painel de Parâmetros (ParameterPanel)

```typescript
interface ParameterPanelProps {
  state: SimulatorState;
  onStateChange: (newState: SimulatorState) => void;
  validationErrors: ValidationResult;
}

// Seções organizadas:
// • 👤 Dados Pessoais (idade, sexo, salário, tempo de serviço)
// • 💼 Parâmetros do Plano (taxa acumulação, aposentadoria)
// • 📊 Base Atuarial (mortalidade, juros, inflação)
// • 🔍 Configurações de Cálculo (horizonte, método)
```

#### 2. Dashboard de Resultados (ResultsDashboard)

```typescript
interface ResultsDashboardProps {
  results: SimulatorResults;
  loading: boolean;
  lastUpdate: DateTime;
}

// Cards principais:
// • 💰 Reservas (RMBA/RMBC com formatação brasileira)
// • 📈 Métricas (Taxa reposição, Custo normal)
// • ⚖️ Cobertura (Funding ratio, Sustentabilidade)
// • 🎯 Projeções (Total contribuições/benefícios)
```

#### 3. Gráficos Interativos

##### Gráfico de Projeção Temporal
```typescript
interface ProjectionChartData {
  years: number[];
  series: {
    salary: number[];
    benefit: number[];
    contributions: number[];
    reserves: number[];
  };
}

// Características:
// • Múltiplas séries simultâneas
// • Tooltip com valores formatados
// • Zoom/pan para análise detalhada
// • Exportação PNG/SVG
```

##### Gráfico de Reservas Matemáticas
```typescript
interface ReservesChartData {
  years: number[];
  rmba: number[];
  rmbc: number[];
  total: number[];
  milestones: {
    retirement_year: number;
    full_vesting: number;
  };
}

// Características:
// • Transição RMBA → RMBC na aposentadoria
// • Marcos importantes destacados
// • Área empilhada para composição
// • Valores absolutos e percentuais
```

#### 4. Análise de Sensibilidade (SensitivityAnalysis)

```typescript
interface SensitivityProps {
  baseResults: SimulatorResults;
  onParameterChange: (param: string, value: number) => void;
}

// Parâmetros analisados:
// • Taxa de desconto (±2pp)
// • Idade aposentadoria (±5 anos) 
// • Taxa de mortalidade (±20%)
// • Crescimento salarial (±1pp)

// Visualização:
// • Sliders interativos
// • Gráfico tornado/waterfall
// • Impacto em R$ e %
// • Elasticidades calculadas
```

## 🔗 Fluxo de Dados Reativo

### Arquitetura WebSocket

```julia
# Backend: WebSocket Handler
function handle_websocket_message(ws, message)
    try
        request = JSON3.read(message, SimulationRequest)
        
        # Validar entrada
        validation = validate_simulation_request(request)
        if !validation.is_valid
            send_error(ws, validation.errors)
            return
        end
        
        # Calcular resultados
        @time results = calculate_individual_simulation(request.state)
        
        # Calcular sensibilidade (paralelo)
        @async begin
            sensitivity = calculate_sensitivity_analysis(request.state)
            send_message(ws, "sensitivity_update", sensitivity)
        end
        
        # Enviar resultados principais
        send_message(ws, "results_update", results)
        
    catch e
        @error "WebSocket calculation error" exception=(e, catch_backtrace())
        send_error(ws, "Erro no cálculo: $(string(e))")
    end
end
```

### Frontend: Estado Reativo

```typescript
// React Query + WebSocket
const useSimulator = () => {
  const [state, setState] = useState<SimulatorState>(defaultState);
  const [results, setResults] = useState<SimulatorResults | null>(null);
  const [loading, setLoading] = useState(false);
  
  // WebSocket connection
  const ws = useWebSocket('ws://localhost:8080/simulator', {
    onMessage: (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'results_update':
          setResults(message.data);
          setLoading(false);
          break;
        case 'sensitivity_update':
          setSensitivity(message.data);
          break;
        case 'error':
          setError(message.data);
          setLoading(false);
          break;
      }
    }
  });
  
  // Debounced calculation trigger
  const debouncedCalculate = useDebouncedCallback(
    (newState: SimulatorState) => {
      setLoading(true);
      ws.send(JSON.stringify({
        type: 'calculate',
        state: newState
      }));
    },
    300 // 300ms debounce
  );
  
  // State update handler
  const updateState = (updates: Partial<SimulatorState>) => {
    const newState = { ...state, ...updates };
    setState(newState);
    debouncedCalculate(newState);
  };
  
  return { state, results, loading, updateState };
};
```

## 📊 Tábuas de Mortalidade Pré-configuradas

### Implementação no Backend

```julia
# src/web/mortality_tables.jl
const MORTALITY_TABLES = Dict{String, Dict{String, Any}}(
    "BR_EMS_2021" => Dict(
        "name" => "BR-EMS 2021 - Experiência Brasileira",
        "description" => "Tábua oficial SUSEP baseada em 94M registros (2004-2018)",
        "source" => "SUSEP - Superintendência de Seguros Privados",
        "data_male" => load_br_ems_2021_male(),
        "data_female" => load_br_ems_2021_female(),
        "is_official" => true,
        "regulatory_approved" => true
    ),
    "AT_2000" => Dict(
        "name" => "AT-2000 - Anuidades Brasileiras", 
        "description" => "Tábua para anuidades aprovada pela SUSEP",
        "source" => "SUSEP",
        "data_male" => load_at_2000_male(),
        "data_female" => load_at_2000_female(), 
        "is_official" => true,
        "regulatory_approved" => true
    ),
    "SOA_2017" => Dict(
        "name" => "SOA 2017 - Experiência Internacional",
        "description" => "Society of Actuaries - EUA (comparativo)",
        "source" => "SOA - Society of Actuaries",
        "data_male" => load_soa_2017_male(),
        "data_female" => load_soa_2017_female(),
        "is_official" => false,
        "regulatory_approved" => false
    )
)

function get_mortality_table_info()::Vector{Dict{String, Any}}
    return [
        Dict(
            "code" => code,
            "name" => table["name"],
            "description" => table["description"],
            "source" => table["source"],
            "is_official" => table["is_official"],
            "regulatory_approved" => table["regulatory_approved"]
        )
        for (code, table) in MORTALITY_TABLES
    ]
end
```

### Seletor de Interface

```typescript
interface MortalityTableSelectorProps {
  selected: string;
  onSelect: (tableCode: string) => void;
}

const MortalityTableSelector: FC<MortalityTableSelectorProps> = ({
  selected,
  onSelect
}) => {
  const { data: tables } = useQuery('mortality-tables', fetchMortalityTables);
  
  return (
    <div className="mortality-table-selector">
      <h3>📋 Tábuas de Mortalidade</h3>
      
      {tables?.map(table => (
        <div 
          key={table.code}
          className={`table-option ${selected === table.code ? 'selected' : ''}`}
          onClick={() => onSelect(table.code)}
        >
          <div className="table-header">
            <span className={`indicator ${table.regulatory_approved ? 'official' : 'comparative'}`}>
              {table.regulatory_approved ? '✓' : '○'}
            </span>
            <strong>{table.name}</strong>
            {table.regulatory_approved && <span className="badge">OFICIAL</span>}
          </div>
          
          <p className="table-description">{table.description}</p>
          <small className="table-source">Fonte: {table.source}</small>
        </div>
      ))}
      
      <div className="authenticity-warning">
        ⚠️ <strong>Uso Profissional:</strong> Tábuas oficiais garantem conformidade 
        regulatória. Tábuas comparativas são apenas para análise.
      </div>
    </div>
  );
};
```

## ⚡ Otimizações de Performance

### Backend Julia

```julia
# Cache de cálculos frequentes
const CALCULATION_CACHE = LRU{String, SimulatorResults}(maxsize=1000)

function calculate_individual_simulation_cached(state::SimulatorState)::SimulatorResults
    cache_key = generate_cache_key(state)
    
    # Verificar cache primeiro
    cached_result = get(CALCULATION_CACHE, cache_key, nothing)
    if cached_result !== nothing
        return cached_result
    end
    
    # Calcular se não estiver em cache
    result = calculate_individual_simulation(state)
    
    # Armazenar no cache
    CALCULATION_CACHE[cache_key] = result
    
    return result
end

# Cálculos paralelos para sensibilidade
function calculate_sensitivity_analysis_parallel(base_state::SimulatorState)::SensitivityResults
    sensitivity_params = [
        ("discount_rate", [0.04, 0.05, 0.06, 0.07, 0.08]),
        ("retirement_age", [60, 62, 65, 67, 70]),
        ("salary_growth", [0.01, 0.02, 0.03, 0.04])
    ]
    
    results = Dict{String, Dict{Float64, Float64}}()
    
    # Processar em paralelo
    @sync for (param_name, values) in sensitivity_params
        @async begin
            param_results = Dict{Float64, Float64}()
            
            Threads.@threads for value in values
                modified_state = modify_parameter(base_state, param_name, value)
                result = calculate_individual_simulation(modified_state)
                param_results[value] = result.rmba  # ou outra métrica relevante
            end
            
            results[param_name] = param_results
        end
    end
    
    return SensitivityResults(results, base_state)
end
```

### Frontend (React)

```typescript
// Memoização pesada de componentes
const ProjectionChart = memo<ProjectionChartProps>(({
  data,
  options
}) => {
  const chartData = useMemo(() => 
    prepareChartData(data), 
    [data]
  );
  
  const chartOptions = useMemo(() => ({
    responsive: true,
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => formatCurrency(context.parsed.y)
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: (value) => formatCurrency(value)
        }
      }
    }
  }), []);
  
  return <Line data={chartData} options={chartOptions} />;
});

// Virtual scrolling para tabelas grandes
const ProjectionTable = () => {
  const { results } = useSimulator();
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 50 });
  
  const visibleData = useMemo(() => 
    results?.projection_years.slice(visibleRange.start, visibleRange.end),
    [results, visibleRange]
  );
  
  return (
    <VirtualList
      height={400}
      itemHeight={35}
      itemCount={results?.projection_years.length || 0}
      renderItem={({ index, style }) => (
        <div style={style} className="table-row">
          <span>Ano {results.projection_years[index]}</span>
          <span>{formatCurrency(results.projected_salaries[index])}</span>
          <span>{formatCurrency(results.projected_benefits[index])}</span>
        </div>
      )}
    />
  );
};
```

## 🎨 Design System e Estilo

### Paleta de Cores Profissional

```scss
// colors.scss - Tema Atuarial
$colors: (
  // Cores principais
  primary: #1e40af,      // Azul corporativo
  secondary: #059669,    // Verde confiabilidade  
  accent: #dc2626,       // Vermelho alertas
  
  // Cores de dados
  salary: #3b82f6,       // Azul para salários
  benefit: #10b981,      // Verde para benefícios
  reserves: #8b5cf6,     // Roxo para reservas
  contributions: #f59e0b, // Âmbar para contribuições
  
  // Estados
  success: #22c55e,      // Verde sucesso
  warning: #eab308,      // Amarelo alerta
  danger: #ef4444,       // Vermelho perigo
  info: #06b6d4,         // Ciano informação
  
  // Neutros
  gray-50: #f8fafc,
  gray-100: #f1f5f9,
  gray-200: #e2e8f0,
  gray-800: #1e293b,
  gray-900: #0f172a
);

// Tipografia profissional
$font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
$font-mono: 'JetBrains Mono', 'Fira Code', monospace;

// Componentes especializados
.parameter-slider {
  .slider-track {
    background: linear-gradient(90deg, $color-danger, $color-warning, $color-success);
  }
  
  .slider-thumb {
    box-shadow: 0 4px 12px rgba($color-primary, 0.3);
    
    &:hover {
      transform: scale(1.1);
    }
  }
}

.results-card {
  border-left: 4px solid $color-primary;
  
  .metric-value {
    font-family: $font-mono;
    font-size: 1.5rem;
    font-weight: 600;
    color: $color-gray-900;
  }
  
  .metric-label {
    font-size: 0.875rem;
    color: $color-gray-600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
}

.chart-container {
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  
  .chart-title {
    background: linear-gradient(135deg, $color-primary, $color-secondary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600;
  }
}
```

### Componentes Estilizados

```typescript
// Slider customizado para parâmetros atuariais
const ActuarialSlider: FC<ActuarialSliderProps> = ({
  label,
  value,
  min,
  max,
  step,
  unit,
  onChange,
  sensitivity
}) => {
  return (
    <div className="actuarial-slider">
      <div className="slider-header">
        <label className="slider-label">{label}</label>
        <span className="slider-value">
          {formatValue(value, unit)}
          {sensitivity && (
            <span className="sensitivity-indicator" 
                  data-impact={sensitivity.impact}>
              {sensitivity.impact > 0.1 ? '🔥' : '📊'}
            </span>
          )}
        </span>
      </div>
      
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="slider-input"
      />
      
      <div className="slider-footer">
        <span className="min-value">{formatValue(min, unit)}</span>
        <span className="max-value">{formatValue(max, unit)}</span>
      </div>
      
      {sensitivity && (
        <div className="impact-preview">
          <span>Impacto: </span>
          <span className={`impact-value ${sensitivity.impact > 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(sensitivity.impact_amount)}
            ({(sensitivity.impact * 100).toFixed(1)}%)
          </span>
        </div>
      )}
    </div>
  );
};
```

## 🚀 Implementação por Fases

### Fase 1: MVP Core (4 semanas)
- ✅ Backend Julia com API básica
- ✅ Interface React com parâmetros editáveis
- ✅ Cálculos RMBA/RMBC determinísticos
- ✅ Gráfico principal de projeções
- ✅ Tábuas BR-EMS e AT-2000

### Fase 2: Interatividade Avançada (3 semanas)
- ✅ WebSocket para reatividade em tempo real
- ✅ Análise de sensibilidade automática
- ✅ Gráficos múltiplos (reservas, fluxo de caixa)
- ✅ Interface mobile-responsive
- ✅ Exportação de relatórios PDF

### Fase 3: Recursos Profissionais (3 semanas)  
- ✅ Comparação de cenários lado a lado
- ✅ Histórico de simulações salvas
- ✅ Templates pré-configurados por categoria
- ✅ Integração com dados externos (ETTJ)
- ✅ Auditoria de cálculos detalhada

### Fase 4: Otimização e Deploy (2 semanas)
- ✅ Cache inteligente e otimizações
- ✅ Testes automatizados E2E
- ✅ Monitoramento e métricas
- ✅ Deploy containerizado
- ✅ Documentação técnica completa

## 🔧 Stack Tecnológica Detalhada

### Backend
- **Julia 1.9+**: Engine de cálculos atuariais
- **HTTP.jl**: Servidor web e API REST
- **WebSockets.jl**: Comunicação em tempo real
- **JSON3.jl**: Serialização otimizada
- **DataFrames.jl**: Manipulação de dados tabulares
- **JuliaActuary**: Pacotes atuariais especializados

### Frontend
- **React 18**: Framework reativo moderno
- **TypeScript**: Tipagem estática para robustez
- **Vite**: Build tool rápido e moderno
- **TanStack Query**: Estado servidor e cache
- **Chart.js / D3.js**: Visualizações interativas
- **Tailwind CSS**: Framework de estilos utilitário
- **React Hook Form**: Gerenciamento de formulários

### Infraestrutura
- **Docker**: Containerização da aplicação
- **Nginx**: Proxy reverso e arquivos estáticos
- **Redis**: Cache de sessões e resultados
- **PostgreSQL**: Persistência de configurações (futuro)

## 📈 Métricas de Sucesso

### Performance
- ⚡ **< 300ms**: Tempo de resposta para cálculos simples
- ⚡ **< 1s**: Cálculos com análise de sensibilidade
- 📱 **< 2s**: Carregamento inicial da página
- 🔄 **< 100ms**: Atualização reativa de parâmetros

### Usabilidade
- 👥 **90%+**: Taxa de satisfação em testes com usuários
- 🎯 **< 5 cliques**: Para realizar simulação completa
- 📚 **< 30 min**: Tempo de aprendizado para novos usuários
- 🔍 **100%**: Cobertura de casos de uso atuariais básicos

### Técnicas
- 🧪 **95%+**: Cobertura de testes automatizados
- 🔧 **99.5%+**: Uptime da aplicação
- 📊 **< 5MB**: Bundle size do frontend
- ♿ **WCAG 2.1 AA**: Conformidade com acessibilidade

---

## 💡 Considerações Finais

Este simulador representa uma evolução natural do sistema `pq_bd1`, mantendo a robustez técnica dos cálculos atuariais enquanto oferece uma experiência de usuário moderna e intuitiva. A arquitectura reativa permite exploração interativa de cenários, fundamental para análise atuarial profissional.

A integração com tábuas oficiais brasileiras garante conformidade regulatória, enquanto a análise de sensibilidade automática oferece insights valiosos para tomada de decisões. O sistema foi projetado para ser extensível, permitindo futuras integrações com outros módulos do `pq_bd1` conforme necessário.

**Próximos passos**: Aprovação da especificação, definição da equipe de desenvolvimento, e início da Fase 1 do cronograma proposto.