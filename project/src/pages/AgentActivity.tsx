import { useEffect, useState } from 'react';
import { LoadingState } from '@/components/States';
import { WorkflowStatusBadge } from '@/components/Badges';
import { formatDateTime } from '@/lib/format';
import { getAgentActivity } from '@/services/api';
import type { AgentActivityEntry } from '@/types';
import { Activity, Clock, Wrench, Bot } from 'lucide-react';

export function AgentActivity() {
  const [loading, setLoading] = useState(true);
  const [entries, setEntries] = useState<AgentActivityEntry[]>([]);

  useEffect(() => {
    let active = true;
    (async () => {
      const a = await getAgentActivity();
      if (!active) return;
      setEntries(a);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <LoadingState message="Loading agent activity…" />;

  const totalMs = entries.reduce((sum, e) => sum + e.durationMs, 0);

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Agent Activity</h1>
        <p className="text-sm text-slate-400">Timeline of the Crew Lead Agent workflow execution.</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="panel p-3">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Steps</p>
          <p className="text-xl font-semibold font-mono text-slate-100 mt-1">{entries.length}</p>
        </div>
        <div className="panel p-3">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Total Duration</p>
          <p className="text-xl font-semibold font-mono text-slate-100 mt-1">{(totalMs / 1000).toFixed(2)}s</p>
        </div>
        <div className="panel p-3">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Agents</p>
          <p className="text-xl font-semibold font-mono text-slate-100 mt-1">{new Set(entries.map((e) => e.agent)).size}</p>
        </div>
        <div className="panel p-3">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Status</p>
          <p className="text-xl font-semibold font-mono text-emerald-300 mt-1">Completed</p>
        </div>
      </div>

      {/* Timeline */}
      <div className="panel">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Activity size={14} className="text-accent-soft" /> Workflow Timeline
          </h2>
        </div>
        <div className="p-4">
          <ol className="relative border-l border-console-700 ml-3 space-y-5">
            {entries.map((e) => (
              <li key={e.id} className="ml-6">
                <span className={`absolute -left-[9px] h-4 w-4 rounded-full border-2 ${
                  e.status === 'Completed' ? 'border-emerald-500 bg-console-900' : 'border-console-600 bg-console-800'
                }`} />
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono text-slate-500">#{e.step}</span>
                      <p className="text-sm font-medium text-slate-200">{e.label}</p>
                      <WorkflowStatusBadge status={e.status} />
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{e.description}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-500 flex-wrap">
                      <span className="flex items-center gap-1"><Bot size={11} /> {e.agent}</span>
                      <span className="flex items-center gap-1"><Wrench size={11} /> {e.tool}</span>
                      <span className="flex items-center gap-1"><Clock size={11} /> {e.durationMs}ms</span>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 font-mono shrink-0">{formatDateTime(e.timestamp)}</span>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
