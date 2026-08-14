import { Modal } from '@/components/Modal';
import { CrewLegalityBadge } from '@/components/Badges';
import { formatTime, delayText } from '@/lib/format';
import type { Flight, Crew } from '@/types';
import { Plane, Users, GitBranch } from 'lucide-react';

interface FlightDetailModalProps {
  flight: Flight | null;
  crewMap: Record<string, Crew>;
  open: boolean;
  onClose: () => void;
  onCrewClick: (crew: Crew) => void;
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-console-800 last:border-0">
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-sm text-slate-200 font-medium">{value}</span>
    </div>
  );
}

export function FlightDetailModal({ flight, crewMap, open, onClose, onCrewClick }: FlightDetailModalProps) {
  if (!flight) return null;
  return (
    <Modal open={open} onClose={onClose} title={`Flight ${flight.number}`} subtitle={`${flight.route} · ${flight.aircraft}`} width="max-w-2xl">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <Plane size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Flight Information</h3>
          </div>
          <InfoRow label="Route" value={flight.route} />
          <InfoRow label="Aircraft" value={flight.aircraft} />
          <InfoRow label="Scheduled Departure" value={formatTime(flight.scheduledDeparture)} />
          <InfoRow label="Estimated Departure" value={formatTime(flight.estimatedDeparture)} />
          <InfoRow label="Arrival" value={formatTime(flight.arrival)} />
          <InfoRow label="Delay" value={delayText(flight.delayMinutes)} />
          <InfoRow label="Crew Status" value={<CrewLegalityBadge status={flight.crewStatus} />} />
        </div>

        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <Users size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Assigned Crew</h3>
          </div>
          <ul className="space-y-1">
            {flight.assignedCrew.map((id) => {
              const c = crewMap[id];
              return (
                <li key={id}>
                  <button
                    onClick={() => c && onCrewClick(c)}
                    className="w-full flex items-center justify-between px-2 py-1.5 rounded text-sm hover:bg-console-800 transition-colors"
                  >
                    <span className="text-slate-200 font-mono">{id}</span>
                    <span className="text-xs text-slate-400">{c?.role ?? 'Unknown'}</span>
                    <span className="text-xs text-slate-500">{c?.base ?? '—'}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="panel p-4 md:col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Downstream Impact</h3>
          </div>
          <InfoRow label="Affected Downstream Flights" value={flight.downstreamImpact} />
          {flight.downstreamFlights.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {flight.downstreamFlights.map((f) => (
                <span key={f} className="chip bg-amber-500/15 text-amber-300 border-amber-500/40 font-mono">
                  {f}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
