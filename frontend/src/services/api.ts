import { ChatPayload, Conversation, HealthStatus, Message } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignore JSON parse errors on non-json responses
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

  // Chat
  async sendChatMessage(payload: ChatPayload): Promise<Message> {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<Message>(res);
  },

  // Conversations
  async getConversations(): Promise<Conversation[]> {
    const res = await fetch(`${BASE_URL}/conversations`);
    return handleResponse<Conversation[]>(res);
  },

  async getConversation(id: string): Promise<Conversation & { messages: Message[] }> {
    const res = await fetch(`${BASE_URL}/conversations/${id}`);
    return handleResponse<Conversation & { messages: Message[] }>(res);
  },

  async deleteConversation(id: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/conversations/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      throw new Error(`Failed to delete conversation: ${res.statusText}`);
    }
  },
};
