import {
  LayoutDashboard,
  AlertTriangle,
  Users,
  Plane,
  ListChecks,
  Bot,
  Activity,
  Settings,
  ShieldCheck,
} from 'lucide-react';

export type Page =
  | 'dashboard'
  | 'disruptions'
  | 'crew'
  | 'flights'
  | 'issues'
  | 'ai'
  | 'activity'
  | 'system'
  | 'settings';

interface SidebarProps {
  active: Page;
  onNavigate: (p: Page) => void;
  counts: { disruptions: number; issues: number; crew: number };
}

const nav: { id: Page; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'disruptions', label: 'Disruptions', icon: AlertTriangle },
  { id: 'crew', label: 'Crew', icon: Users },
  { id: 'flights', label: 'Flights', icon: Plane },
  { id: 'issues', label: 'Issues', icon: ListChecks },
  { id: 'ai', label: 'AI Crew Lead', icon: Bot },
  { id: 'activity', label: 'Agent Activity', icon: Activity },
];

export function Sidebar({ active, onNavigate, counts }: SidebarProps) {
  return (
    <aside className="w-56 shrink-0 bg-console-900 border-r border-console-700 flex flex-col">
      <nav className="flex-1 p-3 space-y-1">
        {nav.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          const badge =
            item.id === 'disruptions' ? counts.disruptions :
            item.id === 'issues' ? counts.issues :
            item.id === 'crew' ? counts.crew : null;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-accent/15 text-accent-soft border border-accent/30'
                  : 'text-slate-400 hover:bg-console-800 hover:text-slate-200 border border-transparent'
              }`}
            >
              <Icon size={16} className={isActive ? 'text-accent-soft' : 'text-slate-500'} />
              <span className="font-medium">{item.label}</span>
              {badge !== null && (
                <span className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded bg-console-700 text-slate-300">
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="p-3 border-t border-console-700 space-y-1">
        <button
          onClick={() => onNavigate('system')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
            active === 'system'
              ? 'bg-accent/15 text-accent-soft border border-accent/30'
              : 'text-slate-400 hover:bg-console-800 hover:text-slate-200 border border-transparent'
          }`}
        >
          <ShieldCheck size={16} className={active === 'system' ? 'text-accent-soft' : 'text-slate-500'} />
          <span className="font-medium">System Status</span>
          <span className="ml-auto h-2 w-2 rounded-full bg-status-ok animate-pulse-soft" />
        </button>
        <button
          onClick={() => onNavigate('settings')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
            active === 'settings'
              ? 'bg-accent/15 text-accent-soft border border-accent/30'
              : 'text-slate-400 hover:bg-console-800 hover:text-slate-200 border border-transparent'
          }`}
        >
          <Settings size={16} className={active === 'settings' ? 'text-accent-soft' : 'text-slate-500'} />
          <span className="font-medium">Settings</span>
        </button>
      </div>
    </aside>
  );
}
