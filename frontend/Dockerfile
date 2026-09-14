# ==============================================================================
# Multi-stage Dockerfile for React Frontend (Lenny Growth Assistant)
# Context: frontend/
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build production static bundle with Vite
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests first for caching
COPY package*.json ./
RUN npm install

# Copy frontend source code
COPY . ./

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build production bundle
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Serve production bundle with Nginx reverse proxy
# ------------------------------------------------------------------------------
FROM nginx:alpine AS runner

# Remove default nginx configurations
RUN rm -rf /etc/nginx/conf.d/*

# Copy customized Nginx reverse proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
