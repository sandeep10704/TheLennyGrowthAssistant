import React, { useRef, useEffect } from 'react';
import { Message, Artifact } from '../../types';
import { MessageBubble } from './MessageBubble';
import { Sparkles, Compass, Rocket, Target, DollarSign, Loader2, FileCode, FileText } from 'lucide-react';

interface ChatContainerProps {
  messages: Message[];
  isSending: boolean;
  onPromptClick: (prompt: string) => void;
  onOpenArtifact?: (artifact: Artifact) => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isSending,
  onPromptClick,
  onOpenArtifact,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const quickPrompts = [
    {
      icon: <Compass className="w-5 h-5 text-amber-500" />,
      tag: "Framework",
      title: "Evaluate PMF",
      desc: "How do I know if my product has true Product-Market Fit?",
    },
    {
      icon: <FileCode className="w-5 h-5 text-brand-500" />,
      tag: "HTML Artifact",
      title: "PMF Survey Calculator",
      desc: "Build landing page for Sean Ellis PMF survey calculator with interactive slider",
    },
    {
      icon: <Rocket className="w-5 h-5 text-indigo-500" />,
      tag: "Essay",
      title: "The 4 Growth Loops",
      desc: "write article on the four growth loops and which one I should prioritize",
    },
    {
      icon: <FileText className="w-5 h-5 text-emerald-500" />,
      tag: "Markdown Artifact",
      title: "Launch Checklist",
      desc: "create checklist for pre-launch product readiness and cohort retention benchmarks",
    },
    {
      icon: <Target className="w-5 h-5 text-rose-500" />,
      tag: "Strategy",
      title: "First 1,000 Users",
      desc: "What are the proven playbooks for acquiring our first 1,000 customers?",
    },
    {
      icon: <DollarSign className="w-5 h-5 text-teal-500" />,
      tag: "Pricing",
      title: "Pricing & Packaging",
      desc: "How do I choose the right Value Metric and price sensitivity model?",
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 max-w-4xl mx-auto w-full">
      {(messages || []).length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[65vh] text-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-500 to-amber-500 flex items-center justify-center text-white mb-4 shadow-md shadow-brand-500/20">
            <Sparkles className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">
            How can I help you grow today?
          </h2>
          <p className="text-xs md:text-sm text-slate-500 max-w-lg mt-2 mb-8 leading-relaxed">
            Synthesizing wisdom from Lenny's interviews with world-class product leaders,
            growth loops, PMF benchmarks, and interactive tools.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full max-w-3xl">
            {quickPrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => onPromptClick(p.desc)}
                className="flex flex-col items-start p-3.5 text-left bg-white hover:bg-slate-50 border border-slate-200 hover:border-brand-300 rounded-xl transition shadow-2xs group"
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <div className="p-1.5 bg-slate-50 rounded-lg group-hover:bg-brand-50 transition">
                    {p.icon}
                  </div>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider bg-slate-100 px-1.5 py-0.5 rounded">
                    {p.tag}
                  </span>
                </div>
                <div className="text-xs font-bold text-slate-800 group-hover:text-brand-600 mb-1">
                  {p.title}
                </div>
                <div className="text-[11px] text-slate-500 line-clamp-2 leading-normal">
                  {p.desc}
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {(messages || []).map((msg, idx) => (
            <MessageBubble
              key={msg?.id || `msg-${idx}`}
              message={msg}
              onOpenArtifact={onOpenArtifact}
            />
          ))}

          {isSending && (
            <div className="flex items-center space-x-2 text-slate-500 text-xs py-2 bg-slate-100/60 rounded-xl px-4 w-fit border border-slate-200/50 animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-500" />
              <span>Querying vector store and synthesizing response...</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
