import React from 'react';
import { Cpu, Cloud } from 'lucide-react';

interface ModelSelectorProps {
  provider: 'openai' | 'ollama';
  setProvider: (provider: 'openai' | 'ollama') => void;
  model: string;
  setModel: (model: string) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  provider,
  setProvider,
  model,
  setModel,
}) => {
  return (
    <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
      {/* Provider Toggle */}
      <button
        onClick={() => {
          setProvider('openai');
          setModel('gpt-4o');
        }}
        className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg transition font-medium ${
          provider === 'openai'
            ? 'bg-white text-slate-900 shadow-sm'
            : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <Cloud className="w-3.5 h-3.5 text-brand-500" />
        <span>OpenAI</span>
      </button>

      <button
        onClick={() => {
          setProvider('ollama');
          setModel('llama3');
        }}
        className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg transition font-medium ${
          provider === 'ollama'
            ? 'bg-white text-slate-900 shadow-sm'
            : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <Cpu className="w-3.5 h-3.5 text-indigo-500" />
        <span>Ollama</span>
      </button>

      {/* Model Selection */}
      <select
        value={model}
        onChange={(e) => setModel(e.target.value)}
        className="bg-transparent border-0 text-slate-700 text-xs font-semibold py-1 pr-2 focus:ring-0 cursor-pointer outline-none"
      >
        {provider === 'openai' ? (
          <>
            <option value="gpt-4o">GPT-4o (Default)</option>
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-4-turbo">GPT-4 Turbo</option>
          </>
        ) : (
          <>
            <option value="llama3">Llama 3</option>
            <option value="llama3.1:8b">Llama 3.1 8B</option>
            <option value="mistral">Mistral</option>
            <option value="phi3">Phi-3</option>
          </>
        )}
      </select>
    </div>
  );
};
