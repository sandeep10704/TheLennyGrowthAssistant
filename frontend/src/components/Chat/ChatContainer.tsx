import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import { MessageBubble } from './MessageBubble';
import { Sparkles, Compass, Rocket, Target, DollarSign, Loader2 } from 'lucide-react';

interface ChatContainerProps {
  messages: Message[];
  isSending: boolean;
  onPromptClick: (prompt: string) => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isSending,
  onPromptClick,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const quickPrompts = [
    {
      icon: <Compass className="w-5 h-5 text-amber-500" />,
      title: "Evaluate PMF",
      desc: "How do I know if my product has true Product-Market Fit?",
    },
    {
      icon: <Rocket className="w-5 h-5 text-indigo-500" />,
      title: "The 4 Growth Loops",
      desc: "Explain the four growth loops and which one I should prioritize.",
    },
    {
      icon: <Target className="w-5 h-5 text-emerald-500" />,
      title: "First 1,000 Users",
      desc: "What are the proven playbooks for getting the first 1,000 customers?",
    },
    {
      icon: <DollarSign className="w-5 h-5 text-brand-500" />,
      title: "Pricing & Packaging",
      desc: "How do I choose the right Value Metric and price sensitivity model?",
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 max-w-4xl mx-auto w-full">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <div className="w-14 h-14 rounded-2xl bg-brand-100 flex items-center justify-center text-brand-600 mb-4 shadow-inner">
            <Sparkles className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">
            How can I help you grow today?
          </h2>
          <p className="text-sm text-slate-500 max-w-md mt-2 mb-8">
            Ask questions about product-market fit, retention metrics, growth loops, and 0-to-1 tactics.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
            {quickPrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => onPromptClick(p.desc)}
                className="flex items-start p-4 text-left bg-white hover:bg-slate-50 border border-slate-200 hover:border-brand-300 rounded-xl transition shadow-sm group"
              >
                <div className="mr-3 p-2 bg-slate-50 rounded-lg group-hover:bg-white transition">
                  {p.icon}
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-800 group-hover:text-brand-600">
                    {p.title}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                    {p.desc}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {isSending && (
            <div className="flex items-center space-x-2 text-slate-400 text-xs py-2">
              <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
              <span>Lenny Assistant is querying vector knowledge and reasoning...</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
