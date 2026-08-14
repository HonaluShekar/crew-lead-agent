import { Search, Bell, ChevronDown } from 'lucide-react';

interface HeaderProps {
  now: Date;
  onSearch: (q: string) => void;
  search: string;
}

export function Header({ now, onSearch, search }: HeaderProps) {
  const dateStr = now.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
  const timeStr = now.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });

  return (
    <header className="h-14 shrink-0 border-b border-console-700 bg-console-900 flex items-center px-4 gap-4">
      <div className="flex items-center gap-2.5">
        <div className="h-8 w-8 rounded-md bg-accent/20 border border-accent/40 flex items-center justify-center">
          <span className="text-accent-soft font-bold text-sm">CL</span>
        </div>
        <div className="leading-tight">
          <h1 className="text-sm font-semibold text-slate-100">Crew Lead Operations Center</h1>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Airline Operations Control</p>
        </div>
      </div>

      <div className="hidden md:flex items-center gap-2 ml-2 px-3 py-1 rounded-md bg-console-850 border border-console-700">
        <span className="h-1.5 w-1.5 rounded-full bg-status-ok animate-pulse-soft" />
        <span className="text-xs text-slate-300 font-mono">{dateStr} · {timeStr} IST</span>
      </div>

      <div className="flex-1 max-w-md mx-auto hidden sm:block">
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Search flights, crew, issues…"
            className="input w-full pl-8"
          />
        </div>
      </div>

      <div className="flex items-center gap-1 ml-auto">
        <button className="btn-ghost relative p-2" title="Notifications">
          <Bell size={16} />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-severity-critical" />
        </button>
        <button className="btn-ghost flex items-center gap-2 px-2 py-1">
          <div className="h-7 w-7 rounded-full bg-console-700 border border-console-600 flex items-center justify-center text-xs font-semibold text-slate-200">
            RS
          </div>
          <div className="hidden md:block text-left leading-tight">
            <p className="text-xs text-slate-200 font-medium">R. Sharma</p>
            <p className="text-[10px] text-slate-500">Crew Lead · DEL</p>
          </div>
          <ChevronDown size={14} className="text-slate-500" />
        </button>
      </div>
    </header>
  );
}
