import React, { useState, useMemo } from 'react';
import { Sparkles, User, ChevronDown, ChevronUp, BookOpen, ExternalLink } from 'lucide-react';
import { Message, Artifact } from '../../types';
import { SecureArtifactViewer } from '../Artifact';

interface MessageBubbleProps {
  message: Message;
  onOpenArtifact?: (artifact: Artifact) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onOpenArtifact }) => {
  const isUser = message.role === 'user';
  const [sourcesOpen, setSourcesOpen] = useState(false);

  // Detect embedded artifacts in assistant messages
  const { textContent, artifact } = useMemo(() => {
    if (isUser) {
      return { textContent: message.content, artifact: null };
    }

    // 1. Check for HTML code block ```html <!DOCTYPE ...> ```
    const fencedHtml = message.content.match(/```(?:html)?\s*(<!DOCTYPE html[\s\S]+?|<html>[\s\S]+?)```/i);
    if (fencedHtml) {
      const code = fencedHtml[1].trim();
      const cleanText = message.content.replace(fencedHtml[0], '').trim();
      return {
        textContent: cleanText,
        artifact: { type: 'html' as const, content: code, title: 'Interactive Web Tool' },
      };
    }

    // 2. Check for standalone <!DOCTYPE html> ... </html>
    const rawDocMatch = message.content.match(/(<!DOCTYPE html[\s\S]+?<\/html>)/i);
    if (rawDocMatch) {
      const code = rawDocMatch[1].trim();
      const cleanText = message.content.replace(rawDocMatch[0], '').trim();
      return {
        textContent: cleanText,
        artifact: { type: 'html' as const, content: code, title: 'Interactive Web Tool' },
      };
    }

    // 3. Check for Markdown code block containing tables or checklists
    const mdBlockMatch = message.content.match(/```(?:markdown|md)\s*([\s\S]+?)```/i);
    if (mdBlockMatch && (mdBlockMatch[1].includes('|') || mdBlockMatch[1].includes('- [ ]') || mdBlockMatch[1].includes('# '))) {
      const code = mdBlockMatch[1].trim();
      const cleanText = message.content.replace(mdBlockMatch[0], '').trim();
      return {
        textContent: cleanText,
        artifact: { type: 'markdown' as const, content: code, title: 'Product Playbook / Spec' },
      };
    }

    return { textContent: message.content, artifact: null };
  }, [message.content, isUser]);

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex max-w-[85%] md:max-w-[75%] space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-semibold ${
            isUser
              ? 'bg-slate-800 text-white shadow-sm'
              : 'bg-brand-500 text-white shadow-sm shadow-brand-500/20'
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
        </div>

        {/* Message Content Body */}
        <div className="flex flex-col space-y-2 flex-1 min-w-0">
          {textContent && (
            <div
              className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                isUser
                  ? 'bg-slate-900 text-white rounded-tr-sm shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm'
              }`}
            >
              {textContent}
            </div>
          )}

          {/* Secure Interactive Artifact Sandbox / Viewer */}
          {artifact && (
            <div className="relative">
              <SecureArtifactViewer
                content={artifact.content}
                type={artifact.type}
                title={artifact.title}
              />
              {onOpenArtifact && (
                <div className="flex justify-end mt-1">
                  <button
                    onClick={() => onOpenArtifact(artifact)}
                    className="inline-flex items-center space-x-1 text-[11px] text-brand-600 hover:text-brand-700 font-medium px-2 py-0.5 rounded hover:bg-brand-50 transition"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>Open in Artifact Studio Panel</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Source Citations for Assistant Responses */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs">
              <button
                onClick={() => setSourcesOpen(!sourcesOpen)}
                className="flex items-center justify-between w-full text-slate-600 hover:text-slate-900 font-medium"
              >
                <div className="flex items-center space-x-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-brand-500" />
                  <span>Referenced Knowledge Sources ({message.sources.length})</span>
                </div>
                {sourcesOpen ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>

              {sourcesOpen && (
                <div className="mt-2.5 space-y-2 border-t border-slate-200/60 pt-2">
                  {message.sources.map((src, idx) => (
                    <div key={idx} className="bg-white p-2.5 rounded-lg border border-slate-100 space-y-1 shadow-2xs">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-slate-700">
                        <span>{src.title || `Source #${idx + 1}`}</span>
                        {src.relevance_score !== undefined && (
                          <span className="text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-1.5 py-0.2 rounded text-[10px]">
                            Similarity: {(src.relevance_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                      <p className="text-slate-500 text-[11px] line-clamp-3 leading-normal font-sans">
                        {src.content}
                      </p>
                      {src.source && (
                        <span className="text-[10px] text-slate-400 font-mono block">
                          File: {src.source}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Model Tag */}
          {!isUser && message.model_used && (
            <span className="text-[10px] text-slate-400 self-start px-1">
              Generated by {message.model_used}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
