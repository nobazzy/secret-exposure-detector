import React from 'react';
import { ShieldAlert, Cpu, Terminal, PlusCircle, RefreshCw } from 'lucide-react';

export default function Navbar({ onOpenNewScan, onRefresh, loading }) {
  return (
    <nav className="border-b border-slate-800 bg-[#0d121f]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-blue-600 p-0.5 flex items-center justify-center glow-critical">
            <div className="w-full h-full bg-[#0a0d14] rounded-[10px] flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-red-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-white tracking-tight">SecretExposure</h1>
              <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">v4.1 Enterprise</span>
            </div>
            <p className="text-xs text-slate-400 font-mono">Detector Estático & Auditor de Configurações</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/50 text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-2 text-xs font-mono"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            Atualizar
          </button>
          
          <button
            onClick={onOpenNewScan}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs flex items-center gap-2 shadow-lg shadow-blue-500/20 transition hover:scale-[1.02]"
          >
            <PlusCircle className="w-4 h-4" />
            Nova Varredura
          </button>
        </div>
      </div>
    </nav>
  );
}
