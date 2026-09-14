import React, { useState, useRef } from 'react';
import { Shield, RefreshCw, Maximize2, Minimize2, AlertTriangle } from 'lucide-react';
import { buildSandboxedSrcDoc, SANDBOX_ATTRIBUTE_VALUE } from '../../utils/sanitizer';

interface SecureIframeRendererProps {
  htmlContent: string;
  title?: string;
  initialHeight?: string;
  allowFullscreen?: boolean;
}

/**
 * SecureIframeRenderer renders untrusted HTML inside a strictly sandboxed iframe.
 *
 * Security Architecture:
 * 1. sandbox="allow-scripts": Permits JavaScript for interactive widgets/calculators.
 * 2. NO allow-same-origin: Treats document as unique opaque null origin.
 *    - Cannot read localStorage, cookies, or auth headers.
 *    - Cannot access window.parent or window.top DOM.
 * 3. NO allow-top-navigation: Prevents phishing redirects.
 * 4. Content-Security-Policy: Blocks untrusted network connects and frames.
 */
export const SecureIframeRenderer: React.FC<SecureIframeRendererProps> = ({
  htmlContent,
  title = 'Interactive Web Artifact',
  initialHeight = '480px',
  allowFullscreen = true,
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [key, setKey] = useState(0);

  const sandboxedSrcDoc = React.useMemo(() => {
    try {
      return buildSandboxedSrcDoc(htmlContent);
    } catch (err) {
      setHasError(true);
      return '';
    }
  }, [htmlContent]);

  const handleReload = () => {
    setIsLoading(true);
    setKey((prev) => prev + 1);
  };

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
  };

  return (
    <div
      className={`flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm transition-all duration-200 ${
        isFullscreen ? 'fixed inset-4 z-50 shadow-2xl border-slate-300' : 'w-full my-3'
      }`}
    >
      {/* Sandbox Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs text-slate-600">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 font-medium text-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="truncate max-w-xs">{title}</span>
          </div>

          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold">
            <Shield className="w-3 h-3 text-emerald-600" />
            <span>Iframe Sandbox (Null Origin)</span>
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-1.5">
          <button
            onClick={handleReload}
            title="Reload artifact"
            className="p-1 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {allowFullscreen && (
            <button
              onClick={toggleFullscreen}
              title={isFullscreen ? 'Exit Fullscreen' : 'Expand Fullscreen'}
              className="p-1 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition"
            >
              {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Frame Container */}
      <div className="relative w-full bg-slate-100 flex-1" style={{ height: isFullscreen ? 'calc(100% - 41px)' : initialHeight }}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-50/80 z-10">
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <RefreshCw className="w-4 h-4 animate-spin text-brand-500" />
              <span>Booting sandbox environment...</span>
            </div>
          </div>
        )}

        {hasError ? (
          <div className="p-6 text-center text-xs text-rose-600 flex flex-col items-center justify-center h-full">
            <AlertTriangle className="w-6 h-6 mb-2 text-rose-500" />
            <span>Failed to render sandboxed document.</span>
          </div>
        ) : (
          <iframe
            key={key}
            ref={iframeRef}
            title={title}
            srcDoc={sandboxedSrcDoc}
            sandbox={SANDBOX_ATTRIBUTE_VALUE}
            loading="lazy"
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setIsLoading(false);
              setHasError(true);
            }}
            className="w-full h-full border-0 bg-white"
          />
        )}
      </div>

      {/* Security Footer Details */}
      <div className="px-4 py-1.5 bg-slate-50/60 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <span>Protected context: Cookies & parent DOM inaccessible</span>
        <span className="font-mono text-[10px]">sandbox="{SANDBOX_ATTRIBUTE_VALUE}"</span>
      </div>
    </div>
  );
};
