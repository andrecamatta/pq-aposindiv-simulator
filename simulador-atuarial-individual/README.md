# 🧮 PrevLab

Plataforma web moderna para simulação atuarial de reservas matemáticas e projeções previdenciárias individuais, desenvolvida com rigor técnico profissional.

## 🎯 Visão Geral

O PrevLab é uma plataforma web completa que permite calcular e visualizar:

- **Reservas Matemáticas**: PMBC (Plano de Benefício Contribuição Definida) e PMBD (Plano de Benefício Definido)
- **Projeções Temporais**: Evolução de salários, contribuições e benefícios
- **Análise de Sensibilidade**: Impacto de variações em parâmetros-chave
- **Sugestões Inteligentes**: Recomendações automáticas baseadas no perfil do participante

### Principais Características

- ⚡ **Interface Reativa**: Atualização instantânea via WebSocket
- 📊 **Dashboard Profissional**: Métricas atuariais formatadas com precisão
- 🔍 **Cálculos Rigorosos**: Engine atuarial com funções matemáticas precisas
- 📋 **Tábuas Oficiais**: BR-EMS 2021 e AT-2000 (SUSEP)
- 🎛️ **Sistema de Abas**: Organização intuitiva por contexto (Participante, Premissas, Técnico, Resultados)

## 🏗️ Arquitetura do Sistema

```
simulador-atuarial-individual/
├── backend/                    # API Python + FastAPI
│   ├── src/
│   │   ├── api/               # Endpoints REST + WebSocket
│   │   ├── core/              # Engine atuarial principal
│   │   ├── models/            # Modelos de dados (Pydantic)
│   │   ├── utils/             # Utilitários matemáticos
│   │   └── scripts/           # Scripts de análise
│   ├── data/
│   │   └── mortality_tables/  # Tábuas CSV oficiais
│   └── pyproject.toml         # Dependências com uv
├── frontend/                   # React + TypeScript
│   ├── src/
│   │   ├── components/        # Componentes UI organizados
│   │   ├── design-system/     # Sistema de design customizado
│   │   ├── hooks/             # Hooks React personalizados
│   │   ├── services/          # Cliente API + WebSocket
│   │   └── types/             # Definições TypeScript
│   └── package.json
└── docs/                      # Documentação técnica
```

## 🚀 Configuração e Execução

### Pré-requisitos

