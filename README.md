# PrevLab

Plataforma web moderna para simulação atuarial de planos de previdência individuais, desenvolvida para análise de sustentabilidade financeira e cálculos de reservas matemáticas.

## 🏗️ Arquitetura

### Backend (Python/FastAPI)
- **Framework**: FastAPI com Uvicorn
- **Cálculos Atuariais**: Numpy para computação matemática
- **Estrutura**: Arquitetura em camadas com separação clara de responsabilidades

### Frontend (React/TypeScript)
- **Framework**: React 18 com TypeScript
- **Build Tool**: Vite
- **UI**: Tailwind CSS com componentes reutilizáveis
- **Gráficos**: Chart.js com React Chart.js 2
- **Estado**: React Query para gerenciamento de estado do servidor

## 🚀 Funcionalidades

### Cálculos Atuariais
- **Reserva Matemática de Benefícios a Conceder (RMBA)**
- **Valor Presente Atuarial (VPA)** de contribuições e benefícios
- **Análise de Sustentabilidade** com déficit/superávit
- **Métodos**: Projected Unit Credit (PUC) e Entry Age Normal (EAN)
- **Tábuas de Mortalidade**: BR-EMS 2021 e outras tábuas brasileiras

### Interface do Usuário
- **Dashboard Interativo** com visualizações em tempo real
- **Formulários Inteligentes** com validação e tooltips explicativos
- **Gráficos Dinâmicos** para análise de cenários
- **Design System** consistente e responsivo
- **Modo Tabular** para análise detalhada

### Configurações Avançadas
- **Parâmetros Financeiros**: Taxas de desconto, crescimento salarial, inflação
- **Configurações Técnicas**: Timing de pagamentos, múltiplos salários anuais
- **Análise de Cenários**: Projeções de longo prazo com diferentes premissas

## 📦 Instalação

### Pré-requisitos
- **Para desenvolvimento local**: Python 3.11+, Node.js 18+, uv (gerenciador de dependências Python)
- **Para containers**: Docker ou Podman

### Opção 1: Desenvolvimento Local

#### Backend
```bash
cd simulador-atuarial-individual/backend
uv venv
uv pip install -r pyproject.toml
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd simulador-atuarial-individual/frontend
npm install
npm run dev
```

### Opção 2: Deploy com Containers (Recomendado)

#### Com Podman (Rootless)
```bash
cd simulador-atuarial-individual

# Build das imagens
podman build -t localhost/prevlab-backend:latest -f backend/Dockerfile backend/
podman build -t localhost/prevlab-frontend:latest -f frontend/Dockerfile frontend/ --ulimit nofile=90000:90000 --network=none

# Iniciar containers
chmod +x start-podman.sh
./start-podman.sh
```

#### Com Docker Compose
```bash
cd simulador-atuarial-individual
docker-compose up -d --build
```

#### Acessar aplicação
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

Para mais detalhes sobre deployment, consulte [docs/deployment/DEPLOY.md](docs/deployment/DEPLOY.md).

## 🔧 Desenvolvimento

### Estrutura do Projeto
```
pq_aposindiv/
├── simulador-atuarial-individual/
│   ├── backend/
│   │   ├── src/
│   │   │   ├── api/           # Endpoints FastAPI
│   │   │   ├── core/          # Lógica atuarial
│   │   │   ├── models/        # Modelos de dados
│   │   │   └── utils/         # Utilitários compartilhados
│   │   └── tests/             # Testes unitários e de integração
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/    # Componentes React
│   │   │   ├── hooks/         # Hooks customizados
│   │   │   ├── utils/         # Utilitários compartilhados
│   │   │   └── design-system/ # Sistema de design
│   │   └── tests/             # Testes E2E (Playwright)
│   └── docs/                  # Especificações técnicas
├── docs/
│   ├── deployment/            # Guias de deploy
│   ├── data-sources/          # Arquivos de referência (Excel)
│   └── README.md              # Índice da documentação
├── CLAUDE.md                  # Instruções de desenvolvimento
└── README.md                  # Este arquivo
```

### Princípios de Código
- **DRY (Don't Repeat Yourself)**: Utilitários reutilizáveis
- **Separação de Responsabilidades**: Camadas bem definidas
- **Type Safety**: TypeScript no frontend e type hints no backend
- **Modularidade**: Componentes e funções pequenos e focados

## 📊 Metodologia Atuarial

### Cálculos Implementados
- **VPA**: Valor presente atuarial usando tábuas de mortalidade
- **RMBA**: Reserva matemática com métodos PUC e EAN
- **Sustentabilidade**: Análise de equilíbrio atuarial
- **Projeções**: Cenários determinísticos de longo prazo

### Premissas Técnicas
- **Frequência**: Cálculos mensais com conversão anual
- **Mortalidade**: Tábuas brasileiras (BR-EMS 2021)
- **Timing**: Pagamentos antecipados ou postecipados
- **Crescimento**: Taxas reais (descontada inflação)

## 🛠️ Tecnologias

### Backend
- FastAPI, Uvicorn, Numpy, Pydantic, Python-multipart, SQLModel, pymort

### Frontend
- React, TypeScript, Vite, Tailwind CSS, Chart.js, React Query, Framer Motion

### Infrastructure & DevOps
- Docker/Podman (containerização)
- Nginx (proxy reverso)
- SQLite (banco de dados)
- uv (gerenciamento de dependências Python)

### Ferramentas
- ESLint, Prettier, TypeScript ESLint, Headless UI, Playwright (E2E testing)

## 📈 Status do Projeto

- ✅ **Core Atuarial**: Cálculos matemáticos implementados
- ✅ **API REST**: Endpoints funcionais
- ✅ **Interface Web**: Dashboard interativo
- ✅ **Design System**: Componentes reutilizáveis
- ✅ **Visualizações**: Gráficos e tabelas
- ✅ **Containerização**: Deploy com Docker/Podman
- ✅ **Tábuas de Mortalidade**: 17 tábuas integradas (pymort + BR-EMS 2021)
- ✅ **Testes E2E**: Playwright configurado
- 🔄 **Documentação**: Em expansão
- 🔄 **Deploy Cloud**: Em planejamento

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

**Resumo da licença:**
- ✅ **Uso pessoal e educacional** livre
- ✅ **Modificação e redistribuição** permitidas
- ❌ **Uso comercial** não permitido
- 📝 **Atribuição obrigatória** ao autor original

Para uso comercial, entre em contato: andrecamatta@gmail.com

Veja o arquivo [LICENSE](LICENSE) para detalhes completos.

## 👨‍💻 Autor

**André Camatta**
- GitHub: [@andrecamatta](https://github.com/andrecamatta)
- Email: andrecamatta@gmail.com

---

*Simulador desenvolvido com foco na precisão atuarial e experiência do usuário, seguindo as melhores práticas de desenvolvimento de software.*