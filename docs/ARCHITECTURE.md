# 🏛️ Lenny Growth Assistant Architecture

This document describes the high-level architecture, component interaction, and RAG data flow of the **Lenny Growth Assistant**.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    User([User Browser])
    
    subgraph Frontend ["Frontend (React + Vite)"]
        UI[Chat Interface & Model Selector]
        APIClient[API Client & React Hooks]
        UI --> APIClient
    end

    subgraph Backend ["Backend (FastAPI)"]
        API[FastAPI REST API /api/v1]
        RAG[Lenny Growth Assistant Service]
        LLMFactory[LLM Provider Factory]
        
        API --> RAG
        RAG --> LLMFactory
    end

    subgraph Storage ["Persistence Layer"]
        Postgres[(PostgreSQL / Supabase)]
        Chroma[(Chroma Vector DB)]
    end

    subgraph LLMProviders ["LLM Inference"]
        OpenAI[OpenAI Cloud API\nGPT-4o & text-embedding-3]
        Ollama[Ollama Local Daemon\nLlama 3 & Mistral]
    end

    User <-->|HTTP / JSON| UI
    APIClient <-->|REST API| API
    
    API <-->|SQLAlchemy 2.0 Async| Postgres
    RAG <-->|Similarity Search / Ingest| Chroma
    
    LLMFactory -->|Cloud Inference| OpenAI
    LLMFactory -->|Local Inference| Ollama
```

---

## 2. RAG (Retrieval-Augmented Generation) Workflow

When a user submits a question through the chat interface:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as React Client
    participant API as FastAPI Backend
    participant Postgres as PostgreSQL (Supabase)
    participant Chroma as Chroma Vector DB
    participant LLM as LLM Provider (OpenAI/Ollama)

    User->>Frontend: Enters query ("How do I measure PMF?")
    Frontend->>API: POST /api/v1/chat
    API->>Postgres: Fetch / Create Conversation & Store User Message
    API->>Chroma: Vector Similarity Query (Top-k Chunks)
    Chroma-->>API: Return relevant snippets & relevance scores
    API->>LLM: Prompt = System Heuristics + Context Chunks + History + Query
    LLM-->>API: Return generated growth advice
    API->>Postgres: Save Assistant Message with Source Citations
    API-->>Frontend: Return ChatResponse JSON (content + sources)
    Frontend-->>User: Render formatted reply with expandable citations
```

---

## 3. Core Component Overview

### A. FastAPI Backend (`backend/app/`)
- **Async First**: Built on Python 3.10+ async/await primitives with `uvicorn` and `asyncpg`.
- **Modular Layering**:
  - `core/`: Settings (Pydantic v2), database connection pools, structured logging.
  - `db/`: Declarative ORM models (`User`, `Conversation`, `Message`).
  - `schemas/`: Request and response validation contracts.
  - `services/`: Business logic, vector index management, and LLM abstraction.
  - `api/v1/`: Versioned API endpoints with dependency injection.

### B. Relational Storage (`PostgreSQL` / `Supabase`)
- Stores user identities, conversations, and granular message histories.
- Compatible with hosted Supabase instances using standard connection pooling or direct connection.

### C. Vector Store (`ChromaDB`)
- Stores embedded text chunks from Lenny's growth essays, frameworks, and playbooks.
- Default collection `lenny_growth_knowledge` automatically bootstrapped with seed heuristics on startup.
- Supports both standalone Chroma HTTP server and local persistent directory modes.

### D. LLM Abstraction Layer
- `BaseLLMService` defines a common interface for `generate_response()`, `get_embeddings()`, and `health_check()`.
- `OpenAIService`: Leverages OpenAI's asynchronous Python SDK for cutting-edge cloud models (`gpt-4o`).
- `OllamaService`: Directly interfaces with local Ollama daemons for private, offline inference (`llama3`).
- `get_llm_service()`: Resolves the target provider dynamically per request or via global environment variables.

### E. Frontend (`React` + `Vite`)
- Built with TypeScript and TailwindCSS.
- Real-time backend health monitoring (PostgreSQL & Chroma statuses).
- Interactive model selector allowing users to toggle between OpenAI and Ollama.
- Expandable citation previews displaying retrieved chunks and semantic similarity scores.