- **Python 3.11+** com [uv](https://docs.astral.sh/uv/) instalado
- **Node.js 18+** com npm
- **Git** para controle de versão

### 1. Backend (FastAPI + Engine Atuarial)

```bash
# Clone o repositório (se necessário)
git clone <repository-url>
cd simulador-atuarial-individual/backend

# Instalar dependências com uv (recomendado)
uv sync

# Executar servidor de desenvolvimento
PYTHONPATH=/path/to/backend uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Endpoints Disponíveis:**
- API REST: http://localhost:8000
- Documentação Swagger: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/{client_id}
- Health Check: http://localhost:8000/health

### 2. Frontend (React + TypeScript)

```bash
# Navegar para o frontend
cd ../frontend

# Instalar dependências
npm install

# Executar servidor de desenvolvimento
npm run dev
```

**Aplicação Web:** http://localhost:5173

## 📊 Funcionalidades Principais

### 1. Engine Atuarial Completo

- ✅ **Reservas Matemáticas**: Cálculo PMBC e PMBD com métodos PUC e EAN
- ✅ **Custo Normal**: Determinação anual precisa
- ✅ **VPA (Valor Presente Atuarial)**: Cálculos de anuidades e fatores
- ✅ **Projeções**: Salários, contribuições e benefícios ao longo do tempo
- ✅ **Tábuas de Mortalidade**: BR-EMS 2021 e AT-2000 oficiais
- ✅ **Modalidades de Conversão**: Renda vitalícia e prazo determinado

### 2. Interface Web Moderna

- ✅ **Sistema de Abas**: Navegação organizada (Participante → Premissas → Técnico → Resultados)
- ✅ **Painel de Parâmetros**: Controles editáveis com validação
- ✅ **Dashboard de Resultados**: Métricas formatadas profissionalmente
- ✅ **Gráficos Interativos**: Visualização da evolução temporal
- ✅ **Comunicação Reativa**: WebSocket com debounce (300ms)
- ✅ **Design System**: Componentes consistentes e reutilizáveis

### 3. Análise Avançada

- ✅ **Análise de Sensibilidade**: Taxa de desconto, idade de aposentadoria, mortalidade
- ✅ **Sugestões Inteligentes**: Recomendações baseadas no perfil
- ✅ **Decomposição de Custos**: Breakdown detalhado dos componentes
- ✅ **Métricas Profissionais**: Taxa de reposição, duration, funding ratio
- ✅ **Performance Tracking**: Tempo de cálculo em tempo real

## 🔧 Stack Tecnológico

### Backend
- **FastAPI 0.104+**: Framework web moderno e rápido
- **Pydantic 2.5+**: Validação de dados robusta
- **NumPy/Pandas**: Computação científica e análise de dados
- **Uvicorn**: Servidor ASGI de alta performance
- **WebSocket**: Comunicação bidirecional em tempo real

### Frontend
- **React 18**: Biblioteca UI com hooks modernos
- **TypeScript**: Tipagem estática para JavaScript
- **TanStack Query**: Gerenciamento de estado do servidor
- **Tailwind CSS**: Framework CSS utilitário
- **Axios**: Cliente HTTP para comunicação com API
- **Chart.js**: Biblioteca de gráficos interativos

## 📋 Tábuas de Mortalidade Oficiais

### BR-EMS 2021 ✅
- **Fonte**: SUSEP - Superintendência de Seguros Privados
- **Base de Dados**: 94 milhões de registros (2004-2018)
- **Status**: Tábua oficial aprovada para uso regulatório
- **Aplicação**: Seguros de vida e previdência no Brasil

### AT-2000 ✅
- **Fonte**: SUSEP - Anuidades Brasileiras
- **Aplicação**: Seguros de anuidades e previdência privada
- **Status**: Aprovada pela SUSEP para uso oficial
- **Características**: Específica para população de anuitários

## ⚡ Performance e Otimização

**Métricas de Performance:**
- Cálculos simples: < 200ms
- Análise de sensibilidade: < 500ms
- Carregamento inicial: < 1s
- Atualização reativa: < 100ms

**Otimizações Implementadas:**
- Cache em memória das tábuas de mortalidade
- Debounce inteligente para evitar cálculos desnecessários
- Memoização de componentes React críticos
- WebSocket eficiente para comunicação bidirecional

## 🧪 Desenvolvimento e Testes

### Comandos do Backend

```bash
cd backend

# Instalar dependências de desenvolvimento
uv sync --dev

# Executar testes
uv run python -m pytest

# Formatação de código
uv run black src/

# Análise de código
uv run ruff check src/

# Executar scripts de análise
uv run python -m src.scripts.analyze_excel_tables
```

### Comandos do Frontend

```bash
cd frontend

# Build para produção
npm run build

# Verificação de tipos
npm run lint

# Testes E2E (Playwright)
npx playwright test

# Preview do build
npm run preview
```

## 🔍 Validações e Conformidade

### Validações de Entrada
- **Idade Atual**: 18-70 anos
- **Idade de Aposentadoria**: Maior que idade atual
- **Salário Atual**: Valor positivo
- **Taxas**: Ranges apropriados (0-30%)
- **Períodos**: Consistência temporal

### Conformidade Regulatória
- ✅ Utilização de tábuas oficiais SUSEP
- ✅ Implementação de métodos atuariais aprovados
- ✅ Terminologia técnica precisa e profissional
- ✅ Validação rigorosa de premissas

## 📈 Principais Casos de Uso

1. **Planejamento Previdenciário Individual**
   - Análise de cenários de aposentadoria
   - Comparação entre modalidades CD e BD
   - Otimização de contribuições

2. **Consultoria Atuarial**
   - Cálculo de reservas matemáticas
   - Análise de sensibilidade para clientes
   - Validação de premissas técnicas

3. **Educação e Treinamento**
   - Demonstração de conceitos atuariais
   - Simulação interativa para aprendizado
   - Visualização de impactos de parâmetros

## ⚠️ Considerações Importantes

**PARA USO PROFISSIONAL**: Este simulador foi desenvolvido para uso por profissionais atuários qualificados. Embora utilize métodos e tábuas oficiais, todos os resultados devem ser validados por atuário responsável antes de uso em análises formais ou regulatórias.

**Limitações Atuais:**
- Simulação determinística (não considera variabilidade estocástica)
- Foco em participante individual (não população)
- Tábuas estáticas (sem projeção de melhoria da mortalidade)
- Taxa de juros fixa (não considera curva de juros dinâmica)

## 📄 Licença

Este projeto está licenciado sob Creative Commons BY-NC 4.0 - desenvolvido para análise atuarial profissional com código disponível para auditoria e validação técnica.

---

**Versão**: 1.2.0  
**Última Atualização**: Setembro 2025  
**Tecnologias**: Python 3.11, FastAPI, React 18, TypeScript, uv, WebSocket