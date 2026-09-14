import React from 'react';
import {
  Sparkles,
  Database,
  Layers,
  MessageSquarePlus,
  PanelRightOpen,
  PanelRightClose,
  Menu,
} from 'lucide-react';
import { HealthStatus } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface HeaderProps {
  health: HealthStatus | null;
  loading: boolean;
  onNewSession?: () => void;
  onToggleArtifacts?: () => void;
  isArtifactsOpen?: boolean;
  artifactsCount?: number;
  onToggleMobileSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  loading,
  onNewSession,
  onToggleArtifacts,
  isArtifactsOpen = false,
  artifactsCount = 0,
  onToggleMobileSidebar,
}) => {
  return (
    <header className="h-16 border-b border-slate-200 bg-white/90 backdrop-blur px-4 md:px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left Branding & Mobile Sidebar Toggle */}
      <div className="flex items-center space-x-3">
        {onToggleMobileSidebar && (
          <button
            onClick={onToggleMobileSidebar}
            className="md:hidden p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition"
            title="Toggle Sessions Menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20 shrink-0">
          <Sparkles className="w-4 h-4 md:w-5 md:h-5" />
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-slate-900 text-sm md:text-base tracking-tight">
              Lenny Growth Assistant
            </h1>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-brand-100 text-brand-700 px-1.5 py-0.5 rounded hidden sm:inline-block">
              v0.1
            </span>
          </div>
          <p className="text-[11px] text-slate-500 hidden sm:block">
            Product heuristics, growth loops & PMF frameworks
          </p>
        </div>
      </div>

      {/* Right Controls: New Session, Health, and Artifact Panel Toggle */}
      <div className="flex items-center space-x-2 md:space-x-3">
        {/* Quick New Session Button in Header */}
        {onNewSession && (
          <button
            onClick={onNewSession}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition border border-slate-200/80 shadow-xs"
            title="Start fresh conversation"
          >
            <MessageSquarePlus className="w-3.5 h-3.5 text-brand-600" />
            <span className="hidden sm:inline">New Session</span>
          </button>
        )}

        {/* Backend & Vector DB Status */}
        {loading ? (
          <span className="text-[11px] text-slate-400 hidden lg:inline">Connecting...</span>
        ) : health ? (
          <div className="hidden lg:flex items-center space-x-2 border-l border-slate-200 pl-3">
            <div className="flex items-center space-x-1 text-[11px] text-slate-500">
              <Database className="w-3 h-3 text-slate-400" />
              <span>Postgres:</span>
              <StatusBadge status={health.database.status} />
            </div>
            <div className="flex items-center space-x-1 text-[11px] text-slate-500">
              <Layers className="w-3 h-3 text-slate-400" />
              <span>Chroma:</span>
              <StatusBadge status={health.vector_store.status} />
            </div>
          </div>
        ) : null}

        {/* Split Screen Artifact Viewer Toggle Button */}
        {onToggleArtifacts && (
          <button
            onClick={onToggleArtifacts}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition shadow-xs border ${
              isArtifactsOpen
                ? 'bg-brand-50 border-brand-200 text-brand-700'
                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
            }`}
            title={isArtifactsOpen ? 'Hide Artifact (Focus Chat)' : 'Open Split Screen (Chat + Artifact)'}
          >
            {isArtifactsOpen ? (
              <PanelRightClose className="w-4 h-4 text-brand-600" />
            ) : (
              <PanelRightOpen className="w-4 h-4 text-slate-600" />
            )}
            <span className="hidden sm:inline">
              {isArtifactsOpen ? 'Split Screen Active' : 'Split Screen'}
            </span>
            {artifactsCount > 0 && (
              <span className="ml-1 px-1.5 py-0.2 bg-brand-500 text-white rounded-full text-[10px] font-bold">
                {artifactsCount}
              </span>
            )}
          </button>
        )}
      </div>
    </header>
  );
};
