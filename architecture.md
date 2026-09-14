# 🏛️ System Architecture & Data Flow

This document details the architectural design, component interactions, data flows, and resilience patterns of the **Lenny Growth Assistant**.

---

## 📑 Table of Contents

- [1. Architectural Principles & Goals](#1-architectural-principles--goals)
- [2. System Design & Component Hierarchy](#2-system-design--component-hierarchy)
  - [Client Tier (React Single Page Application)](#client-tier-react-single-page-application)
  - [Gateway & Reverse Proxy (Nginx)](#gateway--reverse-proxy-nginx)
  - [Application Tier (FastAPI Asynchronous Engine)](#application-tier-fastapi-asynchronous-engine)
  - [Knowledge & Vector Tier (ChromaDB)](#knowledge--vector-tier-chromadb)
  - [Relational Persistence Tier (PostgreSQL / Supabase)](#relational-persistence-tier-postgresql--supabase)
  - [Inference Layer (Dual-Provider LLM Engine)](#inference-layer-dual-provider-llm-engine)
- [3. End-to-End Data Flows](#3-end-to-end-data-flows)
  - [Data Flow 1: Context-Grounded RAG Conversational Turn](#data-flow-1-context-grounded-rag-conversational-turn)
  - [Data Flow 2: Agent Intent Classification & Routing](#data-flow-2-agent-intent-classification--routing)
  - [Data Flow 3: Interactive Digital Artifact Generation & Sandboxed Delivery](#data-flow-3-interactive-digital-artifact-generation--sandboxed-delivery)
  - [Data Flow 4: Resilient Database Persistence & Memory Failover](#data-flow-4-resilient-database-persistence--memory-failover)
  - [Data Flow 5: Dual-Provider LLM Failover Lifecycle](#data-flow-5-dual-provider-llm-failover-lifecycle)
  - [Data Flow 6: Standardized Error Handling & Propagation](#data-flow-6-standardized-error-handling--propagation)
- [4. Database Schema & Data Models](#4-database-schema--data-models)
- [5. Vector Store & RAG Ingestion Pipeline](#5-vector-store--rag-ingestion-pipeline)
- [6. Security & Sandboxing Architecture](#6-security--sandboxing-architecture)

---

## 1. Architectural Principles & Goals

The Lenny Growth Assistant architecture is designed around four core tenets:

1. **Grounded Intelligence (RAG)**: Conversational responses and essay drafts are anchored in real product management playbooks, benchmarks, and podcast transcript excerpts, eliminating ungrounded hallucinations.
2. **Defensive Survivability**: No single component failure breaks the user experience:
   - Database outages gracefully degrade to in-memory session caches without dropping active chats.
   - LLM rate limits or quota exhaustion automatically fail over to local Ollama inference.
   - Queries with zero semantic matches smoothly fall back to foundational growth heuristics.
3. **Strict Security Isolation**: Code execution in user-facing artifacts (HTML/JavaScript tools) is quarantined in an isolated, sandboxed `<iframe>` boundary preventing access to parent DOM, local storage, cookies, and network credentials.
4. **Asynchronous Non-Blocking I/O**: The entire backend is built on asynchronous Python primitives (`asyncio`, `asyncpg`, `httpx`), delivering low latency and high concurrency under multi-user workloads.

---

## 2. System Design & Component Hierarchy

```mermaid
flowchart TB
    subgraph Browser ["Client Presentation Tier (Browser)"]
        ChatUI["Chat & Thread Workspace\n(React 18 / Tailwind CSS)"]
        RouterUI["Intent Selector\n(Chat / Essay / Artifact)"]
        SplitPane["Split-Screen Grid Layout"]
        SandboxedFrame["Isolated iframe Sandbox\n(allow-scripts only)"]
        MarkdownView["GFM Markdown Spec Viewer\n(DOMPurify Sanitized)"]
        
        ChatUI <--> SplitPane
        SplitPane --> SandboxedFrame
        SplitPane --> MarkdownView
    end

    subgraph Ingress ["Network & Ingress Tier"]
        Nginx["Nginx Reverse Proxy (Port 3000)\nStatic Assets + Proxy /api/v1"]
    end

    subgraph BackendApp ["Application Engine (FastAPI on Port 8000)"]
        direction TB
        MainAPI["FastAPI Lifespan & Global Exception Handlers"]
        AgentRouter["Agent Intent Router\n(answer | essay | artifact)"]
        ChatService["Chat Service\n(History + Prompt Synthesis)"]
        EssayService["Ship 30 Essay Generator\n(Outline -> Expand -> Format)"]
        ArtifactService["Artifact Generator\n(HTML5 / Tailwind / Markdown)"]
        VectorService["Vector Knowledge Service\n(ChromaDB Client + RAG Filter)"]
        SessionService["Session & History Service\n(PostgreSQL + Memory Cache)"]
        LLMService["Unified LLM Service\n(OpenAI <-> Ollama Failover)"]

        MainAPI --> AgentRouter
        MainAPI --> ChatService
        MainAPI --> ArtifactService
        AgentRouter --> ChatService
        AgentRouter --> EssayService
        AgentRouter --> ArtifactService
        ChatService --> VectorService
        ChatService --> SessionService
        ChatService --> LLMService
        EssayService --> LLMService
        ArtifactService --> LLMService
    end

    subgraph DataTier ["Persistence & Knowledge Tier"]
        Postgres[("PostgreSQL 16 / Supabase\nAsync Connection Pool\n(chat_sessions, chat_messages)")]
        Chroma[("ChromaDB Vector Store\n(lenny_growth_knowledge)")]
    end

    subgraph LLMTier ["Inference Tier"]
        OpenAI["OpenAI API Cloud\n(gpt-4o-mini / gpt-4o)"]
        Ollama["Local Ollama Daemon\n(llama3.1:8b / llama3)"]
    end

    Browser <-->|HTTP / WebSocket| Nginx
    Nginx <-->|Proxy Pass /api/v1| MainAPI
    VectorService <-->|HTTP / Port 8001| Chroma
    SessionService <-->|asyncpg / Port 5432| Postgres
    LLMService <-->|HTTPS API / 30s Timeout| OpenAI
    LLMService <-->|HTTP / 120s Timeout| Ollama
```

### Client Tier (React Single Page Application)
- **Framework**: React 18 with Vite, TypeScript, and Tailwind CSS.
- **State Management**: Reactive hooks (`useChat`, `useHealth`) coordinating multi-turn conversation state, session switching, and active artifact selection.
- **Artifact Workplace**: Dual-pane responsive layout rendering either conversational advice, full-width Markdown PRDs, or live HTML applications.

### Gateway & Reverse Proxy (Nginx)
- Multi-stage Docker image serving pre-compiled static frontend assets.
- Reverse proxies `/api/v1/*` requests directly to `http://backend:8000`, eliminating cross-origin complications and exposing a single unified port (`3000`).

### Application Tier (FastAPI Asynchronous Engine)
- **Lifespan Management**: Automatically initializes connection pools, performs vector database seeding, and verifies LLM provider readiness on startup.
- **Global Error Interception**: Centralized exception handlers capturing validation failures (422), domain errors (`AppException`), and unhandled exceptions (500), mapping them into predictable, user-friendly JSON payloads.

### Knowledge & Vector Tier (ChromaDB)
- Stores dense embeddings of Lenny's growth playbooks and transcript chunks.
- Performs cosine / squared L2 distance searches with semantic threshold filtering (`RAG_MIN_RELEVANCE_SCORE=0.05`).

### Relational Persistence Tier (PostgreSQL / Supabase)
- Manages long-term conversation storage (`chat_sessions`) and message sequences (`chat_messages`).
- Implements SQLAlchemy 2.0 async engine with connection pooling (`pool_size=15`, `max_overflow=10`, `pool_recycle=1800`), pre-ping validation, and exponential backoff retry.

### Inference Layer (Dual-Provider LLM Engine)
- Abstract provider factory supporting cloud (`OpenAIProvider`) and local (`OllamaProvider`).
- Enforces strict execution deadlines using `asyncio.wait_for` at both provider and service boundaries.

---

## 3. End-to-End Data Flows

### Data Flow 1: Context-Grounded RAG Conversational Turn

```mermaid
sequenceDiagram
    autonumber
    actor User as Product Builder
    participant UI as React Frontend
    participant API as FastAPI (/chat)
    participant Sess as Session Service
    participant Vect as Vector Service
    participant Chroma as ChromaDB (8001)
    participant LLM as LLM Service
    participant DB as PostgreSQL (5432)

    User->>UI: Types: "How do I calculate our Sean Ellis PMF score?"
    UI->>API: POST /chat { message, session_id, model, provider }
    
    API->>Sess: get_or_create_session(session_id)
    Sess->>DB: Check / insert session record (or store in memory cache)
    DB-->>Sess: Session confirmed
    
    API->>Sess: add_user_message(session_id, message)
    Sess->>DB: INSERT into chat_messages (role='user')
    
    API->>Vect: query_knowledge("Sean Ellis PMF score", top_k=5)
    Vect->>Chroma: POST /api/v2/.../query { query_texts }
    Chroma-->>Vect: Return matching chunks & distances
    Vect-->>API: List[SourceCitation] (filtered by relevance threshold)
    
    API->>Sess: get_session_history(session_id, limit=8)
    Sess-->>API: Prior 8 conversational turns
    
    API->>LLM: generate_chat_turn(system_prompt + context + history + query)
    LLM-->>API: Return generated growth guidance
    
    API->>Sess: add_assistant_message(session_id, content, sources, model_used)
    Sess->>DB: INSERT into chat_messages (role='assistant', sources=JSON)
    
    API-->>UI: ChatResponse { message_id, content, sources, provider, model }
    UI-->>User: Renders advisory response + expandable citation drawer
```

---

### Data Flow 2: Agent Intent Classification & Routing

The user prompt is analyzed by the `AgentRouter` to dynamically route requests to the optimal processing pipeline:

```mermaid
flowchart TD
    Prompt["Incoming User Prompt\nPOST /router"] --> Router["classify_intent(prompt)"]
    
    Router -->|Pattern: 'write article', 'draft essay'| EssayIntent["Intent: 'essay' (Confidence: 0.98)"]
    Router -->|Pattern: 'create page', 'build calculator'| ArtIntent["Intent: 'artifact' (Confidence: 0.98)"]
    Router -->|Questions, advisory, benchmarks| AnsIntent["Intent: 'answer' (Confidence: 0.95)"]

    EssayIntent --> EssayGen["Ship30EssayGenerator\n1. Generate 6-part outline\n2. Expand sections (~1200w)\n3. Format Hook, Headings, Bullets"]
    ArtIntent --> ArtGen["ArtifactGenerator\n1. Detect format (html vs markdown)\n2. Generate code & enforce sandbox\n3. Extract pure code block"]
    AnsIntent --> ChatGen["ChatService\n1. Vector retrieval from Chroma\n2. Prompt synthesis\n3. LLM generation with fallback"]

    EssayGen --> Response["Structured JSON Output\n{ type: 'essay', data: EssayData }"]
    ArtGen --> Response["Structured JSON Output\n{ type: 'artifact', data: ArtifactData }"]
    ChatGen --> Response["Structured JSON Output\n{ type: 'answer', data: AnswerData }"]
```

---

### Data Flow 3: Interactive Digital Artifact Generation & Sandboxed Delivery

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant UI as React Frontend
    participant API as FastAPI (/artifacts/generate)
    participant ArtSvc as Artifact Generator
    participant LLM as LLM Service
    participant Frame as Sandboxed iframe

    User->>UI: Prompt: "Create a retention curve calculator"
    UI->>API: POST /artifacts/generate { prompt, output_type: 'html' }
    
    API->>ArtSvc: generate_artifact(prompt, output_type='html')
    ArtSvc->>LLM: generate_response(system_prompt=HTML_INSTRUCTIONS, query=prompt)
    LLM-->>ArtSvc: Raw text with ```html ... ``` code block
    
    ArtSvc->>ArtSvc: Extract HTML code block & inject Tailwind CDN & security headers
    ArtSvc-->>API: ArtifactResponse { type: 'html', content: '...', title: '...' }
    
    API-->>UI: Deliver Artifact JSON
    UI->>Frame: Inject into <iframe sandbox="allow-scripts" srcdoc={content}>
    Frame-->>User: Renders live interactive calculator (parent access blocked)
```

---

### Data Flow 4: Resilient Database Persistence & Memory Failover

When cloud network disruptions or PostgreSQL restarts occur, the application activates its dual-layer resilience protocol:

```mermaid
flowchart TD
    Start["DB Operation\n(Add Message / Create Session)"] --> Retry["execute_with_db_retry()\nAttempt 1..3 with backoff + jitter"]
    
    Retry -->|Database Connected| Success["Commit to PostgreSQL\nReturn operation ID"]
    Retry -->|OperationalError / Timeout (3 attempts)| Failed["Transient DB Failure Detected"]
    
    Failed --> Log["Log: ❌ [DB Failure] Operation failed\nFalling back to in-memory store"]
    Log --> MemCache["Write to SessionService._memory_cache[session_id]\nWrite metadata to _sessions_meta_cache"]
    MemCache --> Continue["Return session_id / message_id to caller"]
    Continue --> Output["User continues conversation seamlessly\nZero 500 error interruption"]
```

---

### Data Flow 5: Dual-Provider LLM Failover Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant App as Application Service
    participant LLM as LLMService Layer
    participant OpenAI as OpenAI Provider (Cloud)
    participant Ollama as Ollama Provider (Local)

    App->>LLM: generate_response(query, context, provider='openai')
    LLM->>OpenAI: generate(timeout=30.0s)
    
    alt OpenAI Success
        OpenAI-->>LLM: Generated advice content
        LLM-->>App: Return content (provider='openai')
    else Rate Limit (429) / Quota Exhaustion / Timeout (504)
        OpenAI-->>LLM: HTTP 429 Insufficient Quota
        LLM->>LLM: Log: ⚠️ Primary provider 'openai' failed. Triggering automatic fallback to 'ollama'...
        LLM->>Ollama: generate(model='llama3.1:8b', timeout=120.0s)
        
        alt Ollama Model Not Found (404)
            Ollama->>Ollama: Check /api/tags -> Auto-resolve model prefix (e.g. llama3 -> llama3.1:8b)
            Ollama->>Ollama: Retry generation with resolved model
        end
        
        Ollama-->>LLM: Generated advice content
        LLM-->>App: Return content (provider='ollama', fallback_used=true)
    else Both Providers Fail
        LLM-->>App: Raise LLMServiceError with friendly user_message & actionable tip
    end
```

---

### Data Flow 6: Standardized Error Handling & Propagation

All runtime exceptions flow through centralized FastAPI error handlers:

```mermaid
flowchart LR
    Exception["Exception Triggered\n(Database / Timeout / Missing Key / Empty RAG)"] --> Handler{"Exception Type"}
    
    Handler -->|AppException| AppH["app_exception_handler\nExtract code, status, user_message, tip"]
    Handler -->|RequestValidationError| ValH["validation_exception_handler\nMap field violations to friendly tip (422)"]
    Handler -->|HTTPException| HttpH["http_exception_handler\nMap standard 401/403/404 messages"]
    Handler -->|Unhandled Exception| UnhandledH["unhandled_exception_handler\nLog 💥 [Internal Error], mask stack trace (500)"]

    AppH --> Response["JSONResponse\nErrorResponse Schema"]
    ValH --> Response
    HttpH --> Response
    UnhandledH --> Response
```

---

## 4. Database Schema & Data Models

The relational schema is defined via SQLAlchemy 2.0 in [`backend/models/database.py`](file:///C:/Users/saive/Documents/clg/project01/backend/models/database.py):

```mermaid
erDiagram
    chat_sessions ||--o{ chat_messages : contains
    
    chat_sessions {
        string(64) id PK "Unique UUID identifier"
        string(255) title "Session title / first query preview"
        datetime created_at "Creation timestamp (UTC)"
        datetime updated_at "Last interaction timestamp (UTC)"
    }

    chat_messages {
        string(64) id PK "Message UUID"
        string(64) session_id FK "References chat_sessions.id (CASCADE)"
        string(32) role "'user' | 'assistant' | 'system'"
        text content "Message body"
        json sources "Array of citation metadata chunks"
        string(100) model_used "e.g. 'openai:gpt-4o-mini' or 'ollama:llama3.1:8b'"
        datetime created_at "Message timestamp (UTC)"
    }
```

---

## 5. Vector Store & RAG Ingestion Pipeline

ChromaDB serves as the semantic index for Lenny's product frameworks:

1. **Ingestion & Chunking**:
   - Transcripts and essays are parsed into semantic chunks using sliding windows (200-500 tokens with 50-token overlap).
   - Provenance metadata is preserved (`title`, `source`, `speaker`, `episode_title`).
2. **Dense Vector Embeddings**:
   - Chunks are vectorized using OpenAI `text-embedding-3-small` (or local `nomic-embed-text` in offline mode).
3. **Retrieval & Relevance Filtering**:
   - On incoming query, the top-k nearest neighbors are fetched via cosine/L2 distance.
   - Chunks failing the semantic threshold (`score < 0.05`) are discarded, triggering graceful fallback heuristics to avoid polluting LLM context with irrelevant noise.

---

## 6. Security & Sandboxing Architecture

To allow users to safely run generated HTML5 and JavaScript mini-tools without risking host compromise:

```mermaid
flowchart TD
    subgraph HostOrigin ["Parent Host Origin (http://localhost:3000)"]
        ParentDOM["Parent DOM & Application State"]
        LocalStorage["Local Storage & Session Tokens"]
        AuthCookies["Authentication Cookies"]
    end

    subgraph SecurityBoundary ["Browser Security Sandbox Boundary"]
        Iframe["<iframe sandbox='allow-scripts'>"]
    end

    subgraph UntrustedOrigin ["Sandboxed Context (Unique / Null Origin)"]
        ArtifactJS["Generated Artifact JavaScript"]
        TailwindCDN["Tailwind CSS CDN Stylesheet"]
        ArtifactDOM["Artifact UI Components"]
    end

    Iframe --> UntrustedOrigin
    ArtifactJS -.->|BLOCKED: SecurityError| ParentDOM
    ArtifactJS -.->|BLOCKED: SecurityError| LocalStorage
    ArtifactJS -.->|BLOCKED: SecurityError| AuthCookies
```

- **Sandbox Restrictions**: The `iframe` is strictly configured with `sandbox="allow-scripts"`.
- **Blocked Privileges**:
  - `allow-same-origin` is omitted, assigning the iframe a unique opaque origin that cannot access parent `window`, `document`, or `localStorage`.
  - `allow-top-navigation` is omitted, preventing the artifact from redirecting the parent page.
  - `allow-popups` and `allow-modals` are omitted, preventing deceptive alerts or popup phishing.
