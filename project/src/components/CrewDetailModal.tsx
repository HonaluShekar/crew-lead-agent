import { Modal } from '@/components/Modal';
import { RiskBadge, AvailabilityBadge } from '@/components/Badges';
import { formatTime, formatDuration, formatDateTime } from '@/lib/format';
import type { Crew } from '@/types';
import { Clock, Plane, AlertTriangle, Award, CalendarClock } from 'lucide-react';

interface CrewDetailModalProps {
  crew: Crew | null;
  open: boolean;
  onClose: () => void;
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-console-800 last:border-0">
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-sm text-slate-200 font-medium">{value}</span>
    </div>
  );
}

export function CrewDetailModal({ crew, open, onClose }: CrewDetailModalProps) {
  if (!crew) return null;
  return (
    <Modal open={open} onClose={onClose} title={`Crew ${crew.id}`} subtitle={`${crew.role} · Base ${crew.base}`} width="max-w-2xl">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <Award size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Qualifications</h3>
          </div>
          <InfoRow label="Role" value={crew.role} />
          <InfoRow label="Base" value={crew.base} />
          <InfoRow label="Qualification" value={crew.qualification} />
        </div>

        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <Clock size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Duty Information</h3>
          </div>
          <InfoRow label="Duty Start" value={crew.dutyStart ? formatTime(crew.dutyStart) : '—'} />
          <InfoRow label="Duty Elapsed" value={formatDuration(crew.dutyElapsedMinutes)} />
          <InfoRow label="Duty Remaining" value={formatDuration(crew.dutyRemainingMinutes)} />
          <InfoRow label="Rest Status" value={crew.restStatus} />
        </div>

        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <Plane size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Current Assignment</h3>
          </div>
          <InfoRow label="Current Flight" value={crew.currentFlight ?? '—'} />
          <InfoRow label="Availability" value={<AvailabilityBadge availability={crew.availability} />} />
          <InfoRow label="Risk Status" value={<RiskBadge risk={crew.riskStatus} />} />
        </div>

        <div className="panel p-4">
          <div className="flex items-center gap-2 mb-3">
            <CalendarClock size={14} className="text-accent-soft" />
            <h3 className="text-sm font-semibold text-slate-200">Upcoming Assignments</h3>
          </div>
          {crew.upcoming.length === 0 ? (
            <p className="text-xs text-slate-500 py-2">No upcoming assignments.</p>
          ) : (
            <ul className="space-y-2">
              {crew.upcoming.map((u) => (
                <li key={u.flightNumber} className="flex items-center justify-between text-sm">
                  <span className="text-slate-200 font-mono">{u.flightNumber}</span>
                  <span className="text-slate-400 text-xs">{u.route}</span>
                  <span className="text-slate-500 text-xs font-mono">{formatDateTime(u.departure)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel p-4 md:col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={14} className="text-severity-high" />
            <h3 className="text-sm font-semibold text-slate-200">Conflicts</h3>
          </div>
          {crew.conflicts.length === 0 ? (
            <p className="text-xs text-emerald-400">No conflicts detected.</p>
          ) : (
            <ul className="space-y-1.5">
              {crew.conflicts.map((c, i) => (
                <li key={i} className="text-sm text-orange-300 flex items-start gap-2">
                  <span className="text-orange-500 mt-0.5">•</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Modal>
  );
}
