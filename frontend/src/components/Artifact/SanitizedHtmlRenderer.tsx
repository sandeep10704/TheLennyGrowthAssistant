import React, { useMemo } from 'react';
import { ShieldCheck, Info } from 'lucide-react';
import { sanitizeHtml, ALLOWED_TAGS } from '../../utils/sanitizer';

interface SanitizedHtmlRendererProps {
  htmlContent: string;
  title?: string;
  maxHeight?: string;
}

/**
 * SanitizedHtmlRenderer safely parses and sanitizes untrusted HTML using DOMPurify.
 *
 * Security Architecture:
 * 1. Strict Tag Whitelist: Permits only semantic presentation and structure tags.
 * 2. Blocked Scripts: Completely strips <script>, <object>, <iframe>, and all on* inline event handlers.
 * 3. Reverse Tabnabbing Protection: Automatically forces target="_blank" and rel="noopener noreferrer".
 * 4. XSS Prevention: Neutralizes javascript: and malicious pseudo-protocol injection.
 */
export const SanitizedHtmlRenderer: React.FC<SanitizedHtmlRendererProps> = ({
  htmlContent,
  title = 'Sanitized Document View',
  maxHeight = '500px',
}) => {
  const { cleanHtml, scriptsDetected } = useMemo(() => {
    const rawHasScript = /<script\b|javascript:|onerror=|onload=/i.test(htmlContent);
    const sanitized = sanitizeHtml(htmlContent);
    return {
      cleanHtml: sanitized,
      scriptsDetected: rawHasScript,
    };
  }, [htmlContent]);

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm my-3 w-full">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs text-slate-600">
        <div className="flex items-center space-x-2">
          <span className="font-medium text-slate-800 truncate max-w-xs">{title}</span>
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-semibold">
            <ShieldCheck className="w-3 h-3 text-blue-600" />
            <span>DOMPurify Sanitized</span>
          </span>
        </div>

        <span className="text-[11px] text-slate-400">
          {ALLOWED_TAGS.length} Allowed Tags
        </span>
      </div>

      {/* Script Stripping Warning Banner */}
      {scriptsDetected && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center space-x-2 text-[11px] text-amber-800">
          <Info className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span>
            Active scripts and inline handlers were stripped from this document to prevent XSS attacks.
          </span>
        </div>
      )}

      {/* Sanitized Content Body */}
      <div
        className="p-6 overflow-y-auto prose prose-slate max-w-none text-sm leading-relaxed"
        style={{ maxHeight }}
        dangerouslySetInnerHTML={{ __html: cleanHtml }}
      />

      {/* Security Footer Details */}
      <div className="px-4 py-1.5 bg-slate-50/60 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <span>XSS Vector Defense Active (Scripts, Iframes, & On* Event Handlers Purged)</span>
        <span className="font-mono text-[10px]">DOMPurify v3</span>
      </div>
    </div>
  );
};
