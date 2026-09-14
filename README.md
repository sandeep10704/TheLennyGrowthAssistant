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

## ⚡ Quick Start

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v20+)
- [Python](https://www.python.org/) 3.10+
- [Node.js](https://nodejs.org/) 18+ (for local frontend development)
- (Optional) [Ollama](https://ollama.com/) installed locally for offline LLM support

### 2. Clone & Setup Environment
```bash
# Clone the repository
git clone <repository-url>
cd lenny-growth-assistant

# Create environment file from template
cp .env.example .env
```

Edit `.env` to configure your `OPENAI_API_KEY`, Supabase/Postgres credentials, and LLM preferences.

### 3. Run with Docker Compose (Recommended)
```bash
# Build and spin up all services (Backend, Frontend, Postgres, Chroma)
docker compose up --build
```

- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ChromaDB**: [http://localhost:8001](http://localhost:8001)

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
