import React, { useState } from 'react';
import {
  Shield,
  ShieldAlert,
  Code,
  Eye,
  Check,
  Copy,
  Info,
  Sparkles,
  FileText,
} from 'lucide-react';
import { SecureRenderingMode } from '../../types';
import { SecureIframeRenderer } from './SecureIframeRenderer';
import { SanitizedHtmlRenderer } from './SanitizedHtmlRenderer';
import { getSecurityPolicyExplanation, ALLOWED_TAGS } from '../../utils/sanitizer';

interface SecureArtifactViewerProps {
  content: string;
  type?: 'html' | 'markdown';
  title?: string;
  initialMode?: SecureRenderingMode;
}

export const SecureArtifactViewer: React.FC<SecureArtifactViewerProps> = ({
  content,
  type = 'html',
  title = 'Generated Artifact',
  initialMode = 'iframe-sandbox',
}) => {
  const [mode, setMode] = useState<SecureRenderingMode>(
    type === 'markdown' ? 'sanitized-dom' : initialMode
  );
  const [showSecurityDetails, setShowSecurityDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const policyInfo = getSecurityPolicyExplanation(mode);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col w-full bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm my-4">
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200 gap-2">
        {/* Title & Type Badge */}
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-brand-500 text-white flex items-center justify-center font-bold text-xs shadow-sm shadow-brand-500/20">
            {type === 'html' ? <Sparkles className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-900">{title}</h3>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono font-medium">
              Format: {type.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex items-center space-x-1 bg-slate-200/70 p-1 rounded-lg text-xs font-medium">
          {type === 'html' && (
            <button
              onClick={() => setMode('iframe-sandbox')}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md transition ${
                mode === 'iframe-sandbox'
                  ? 'bg-white text-slate-800 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-emerald-600" />
              <span>Iframe Sandbox</span>
            </button>
          )}

          <button
            onClick={() => setMode('sanitized-dom')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md transition ${
              mode === 'sanitized-dom'
                ? 'bg-white text-slate-800 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Eye className="w-3.5 h-3.5 text-blue-600" />
            <span>Sanitized HTML</span>
          </button>

          <button
            onClick={() => setMode('source-code')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md transition ${
              mode === 'source-code'
                ? 'bg-white text-slate-800 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Code className="w-3.5 h-3.5 text-slate-600" />
            <span>Source Code</span>
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSecurityDetails(!showSecurityDetails)}
            className={`flex items-center space-x-1 text-xs px-2.5 py-1 rounded-lg border transition ${
              showSecurityDetails
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-100'
            }`}
            title="Inspect security sandbox policy & reasoning"
          >
            <Info className="w-3.5 h-3.5" />
            <span>Security Policy</span>
          </button>

          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-xs px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Security Explanation Accordion Panel */}
      {showSecurityDetails && (
        <div className="bg-slate-900 text-slate-100 p-4 border-b border-slate-800 text-xs animate-in fade-in duration-150">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
              <span className="font-semibold text-white">Active Defense Architecture: {policyInfo.mode.toUpperCase()}</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">Zero-Trust Untrusted Content Boundary</span>
          </div>

          <p className="text-slate-300 leading-relaxed mb-4 text-[11px]">
            {policyInfo.reasoning}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px]">
            {/* Allowed Elements */}
            <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700 space-y-1.5">
              <div className="text-emerald-400 font-semibold flex items-center space-x-1.5">
                <Check className="w-3.5 h-3.5" />
                <span>Allowed Tags & Capabilities</span>
              </div>
              <p className="text-slate-300 text-[10px] leading-normal font-mono">
                {mode === 'iframe-sandbox'
                  ? 'All standard HTML5, Tailwind CSS, and vanilla JS widgets inside unique opaque (null) origin.'
                  : `Whitelisted safe semantic tags (${ALLOWED_TAGS.length}): h1-h6, p, div, span, table, a, img, button, input (range/checkbox).`}
              </p>
            </div>

            {/* Blocked Elements & Scripts */}
            <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700 space-y-1.5">
              <div className="text-rose-400 font-semibold flex items-center space-x-1.5">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Blocked Scripts & Vectors</span>
              </div>
              <ul className="text-slate-300 text-[10px] space-y-0.5 list-disc list-inside">
                {policyInfo.blockedElements.slice(0, 4).map((item, idx) => (
                  <li key={idx} className="truncate">{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Main Rendering Viewport */}
      <div className="p-4 bg-slate-50/50">
        {mode === 'iframe-sandbox' && (
          <SecureIframeRenderer htmlContent={content} title={title} />
        )}

        {mode === 'sanitized-dom' && (
          <SanitizedHtmlRenderer htmlContent={content} title={title} />
        )}

        {mode === 'source-code' && (
          <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto text-slate-100 font-mono text-xs max-h-96">
            <pre>{content}</pre>
          </div>
        )}
      </div>
    </div>
  );
};
