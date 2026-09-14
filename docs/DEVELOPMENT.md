# 💻 Local Development Guide

This guide walks you through setting up and running **Lenny Growth Assistant** on your local workstation.

---

## 1. Prerequisites

Ensure you have the following installed:
- **Python 3.10+** (`python --version`)
- **Node.js 18+ & npm** (`node --version`, `npm --version`)
- **Docker Desktop** (optional, recommended for database services)
- **Git**

---

## 2. Environment Configuration

Copy `.env.example` into a root `.env` file:

```bash
cp .env.example .env
```

Set your configuration:
- `OPENAI_API_KEY`: Your OpenAI API key (or set `LLM_PROVIDER=ollama`)
- `DATABASE_URL`: Your PostgreSQL / Supabase connection URL
- `CHROMA_HOST` and `CHROMA_PORT`: Point to your Chroma instance

---

## 3. Option A: Full Docker Development (Fastest)

Run all services (Frontend, Backend, PostgreSQL, Chroma) with live code reloading:

```bash
docker compose -f docker/docker-compose.dev.yml up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- ChromaDB: [http://localhost:8001](http://localhost:8001)

---

## 4. Option B: Hybrid Development (Local Backend & Frontend)

### Step 1: Start PostgreSQL and Chroma in Docker
```bash
docker compose up -d postgres chroma
```

### Step 2: Set Up Python Backend
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS / Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Set Up React Frontend
```bash
cd frontend

# Install Node packages
npm install

# Start Vite development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Running Tests

### Backend Unit & Integration Tests
```bash
cd backend
pytest -v
```

### Linting and Formatting
```bash
# Python (Ruff)
cd backend
ruff check .
ruff format .

# Frontend (TypeScript check)
cd frontend
npm run build
```

---

## 6. Using Ollama for Offline / Local LLM Inference

1. Install [Ollama](https://ollama.com/).
2. Pull the desired model:
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```
4. Set `LLM_PROVIDER=ollama` in `.env` (or select "Ollama" in the frontend UI).
