import { ChatPayload, Conversation, HealthStatus, Message, Artifact } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.error) {
        errorMessage = errorData.error;
      } else if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string'
          ? errorData.detail
          : JSON.stringify(errorData.detail);
      }
    } catch {
      // Non-JSON response
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export const api = {
  // System Health
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse<HealthStatus>(res);
  },

  // Chat Endpoint
  async sendChatMessage(payload: ChatPayload): Promise<Message> {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: payload.message,
        session_id: payload.conversation_id,
        provider: payload.provider,
        model: payload.model,
        temperature: payload.temperature,
        top_k_sources: payload.top_k_sources,
      }),
    });
    const data = await handleResponse<any>(res);
    return {
      id: data.message_id || `msg-${Date.now()}`,
      conversation_id: data.session_id,
      role: 'assistant',
      content: data.content,
      sources: data.sources || [],
      model_used: `${data.provider}:${data.model}`,
      created_at: data.created_at || new Date().toISOString(),
    };
  },

  // Sessions / Conversations
  async getConversations(): Promise<Conversation[]> {
    const res = await fetch(`${BASE_URL}/chat/sessions`);
    const data = await handleResponse<any[]>(res);
    return data.map((item) => ({
      id: item.session_id || item.id,
      title: item.title || 'Growth Advisory Session',
      created_at: item.created_at,
      updated_at: item.updated_at || item.created_at,
    }));
  },

  async getConversation(id: string): Promise<Conversation & { messages: Message[] }> {
    const res = await fetch(`${BASE_URL}/chat/sessions/${id}`);
    const data = await handleResponse<any>(res);
    const messages: Message[] = (data.messages || []).map((m: any) => ({
      id: m.id || `msg-${Date.now()}`,
      conversation_id: data.session_id || id,
      role: m.role,
      content: m.content,
      sources: m.sources || [],
      model_used: m.model_used,
      created_at: m.created_at || new Date().toISOString(),
    }));

    return {
      id: data.session_id || id,
      title: data.title || 'Growth Session',
      created_at: data.created_at || new Date().toISOString(),
      updated_at: data.updated_at || new Date().toISOString(),
      messages,
    };
  },

  async deleteConversation(id: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/chat/sessions/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      throw new Error(`Failed to delete session: ${res.statusText}`);
    }
  },

  // Artifact Generator Endpoint
  async generateArtifact(
    prompt: string,
    outputType?: 'html' | 'markdown',
    context?: string,
    provider?: string,
    model?: string
  ): Promise<Artifact> {
    const res = await fetch(`${BASE_URL}/artifacts/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        output_type: outputType,
        context,
        provider,
        model,
      }),
    });
    const data = await handleResponse<any>(res);
    return {
      type: data.type,
      content: data.content,
      title: prompt,
    };
  },

  // Agent Router Endpoint
  async routeAgent(prompt: string, sessionId?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/router`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        session_id: sessionId,
      }),
    });
    return handleResponse<any>(res);
  },
};
