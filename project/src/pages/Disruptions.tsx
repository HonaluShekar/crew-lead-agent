import { useEffect, useMemo, useState } from 'react';
import { LoadingState, EmptyState } from '@/components/States';
import { SeverityBadge, CrewLegalityBadge, DisruptionTypeBadge } from '@/components/Badges';
import { formatTime, delayText } from '@/lib/format';
import { getDisruptions } from '@/services/api';
import type { Disruption } from '@/types';
import { Search, Filter } from 'lucide-react';

interface DisruptionsProps {
  onOpenDisruption: (d: Disruption) => void;
}

const severityFilters = ['Critical', 'High', 'Medium', 'Low'] as const;
const typeFilters = ['Delay', 'Cancellation', 'Crew Legality', 'Replacement Required'] as const;

export function Disruptions({ onOpenDisruption }: DisruptionsProps) {
  const [loading, setLoading] = useState(true);
  const [disruptions, setDisruptions] = useState<Disruption[]>([]);
  const [search, setSearch] = useState('');
  const [sevFilter, setSevFilter] = useState<Set<string>>(new Set());
  const [typeFilter, setTypeFilter] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    (async () => {
      const d = await getDisruptions();
      if (!active) return;
      setDisruptions(d);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return disruptions.filter((d) => {
      if (search) {
        const q = search.toLowerCase();
        if (!d.flightNumber.toLowerCase().includes(q) && !d.origin.toLowerCase().includes(q) && !d.destination.toLowerCase().includes(q)) return false;
      }
      if (sevFilter.size && !sevFilter.has(d.severity)) return false;
      if (typeFilter.size && !typeFilter.has(d.type)) return false;
      return true;
    });
  }, [disruptions, search, sevFilter, typeFilter]);

  const toggle = (set: Set<string>, val: string, setter: (s: Set<string>) => void) => {
    const next = new Set(set);
    if (next.has(val)) next.delete(val);
    else next.add(val);
    setter(next);
  };

  if (loading) return <LoadingState message="Loading disruptions…" />;

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Disruption Management</h1>
        <p className="text-sm text-slate-400">Monitor and analyze active crew-related flight disruptions.</p>
      </div>

      {/* Filters */}
      <div className="panel p-3 flex flex-col md:flex-row md:items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search flight, route…"
            className="input w-full pl-8"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 flex items-center gap-1"><Filter size={12} /> Severity:</span>
          {severityFilters.map((s) => (
            <button
              key={s}
              onClick={() => toggle(sevFilter, s, setSevFilter)}
              className={`chip cursor-pointer transition-colors ${
                sevFilter.has(s) ? 'bg-accent/20 text-accent-soft border-accent/40' : 'bg-console-800 text-slate-400 border-console-700 hover:text-slate-200'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500">Type:</span>
          {typeFilters.map((t) => (
            <button
              key={t}
              onClick={() => toggle(typeFilter, t, setTypeFilter)}
              className={`chip cursor-pointer transition-colors ${
                typeFilter.has(t) ? 'bg-accent/20 text-accent-soft border-accent/40' : 'bg-console-800 text-slate-400 border-console-700 hover:text-slate-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="panel">
        {filtered.length === 0 ? (
          <EmptyState title="No disruptions match your filters" message="Try clearing filters or searching a different flight." />
        ) : (
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-console-700">
                  <th className="px-4 py-2 font-medium">Flight</th>
                  <th className="px-4 py-2 font-medium">Route</th>
                  <th className="px-4 py-2 font-medium">Sched. Dep</th>
                  <th className="px-4 py-2 font-medium">Est. Dep</th>
                  <th className="px-4 py-2 font-medium">Delay</th>
                  <th className="px-4 py-2 font-medium">Crew</th>
                  <th className="px-4 py-2 font-medium">Legality</th>
                  <th className="px-4 py-2 font-medium">Downstream</th>
                  <th className="px-4 py-2 font-medium">Type</th>
                  <th className="px-4 py-2 font-medium">Severity</th>
                  <th className="px-4 py-2 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-800">
                {filtered.map((d) => (
                  <tr key={d.id} className="row-hover" onClick={() => onOpenDisruption(d)}>
                    <td className="px-4 py-2.5 font-mono text-slate-200">{d.flightNumber}</td>
                    <td className="px-4 py-2.5 text-slate-300">{d.origin} → {d.destination}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{formatTime(d.scheduledDeparture)}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{formatTime(d.estimatedDeparture)}</td>
                    <td className="px-4 py-2.5">
                      <span className={d.delayMinutes > 60 ? 'text-red-300' : d.delayMinutes > 0 ? 'text-amber-300' : 'text-emerald-300'}>
                        {delayText(d.delayMinutes)}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{d.assignedCrew.join(', ')}</td>
                    <td className="px-4 py-2.5"><CrewLegalityBadge status={d.crewLegality} /></td>
                    <td className="px-4 py-2.5 text-slate-300">{d.downstreamFlights.length}</td>
                    <td className="px-4 py-2.5"><DisruptionTypeBadge type={d.type} /></td>
                    <td className="px-4 py-2.5"><SeverityBadge severity={d.severity} /></td>
                    <td className="px-4 py-2.5 text-right">
                      <button onClick={(e) => { e.stopPropagation(); onOpenDisruption(d); }} className="btn-primary text-xs py-1">
                        Analyze
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
