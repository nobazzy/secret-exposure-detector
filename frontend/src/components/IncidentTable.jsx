import React, { useState } from 'react';
import { Eye, EyeOff, Copy, Check, Download, Shield, Filter, Search } from 'lucide-react';

export default function IncidentTable({ incidents, jobId, onExport }) {
  const [revealedIds, setRevealedIds] = useState(new Set());
  const [copiedId, setCopiedId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCriticality, setFilterCriticality] = useState('ALL');

  const toggleReveal = (id) => {
    setRevealedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleCopy = (id, value) => {
    if (!value) return;
    navigator.clipboard.writeText(value);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredIncidents = incidents.filter((inc) => {
    const matchesSearch =
      inc.variable_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.relative_path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.capability.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter = filterCriticality === 'ALL' || inc.criticality === filterCriticality;

    return matchesSearch && matchesFilter;
  });

  const getBadgeStyle = (crit) => {
    switch (crit) {
      case 'CRÍTICO':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'ALTO':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'MÉDIO':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
      default:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    }
  };

  const maskValue = (val) => {
    if (!val) return '—';
    if (val.length <= 8) return '••••••••';
    return val.substring(0, 4) + '••••••••' + val.substring(val.length - 4);
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 p-6 shadow-xl">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <Shield className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">Incidentes Detectados</h3>
            <p className="text-xs text-slate-400">Varredura de credenciais com valores capturados localmente</p>
          </div>
        </div>

        {/* Export Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => onExport('sarif')}
            className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-xs font-mono text-slate-300 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-blue-400" />
            SARIF
          </button>
          <button
            onClick={() => onExport('json')}
            className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-xs font-mono text-slate-300 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            JSON
          </button>
          <button
            onClick={() => onExport('csv')}
            className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-xs font-mono text-slate-300 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            CSV
          </button>
          <button
            onClick={() => onExport('markdown')}
            className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-xs font-mono text-slate-300 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-yellow-400" />
            Markdown
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row items-center gap-3 mb-6">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por variável, arquivo ou capacidade..."
            className="w-full bg-[#0a0d14] border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-1 w-full sm:w-auto bg-[#0a0d14] border border-slate-800 rounded-xl p-1">
          {['ALL', 'CRÍTICO', 'ALTO', 'MÉDIO', 'BAIXO'].map((crit) => (
            <button
              key={crit}
              onClick={() => setFilterCriticality(crit)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition ${
                filterCriticality === crit
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {crit}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800/80">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/40 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              <th className="py-3.5 px-4">Criticidade</th>
              <th className="py-3.5 px-4">Variável Detectada</th>
              <th className="py-3.5 px-4">Valor Capturado (Local)</th>
              <th className="py-3.5 px-4">Arquivo & Linha</th>
              <th className="py-3.5 px-4">Capacidade</th>
              <th className="py-3.5 px-4 text-right">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 text-xs font-mono">
            {filteredIncidents.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  Nenhum incidente encontrado com os filtros atuais.
                </td>
              </tr>
            ) : (
              filteredIncidents.map((inc) => {
                const isRevealed = revealedIds.has(inc.id);
                return (
                  <tr key={inc.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-semibold border ${getBadgeStyle(
                          inc.criticality
                        )}`}
                      >
                        {inc.criticality}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-semibold text-slate-200">{inc.variable_name}</td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <span className="bg-[#0a0d14] px-2.5 py-1 rounded border border-slate-800 text-slate-300 text-[11px]">
                          {isRevealed ? inc.secret_value : maskValue(inc.secret_value)}
                        </span>
                        {inc.secret_value && (
                          <>
                            <button
                              onClick={() => toggleReveal(inc.id)}
                              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
                              title={isRevealed ? 'Ocultar Valor' : 'Revelar Valor'}
                            >
                              {isRevealed ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                            </button>
                            <button
                              onClick={() => handleCopy(inc.id, inc.secret_value)}
                              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
                              title="Copiar Segredo"
                            >
                              {copiedId === inc.id ? (
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </>
                        )}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      <span className="text-slate-300">{inc.relative_path}</span>
                      <span className="text-blue-400 ml-1.5">:L{inc.line_number}</span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">{inc.capability}</td>

                    <td className="py-3.5 px-4 text-right font-bold text-slate-200">{inc.risk_score}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
