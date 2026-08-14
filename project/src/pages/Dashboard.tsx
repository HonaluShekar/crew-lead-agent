import { useEffect, useState } from 'react';
import { KPICard } from '@/components/KPICard';
import { SeverityBadge, CrewLegalityBadge, DisruptionTypeBadge } from '@/components/Badges';
import { LoadingState } from '@/components/States';
import { useToast } from '@/components/Toast';
import { formatTime, delayText } from '@/lib/format';
import {
  getDisruptions,
  getIssues,
  getCrew,
  getFlights,
  getRecentRecommendations,
  getCrewAvailabilitySnapshot,
} from '@/services/api';
import type { Disruption, Issue, Crew, Flight, Severity } from '@/types';
import {
  AlertTriangle,
  Users,
  Search,
  ListChecks,
  Bot,
  ArrowRight,
  Activity,
} from 'lucide-react';

interface DashboardProps {
  onOpenDisruption: (d: Disruption) => void;
  onNavigate: (p: 'disruptions' | 'ai' | 'crew' | 'flights' | 'issues') => void;
}

export function Dashboard({ onOpenDisruption, onNavigate }: DashboardProps) {
  const { push } = useToast();
  const [loading, setLoading] = useState(true);
  const [disruptions, setDisruptions] = useState<Disruption[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [crew, setCrew] = useState<Crew[]>([]);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [recs, setRecs] = useState<{ flight: string; text: string; severity: Severity; time: string }[]>([]);
  const [snapshot, setSnapshot] = useState<Record<string, number>>({});

  useEffect(() => {
    let active = true;
    (async () => {
      const [d, i, c, f, r, s] = await Promise.all([
        getDisruptions(),
        getIssues(),
        getCrew(),
        getFlights(),
        getRecentRecommendations(),
        getCrewAvailabilitySnapshot(),
      ]);
      if (!active) return;
      setDisruptions(d);
      setIssues(i);
      setCrew(c);
      setFlights(f);
      setRecs(r);
      setSnapshot(s);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <LoadingState message="Loading operations overview…" />;

  const criticalIssues = issues.filter((i) => i.severity === 'Critical').length;
  const activeDisruptions = disruptions.filter((d) => d.status === 'Active').length;
  const crewAtRisk = crew.filter((c) => c.riskStatus === 'At Risk' || c.riskStatus === 'Critical').length;
  const replacementReqs = issues.filter((i) => i.type === 'Replacement Required' && i.status !== 'Resolved').length;
  const unresolved = issues.filter((i) => i.status !== 'Resolved').length;

  const criticalIssuesList = issues.filter((i) => i.severity === 'Critical' || i.severity === 'High').slice(0, 4);

  const snapshotColors: Record<string, string> = {
    Available: 'bg-emerald-500',
    Assigned: 'bg-blue-500',
    'On Duty': 'bg-accent',
    Resting: 'bg-slate-500',
    Unavailable: 'bg-red-500',
    'At Risk': 'bg-orange-500',
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <KPICard label="Critical Issues" value={criticalIssues} tone="critical" icon={AlertTriangle} trend="up" delta="2" />
        <KPICard label="Active Disruptions" value={activeDisruptions} tone="warning" icon={Activity} trend="up" delta="1" />
        <KPICard label="Crew at Risk" value={crewAtRisk} tone="warning" icon={Users} trend="up" delta="3" />
        <KPICard label="Replacement Requests" value={replacementReqs} tone="info" icon={Search} trend="flat" delta="0" />
        <KPICard label="Unresolved Issues" value={unresolved} tone="neutral" icon={ListChecks} trend="down" delta="1" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Critical Crew Issues */}
        <div className="panel lg:col-span-2">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-slate-200">Critical Crew Issues</h2>
            <button onClick={() => onNavigate('issues')} className="btn-ghost text-xs">
              View all <ArrowRight size={12} />
            </button>
          </div>
          <div className="divide-y divide-console-800">
            {criticalIssuesList.map((issue) => {
              const flight = flights.find((f) => f.number === issue.flight);
              return (
                <button
                  key={issue.id}
                  onClick={() => {
                    const d = disruptions.find((x) => x.flightNumber === issue.flight);
                    if (d) onOpenDisruption(d);
                    else push('info', `Issue ${issue.id} on ${issue.flight} — no active disruption record.`);
                  }}
                  className="w-full text-left px-4 py-3 row-hover flex items-center gap-4"
                >
                  <div className="flex flex-col items-center w-16 shrink-0">
                    <span className="text-sm font-semibold text-slate-100 font-mono">{issue.flight}</span>
                    <span className="text-[10px] text-slate-500">{flight?.route}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200 truncate">{issue.description}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                      <span>{issue.crewAffected} crew affected</span>
                      {flight && flight.downstreamImpact > 0 && (
                        <span className="text-amber-400">{flight.downstreamImpact} downstream flights</span>
                      )}
                      <span className="text-slate-500">{issue.recommendedAction}</span>
                    </div>
                  </div>
                  <SeverityBadge severity={issue.severity} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Crew Availability Snapshot */}
        <div className="panel">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-slate-200">Crew Availability Snapshot</h2>
            <button onClick={() => onNavigate('crew')} className="btn-ghost text-xs">
              Details <ArrowRight size={12} />
            </button>
          </div>
          <div className="p-4 space-y-3">
            {Object.entries(snapshot).map(([key, val]) => {
              const total = Object.values(snapshot).reduce((a, b) => a + b, 0);
              const pct = total > 0 ? (val / total) * 100 : 0;
              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className={`h-2 w-2 rounded-full ${snapshotColors[key]}`} />
                      <span className="text-xs text-slate-300">{key}</span>
                    </div>
                    <span className="text-sm font-mono text-slate-200">{val}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-console-800 overflow-hidden">
                    <div className={`h-full rounded-full ${snapshotColors[key]}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Active Disruptions table */}
      <div className="panel">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200">Active Disruptions</h2>
          <button onClick={() => onNavigate('disruptions')} className="btn-ghost text-xs">
            View all <ArrowRight size={12} />
          </button>
        </div>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-console-700">
                <th className="px-4 py-2 font-medium">Flight</th>
                <th className="px-4 py-2 font-medium">Route</th>
                <th className="px-4 py-2 font-medium">Delay</th>
                <th className="px-4 py-2 font-medium">Assigned Crew</th>
                <th className="px-4 py-2 font-medium">Duty Risk</th>
                <th className="px-4 py-2 font-medium">Downstream</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-console-800">
              {disruptions.map((d) => (
                <tr key={d.id} className="row-hover">
                  <td className="px-4 py-2.5 font-mono text-slate-200">{d.flightNumber}</td>
                  <td className="px-4 py-2.5 text-slate-300">{d.origin} → {d.destination}</td>
                  <td className="px-4 py-2.5">
                    <span className={d.delayMinutes > 60 ? 'text-red-300' : d.delayMinutes > 0 ? 'text-amber-300' : 'text-emerald-300'}>
                      {delayText(d.delayMinutes)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{d.assignedCrew.join(', ')}</td>
                  <td className="px-4 py-2.5"><CrewLegalityBadge status={d.crewLegality} /></td>
                  <td className="px-4 py-2.5 text-slate-300">{d.downstreamFlights.length}</td>
                  <td className="px-4 py-2.5"><DisruptionTypeBadge type={d.type} /></td>
                  <td className="px-4 py-2.5 text-right">
                    <button onClick={() => onOpenDisruption(d)} className="btn-outline text-xs py-1">
                      Analyze
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Agent Recommendations */}
      <div className="panel">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Bot size={14} className="text-accent-soft" /> Recent Agent Recommendations
          </h2>
          <button onClick={() => onNavigate('ai')} className="btn-ghost text-xs">
            Open AI Crew Lead <ArrowRight size={12} />
          </button>
        </div>
        <div className="divide-y divide-console-800">
          {recs.map((r) => (
            <div key={r.flight + r.time} className="px-4 py-3 flex items-center gap-4">
              <SeverityBadge severity={r.severity} />
              <span className="text-sm font-mono text-slate-200">{r.flight}</span>
              <p className="text-sm text-slate-300 flex-1">{r.text}</p>
              <span className="text-xs text-slate-500 font-mono">{formatTime(r.time)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
