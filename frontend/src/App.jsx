import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricsPanel from './components/MetricsPanel';
import IncidentTable from './components/IncidentTable';
import AIReportCard from './components/AIReportCard';
import NewScanModal from './components/NewScanModal';
import { History, Shield, Play } from 'lucide-react';

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
        if (data.length > 0 && !selectedJob) {
          selectJob(data[0].id);
        }
      }
    } catch (err) {
      console.error('Erro ao buscar jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectJob = async (jobId) => {
    try {
      const jobRes = await fetch(`/api/jobs/${jobId}`);
      if (jobRes.ok) {
        const jobData = await jobRes.json();
        setSelectedJob(jobData);
      }

      const incRes = await fetch(`/api/jobs/${jobId}/incidents`);
      if (incRes.ok) {
        const incData = await incRes.json();
        setIncidents(incData);
      }
    } catch (err) {
      console.error('Erro ao buscar detalhes do job:', err);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleStartScan = async (targetPath, runAi) => {
    try {
      const res = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_path: targetPath,
          run_ai_enrichment: runAi,
        }),
      });

      if (res.ok) {
        const newJob = await res.json();
        fetchJobs();
        // Poll for completion
        const interval = setInterval(async () => {
          const pollRes = await fetch(`/api/jobs/${newJob.id}`);
          if (pollRes.ok) {
            const updated = await pollRes.json();
            if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
              clearInterval(interval);
              fetchJobs();
              selectJob(updated.id);
            }
          }
        }, 1000);
      }
    } catch (err) {
      console.error('Erro ao criar job:', err);
    }
  };

  const handleExport = (format) => {
    if (!selectedJob) return;
    window.open(`/api/jobs/${selectedJob.id}/export/${format}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col">
      <Navbar onOpenNewScan={() => setIsModalOpen(true)} onRefresh={fetchJobs} loading={loading} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {/* Job History Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 glass-panel p-4 rounded-2xl">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-slate-800 border border-slate-700">
              <History className="w-5 h-5 text-slate-300" />
            </div>
            <div>
              <span className="text-xs font-mono text-slate-400 block">Sessão de Varredura</span>
              <select
                value={selectedJob?.id || ''}
                onChange={(e) => selectJob(e.target.value)}
                className="bg-[#0a0d14] border border-slate-800 text-sm font-mono text-slate-200 rounded-xl px-3 py-1.5 focus:outline-none focus:border-blue-500 font-semibold"
              >
                {jobs.length === 0 ? (
                  <option value="">Nenhuma varredura registrada</option>
                ) : (
                  jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      Job #{j.id} — {j.target_path} ({j.status})
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          {selectedJob && (
            <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
              <div>
                <span className="text-slate-500">Status: </span>
                <span className="text-emerald-400 font-bold">{selectedJob.status}</span>
              </div>
              <div>
                <span className="text-slate-500">Executado em: </span>
                <span className="text-slate-300">{new Date(selectedJob.created_at).toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>

        {/* Empty State */}
        {jobs.length === 0 ? (
          <div className="glass-panel rounded-3xl p-12 text-center my-12 max-w-xl mx-auto border border-slate-800">
            <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mx-auto mb-4">
              <Shield className="w-8 h-8 text-blue-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Nenhuma auditoria realizada ainda</h3>
            <p className="text-xs text-slate-400 mb-6">
              Inicie uma nova varredura em qualquer repositório ou diretório da sua máquina para auditar segredos expostos.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-lg shadow-blue-500/20 inline-flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Iniciar Primeira Varredura
            </button>
          </div>
        ) : (
          <>
            {/* Metrics */}
            <MetricsPanel selectedJob={selectedJob} />

            {/* AI Insights Card */}
            {selectedJob?.ai_summary && <AIReportCard summary={selectedJob.ai_summary} />}

            {/* Incidents Table */}
            <IncidentTable incidents={incidents} jobId={selectedJob?.id} onExport={handleExport} />
          </>
        )}
      </main>

      <NewScanModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleStartScan}
      />
    </div>
  );
}
