import React from 'react';
import { Header } from './components/Layout/Header';
import { Sidebar } from './components/Layout/Sidebar';
import { ChatContainer } from './components/Chat/ChatContainer';
import { ChatInput } from './components/Chat/ChatInput';
import { ModelSelector } from './components/Chat/ModelSelector';
import { useHealth } from './hooks/useHealth';
import { useChat } from './hooks/useChat';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const { health, loading: healthLoading } = useHealth();
  const {
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
  } = useChat();

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeConversationId}
        onSelect={setActiveConversationId}
        onNewChat={startNewChat}
        onDelete={removeConversation}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <Header health={health} loading={healthLoading} />

        {/* Error Notification Banner */}
        {error && (
          <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 flex items-center space-x-2 text-xs text-rose-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Top Controls Toolbar */}
        <div className="px-6 py-3 border-b border-slate-200/60 bg-white/40 flex items-center justify-between">
          <div className="text-xs font-medium text-slate-500">
            {activeConversationId ? 'Ongoing Discussion' : 'New Session'}
          </div>
          <ModelSelector
            provider={provider}
            setProvider={setProvider}
            model={model}
            setModel={setModel}
          />
        </div>

        {/* Chat Stream View */}
        <ChatContainer
          messages={messages}
          isSending={isSending}
          onPromptClick={sendMessage}
        />

        {/* Bottom Input Area */}
        <div className="p-4 md:p-6 bg-white/80 border-t border-slate-200 backdrop-blur">
          <div className="max-w-4xl mx-auto">
            <ChatInput onSend={sendMessage} disabled={isSending} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
