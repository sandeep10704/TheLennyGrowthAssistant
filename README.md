# 🚀 Lenny Growth Assistant

A production-ready, modular full-stack AI Assistant designed for product managers, founders, and growth professionals. Inspired by Lenny's Podcast and growth frameworks, this platform provides context-aware answers, product growth heuristics, and playbook recommendations using Retrieval-Augmented Generation (RAG).

---

## 🏗️ Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+) | High-performance asynchronous REST API |
| **Frontend** | [React](https://react.dev/) + [Vite](https://vitejs.dev/) + [TailwindCSS](https://tailwindcss.com/) | Modern, reactive, lightweight user interface |
| **Database** | [PostgreSQL](https://www.postgresql.org/) (Supabase Compatible) | Relational store for users, chats, and messages |
| **Vector DB** | [Chroma](https://www.trychroma.com/) | High-speed vector embeddings store for RAG retrieval |
| **LLM Orchestration** | OpenAI (`gpt-4o`) + Ollama (`llama3`) | Dual-provider support (cloud and local private inference) |
| **Containerization** | [Docker](https://www.docker.com/) & Docker Compose | Multi-container reproducible development and deployment |

---

## 📂 Project Structure

```plaintext
lenny-growth-assistant/
├── .gitignore                     # Git ignore rules for Python, Node, Docker, & Env
├── README.md                      # Project documentation and quick start
├── docker-compose.yml             # Full-stack Docker orchestration
├── .env.example                   # Master environment template
│
├── backend/                       # FastAPI Backend Application
│   ├── app/
│   │   ├── api/                   # API routes and dependencies (v1)
│   │   ├── core/                  # Configuration, database connection, logging
│   │   ├── db/                    # SQLAlchemy models and declarative base
│   │   ├── schemas/               # Pydantic schemas for request/response validation
│   │   ├── services/              # Business logic (LLM factory, ChromaDB, RAG assistant)
│   │   ├── tests/                 # Pytest test suite
│   │   └── main.py                # FastAPI application entrypoint & lifespan
│   ├── pyproject.toml             # Python project dependencies and tool configs
│   ├── requirements.txt           # Production dependencies
│   └── .env.example               # Backend-specific environment variables
│
├── frontend/                      # React (Vite) Frontend Application
│   ├── src/
│   │   ├── components/            # UI components (Chat, Layout, common)
│   │   ├── hooks/                 # Custom React hooks (useChat, useHealth)
│   │   ├── services/              # API client and network layer
│   │   ├── types/                 # TypeScript type declarations
│   │   ├── App.tsx                # App root component
│   │   └── main.tsx               # Entrypoint
│   ├── index.html                 # HTML template
│   ├── vite.config.ts             # Vite build configuration
│   ├── package.json               # Node dependencies and scripts
│   └── .env.example               # Frontend environment template
│
├── docker/                        # Dockerfiles and container configurations
│   ├── Dockerfile.backend         # Production multi-stage build for FastAPI
│   ├── Dockerfile.frontend        # Production multi-stage build with Nginx
│   ├── nginx.conf                 # Reverse proxy configuration
│   └── docker-compose.dev.yml     # Local dev orchestration with hot reloading
│
└── docs/                          # Comprehensive technical documentation
    ├── ARCHITECTURE.md            # System architecture and RAG workflow
    ├── API.md                     # Endpoint specifications and schemas
    ├── DEVELOPMENT.md             # Local setup and testing guidelines
    └── DEPLOYMENT.md              # Production deployment & Supabase integration
```

---

## 🐳 One-Command Docker Setup

The entire stack is configured to run with a single command using Docker Compose.

### 1. Configure Environment Variables
```bash
# Copy template to active .env
cp .env.example .env
```
Edit `.env` to set your preferences:
- `LLM_PROVIDER`: `openai` or `ollama`
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
- `DATABASE_URL`: Set your Supabase connection string, or leave blank to automatically use the local PostgreSQL container.

### 2. Start All Services
```bash
# Launch backend, frontend, chroma, and local postgres (if not using Supabase)
docker-compose up --build
```

### 3. Service Ports & Access Points
| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend UI** | [http://localhost:3000](http://localhost:3000) | Split-screen Chat & Sandboxed Artifact Viewer |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | FastAPI server & Health check (`/health`) |
| **Interactive Swagger** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI interactive schema explorer |
| **Chroma Vector DB** | [http://localhost:8001](http://localhost:8001) | RAG embeddings vector collection |
| **PostgreSQL** | `localhost:5432` | Relational store (skipped if using Supabase) |

---

## 🦙 Ollama Local LLM Integration

Run 100% private, local inference without external API costs or data transmission.

### Option A: Run Ollama on Host Machine (Recommended for GPU Acceleration)
1. Install Ollama from [ollama.com](https://ollama.com) and pull the models:
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```
2. In `.env`, set:
   ```ini
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   OLLAMA_MODEL=llama3
   OLLAMA_EMBEDDING_MODEL=nomic-embed-text
   ```
   *(The backend container connects via `host.docker.internal:host-gateway`)*.
3. Run `docker-compose up`.

### Option B: Run Ollama Completely in Docker
```bash
# Boot the stack including the containerized Ollama service
docker compose --profile ollama up -d

# Download models into the container
docker exec -it lenny-ollama ollama pull llama3
docker exec -it lenny-ollama ollama pull nomic-embed-text
```

For comprehensive troubleshooting and network bridge configurations, see [docs/OLLAMA_INTEGRATION.md](file:///C:/Users/saive/Documents/clg/project01/docs/OLLAMA_INTEGRATION.md).

---

## 🗄️ Database Options: Local PostgreSQL vs. Supabase

- **Option A: Local PostgreSQL (Zero Setup)**: Leave `DATABASE_URL` blank or commented out in `.env`. Docker Compose automatically spins up the `postgres:16-alpine` container, creates tables, and handles connection pooling and retries.
- **Option B: Remote Supabase**: Supply your Supabase connection string in `.env`:
  ```ini
  DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.co:6543/postgres
  ```
  The backend automatically uses Supabase, rendering the local PostgreSQL container optional.

---

## 🛠️ Local Development (Without Docker)

### Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 LLM Provider Configuration

The assistant supports switching seamlessly between cloud and local LLMs via `.env`:

```env
# Switch between "openai" and "ollama"
LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## 📖 Documentation

- [Architecture Design](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Local Development Guide](docs/DEVELOPMENT.md)
- [Deployment & Supabase Setup](docs/DEPLOYMENT.md)

---

## 📄 License
MIT License. See `LICENSE` for details.
