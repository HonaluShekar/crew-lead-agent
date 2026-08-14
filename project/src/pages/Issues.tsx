import { useEffect, useMemo, useState } from 'react';
import { LoadingState, EmptyState } from '@/components/States';
import { SeverityBadge, IssueStatusBadge } from '@/components/Badges';
import { formatDateTime } from '@/lib/format';
import { getIssues } from '@/services/api';
import type { Issue, Severity, IssueStatus } from '@/types';
import { Search, ArrowUpDown } from 'lucide-react';

type SortKey = 'severity' | 'status' | 'created';

const severityRank: Record<Severity, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 };
const statusRank: Record<IssueStatus, number> = { 'Action Required': 0, New: 1, Investigating: 2, Resolved: 3 };

export function Issues() {
  const [loading, setLoading] = useState(true);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [search, setSearch] = useState('');
  const [sevFilter, setSevFilter] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<Set<string>>(new Set());
  const [sortKey, setSortKey] = useState<SortKey>('severity');

  useEffect(() => {
    let active = true;
    (async () => {
      const i = await getIssues();
      if (!active) return;
      setIssues(i);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const result = issues.filter((i) => {
      if (search) {
        const q = search.toLowerCase();
        if (!i.id.toLowerCase().includes(q) && !i.flight.toLowerCase().includes(q) && !i.type.toLowerCase().includes(q)) return false;
      }
      if (sevFilter.size && !sevFilter.has(i.severity)) return false;
      if (statusFilter.size && !statusFilter.has(i.status)) return false;
      return true;
    });
    result.sort((a, b) => {
      if (sortKey === 'severity') return severityRank[a.severity] - severityRank[b.severity];
      if (sortKey === 'status') return statusRank[a.status] - statusRank[b.status];
      return new Date(a.createdTime).getTime() - new Date(b.createdTime).getTime();
    });
    return result;
  }, [issues, search, sevFilter, statusFilter, sortKey]);

  const toggle = (set: Set<string>, val: string, setter: (s: Set<string>) => void) => {
    const next = new Set(set);
    if (next.has(val)) next.delete(val);
    else next.add(val);
    setter(next);
  };

  if (loading) return <LoadingState message="Loading issues…" />;

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Issue Management</h1>
        <p className="text-sm text-slate-400">Track and prioritize crew-related operational issues.</p>
      </div>

      <div className="panel p-3 flex flex-col lg:flex-row lg:items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search issue ID, flight, type…" className="input w-full pl-8" />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-500">Severity:</span>
          {(['Critical', 'High', 'Medium', 'Low'] as Severity[]).map((s) => (
            <button key={s} onClick={() => toggle(sevFilter, s, setSevFilter)} className={`chip cursor-pointer ${sevFilter.has(s) ? 'bg-accent/20 text-accent-soft border-accent/40' : 'bg-console-800 text-slate-400 border-console-700 hover:text-slate-200'}`}>{s}</button>
          ))}
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-500">Status:</span>
          {(['New', 'Investigating', 'Action Required', 'Resolved'] as IssueStatus[]).map((s) => (
            <button key={s} onClick={() => toggle(statusFilter, s, setStatusFilter)} className={`chip cursor-pointer ${statusFilter.has(s) ? 'bg-accent/20 text-accent-soft border-accent/40' : 'bg-console-800 text-slate-400 border-console-700 hover:text-slate-200'}`}>{s}</button>
          ))}
        </div>
        <div className="flex items-center gap-1.5">
          <ArrowUpDown size={12} className="text-slate-500" />
          <select value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)} className="input text-xs py-1">
            <option value="severity">Sort: Severity</option>
            <option value="status">Sort: Status</option>
            <option value="created">Sort: Created</option>
          </select>
        </div>
      </div>

      <div className="panel">
        {filtered.length === 0 ? (
          <EmptyState title="No issues match your filters" />
        ) : (
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-console-700">
                  <th className="px-4 py-2 font-medium">Issue ID</th>
                  <th className="px-4 py-2 font-medium">Type</th>
                  <th className="px-4 py-2 font-medium">Flight</th>
                  <th className="px-4 py-2 font-medium">Severity</th>
                  <th className="px-4 py-2 font-medium">Crew Affected</th>
                  <th className="px-4 py-2 font-medium">Created</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Owner</th>
                  <th className="px-4 py-2 font-medium">Recommended Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-800">
                {filtered.map((i) => (
                  <tr key={i.id} className="hover:bg-console-850 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-slate-200">{i.id}</td>
                    <td className="px-4 py-2.5 text-slate-300">{i.type}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-200">{i.flight}</td>
                    <td className="px-4 py-2.5"><SeverityBadge severity={i.severity} /></td>
                    <td className="px-4 py-2.5 text-slate-300">{i.crewAffected}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{formatDateTime(i.createdTime)}</td>
                    <td className="px-4 py-2.5"><IssueStatusBadge status={i.status} /></td>
                    <td className="px-4 py-2.5 text-slate-300 text-xs">{i.owner}</td>
                    <td className="px-4 py-2.5 text-slate-400 text-xs max-w-xs">{i.recommendedAction}</td>
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
