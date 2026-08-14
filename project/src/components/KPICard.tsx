import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  label: string;
  value: number | string;
  delta?: string;
  trend?: 'up' | 'down' | 'flat';
  tone?: 'critical' | 'warning' | 'info' | 'ok' | 'neutral';
  icon?: React.ElementType;
}

const toneStyles: Record<string, string> = {
  critical: 'border-severity-critical/30 bg-severity-critical/5',
  warning: 'border-severity-high/30 bg-severity-high/5',
  info: 'border-accent/30 bg-accent/5',
  ok: 'border-status-ok/30 bg-status-ok/5',
  neutral: 'border-console-700 bg-console-900',
};

const valueColor: Record<string, string> = {
  critical: 'text-red-300',
  warning: 'text-orange-300',
  info: 'text-blue-300',
  ok: 'text-emerald-300',
  neutral: 'text-slate-100',
};

export function KPICard({ label, value, delta, trend = 'flat', tone = 'neutral', icon: Icon }: KPICardProps) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-red-400' : trend === 'down' ? 'text-emerald-400' : 'text-slate-500';
  return (
    <div className={`panel rounded-lg p-4 ${toneStyles[tone]}`}>
      <div className="flex items-start justify-between">
        <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">{label}</p>
        {Icon && <Icon size={16} className="text-slate-500" />}
      </div>
      <div className="mt-2 flex items-end justify-between">
        <p className={`text-2xl font-semibold font-mono ${valueColor[tone]}`}>{value}</p>
        {delta && (
          <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
            <TrendIcon size={12} />
            <span>{delta}</span>
          </div>
        )}
      </div>
    </div>
  );
}
