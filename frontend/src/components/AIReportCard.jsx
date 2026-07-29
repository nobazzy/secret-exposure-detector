import React from 'react';
import { Bot, ShieldCheck, AlertCircle } from 'lucide-react';

export default function AIReportCard({ summary }) {
  if (!summary) return null;

  return (
    <div className="glass-panel rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/20 to-blue-950/20 p-6 mb-8 relative overflow-hidden">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center shrink-0">
          <Bot className="w-5 h-5 text-indigo-400" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-bold text-base text-white">Análise do Assistente de IA (Ollama)</h3>
            <span className="px-2 py-0.5 text-[10px] font-mono bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full">
              Resumo & Remediação
            </span>
          </div>

          <div className="text-xs text-slate-300 font-mono whitespace-pre-line leading-relaxed border-t border-indigo-500/10 pt-3">
            {summary}
          </div>
        </div>
      </div>
    </div>
  );
}
