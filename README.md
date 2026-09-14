# 🚀 Lenny Growth Assistant

A production-grade, full-stack AI Advisory Platform built for product managers, startup founders, and growth professionals. Grounded in Lenny Rachitsky’s product playbooks, newsletter frameworks, and podcast insights, the application provides context-grounded advisory, automated Ship 30 essay generation, and live interactive digital artifacts (HTML/Tailwind tools and Markdown specifications) powered by a robust Retrieval-Augmented Generation (RAG) pipeline.

---

## 📑 Table of Contents

- [Features](#-features)
- [System Architecture Overview](#-system-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Quick Start: Docker (Recommended)](#-quick-start-docker-recommended)
- [Local Setup & Run Steps (Without Docker)](#-local-setup--run-steps-without-docker)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Docker Usage & Commands](#-docker-usage--commands)
- [Environment Variables Reference](#-environment-variables-reference)
- [Database Options: Local PostgreSQL vs. Supabase](#-database-options-local-postgresql-vs-supabase)
- [LLM Provider Configuration & Fallback](#-llm-provider-configuration--fallback)
- [Error Handling & Observability](#-error-handling--observability)
- [Verification & Testing](#-verification--testing)
- [Documentation Directory](#-documentation-directory)

---

## ✨ Features

- **Context-Grounded Chat**: Dual-provider conversational assistant querying Lenny’s growth playbooks with transparent source citations and relevance scores.
- **Intent Router**: Automatically classifies user intent into question answering (`answer`), Ship 30 executive article generation (`essay`), or interactive web application / PRD creation (`artifact`).
- **Interactive Digital Artifacts**: Split-screen interface rendering Markdown specifications and interactive HTML5/Tailwind/JavaScript mini-tools in a secure iframe sandbox.
- **Resilient Multi-Provider Fallback**: Seamless automatic switching between OpenAI (`gpt-4o-mini`, `gpt-4o`) and local Ollama (`llama3.1:8b`, `llama3`) on rate limits, quota exhaustion, or timeouts.
- **Robust Session Survivability**: Async PostgreSQL/Supabase session persistence with in-memory caching that keeps conversations active even during database outages.
- **Defensive Error Handling**: User-friendly, structured error responses (`ErrorResponse`) with actionable tips and structured server logs (`❌ [DB Failure]`, `⏱️ [LLM Timeout]`, `ℹ️ [Empty RAG Results]`, `🔑 [Missing API Key]`).

---

## 🏗️ System Architecture Overview

```mermaid
flowchart LR
    subgraph Client ["Frontend Client (React + Vite)"]
        UI["Chat Interface\n& Model Selector"]
        Split["Split-Screen Panel"]
        Viewer["Sandboxed Artifact Viewer\n(iframe + Markdown)"]
        UI <--> Split
        Split <--> Viewer
    end

    subgraph Gateway ["Nginx & Reverse Proxy (Port 3000)"]
        Proxy["Nginx API Proxy\n/api/v1 -> Backend"]
    end

    subgraph Backend ["FastAPI REST Engine (Port 8000)"]
        Router["Intent Router\n(/router)"]
        ChatSvc["Chat Service\n(/chat)"]
        ArtSvc["Artifact Generator\n(/artifacts)"]
        LLM["Unified LLM Service\n(OpenAI / Ollama Fallback)"]
        SessSvc["Session Service\n(Postgres + Memory Cache)"]
        VectSvc["Vector Service\n(Semantic Search)"]
    end

    subgraph Storage ["Persistence & Data"]
        Chroma[("ChromaDB Vector Store\n(Port 8001)")]
        DB[("PostgreSQL / Supabase\n(Port 5432 / 6543)")]
    end

    Client --> Gateway
    Gateway --> Backend
    ChatSvc <--> VectSvc
    ChatSvc <--> SessSvc
    ChatSvc <--> LLM
    Router --> ChatSvc
    Router --> ArtSvc
    VectSvc <--> Chroma
    SessSvc <--> DB
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | React, Vite, TypeScript | React 18, Vite 5 | Reactive Single Page Application |
| **Styling & UI** | Tailwind CSS, Lucide React | 3.4+ | Clean modern UI with responsive dark/light theme |
| **Rendering** | DOMPurify, React-Markdown | Latest | Sandboxed iframe and sanitized GFM markdown rendering |
| **Backend** | FastAPI, Uvicorn, Python | 3.10+ | Asynchronous REST API, dependency injection |
| **ORM & DB** | SQLAlchemy 2.0, asyncpg | 2.0+, 0.31+ | Non-blocking async pooling and transaction management |
| **Vector DB** | ChromaDB | 0.6.3 | Transcript chunk embeddings and cosine/L2 retrieval |
| **LLM Cloud** | OpenAI Python SDK | 1.109+ | Primary cloud model inference (`gpt-4o-mini`, `gpt-4o`) |
| **LLM Local** | Ollama, httpx | Latest | 100% offline, private inference (`llama3.1:8b`, `llama3`) |
| **Containers** | Docker & Docker Compose | Compose v2 | Multi-stage production and dev container orchestration |

---

## 🐳 Quick Start: Docker (Recommended)

Run the entire full-stack application (frontend, backend, ChromaDB, and PostgreSQL) with a single command.

### 1. Clone & Configure Environment
```bash
# Clone the repository
git clone <repository-url>
cd project01

# Copy environment configuration
cp .env.example .env
```

### 2. Configure `.env`
Open `.env` and verify key settings:
```ini
# Choose active provider: "openai" or "ollama"
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Database: Leave blank for automated local PostgreSQL container, or set Supabase:
# DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-supabase.supabase.co:5432/postgres
```

### 3. Launch Services
```bash
# Start all containers in detached mode with build
docker compose up --build -d
```

### 4. Verify Service Endpoints
Once launched, the services are available at:

| Component | URL | Credentials / Notes |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | Full UI with chat, sessions, and artifact viewer |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | Root service discovery endpoint |
| **Swagger / OpenAPI Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API testing documentation |
| **System Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Real-time status of DB pool, Chroma, and LLM |
| **ChromaDB Server** | [http://localhost:8001](http://localhost:8001) | Vector database HTTP API |
| **Local PostgreSQL** | `localhost:5432` | User: `postgres`, Password: `postgres`, DB: `lenny_growth` |

---

## 💻 Local Setup & Run Steps (Without Docker)

If you prefer developing directly on your host machine without Docker:

### Prerequisites
- **Python**: 3.10 or higher (`python --version`)
- **Node.js**: 18.0.0 or higher & npm (`node --version`)
- **PostgreSQL**: PostgreSQL 15+ running locally OR a remote Supabase instance
- **ChromaDB**: Local file persistence mode or running Chroma instance

---

### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a virtual environment
# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure local environment variables
# Copy .env from root or create backend/.env
cp ../.env .env

# 5. Start the FastAPI development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend API will be running at `http://localhost:8000` (Docs: `http://localhost:8000/docs`).

---

### Frontend Setup

```bash
# 1. Navigate to frontend directory in a new terminal
cd frontend

# 2. Install npm dependencies
npm install

# 3. Start Vite development server
npm run dev
```
Frontend development server will be running at `http://localhost:5173` (or proxy at `http://localhost:3000`).

---

## 🚢 Docker Usage & Commands

### Common Docker Compose Commands

```bash
# Build and start all services in the background
docker compose up --build -d

# View real-time logs across all services
docker compose logs -f

# View backend logs specifically
docker compose logs -f backend

# Check status and health of all containers
docker compose ps

# Restart a specific service (e.g., backend after editing code)
docker compose restart backend

# Execute pytest inside the running backend container
docker exec lenny-backend pytest -v

# Open an interactive shell inside the backend container
docker exec -it lenny-backend /bin/bash

# Stop all services (preserves database and vector volumes)
docker compose down

# Stop all services and wipe all data volumes (clean slate)
docker compose down -v
```

### Container Resource Map

```plaintext
project01-stack/
├── lenny-frontend   (Port 3000 -> Nginx + Vite React Production Bundle)
├── lenny-backend    (Port 8000 -> Uvicorn FastAPI + RAG & Router Engine)
├── lenny-chromadb   (Port 8001 -> Chroma Vector Engine v0.6.3)
└── lenny-postgres   (Port 5432 -> PostgreSQL 16 Alpine Relational Store)
```

---

## ⚙️ Environment Variables Reference

All configurations are managed through `.env`. Below is a comprehensive description of every variable supported by the application:

### Core & Server Settings
| Variable | Default | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Deployment environment (`development`, `staging`, `production`) |
| `PROJECT_NAME` | `Lenny Growth Assistant` | Application identity name |
| `DEBUG` | `true` | Enable debug logs and verbose error details |
| `BACKEND_HOST` | `0.0.0.0` | IP binding address for FastAPI |
| `BACKEND_PORT` | `8000` | Port for the backend API |
| `FRONTEND_PORT` | `3000` | Port for the frontend interface |
| `ALLOWED_CORS_ORIGINS` | `["http://localhost:3000","..."]` | JSON array of authorized CORS origin URLs |

### Database & Pooling (PostgreSQL / Supabase)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | *(local postgres string)* | Async SQLAlchemy connection URI (`postgresql+asyncpg://...`) |
| `POSTGRES_USER` | `postgres` | Database username for local postgres container |
| `POSTGRES_PASSWORD` | `postgres` | Database password for local postgres container |
| `POSTGRES_DB` | `lenny_growth` | Database name for local postgres container |
| `POSTGRES_PORT` | `5432` | Port exposed by PostgreSQL |
| `DB_POOL_SIZE` | `15` | Persistent connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Temporary connections permitted during load bursts |
| `DB_POOL_TIMEOUT` | `30` | Seconds to wait before timing out connection acquisition |
| `DB_POOL_RECYCLE` | `1800` | Connection recycling period in seconds (prevents stale sockets) |
| `DB_POOL_PRE_PING` | `true` | Executes `SELECT 1` ping before checkout to drop dead sockets |
| `DB_STATEMENT_CACHE_SIZE` | `0` | Set to `0` for Supabase/PgBouncer transaction pooler compatibility |
| `DB_MAX_RETRIES` | `3` | Max retry attempts for transient connection errors |
| `DB_RETRY_BASE_DELAY` | `0.5` | Exponential backoff base delay in seconds |
| `DB_RETRY_MAX_DELAY` | `3.0` | Maximum retry backoff delay in seconds |

### Vector Store (ChromaDB)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `CHROMA_HOST` | `chroma` (or `localhost`) | Hostname of the Chroma service |
| `CHROMA_PORT` | `8000` | Internal port of ChromaDB service |
| `CHROMA_COLLECTION_NAME` | `lenny_growth_knowledge` | Chroma collection name storing growth chunks |
| `CHROMA_USE_HTTP` | `true` | If `true`, connects via HTTP client; otherwise uses local file directory |
| `CHROMA_PERSISTENCE_DIR` | `./chroma_data` | Directory path when using local file persistence |
| `RAG_MIN_RELEVANCE_SCORE` | `0.05` | Minimum similarity score threshold to prevent irrelevant citations |

### LLM Providers & Fallback
| Variable | Default | Description |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `openai` | Primary active LLM provider (`openai` or `ollama`) |
| `LLM_TIMEOUT_SECONDS` | `30.0` | Hard timeout limit for OpenAI requests |
| `LLM_FALLBACK_ENABLED` | `true` | Enables automatic failover to secondary provider on errors/quota limit |
| `LLM_FALLBACK_PROVIDER` | `ollama` | Provider to fall back to if the primary fails |
| `OPENAI_API_KEY` | `""` | OpenAI API Secret Key (`sk-...`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Default OpenAI model (`gpt-4o-mini`, `gpt-4o`) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for semantic vector representation |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama daemon URL (use `localhost` outside Docker) |
| `OLLAMA_MODEL` | `llama3.1:8b` | Default Ollama model installed locally (`llama3`, `mistral`) |
| `OLLAMA_TIMEOUT_SECONDS` | `120.0` | Timeout threshold for local Ollama CPU/GPU inference |

### Frontend Client
| Variable | Default | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Base URL used by React to communicate with FastAPI |

---

## 🗄️ Database Options: Local PostgreSQL vs. Supabase

The platform natively supports zero-configuration local Docker storage as well as hosted cloud Supabase instances:

### Option 1: Zero-Config Local PostgreSQL (Default)
Do not set or modify `DATABASE_URL` in `.env`. Docker Compose automatically spins up `lenny-postgres`, initializes schemas, runs migrations, and handles connection pooling.

### Option 2: Remote Hosted Supabase
Supply your Supabase connection string in `.env`:
```ini
# Supabase Transaction Pooler (Port 6543 - Recommended for containerized apps):
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Or Supabase Direct Connection (Port 5432):
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```
When a valid Supabase URL is detected:
- The backend automatically points to Supabase.
- Statement caching is automatically disabled (`statement_cache_size=0`) to ensure 100% compatibility with PgBouncer.
- Pre-ping and exponential backoff retry policies handle cloud network transients.

---

## 🦙 LLM Provider Configuration & Fallback

The application features an enterprise-grade resilient dual-provider architecture:

### 1. Cloud OpenAI Mode
```ini
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### 2. Private Local Ollama Mode
Run 100% private, free inference with zero API key dependencies:
1. Install [Ollama](https://ollama.com) on your host machine.
2. Pull the model: `ollama pull llama3.1:8b`
3. Configure `.env`:
   ```ini
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   OLLAMA_MODEL=llama3.1:8b
   ```

### 3. Automated Dual Failover Logic
If OpenAI experiences rate limits (`HTTP 429 quota exhausted`), network timeouts, or 5xx server errors, the system:
1. Logs a warning: `⚠️ Primary provider 'openai' failed. Triggering automatic fallback to 'ollama'...`
2. Automatically routes the user query to the local Ollama daemon.
3. Successfully returns the generated response to the user with `fallback_used: true` metadata.

---

## 🚨 Error Handling & Observability

The application implements defensive error handling across four failure modes:

| Failure Mode | HTTP Status | Error Code | Behavior |
| :--- | :--- | :--- | :--- |
| **Database Failure** | `503` | `DATABASE_ERROR` | Preserves active conversations in-memory (`_memory_cache`); logs `❌ [DB Failure]`. |
| **LLM Timeout** | `504` | `LLM_TIMEOUT` | Provider and service-level timeout enforcement; returns helpful model selection tip; logs `⏱️ [LLM Timeout]`. |
| **Empty RAG Results** | `404` / Fallback | `EMPTY_RAG_RESULTS` | Chat injects baseline heuristics without breaking; strict search returns 404 with search tips; logs `ℹ️ [Empty RAG Results]`. |
| **Missing API Key** | `401` | `MISSING_API_KEY` | Re-raises immediately with clear instructions to configure `.env` or toggle to Ollama; logs `🔑 [Missing API Key]`. |

### Standardized Error Format:
```json
{
  "success": false,
  "error": "Short technical description",
  "user_message": "Friendly explanation suitable for display to end-users",
  "actionable_tip": "Concrete instructions on how to resolve the issue",
  "detail": { ... },
  "code": "MACHINE_READABLE_CODE",
  "timestamp": "2026-09-14T15:20:00.000000Z"
}
```

---

## 🧪 Verification & Testing

Execute the test suite using `pytest` inside the backend container or locally:

```bash
# Run all tests inside docker
docker exec lenny-backend pytest -v

# Run only error handling verification tests
docker exec lenny-backend pytest -v tests/test_error_handling.py

# Run database pooling & session tests
docker exec lenny-backend pytest -v tests/test_database.py

# Run LLM timeout & fallback tests
docker exec lenny-backend pytest -v tests/test_llm.py

# Run RAG ingestion & retrieval tests
docker exec lenny-backend pytest -v tests/test_rag.py
```

---

## 📚 Documentation Directory

- [Architecture Design & Data Flows](architecture.md) (`architecture.md`)
- [UI/UX Design Decisions](design.md) (`design.md`)
- [API Specifications & Contracts](docs/API.md) (`docs/API.md`)
- [Ollama Integration Deep Dive](docs/OLLAMA_INTEGRATION.md) (`docs/OLLAMA_INTEGRATION.md`)
- [Secure Sandboxed Rendering Protocol](docs/SECURE_RENDERING.md) (`docs/SECURE_RENDERING.md`)
- [Deployment Guide](docs/DEPLOYMENT.md) (`docs/DEPLOYMENT.md`)

---

## 📄 License

MIT License. Crafted for high-growth founders and product builders.
