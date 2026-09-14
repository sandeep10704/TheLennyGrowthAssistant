export interface SourceCitation {
  title?: string;
  source?: string;
  content: string;
  relevance_score?: number;
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  conversation_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  model_used?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ComponentStatus {
  status: string;
  details?: Record<string, any>;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  version: string;
  environment: string;
  database: ComponentStatus;
  vector_store: ComponentStatus;
  llm: ComponentStatus;
}

export interface ChatPayload {
  message: string;
  conversation_id?: string;
  provider?: 'openai' | 'ollama';
  model?: string;
  temperature?: number;
  top_k_sources?: number;
}
