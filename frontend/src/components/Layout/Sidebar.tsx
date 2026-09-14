import React from 'react';
import { MessageSquarePlus, Trash2, BookOpen, MessageSquare, Cpu } from 'lucide-react';
import { Conversation } from '../../types';

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
}) => {
  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col h-full">
      {/* Action button */}
      <div className="p-4 border-b border-slate-100">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 bg-brand-500 hover:bg-brand-600 text-white font-medium py-2.5 px-4 rounded-xl shadow-sm transition duration-150 ease-in-out"
        >
          <MessageSquarePlus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Recent Chats
        </div>

        {conversations.length === 0 ? (
          <div className="text-xs text-slate-400 px-3 py-4 text-center">
            No chats yet. Start asking growth questions!
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === activeId;
            return (
              <div
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`group flex items-center justify-between px-3 py-2 text-sm rounded-lg cursor-pointer transition ${
                  isActive
                    ? 'bg-brand-50 text-brand-900 font-medium'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate mr-2">
                  <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? 'text-brand-500' : 'text-slate-400'}`} />
                  <span className="truncate">{conv.title}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-500 transition rounded"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Links */}
      <div className="p-4 border-t border-slate-200 text-xs text-slate-500 space-y-2">
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center space-x-2 hover:text-brand-600 transition"
        >
          <BookOpen className="w-4 h-4" />
          <span>Swagger API Docs</span>
        </a>
        <div className="flex items-center space-x-2 text-slate-400">
          <Cpu className="w-4 h-4" />
          <span>PostgreSQL + Chroma + FastAPI</span>
        </div>
      </div>
    </aside>
  );
};
