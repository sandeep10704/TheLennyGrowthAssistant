import React from 'react';

interface StatusBadgeProps {
  status: 'healthy' | 'degraded' | 'unavailable' | string;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const isHealthy = status === 'healthy' || status === 'ready';
  const isDegraded = status === 'degraded' || status === 'unconfigured_api_key';

  return (
    <div className="flex items-center space-x-1.5 text-xs font-medium px-2 py-0.5 rounded-full border">
      <span
        className={`w-2 h-2 rounded-full ${
          isHealthy
            ? 'bg-emerald-500 animate-pulse'
            : isDegraded
            ? 'bg-amber-500'
            : 'bg-rose-500'
        }`}
      />
      <span className="capitalize text-slate-700">
        {label ? `${label}: ` : ''}
        {status}
      </span>
    </div>
  );
};
