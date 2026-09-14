import React, { useMemo, useState } from 'react';
import { FileText, Copy, Check, Info, BookOpen } from 'lucide-react';
import { parseMarkdownToHtml } from '../../utils/markdown';
import { sanitizeHtml } from '../../utils/sanitizer';

interface MarkdownRendererProps {
  content: string;
  title?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  title = 'Markdown Specification / Document',
}) => {
  const [copied, setCopied] = useState(false);

  // Convert and sanitize markdown
  const formattedHtml = useMemo(() => {
    const rawHtml = parseMarkdownToHtml(content);
    return sanitizeHtml(rawHtml);
  }, [content]);

  // Statistics
  const { wordCount, readTimeMins } = useMemo(() => {
    const words = content.trim().split(/\s+/).filter(Boolean).length;
    return {
      wordCount: words,
      readTimeMins: Math.max(1, Math.ceil(words / 200)),
    };
  }, [content]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col w-full h-full bg-white rounded-xl overflow-hidden border border-slate-200 shadow-xs">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-5 py-3 bg-slate-50 border-b border-slate-200 text-xs">
        <div className="flex items-center space-x-2.5">
          <div className="w-6 h-6 rounded-lg bg-emerald-500 text-white flex items-center justify-center font-bold text-xs shadow-xs">
            <FileText className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-semibold text-slate-800 truncate max-w-sm block">{title}</span>
            <span className="text-[10px] text-slate-400 font-mono">
              {wordCount} words • ~{readTimeMins} min read
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold">
            <BookOpen className="w-3 h-3 text-emerald-600" />
            <span>Rendered GFM</span>
          </span>

          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 rounded-lg text-xs font-medium transition"
            title="Copy Raw Markdown"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Rendered Markdown Body */}
      <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-white selection:bg-brand-100">
        <div
          className="markdown-body max-w-3xl mx-auto space-y-4 text-slate-800 text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: formattedHtml }}
        />
      </div>

      {/* Footer Info */}
      <div className="px-5 py-2 bg-slate-50/80 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <span>GitHub Flavored Markdown (Tables, Checklists, & Alert Callouts Active)</span>
        <span className="font-mono text-[10px]">GFM Parser</span>
      </div>
    </div>
  );
};
