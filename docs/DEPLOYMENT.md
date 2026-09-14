# 🚀 Production Deployment & Supabase Guide

This guide describes deploying **Lenny Growth Assistant** to production environments and connecting to a cloud-hosted **Supabase** PostgreSQL database.

---

## 1. Connecting to Supabase PostgreSQL

Supabase offers a managed PostgreSQL database that is 100% compatible with SQLAlchemy and this application.

### Obtaining your Supabase Connection String:
1. Log in to [Supabase](https://app.supabase.com/) and select your project.
2. Navigate to **Project Settings** > **Database**.
3. Under **Connection String**, select the **URI** tab.
4. Choose **Transaction Pooler** (recommended for serverless/containerized deployments on port `6543`) or **Session Pooler** (`5432`).
5. Replace `[YOUR-PASSWORD]` with your actual database password.

### Format for SQLAlchemy (asyncpg):
In your production `.env` file or cloud secrets manager, set:

```env
DATABASE_URL=postgresql+asyncpg://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

> **Note:** The driver prefix must be `postgresql+asyncpg://` for asynchronous operation.

---

## 2. Production Docker Deployment

The repository includes production multi-stage Dockerfiles designed for minimal footprint and maximum security:

- **Backend**: `docker/Dockerfile.backend` (runs as unprivileged `appuser`, includes healthcheck).
- **Frontend**: `docker/Dockerfile.frontend` (compiles Vite static assets and serves via optimized `nginx:alpine`).

### Launching with Docker Compose:
```bash
# 1. Prepare production environment variables
cp .env.example .env
# Edit .env with production secrets

# 2. Build and run in detached mode
docker compose -f docker-compose.yml up -d --build
```

---

## 3. Cloud Deployment Targets

### Option A: Railway / Render / Fly.io
1. **Backend Service**:
   - Build using `docker/Dockerfile.backend`.
   - Set environment variables (`DATABASE_URL`, `OPENAI_API_KEY`, etc.).
   - Configure health check path `/api/v1/health`.
2. **ChromaDB**:
   - Deploy image `chromadb/chroma:latest` with a persistent volume attached.
3. **Frontend Service**:
   - Build using `docker/Dockerfile.frontend` with build argument `VITE_API_BASE_URL=https://your-backend-domain.com/api/v1`.

### Option B: AWS ECS / Kubernetes
- Deploy the Docker images to Amazon ECR.
- Use Amazon Aurora PostgreSQL or Supabase.
- Run Chroma in a persistent StatefulSet or ECS service with EBS.

---

## 4. Security Checklist for Production

- [ ] Change `SECRET_KEY` in `.env` to a cryptographically random 32+ character string.
- [ ] Ensure `DEBUG=false` in production.
- [ ] Set `ALLOWED_CORS_ORIGINS` to your exact production frontend domain.
- [ ] Secure ChromaDB behind an internal private VPC network or enable token authentication.
- [ ] Verify SSL/TLS encryption for database and web traffic.
