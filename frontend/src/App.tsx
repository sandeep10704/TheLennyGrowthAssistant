import React, { useState, useEffect } from 'react';
import { Header } from './components/Layout/Header';
import { Sidebar } from './components/Layout/Sidebar';
import { ChatContainer } from './components/Chat/ChatContainer';
import { ChatInput } from './components/Chat/ChatInput';
import { ModelSelector } from './components/Chat/ModelSelector';
import { ArtifactViewer } from './components/Artifact';
import { useHealth } from './hooks/useHealth';
import { useChat } from './hooks/useChat';
import { Artifact } from './types';
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

  // Split-Screen Artifact State
  const [isArtifactOpen, setIsArtifactOpen] = useState(false);
  const [isFullscreenArtifact, setIsFullscreenArtifact] = useState(false);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [artifactsHistory, setArtifactsHistory] = useState<Artifact[]>([]);

  // Mobile Navigation Drawer State
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Auto-detect artifacts generated in assistant messages
  useEffect(() => {
    messages.forEach((msg) => {
      if (msg.role !== 'assistant') return;

      // 1. Extract HTML artifact
      const htmlMatch =
        msg.content.match(/```(?:html)?\s*(<!DOCTYPE html[\s\S]+?|<html>[\s\S]+?)```/i) ||
        msg.content.match(/(<!DOCTYPE html[\s\S]+?<\/html>)/i);
      if (htmlMatch) {
        const content = htmlMatch[1].trim();
        setArtifactsHistory((prev) => {
          if (prev.some((a) => a.content === content)) return prev;
          const newArt: Artifact = {
            type: 'html',
            content,
            title: 'Interactive Web Tool',
          };
          if (!activeArtifact) {
            setActiveArtifact(newArt);
            setIsArtifactOpen(true);
          }
          return [newArt, ...prev];
        });
      }

      // 2. Extract Markdown artifact (tables, checklists, or specs)
      const mdMatch = msg.content.match(/```(?:markdown|md)\s*([\s\S]+?)```/i);
      if (
        mdMatch &&
        (mdMatch[1].includes('|') || mdMatch[1].includes('- [ ]') || mdMatch[1].includes('# '))
      ) {
        const content = mdMatch[1].trim();
        setArtifactsHistory((prev) => {
          if (prev.some((a) => a.content === content)) return prev;
          const newArt: Artifact = {
            type: 'markdown',
            content,
            title: 'Product Playbook / Spec',
          };
          if (!activeArtifact) {
            setActiveArtifact(newArt);
            setIsArtifactOpen(true);
          }
          return [newArt, ...prev];
        });
      }
    });
  }, [messages, activeArtifact]);

  const handleOpenArtifact = (artifact: Artifact) => {
    setActiveArtifact(artifact);
    setIsArtifactOpen(true);
  };

  const handleToggleSplitScreen = () => {
    if (!isArtifactOpen && !activeArtifact && artifactsHistory.length > 0) {
      setActiveArtifact(artifactsHistory[0]);
    }
    setIsArtifactOpen(!isArtifactOpen);
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans relative">
      {/* 1. Left Sidebar Navigation (Desktop Static + Mobile Drawer) */}
      {/* Mobile Drawer Backdrop */}
      {isMobileSidebarOpen && (
        <div
          onClick={() => setIsMobileSidebarOpen(false)}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-30 md:hidden transition-opacity duration-200"
        />
      )}

      <div
        className={`fixed inset-y-0 left-0 z-40 md:static md:z-auto transition-transform duration-200 ease-in-out ${
          isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <Sidebar
          conversations={conversations}
          activeId={activeConversationId}
          onSelect={(id) => {
            setActiveConversationId(id);
            setIsMobileSidebarOpen(false);
          }}
          onNewChat={() => {
            startNewChat();
            setIsMobileSidebarOpen(false);
          }}
          onDelete={removeConversation}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
        />
      </div>

      {/* 2. Main Workspace Layout Area (Split Screen: Chat + Artifact) */}
      <div className="flex-1 flex h-full overflow-hidden min-w-0">
        {/* Left Pane: Chat Interface */}
        <div
          className={`flex flex-col h-full overflow-hidden transition-all duration-300 ease-in-out ${
            isArtifactOpen
              ? 'w-full lg:w-1/2 xl:w-[50%] border-r border-slate-200 shrink-0'
              : 'w-full'
          }`}
        >
          {/* Header */}
          <Header
            health={health}
            loading={healthLoading}
            onNewSession={startNewChat}
            onToggleArtifacts={handleToggleSplitScreen}
            isArtifactsOpen={isArtifactOpen}
            artifactsCount={artifactsHistory.length}
            onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
          />

          {/* Error Banner */}
          {error && (
            <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 flex items-center space-x-2 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Top Controls Toolbar: Session Indicator & Model Selector */}
          <div className="px-4 md:px-6 py-2.5 border-b border-slate-200/70 bg-white/50 backdrop-blur flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-medium text-slate-500">
              <span className="w-2 h-2 rounded-full bg-brand-500"></span>
              <span>{activeConversationId ? 'Active Discussion Session' : 'New Advisory Session'}</span>
            </div>

            <ModelSelector
              provider={provider}
              setProvider={setProvider}
              model={model}
              setModel={setModel}
            />
          </div>

          {/* Chat Timeline Stream */}
          <ChatContainer
            messages={messages}
            isSending={isSending}
            onPromptClick={sendMessage}
            onOpenArtifact={handleOpenArtifact}
          />

          {/* Bottom Input Area */}
          <div className="p-4 md:p-6 bg-white/90 border-t border-slate-200/80 backdrop-blur">
            <div className="max-w-3xl mx-auto">
              <ChatInput onSend={sendMessage} disabled={isSending} />
            </div>
          </div>
        </div>

        {/* Right Pane: Split-Screen Artifact Viewer (Desktop Side-by-Side) */}
        {isArtifactOpen && (
          <div
            className={`hidden lg:flex flex-col flex-1 h-full min-w-0 bg-slate-50 transition-all duration-300 ease-in-out ${
              isFullscreenArtifact ? 'fixed inset-0 z-50 bg-white' : ''
            }`}
          >
            <ArtifactViewer
              artifact={activeArtifact}
              onClose={() => setIsArtifactOpen(false)}
              onToggleFullscreen={() => setIsFullscreenArtifact(!isFullscreenArtifact)}
              isFullscreen={isFullscreenArtifact}
              artifactsList={artifactsHistory}
              onSelectArtifact={setActiveArtifact}
            />
          </div>
        )}

        {/* Mobile & Tablet (<lg) Slide-Over Viewport */}
        {isArtifactOpen && (
          <div className="lg:hidden fixed inset-0 z-50 bg-white flex flex-col animate-in slide-in-from-right duration-200">
            <ArtifactViewer
              artifact={activeArtifact}
              onClose={() => setIsArtifactOpen(false)}
              artifactsList={artifactsHistory}
              onSelectArtifact={setActiveArtifact}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
