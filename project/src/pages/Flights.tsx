import { useEffect, useMemo, useState } from 'react';
import { LoadingState, EmptyState } from '@/components/States';
import { CrewLegalityBadge } from '@/components/Badges';
import { formatTime, delayText } from '@/lib/format';
import { getFlights, getCrew } from '@/services/api';
import type { Flight, Crew } from '@/types';
import { Search } from 'lucide-react';

interface FlightsProps {
  onFlightClick: (f: Flight, crewMap: Record<string, Crew>) => void;
}

export function Flights({ onFlightClick }: FlightsProps) {
  const [loading, setLoading] = useState(true);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [crewMap, setCrewMap] = useState<Record<string, Crew>>({});
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    (async () => {
      const [f, c] = await Promise.all([getFlights(), getCrew()]);
      if (!active) return;
      setFlights(f);
      setCrewMap(Object.fromEntries(c.map((x) => [x.id, x])));
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return flights.filter((f) => {
      if (search) {
        const q = search.toLowerCase();
        if (!f.number.toLowerCase().includes(q) && !f.route.toLowerCase().includes(q) && !f.aircraft.toLowerCase().includes(q)) return false;
      }
      if (statusFilter.size && !statusFilter.has(f.disruptionStatus)) return false;
      return true;
    });
  }, [flights, search, statusFilter]);

  const toggle = (set: Set<string>, val: string, setter: (s: Set<string>) => void) => {
    const next = new Set(set);
    if (next.has(val)) next.delete(val);
    else next.add(val);
    setter(next);
  };

  const statusOptions = ['None', 'Delay', 'Cancellation', 'Crew Issue'];

  if (loading) return <LoadingState message="Loading flight operations…" />;

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Flight Operations</h1>
        <p className="text-sm text-slate-400">All flights with crew status and disruption indicators.</p>
      </div>

      <div className="panel p-3 flex flex-col md:flex-row md:items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search flight, route, aircraft…" className="input w-full pl-8" />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-500">Status:</span>
          {statusOptions.map((s) => (
            <button key={s} onClick={() => toggle(statusFilter, s, setStatusFilter)} className={`chip cursor-pointer ${statusFilter.has(s) ? 'bg-accent/20 text-accent-soft border-accent/40' : 'bg-console-800 text-slate-400 border-console-700 hover:text-slate-200'}`}>{s}</button>
          ))}
        </div>
      </div>

      <div className="panel">
        {filtered.length === 0 ? (
          <EmptyState title="No flights match your filters" />
        ) : (
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-console-700">
                  <th className="px-4 py-2 font-medium">Flight</th>
                  <th className="px-4 py-2 font-medium">Route</th>
                  <th className="px-4 py-2 font-medium">Aircraft</th>
                  <th className="px-4 py-2 font-medium">Departure</th>
                  <th className="px-4 py-2 font-medium">Arrival</th>
                  <th className="px-4 py-2 font-medium">Delay</th>
                  <th className="px-4 py-2 font-medium">Crew</th>
                  <th className="px-4 py-2 font-medium">Crew Status</th>
                  <th className="px-4 py-2 font-medium">Disruption</th>
                  <th className="px-4 py-2 font-medium">Downstream</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-800">
                {filtered.map((f) => (
                  <tr key={f.id} className="row-hover" onClick={() => onFlightClick(f, crewMap)}>
                    <td className="px-4 py-2.5 font-mono text-slate-200">{f.number}</td>
                    <td className="px-4 py-2.5 text-slate-300">{f.route}</td>
                    <td className="px-4 py-2.5 text-slate-400 text-xs">{f.aircraft}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{formatTime(f.scheduledDeparture)}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{formatTime(f.arrival)}</td>
                    <td className="px-4 py-2.5">
                      <span className={f.delayMinutes > 60 ? 'text-red-300' : f.delayMinutes > 0 ? 'text-amber-300' : 'text-emerald-300'}>{delayText(f.delayMinutes)}</span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{f.assignedCrew.join(', ')}</td>
                    <td className="px-4 py-2.5"><CrewLegalityBadge status={f.crewStatus} /></td>
                    <td className="px-4 py-2.5">
                      <span className={`chip ${f.disruptionStatus === 'None' ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' : 'bg-amber-500/15 text-amber-300 border-amber-500/40'}`}>{f.disruptionStatus}</span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-300">{f.downstreamImpact}</td>
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
