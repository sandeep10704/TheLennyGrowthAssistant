import React from 'react';
import { MessageSquarePlus, Trash2, BookOpen, MessageSquare, Cpu, X } from 'lucide-react';
import { Conversation } from '../../types';

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  onCloseMobile,
}) => {
  return (
    <aside className="w-64 md:w-72 border-r border-slate-200 bg-white flex flex-col h-full shrink-0 select-none">
      {/* Top Header for Mobile Drawer */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <button
          onClick={() => {
            onNewChat();
            if (onCloseMobile) onCloseMobile();
          }}
          className="flex-1 flex items-center justify-center space-x-2 bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold py-2.5 px-4 rounded-xl shadow-sm transition"
        >
          <MessageSquarePlus className="w-4 h-4" />
          <span>New Session</span>
        </button>

        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="md:hidden ml-2 p-2 text-slate-400 hover:text-slate-600 rounded-lg"
            title="Close Drawer"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Recent Sessions ({conversations?.length || 0})
        </div>

        {(conversations || []).length === 0 ? (
          <div className="text-xs text-slate-400 px-3 py-6 text-center leading-relaxed">
            No previous sessions.<br />Ask a question or request an artifact to begin!
          </div>
        ) : (
          (conversations || []).map((conv) => {
            const isActive = conv?.id === activeId;
            return (
              <div
                key={conv?.id}
                onClick={() => {
                  if (conv?.id) {
                    onSelect(conv.id);
                    if (onCloseMobile) onCloseMobile();
                  }
                }}
                className={`group flex items-center justify-between px-3 py-2.5 text-xs rounded-xl cursor-pointer transition ${
                  isActive
                    ? 'bg-brand-50 text-brand-900 font-semibold shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate mr-2">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-brand-500' : 'text-slate-400'}`} />
                  <span className="truncate">{conv?.title || 'Growth Session'}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (conv?.id) onDelete(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-500 transition rounded"
                  title="Delete session"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Info Links */}
      <div className="p-4 border-t border-slate-100 text-[11px] text-slate-500 space-y-2 bg-slate-50/50">
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center space-x-2 text-slate-600 hover:text-brand-600 transition font-medium"
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Interactive Swagger Docs</span>
        </a>
        <div className="flex items-center space-x-1.5 text-slate-400 text-[10px]">
          <Cpu className="w-3 h-3" />
          <span>PostgreSQL + ChromaDB + Docker</span>
        </div>
      </div>
    </aside>
  );
};
