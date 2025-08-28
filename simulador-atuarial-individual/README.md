# 🧮 Simulador Atuarial Interativo Individual

Sistema web completo para simulação determinística de reservas matemáticas e projeções previdenciárias personalizadas, desenvolvido com rigor atuarial profissional.

## 🎯 Características Principais

- **⚡ Reatividade Total**: Alterações em parâmetros atualizam resultados instantaneamente via WebSocket
- **📊 Interface Profissional**: Design moderno com terminologia atuarial técnica precisa
- **🔍 Rigor Atuarial**: Implementação completa de funções atuariais com precisão profissional
- **📋 Tábuas Oficiais**: BR-EMS 2021 e AT-2000 com dados reais da SUSEP
- **⚖️ Conformidade Regulatória**: Métodos aprovados (PUC, EAN) e validação de premissas
- **🎛️ Análise de Sensibilidade**: Impacto automático de variações em parâmetros-chave

## 🏗️ Arquitetura

```
simulador-atuarial-individual/
├── backend/                   # API Python + FastAPI
│   ├── src/
│   │   ├── core/             # Engine atuarial
│   │   ├── api/              # REST API + WebSocket
│   │   ├── models/           # Modelos Pydantic
│   │   └── utils/            # Utilitários
│   ├── data/
│   │   └── mortality_tables/ # Tábuas oficiais CSV
│   └── pyproject.toml        # Dependências uv
├── frontend/                  # React + TypeScript
│   ├── src/
│   │   ├── components/       # Componentes UI
│   │   ├── hooks/            # Hooks personalizados
│   │   ├── services/         # API client + WebSocket
│   │   └── types/            # Tipos TypeScript
│   └── package.json
└── README.md
```

## 🚀 Instalação e Execução

### Pré-requisitos

- **Python 3.11+** com `uv` instalado
- **Node.js 18+** com `npm`
- **Git**

### Backend (FastAPI)

```bash
# Navegar para o diretório backend
cd backend

# Criar ambiente virtual com uv
uv venv

# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instalar dependências com uv
uv pip install -e .

# Executar servidor de desenvolvimento
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

O backend estará disponível em:
- API: http://localhost:8000
- Documentação: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/{client_id}

### Frontend (React)

```bash
# Navegar para o diretório frontend
cd frontend

# Instalar dependências
npm install

# Executar servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em: http://localhost:5173

## 📊 Funcionalidades Implementadas

### Engine Atuarial

- ✅ **Reservas Matemáticas**: RMBA e RMBC com métodos PUC e EAN
- ✅ **Custo Normal**: Cálculo anual preciso
- ✅ **Projeções Temporais**: Salários, benefícios, contribuições
- ✅ **Matemática Financeira**: VPA, anuidades, duration, convexidade
- ✅ **Tábuas de Mortalidade**: BR-EMS 2021 e AT-2000 oficiais

### Interface Web

- ✅ **Painel de Parâmetros**: Controles editáveis organizados por categoria
- ✅ **Dashboard de Resultados**: Métricas principais formatadas
- ✅ **Comunicação Reativa**: WebSocket com debounce (300ms)
- ✅ **Status de Conexão**: Indicador visual em tempo real
- ✅ **Validação de Entrada**: Ranges apropriados e tipos corretos

### Análise Avançada

- ✅ **Sensibilidade Automática**: Taxa desconto, idade aposentadoria, mortalidade
- ✅ **Decomposição Atuarial**: VPA detalhado e breakdown de custos  
- ✅ **Métricas Profissionais**: Taxa reposição, duration, funding ratio
- ✅ **Performance Tracking**: Tempo de cálculo em milissegundos

## 🔧 Estrutura Técnica

### Backend (Python)

**Stack Principal:**
- FastAPI 0.104+ para API REST e WebSocket
- Pydantic 2.5+ para validação de dados
- NumPy/Pandas para cálculos atuariais
- Uvicorn como servidor ASGI

**Componentes:**
- `ActuarialEngine`: Motor de cálculos atuariais
- `MortalityTables`: Carregamento de tábuas oficiais
- `FinancialMath`: Funções matemática financeira
- `WebSocketManager`: Gerenciamento de conexões reativas

### Frontend (React)

**Stack Principal:**
- React 18 com TypeScript
- TanStack Query para estado servidor
- Axios para HTTP client
- Tailwind CSS para estilos

**Componentes:**
- `ParameterPanel`: Painel de entrada de parâmetros
- `ResultsDashboard`: Dashboard de resultados
- `useSimulator`: Hook principal de estado
- `WebSocketClient`: Cliente WebSocket customizado

## 📋 Tábuas de Mortalidade

### BR-EMS 2021 ✅ OFICIAL
- **Fonte**: SUSEP - Superintendência de Seguros Privados  
- **Base**: 94 milhões de registros (2004-2018)
- **Status**: Tábua oficial aprovada para uso regulatório
- **Formato**: CSV com colunas `idade,qx`

### AT-2000 ✅ OFICIAL  
- **Fonte**: SUSEP - Anuidades Brasileiras
- **Aplicação**: Seguros de anuidades e previdência
- **Status**: Aprovada pela SUSEP para uso oficial
- **Formato**: CSV com colunas `idade,qx`

## ⚡ Performance

**Métricas de Objetivo:**
- Cálculos simples: < 300ms
- Análise sensibilidade: < 1s  
- Carregamento inicial: < 2s
- Atualização reativa: < 100ms

**Otimizações Implementadas:**
- Cache de tábuas de mortalidade
- Debounce em alterações de parâmetros
- Cálculos paralelos para sensibilidade
- Memoização de componentes React

## 🔍 Validações e Conformidade

### Validações de Entrada
- Idade atual: 18-70 anos
- Idade aposentadoria: > idade atual
- Salário: > 0
- Taxas: Ranges apropriados (0-20%)

### Conformidade Regulatória  
- ✅ Tábuas oficiais SUSEP
- ✅ Métodos atuariais aprovados (PUC, EAN)
- ✅ Terminologia técnica precisa
- ✅ Validação de premissas

## 🧪 Desenvolvimento

### Estrutura de Comandos

```bash
# Backend
cd backend
uv pip install -e ".[dev]"          # Instalar deps desenvolvimento
python -m pytest                     # Executar testes
python -m black src/                  # Formatar código  
python -m ruff check src/            # Linting

# Frontend  
cd frontend
npm run build                        # Build produção
npm run type-check                   # Verificar tipos
npm run lint                         # ESLint
```

### Extensões Planejadas

- 🔄 Cache Redis para sessões
- 📈 Gráficos interativos (Chart.js)
- 💾 Persistência de simulações  
- 📊 Relatórios PDF exportáveis
- 🌐 Multi-idioma (PT/EN)

## ⚠️ Considerações Profissionais

**IMPORTANTE**: Este simulador é desenvolvido para uso profissional por atuários qualificados. Embora utilize tábuas oficiais e métodos aprovados, todos os resultados devem ser validados por atuário responsável antes de uso em análises formais ou regulatórias.

**Limitações Atuais**:
- Simulação determinística (não estocástica)
- Apenas participante individual (não população)
- Tábuas estáticas (sem projeção de melhoria)
- ETTJ fixa (não curva de juros dinâmica)

## 📄 Licença

Desenvolvido para análise atuarial profissional. Código disponível para auditoria e validação técnica.

---

**Versão**: 1.0.0  
**Última Atualização**: 2024  
**Desenvolvido com**: Python 3.11, FastAPI, React 18, TypeScript