import React, { useState } from 'react';
import {
  FileCode,
  FileText,
  Copy,
  Check,
  Maximize2,
  Minimize2,
  X,
  Code,
  Eye,
  Layers,
} from 'lucide-react';
import { Artifact } from '../../types';
import { SecureIframeRenderer } from './SecureIframeRenderer';
import { MarkdownRenderer } from './MarkdownRenderer';

interface ArtifactViewerProps {
  artifact: Artifact | null;
  onClose: () => void;
  onToggleFullscreen?: () => void;
  isFullscreen?: boolean;
  artifactsList?: Artifact[];
  onSelectArtifact?: (artifact: Artifact) => void;
}

/**
 * ArtifactViewer renders AI-generated artifacts matching the requested specifications:
 * - Markdown -> Render Formatted (GFM tables, task checklists, callout alerts, typography)
 * - HTML -> Render in Iframe Sandbox (Null origin, CSP, Tailwind CSS CDN, interactive vanilla JS)
 *
 * Integrated into the Split-Screen layout (Chat + Artifact).
 */
export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifact,
  onClose,
  onToggleFullscreen,
  isFullscreen = false,
  artifactsList = [],
  onSelectArtifact,
}) => {
  const [viewMode, setViewMode] = useState<'preview' | 'source'>('preview');
  const [copied, setCopied] = useState(false);

  if (!artifact) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-slate-50 border-l border-slate-200">
        <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-center text-slate-400 mb-3">
          <Layers className="w-7 h-7" />
        </div>
        <h3 className="text-sm font-bold text-slate-800">No Artifact Active</h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1.5 leading-relaxed">
          Ask Lenny to <span className="font-semibold text-slate-700">"create page ..."</span> or <span className="font-semibold text-slate-700">"create spec / checklist ..."</span> to generate an artifact here.
        </p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isHtml = artifact.type === 'html';

  return (
    <div className="flex flex-col h-full bg-slate-50 border-l border-slate-200 overflow-hidden select-none">
      {/* 1. Main Viewer Header */}
      <div className="h-14 px-4 bg-white border-b border-slate-200 flex items-center justify-between shrink-0 shadow-2xs">
        {/* Left: Icon, Title & Badges */}
        <div className="flex items-center space-x-2.5 truncate mr-2">
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center text-white shrink-0 shadow-xs ${
              isHtml ? 'bg-brand-500' : 'bg-emerald-500'
            }`}
          >
            {isHtml ? <FileCode className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
          </div>

          <div className="truncate">
            <h2 className="text-xs font-bold text-slate-900 truncate">
              {artifact.title || (isHtml ? 'Web Component Artifact' : 'Product Specification')}
            </h2>
            <div className="flex items-center space-x-1.5">
              <span
                className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded ${
                  isHtml ? 'bg-brand-50 text-brand-700' : 'bg-emerald-50 text-emerald-700'
                }`}
              >
                {artifact.type}
              </span>
              <span className="text-[10px] text-slate-400 font-medium">
                {isHtml ? 'Iframe Sandbox' : 'Rendered Formatted'}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Controls (Preview vs Source, Copy, Fullscreen, Close) */}
        <div className="flex items-center space-x-1.5 shrink-0">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-medium mr-1">
            <button
              onClick={() => setViewMode('preview')}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] transition ${
                viewMode === 'preview'
                  ? 'bg-white text-slate-800 shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Eye className="w-3 h-3" />
              <span>Preview</span>
            </button>

            <button
              onClick={() => setViewMode('source')}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] transition ${
                viewMode === 'source'
                  ? 'bg-white text-slate-800 shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Code className="w-3 h-3" />
              <span>Source</span>
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition"
            title="Copy Code"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
          </button>

          {/* Fullscreen Toggle */}
          {onToggleFullscreen && (
            <button
              onClick={onToggleFullscreen}
              className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition"
              title={isFullscreen ? 'Exit Fullscreen' : 'Expand Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          )}

          {/* Close Panel Button */}
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
            title="Close Split Screen"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Optional Session Artifacts Quick Bar (if multiple artifacts exist) */}
      {artifactsList.length > 1 && onSelectArtifact && (
        <div className="flex items-center space-x-1 px-4 py-1.5 bg-slate-100/80 border-b border-slate-200/80 overflow-x-auto text-[11px]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1 shrink-0">
            Session Artifacts:
          </span>
          {artifactsList.map((art, idx) => {
            const isSelected = art.content === artifact.content;
            return (
              <button
                key={idx}
                onClick={() => onSelectArtifact(art)}
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold shrink-0 transition flex items-center space-x-1 ${
                  isSelected
                    ? 'bg-brand-500 text-white shadow-2xs'
                    : 'bg-white text-slate-600 hover:bg-slate-200 border border-slate-200'
                }`}
              >
                <span>{art.title || `Artifact #${idx + 1}`}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* 3. Main Viewport */}
      <div className="flex-1 overflow-hidden p-4">
        {viewMode === 'source' ? (
          <div className="h-full bg-slate-900 text-slate-100 rounded-xl p-4 overflow-auto font-mono text-xs shadow-inner leading-relaxed">
            <pre>{artifact.content}</pre>
          </div>
        ) : isHtml ? (
          /* HTML -> Render in Iframe Sandbox */
          <div className="h-full w-full">
            <SecureIframeRenderer
              htmlContent={artifact.content}
              title={artifact.title || 'Interactive Web Artifact'}
              initialHeight="100%"
              allowFullscreen={false}
            />
          </div>
        ) : (
          /* Markdown -> Render Formatted */
          <div className="h-full w-full">
            <MarkdownRenderer
              content={artifact.content}
              title={artifact.title || 'Product Specification'}
            />
          </div>
        )}
      </div>
    </div>
  );
};
