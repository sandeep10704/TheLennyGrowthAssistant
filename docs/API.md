# 📡 Lenny Growth Assistant API Specification

Base URL: `http://localhost:8000/api/v1`  
Interactive Documentation (Swagger): `http://localhost:8000/docs`  
Alternative Documentation (ReDoc): `http://localhost:8000/redoc`

---

## 1. System Health

### `GET /health`
Verifies operational status of the backend, database connection, vector store, and LLM provider.

#### Response `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "database": {
    "status": "healthy",
    "details": { "url": "localhost:5432/lenny_growth" }
  },
  "vector_store": {
    "status": "healthy",
    "details": {
      "collection": "lenny_growth_knowledge",
      "document_count": 6
    }
  },
  "llm": {
    "status": "ready",
    "details": {
      "provider": "openai",
      "configured": true,
      "default_model": "gpt-4o"
    }
  }
}
```

---

## 2. Chat & Conversations

### `POST /chat`
Sends a prompt to Lenny Growth Assistant. Performs semantic retrieval against ChromaDB, generates advice via LLM, and persists history.

#### Request Body
```json
{
  "message": "How do I know when our startup has reached Product-Market Fit?",
  "conversation_id": "optional-uuid-to-continue-chat",
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.7,
  "top_k_sources": 4
}
```

#### Response `200 OK`
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "c9a646d3-9c61-4cc9-bc56-4c4f9a0c0001",
  "role": "assistant",
  "content": "Product-Market Fit (PMF) is best identified by three primary signals...",
  "sources": [
    {
      "title": "Finding Product-Market Fit (PMF)",
      "source": "Lenny's Newsletter: The PMF Guide",
      "content": "Product-Market Fit (PMF) is not a single point in time...",
      "relevance_score": 0.8921,
      "metadata": { "source": "Lenny's Newsletter: The PMF Guide" }
    }
  ],
  "provider": "openai",
  "model": "gpt-4o",
  "created_at": "2026-09-14T12:00:00Z"
}
```

### `GET /conversations`
Retrieves a paginated list of chat conversations.

#### Query Parameters
- `limit` (int, default: 20)

#### Response `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "How do I know when our startup has reach...",
    "created_at": "2026-09-14T12:00:00Z",
    "updated_at": "2026-09-14T12:05:00Z"
  }
]
```

### `GET /conversations/{conversation_id}`
Fetches conversation metadata and full message history.

#### Response `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "PMF Discussion",
  "created_at": "2026-09-14T12:00:00Z",
  "updated_at": "2026-09-14T12:05:00Z",
  "messages": [
    {
      "id": "msg-001",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "How do I know if I have PMF?",
      "sources": null,
      "model_used": null,
      "created_at": "2026-09-14T12:00:00Z"
    }
  ]
}
```

### `DELETE /conversations/{conversation_id}`
Deletes the conversation and cascades to delete all contained messages.

#### Response `204 No Content`

---

## 3. Knowledge Base & Vector Indexing

### `POST /documents/ingest`
Ingests custom text articles, notes, or playbooks into ChromaDB.

#### Request Body
```json
{
  "documents": [
    {
      "title": "B2B SaaS Onboarding Heuristics",
      "source": "Growth Library",
      "content": "Time-to-value is the primary driver of 30-day user activation...",
      "metadata": { "category": "onboarding", "tier": "enterprise" }
    }
  ]
}
```

#### Response `201 Created`
```json
{
  "status": "success",
  "chunks_indexed": 1,
  "message": "Successfully indexed 1 document chunks into vector database."
}
```

### `POST /documents/search`
Direct vector similarity search test endpoint.

#### Request Body
```json
{
  "query": "Sean Ellis survey benchmark",
  "n_results": 3
}
```

#### Response `200 OK`
```json
[
  {
    "id": "seed_1",
    "content": "Product-Market Fit (PMF) is not a single point...",
    "metadata": { "title": "Finding Product-Market Fit (PMF)" },
    "distance": 0.845
  }
]
```
