# Dockerfile para Backend PrevLab
FROM docker.io/library/python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias para WeasyPrint e outras bibliotecas
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para gerenciamento de dependências Python
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copiar arquivos de dependências
COPY pyproject.toml ./

# Instalar dependências usando uv
RUN uv pip install --system .

# Copiar código da aplicação
COPY src/ ./src/

# Criar diretórios necessários
RUN mkdir -p data/db data/uploads data/reports logs

# Copiar banco de dados com tábuas de mortalidade (usar nome correto: simulador.db)
COPY data/simulador.db ./data/simulador.db

# Expor porta do servidor
EXPOSE 8000

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./data/db/prevlab.db
ENV LOG_LEVEL=info
ENV WORKERS=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando para iniciar o servidor
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
