import { ShieldCheck, Database, Bot, Server, Wifi } from 'lucide-react';

export function SystemStatus() {
  const services = [
    { name: 'Crew Roster Service', status: 'Operational', latency: '42ms', icon: Database },
    { name: 'Flight Operations API', status: 'Operational', latency: '38ms', icon: Server },
    { name: 'Duty Rules Engine', status: 'Operational', latency: '51ms', icon: ShieldCheck },
    { name: 'AI Crew Lead Agent', status: 'Degraded', latency: '1.2s', icon: Bot },
    { name: 'Realtime Notifications', status: 'Operational', latency: '12ms', icon: Wifi },
  ];

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">System Status</h1>
        <p className="text-sm text-slate-400">Health of integrated operations services.</p>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200">Services</h2>
          <span className="chip bg-amber-500/15 text-amber-300 border-amber-500/40">1 Degraded</span>
        </div>
        <div className="divide-y divide-console-800">
          {services.map((s) => {
            const Icon = s.icon;
            const ok = s.status === 'Operational';
            return (
              <div key={s.name} className="px-4 py-3 flex items-center gap-4">
                <Icon size={16} className={ok ? 'text-emerald-400' : 'text-amber-400'} />
                <div className="flex-1">
                  <p className="text-sm text-slate-200 font-medium">{s.name}</p>
                  <p className="text-xs text-slate-500">Latency: {s.latency}</p>
                </div>
                <span className={`chip ${ok ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' : 'bg-amber-500/15 text-amber-300 border-amber-500/40'}`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${ok ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse-soft'}`} />
                  {s.status}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="panel p-4">
        <p className="text-xs text-slate-400">Note: Crew assessments are backed by the Python deterministic workflow. The optional LLM agent remains separate and does not execute operational changes.</p>
      </div>
    </div>
  );
}
