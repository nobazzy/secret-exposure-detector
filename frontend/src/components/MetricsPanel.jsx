import React from 'react';
import { AlertOctagon, AlertTriangle, AlertCircle, CheckCircle, FileText, Zap, Clock } from 'lucide-react';

export default function MetricsPanel({ selectedJob }) {
  if (!selectedJob) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-2xl glass-panel animate-pulse"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
      {/* Critical */}
      <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-red-500 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider">Críticos</span>
          <AlertOctagon className="w-5 h-5 text-red-500" />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-white">{selectedJob.critical_count}</span>
          <span className="text-xs text-red-400 font-mono">🔴 Resposta imediata</span>
        </div>
      </div>

      {/* High */}
      <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-orange-500 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider">Altos</span>
          <AlertTriangle className="w-5 h-5 text-orange-500" />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-white">{selectedJob.high_count}</span>
          <span className="text-xs text-orange-400 font-mono">🟠 Atenção prioritária</span>
        </div>
      </div>

      {/* Medium */}
      <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-yellow-500 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider">Médios</span>
          <AlertCircle className="w-5 h-5 text-yellow-500" />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-white">{selectedJob.medium_count}</span>
          <span className="text-xs text-yellow-400 font-mono">🟡 Configs & Dev</span>
        </div>
      </div>

      {/* Files Scanned */}
      <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-blue-500 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider">Arquivos Analisados</span>
          <FileText className="w-5 h-5 text-blue-400" />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-white">{selectedJob.analyzed_files}</span>
          <span className="text-xs text-blue-400 font-mono">({selectedJob.cached_files} em cache)</span>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-emerald-500 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider">Throughput</span>
          <Zap className="w-5 h-5 text-emerald-400" />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-white">{selectedJob.throughput_files_per_sec.toFixed(1)}</span>
          <span className="text-xs text-emerald-400 font-mono">arq/s ({selectedJob.duration_ms.toFixed(0)}ms)</span>
        </div>
      </div>
    </div>
  );
}
