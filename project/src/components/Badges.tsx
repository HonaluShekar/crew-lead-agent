import type { Severity, IssueStatus, WorkflowStatus, RiskStatus } from '@/types';

const severityStyles: Record<Severity, string> = {
  Critical: 'bg-severity-critical/15 text-red-300 border-severity-critical/40',
  High: 'bg-severity-high/15 text-orange-300 border-severity-high/40',
  Medium: 'bg-severity-medium/15 text-amber-300 border-severity-medium/40',
  Low: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
};

const severityDot: Record<Severity, string> = {
  Critical: 'bg-severity-critical',
  High: 'bg-severity-high',
  Medium: 'bg-severity-medium',
  Low: 'bg-slate-400',
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`chip ${severityStyles[severity]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${severityDot[severity]}`} />
      {severity}
    </span>
  );
}

const statusStyles: Record<IssueStatus, string> = {
  New: 'bg-blue-500/15 text-blue-300 border-blue-500/40',
  Investigating: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  'Action Required': 'bg-red-500/15 text-red-300 border-red-500/40',
  Resolved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
};

export function IssueStatusBadge({ status }: { status: IssueStatus }) {
  return <span className={`chip ${statusStyles[status]}`}>{status}</span>;
}

const workflowStyles: Record<WorkflowStatus, string> = {
  Waiting: 'bg-slate-500/15 text-slate-400 border-slate-500/40',
  Running: 'bg-blue-500/15 text-blue-300 border-blue-500/40 animate-pulse-soft',
  Completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
  Failed: 'bg-red-500/15 text-red-300 border-red-500/40',
};

export function WorkflowStatusBadge({ status }: { status: WorkflowStatus }) {
  return <span className={`chip ${workflowStyles[status]}`}>{status}</span>;
}

const riskStyles: Record<RiskStatus, string> = {
  Safe: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
  Watch: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  'At Risk': 'bg-orange-500/15 text-orange-300 border-orange-500/40',
  Critical: 'bg-red-500/15 text-red-300 border-red-500/40',
};

export function RiskBadge({ risk }: { risk: RiskStatus }) {
  return <span className={`chip ${riskStyles[risk]}`}>{risk}</span>;
}

export function AvailabilityBadge({ availability }: { availability: string }) {
  const map: Record<string, string> = {
    Available: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
    Assigned: 'bg-blue-500/15 text-blue-300 border-blue-500/40',
    'On Duty': 'bg-accent/15 text-blue-300 border-accent/40',
    Resting: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
    Unavailable: 'bg-red-500/15 text-red-300 border-red-500/40',
    'At Risk': 'bg-orange-500/15 text-orange-300 border-orange-500/40',
  };
  return <span className={`chip ${map[availability] ?? 'bg-slate-500/15 text-slate-300 border-slate-500/40'}`}>{availability}</span>;
}

export function CrewLegalityBadge({ status }: { status: 'Legal' | 'At Risk' | 'Illegal' }) {
  const map = {
    Legal: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
    'At Risk': 'bg-orange-500/15 text-orange-300 border-orange-500/40',
    Illegal: 'bg-red-500/15 text-red-300 border-red-500/40',
  };
  return <span className={`chip ${map[status]}`}>{status}</span>;
}

export function DisruptionTypeBadge({ type }: { type: string }) {
  const map: Record<string, string> = {
    Delay: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
    Cancellation: 'bg-red-500/15 text-red-300 border-red-500/40',
    'Crew Legality': 'bg-orange-500/15 text-orange-300 border-orange-500/40',
    'Replacement Required': 'bg-blue-500/15 text-blue-300 border-blue-500/40',
  };
  return <span className={`chip ${map[type] ?? 'bg-slate-500/15 text-slate-300 border-slate-500/40'}`}>{type}</span>;
}
