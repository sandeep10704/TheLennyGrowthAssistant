import React from 'react';
import { Sparkles, Database, Layers } from 'lucide-react';
import { HealthStatus } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface HeaderProps {
  health: HealthStatus | null;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, loading }) => {
  return (
    <header className="h-16 border-b border-slate-200 bg-white/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-slate-900 text-lg tracking-tight">Lenny Growth Assistant</h1>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-brand-100 text-brand-700 px-1.5 py-0.5 rounded">
              v0.1
            </span>
          </div>
          <p className="text-xs text-slate-500">Product heuristics, growth loops & PMF frameworks</p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {loading ? (
          <span className="text-xs text-slate-400">Connecting...</span>
        ) : health ? (
          <div className="hidden sm:flex items-center space-x-2">
            <div className="flex items-center space-x-1 text-xs text-slate-500">
              <Database className="w-3.5 h-3.5 text-slate-400" />
              <span>Postgres:</span>
              <StatusBadge status={health.database.status} />
            </div>
            <div className="flex items-center space-x-1 text-xs text-slate-500">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>Chroma:</span>
              <StatusBadge status={health.vector_store.status} />
            </div>
          </div>
        ) : null}
      </div>
    </header>
  );
};
