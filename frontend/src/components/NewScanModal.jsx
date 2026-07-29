import React, { useState } from 'react';
import { X, FolderSearch, Sparkles } from 'lucide-react';

export default function NewScanModal({ isOpen, onClose, onSubmit }) {
  const [path, setPath] = useState('');
  const [runAi, setRunAi] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!path.trim()) return;
    onSubmit(path.trim(), runAi);
    setPath('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-lg rounded-2xl border border-slate-800 p-6 shadow-2xl relative animate-in fade-in zoom-in-95">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <FolderSearch className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="font-bold text-lg text-white">Nova Auditoria de Segredos</h3>
            <p className="text-xs text-slate-400">Informe o caminho completo do repositório ou pasta local</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-mono font-medium text-slate-300 mb-2">
              Caminho do Diretório ou Repositório
            </label>
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="Ex: C:\Users\vasco\meu-projeto ou /home/user/repo"
              required
              className="w-full bg-[#0a0d14] border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
            />
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <div>
                <p className="text-xs font-medium text-slate-200">Enriquecimento por IA (Ollama)</p>
                <p className="text-[11px] text-slate-400">Gerar resumo executivo e sugestões de rotação</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={runAi}
              onChange={(e) => setRunAi(e.target.checked)}
              className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-800 text-slate-300 hover:bg-slate-800 text-xs font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-lg shadow-blue-500/20"
            >
              Iniciar Varredura
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
