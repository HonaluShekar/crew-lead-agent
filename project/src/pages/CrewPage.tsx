import { useEffect, useMemo, useState } from 'react';
import { LoadingState, EmptyState } from '@/components/States';
import { RiskBadge, AvailabilityBadge } from '@/components/Badges';
import { formatTime, formatDuration } from '@/lib/format';
import { getCrew } from '@/services/api';
import type { Crew } from '@/types';
import { Search } from 'lucide-react';

interface CrewPageProps {
  onCrewClick: (c: Crew) => void;
}

export function CrewPage({ onCrewClick }: CrewPageProps) {
  const [loading, setLoading] = useState(true);
  const [crew, setCrew] = useState<Crew[]>([]);
  const [search, setSearch] = useState('');
  const [availFilter, setAvailFilter] = useState<Set<string>>(new Set());
  const [riskFilter, setRiskFilter] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    (async () => {
      const c = await getCrew();
      if (!active) return;
      setCrew(c);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return crew.filter((c) => {
      if (search) {
        const q = search.toLowerCase();
        if (!c.id.toLowerCase().includes(q) && !c.role.toLowerCase().includes(q) && !c.base.toLowerCase().includes(q) && !c.qualification.toLowerCase().includes(q)) return false;
      }
      if (availFilter.size && !availFilter.has(c.availability)) return false;
      if (riskFilter.size && !riskFilter.has(c.riskStatus)) return false;
      return true;
    });
  }, [crew, search, availFilter, riskFilter]);

  const toggle = (set: Set<string>, val: string, setter: (s: Set<string>) => void) => {
    const next = new Set(set);
    if (next.has(val)) next.delete(val);
    else next.add(val);
    setter(next);
  };

  const availOptions = ['Available', 'Assigned', 'On Duty', 'Resting', 'Unavailable', 'At Risk'];
  const riskOptions = ['Safe', 'Watch', 'At Risk', 'Critical'];

  if (loading) return <LoadingState message="Loading crew roster…" />;

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Crew Management</h1>
        <p className="text-sm text-slate-400">Searchable roster of crew with duty-time, rest, and risk status.</p>
      </div>

      <div className="panel p-3 flex flex-col lg:flex-row lg:items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search crew ID, role, base…" className="input w-full pl-8" />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-500">Availability:</span>
          {availOptions.map((a) => (
            <button key={a} onClick={() => toggle(availFilter, a, setAvailFilter)} className={`chip cursor-pointer ${availFilter.has(a) ? 'bg-accent/20 text-accent-soft border-accent/40' : 'bg-console-800 text-slate-400 border-console-700 hover:text-slate-200'}`}>{a}</button>
          ))}
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-500">Risk:</span>
          {riskOptions.map((r) => (
            <button key={r} onClick={() => toggle(riskFilter, r, setRiskFilter)} className={`chip cursor-pointer ${riskFilter.has(r) ? 'bg-accent/20 text-accent-soft border-accent/40' : 'bg-console-800 text-slate-400 border-console-700 hover:text-slate-200'}`}>{r}</button>
          ))}
        </div>
      </div>

      <div className="panel">
        {filtered.length === 0 ? (
          <EmptyState title="No crew match your filters" />
        ) : (
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-console-700">
                  <th className="px-4 py-2 font-medium">Crew ID</th>
                  <th className="px-4 py-2 font-medium">Role</th>
                  <th className="px-4 py-2 font-medium">Base</th>
                  <th className="px-4 py-2 font-medium">Qualification</th>
                  <th className="px-4 py-2 font-medium">Current Flight</th>
                  <th className="px-4 py-2 font-medium">Duty Start</th>
                  <th className="px-4 py-2 font-medium">Elapsed</th>
                  <th className="px-4 py-2 font-medium">Remaining</th>
                  <th className="px-4 py-2 font-medium">Rest</th>
                  <th className="px-4 py-2 font-medium">Availability</th>
                  <th className="px-4 py-2 font-medium">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-800">
                {filtered.map((c) => (
                  <tr key={c.id} className="row-hover" onClick={() => onCrewClick(c)}>
                    <td className="px-4 py-2.5 font-mono text-slate-200">{c.id}</td>
                    <td className="px-4 py-2.5 text-slate-300">{c.role}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono">{c.base}</td>
                    <td className="px-4 py-2.5 text-slate-300 text-xs">{c.qualification}</td>
                    <td className="px-4 py-2.5 text-slate-300 font-mono text-xs">{c.currentFlight ?? '—'}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{c.dutyStart ? formatTime(c.dutyStart) : '—'}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{formatDuration(c.dutyElapsedMinutes)}</td>
                    <td className={`px-4 py-2.5 font-mono text-xs ${c.dutyRemainingMinutes < 90 ? 'text-orange-300' : 'text-slate-300'}`}>{formatDuration(c.dutyRemainingMinutes)}</td>
                    <td className="px-4 py-2.5 text-slate-300 text-xs">{c.restStatus}</td>
                    <td className="px-4 py-2.5"><AvailabilityBadge availability={c.availability} /></td>
                    <td className="px-4 py-2.5"><RiskBadge risk={c.riskStatus} /></td>
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
