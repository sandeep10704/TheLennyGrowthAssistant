import { useState, useEffect, useCallback } from 'react';
import { Conversation, Message } from '../types';
import { api } from '../services/api';

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [provider, setProvider] = useState<'openai' | 'ollama'>('openai');
  const [model, setModel] = useState<string>('gpt-4o');
  const [error, setError] = useState<string | null>(null);

  // Load conversations list
  const loadConversations = useCallback(async () => {
    try {
      const list = await api.getConversations();
      setConversations(list);
    } catch (err: any) {
      console.warn('Failed to load conversations:', err.message);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load active conversation messages
  useEffect(() => {
    if (!activeConversationId) {
      setMessages([]);
      return;
    }

    async function loadActiveMessages() {
      try {
        const conv = await api.getConversation(activeConversationId!);
        setMessages(conv.messages || []);
      } catch (err: any) {
        setError(err.message || 'Failed to load conversation');
      }
    }

    loadActiveMessages();
  }, [activeConversationId]);

  // Send a message
  const sendMessage = async (content: string) => {
    if (!content.trim() || isSending) return;

    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConversationId || undefined,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsSending(true);
    setError(null);

    try {
      const response = await api.sendChatMessage({
        message: content,
        conversation_id: activeConversationId || undefined,
        provider,
        model,
      });

      // Update active conversation id if it was newly created
      if (!activeConversationId && response.conversation_id) {
        setActiveConversationId(response.conversation_id);
      }

      setMessages((prev) => [...prev, response]);
      await loadConversations();
    } catch (err: any) {
      setError(err.message || 'Failed to get response');
    } finally {
      setIsSending(false);
    }
  };

  const startNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setError(null);
  };

  const removeConversation = async (id: string) => {
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        startNewChat();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete conversation');
    }
  };

  return {
    conversations,
    activeConversationId,
    setActiveConversationId,
    messages,
    isSending,
    provider,
    setProvider,
    model,
    setModel,
    error,
    sendMessage,
    startNewChat,
    removeConversation,
  };
}
