import { Modal } from '@/components/Modal';
import { SeverityBadge, CrewLegalityBadge, DisruptionTypeBadge } from '@/components/Badges';
import { formatTime, delayText } from '@/lib/format';
import type { Disruption, Crew, Flight } from '@/types';
import { Plane, Clock, GitBranch, AlertTriangle, Bot } from 'lucide-react';

interface DisruptionDetailModalProps {
  disruption: Disruption | null;
  crewMap: Record<string, Crew>;
  flightMap: Record<string, Flight>;
  open: boolean;
  onClose: () => void;
  onCrewClick: (crew: Crew) => void;
  onAnalyze: (disruption: Disruption) => void;
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-console-800 last:border-0">
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-sm text-slate-200 font-medium">{value}</span>
    </div>
  );
}

export function DisruptionDetailModal({
  disruption,
  crewMap,
  open,
  onClose,
  onCrewClick,
  onAnalyze,
}: DisruptionDetailModalProps) {
  if (!disruption) return null;
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Disruption · ${disruption.flightNumber}`}
      subtitle={`${disruption.origin} → ${disruption.destination}`}
      width="max-w-3xl"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <Plane size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Flight Information</h3>
          </div>
          <InfoRow label="Flight" value={disruption.flightNumber} />
          <InfoRow label="Route" value={`${disruption.origin} → ${disruption.destination}`} />
          <InfoRow label="Scheduled Departure" value={formatTime(disruption.scheduledDeparture)} />
          <InfoRow label="Estimated Departure" value={formatTime(disruption.estimatedDeparture)} />
          <InfoRow label="Delay" value={delayText(disruption.delayMinutes)} />
          <InfoRow label="Type" value={<DisruptionTypeBadge type={disruption.type} />} />
          <InfoRow label="Severity" value={<SeverityBadge severity={disruption.severity} />} />
        </div>

        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <Clock size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Crew Duty Information</h3>
          </div>
          <InfoRow label="Crew Legality" value={<CrewLegalityBadge status={disruption.crewLegality} />} />
          <div className="mt-3">
            <p className="text-xs text-slate-400 mb-2">Assigned Crew</p>
            <ul className="space-y-1">
              {disruption.assignedCrew.map((id) => {
                const c = crewMap[id];
                return (
                  <li key={id}>
                    <button
                      onClick={() => c && onCrewClick(c)}
                      className="w-full flex items-center justify-between px-2 py-1.5 rounded text-sm hover:bg-console-800 transition-colors"
                    >
                      <span className="text-slate-200 font-mono">{id}</span>
                      <span className="text-xs text-slate-400">{c?.role ?? 'Unknown'}</span>
                      <span className="text-xs text-slate-500">Duty rem: {c ? Math.floor(c.dutyRemainingMinutes / 60) : '—'}h{c ? c.dutyRemainingMinutes % 60 : ''}m</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>

        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={14} className="text-severity-high" />
            <h3 className="text-sm font-semibold text-slate-200">Current Disruption</h3>
          </div>
          <p className="text-sm text-slate-300">{disruption.reason}</p>
        </div>

        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Downstream Flights</h3>
          </div>
          {disruption.downstreamFlights.length === 0 ? (
            <p className="text-xs text-slate-500">No downstream flights affected.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {disruption.downstreamFlights.map((f) => (
                <span key={f} className="chip bg-amber-500/15 text-amber-300 border-amber-500/40 font-mono">
                  {f}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="panel p-4 md:col-span-2 border-dashed">
          <div className="flex items-center gap-2 mb-3">
            <Bot size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">AI Recommendation</h3>
            <span className="chip bg-slate-500/15 text-slate-400 border-slate-500/40 ml-auto">Placeholder</span>
          </div>
          <p className="text-sm text-slate-400">
            Run the AI Crew Lead analysis to generate a recommendation for this disruption. The agent will evaluate crew
            availability, duty-time limits, downstream impact, and qualifications.
          </p>
          <button onClick={() => onAnalyze(disruption)} className="btn-primary mt-3">
            <Bot size={14} /> Analyze Disruption
          </button>
        </div>
      </div>
    </Modal>
  );
}
