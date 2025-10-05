# Multi-stage build para Frontend PrevLab

# Stage 1: Build
FROM docker.io/library/node:20-alpine AS builder

WORKDIR /app

# Copiar package.json e package-lock.json
COPY package*.json ./

# Instalar dependências (usar npm install para resolver conflitos)
RUN npm install

# Copiar código fonte
COPY . .

# Build da aplicação
# A variável VITE_API_BASE_URL deve ser configurada em tempo de build
ARG VITE_API_BASE_URL=/api

# Limitar workers do Vite para evitar EMFILE
ENV NODE_OPTIONS="--max-old-space-size=4096"
# Usar ulimit para aumentar limite de arquivos abertos
RUN sh -c 'ulimit -n 65536 && VITE_API_BASE_URL=${VITE_API_BASE_URL} npm run build -- --logLevel=error'

# Stage 2: Production
FROM docker.io/library/nginx:alpine

# Copiar arquivos buildados
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expor porta 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
