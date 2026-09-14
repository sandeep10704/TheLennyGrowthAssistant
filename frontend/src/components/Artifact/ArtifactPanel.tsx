import React, { useState } from 'react';
import {
  X,
  Sparkles,
  PlusCircle,
  FileCode,
  FileText,
  Clock,
  Layers,
  Send,
  Loader2,
  ChevronRight,
  Shield,
} from 'lucide-react';
import { Artifact, ArtifactType } from '../../types';
import { SecureArtifactViewer } from './SecureArtifactViewer';

interface ArtifactPanelProps {
  isOpen: boolean;
  onClose: () => void;
  activeArtifact: Artifact | null;
  onSelectArtifact: (artifact: Artifact) => void;
  artifactsHistory: Artifact[];
  onGenerateNewArtifact: (prompt: string, type: ArtifactType) => Promise<void>;
  isGenerating?: boolean;
}

export const ArtifactPanel: React.FC<ArtifactPanelProps> = ({
  isOpen,
  onClose,
  activeArtifact,
  onSelectArtifact,
  artifactsHistory,
  onGenerateNewArtifact,
  isGenerating = false,
}) => {
  const [activeTab, setActiveTab] = useState<'canvas' | 'generator' | 'history'>('canvas');
  const [promptInput, setPromptInput] = useState('');
  const [selectedFormat, setSelectedFormat] = useState<ArtifactType>('html');

  if (!isOpen) return null;

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptInput.trim() || isGenerating) return;
    await onGenerateNewArtifact(promptInput.trim(), selectedFormat);
    setPromptInput('');
    setActiveTab('canvas');
  };

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-[540px] lg:w-[620px] bg-white border-l border-slate-200 shadow-2xl flex flex-col transition-all duration-300 ease-in-out">
      {/* Panel Top Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 bg-slate-50/80 backdrop-blur">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white shadow-sm shadow-brand-500/20">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-slate-900">Artifact Studio</h2>
              <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded-full flex items-center space-x-1">
                <Shield className="w-2.5 h-2.5" />
                <span>Sandboxed</span>
              </span>
            </div>
            <p className="text-[11px] text-slate-500">Secure rendering for HTML/CSS and Markdown playbooks</p>
          </div>
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition"
          title="Close Artifact Panel"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Internal Navigation Tabs */}
      <div className="flex items-center border-b border-slate-200 px-5 bg-white text-xs font-medium text-slate-600">
        <button
          onClick={() => setActiveTab('canvas')}
          className={`py-3 px-3 border-b-2 flex items-center space-x-1.5 transition ${
            activeTab === 'canvas'
              ? 'border-brand-500 text-brand-600 font-semibold'
              : 'border-transparent hover:text-slate-900'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Active Canvas {activeArtifact ? '(1)' : ''}</span>
        </button>

        <button
          onClick={() => setActiveTab('generator')}
          className={`py-3 px-3 border-b-2 flex items-center space-x-1.5 transition ${
            activeTab === 'generator'
              ? 'border-brand-500 text-brand-600 font-semibold'
              : 'border-transparent hover:text-slate-900'
          }`}
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Generate New</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`py-3 px-3 border-b-2 flex items-center space-x-1.5 transition ${
            activeTab === 'history'
              ? 'border-brand-500 text-brand-600 font-semibold'
              : 'border-transparent hover:text-slate-900'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Session History ({artifactsHistory.length})</span>
        </button>
      </div>

      {/* Panel Scrollable Content Body */}
      <div className="flex-1 overflow-y-auto p-5 bg-slate-50/50">
        {/* Tab 1: Active Canvas */}
        {activeTab === 'canvas' && (
          <div>
            {activeArtifact ? (
              <div className="space-y-4">
                <SecureArtifactViewer
                  content={activeArtifact.content}
                  type={activeArtifact.type}
                  title={activeArtifact.title || 'Growth Artifact'}
                  initialMode={activeArtifact.type === 'html' ? 'iframe-sandbox' : 'sanitized-dom'}
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
                  <Layers className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800">No active artifact selected</h3>
                <p className="text-xs text-slate-500 max-w-xs mt-1 mb-4 leading-normal">
                  Generate an interactive tool or choose an artifact from your conversation history.
                </p>
                <button
                  onClick={() => setActiveTab('generator')}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-semibold shadow-sm transition"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Create First Artifact</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Generator Studio */}
        {activeTab === 'generator' && (
          <form onSubmit={handleGenerate} className="space-y-5 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                Artifact Prompt & Purpose
              </label>
              <textarea
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                placeholder="e.g. Build an interactive PMF survey calculator with Sean Ellis 40% benchmark benchmark status box and range slider..."
                rows={4}
                className="w-full text-xs p-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-brand-500 focus:outline-none placeholder:text-slate-400"
                required
              />
            </div>

            {/* Format Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-2">
                Output Format
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedFormat('html')}
                  className={`p-3 rounded-xl border text-left transition ${
                    selectedFormat === 'html'
                      ? 'border-brand-500 bg-brand-50/50 text-brand-900 ring-1 ring-brand-500'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-2 font-semibold text-xs mb-1">
                    <FileCode className="w-4 h-4 text-brand-600" />
                    <span>HTML / CSS</span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Interactive page with Tailwind CSS, vanilla JS widgets, and sandbox isolation.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedFormat('markdown')}
                  className={`p-3 rounded-xl border text-left transition ${
                    selectedFormat === 'markdown'
                      ? 'border-brand-500 bg-brand-50/50 text-brand-900 ring-1 ring-brand-500'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-2 font-semibold text-xs mb-1">
                    <FileText className="w-4 h-4 text-brand-600" />
                    <span>Markdown</span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Product specifications, benchmark tables, and task execution checklists.
                  </p>
                </button>
              </div>
            </div>

            {/* Action Button */}
            <button
              type="submit"
              disabled={isGenerating || !promptInput.trim()}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-brand-500 hover:bg-brand-600 disabled:bg-slate-200 disabled:text-slate-400 text-white text-xs font-semibold rounded-xl shadow-sm transition"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Synthesizing Artifact with Lenny Engine...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Generate Digital Artifact</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* Tab 3: Session History */}
        {activeTab === 'history' && (
          <div className="space-y-3">
            {artifactsHistory.length === 0 ? (
              <div className="text-center py-12 text-xs text-slate-400">
                No artifacts have been generated in this session yet.
              </div>
            ) : (
              artifactsHistory.map((art, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    onSelectArtifact(art);
                    setActiveTab('canvas');
                  }}
                  className="p-3.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl cursor-pointer transition flex items-center justify-between group shadow-xs"
                >
                  <div className="flex items-center space-x-3 truncate mr-2">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600 group-hover:text-brand-600 group-hover:bg-brand-50 transition shrink-0">
                      {art.type === 'html' ? <FileCode className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                    </div>
                    <div className="truncate">
                      <h4 className="text-xs font-semibold text-slate-800 truncate group-hover:text-brand-600">
                        {art.title || `Artifact #${idx + 1}`}
                      </h4>
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                        {art.type}
                      </span>
                    </div>
                  </div>

                  <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-brand-500 transition shrink-0" />
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
