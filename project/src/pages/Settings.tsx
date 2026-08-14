import { useState } from 'react';
import { useToast } from '@/components/Toast';
import { Settings as SettingsIcon, Bell, Shield, Database, Bot } from 'lucide-react';

export function Settings() {
  const { push } = useToast();
  const [notifCritical, setNotifCritical] = useState(true);
  const [notifHigh, setNotifHigh] = useState(true);
  const [notifMedium, setNotifMedium] = useState(false);
  const [autoAnalyze, setAutoAnalyze] = useState(false);
  const [dutyBuffer, setDutyBuffer] = useState(15);

  const Toggle = ({ on, onClick }: { on: boolean; onClick: () => void }) => (
    <button
      onClick={onClick}
      className={`relative h-5 w-9 rounded-full transition-colors ${on ? 'bg-accent' : 'bg-console-700'}`}
    >
      <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${on ? 'translate-x-4' : 'translate-x-0.5'}`} />
    </button>
  );

  const Row = ({ icon: Icon, title, desc, children }: { icon: React.ElementType; title: string; desc: string; children: React.ReactNode }) => (
    <div className="flex items-center justify-between py-3 border-b border-console-800 last:border-0">
      <div className="flex items-center gap-3">
        <Icon size={16} className="text-slate-500" />
        <div>
          <p className="text-sm text-slate-200 font-medium">{title}</p>
          <p className="text-xs text-slate-500">{desc}</p>
        </div>
      </div>
      {children}
    </div>
  );

  return (
    <div className="space-y-4 animate-fade-in max-w-2xl">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Settings</h1>
        <p className="text-sm text-slate-400">Configure Crew Lead Operations Center preferences.</p>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2"><Bell size={14} /> Notifications</h2>
        </div>
        <div className="px-4">
          <Row icon={SettingsIcon} title="Critical alerts" desc="Notify on critical crew issues">
            <Toggle on={notifCritical} onClick={() => setNotifCritical(!notifCritical)} />
          </Row>
          <Row icon={SettingsIcon} title="High severity" desc="Notify on high severity disruptions">
            <Toggle on={notifHigh} onClick={() => setNotifHigh(!notifHigh)} />
          </Row>
          <Row icon={SettingsIcon} title="Medium severity" desc="Notify on medium severity issues">
            <Toggle on={notifMedium} onClick={() => setNotifMedium(!notifMedium)} />
          </Row>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2"><Bot size={14} /> AI Agent</h2>
        </div>
        <div className="px-4">
          <Row icon={Bot} title="Auto-analyze disruptions" desc="Run AI analysis automatically on new critical disruptions">
            <Toggle on={autoAnalyze} onClick={() => setAutoAnalyze(!autoAnalyze)} />
          </Row>
          <div className="flex items-center justify-between py-3 border-b border-console-800 last:border-0">
            <div className="flex items-center gap-3">
              <Shield size={16} className="text-slate-500" />
              <div>
                <p className="text-sm text-slate-200 font-medium">Duty-time buffer</p>
                <p className="text-xs text-slate-500">Minimum remaining duty minutes before flagging risk</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input type="number" value={dutyBuffer} onChange={(e) => setDutyBuffer(Number(e.target.value))} className="input w-16 text-center" />
              <span className="text-xs text-slate-500">min</span>
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2"><Database size={14} /> Backend</h2>
        </div>
          <div className="p-4">
            <p className="text-xs text-slate-400">
            The frontend reads CSV-backed operational data and deterministic assessments from the Python FastAPI service through <code className="text-slate-300 font-mono">src/services/api.ts</code>.
            </p>
          <button onClick={() => push('info', 'Settings saved.')} className="btn-primary mt-3">Save Settings</button>
        </div>
      </div>
    </div>
  );
}
