import { useEffect, useRef, useState } from 'react';
import { WorkflowStatusBadge } from '@/components/Badges';
import { useToast } from '@/components/Toast';
import { runAnalysis } from '@/services/api';
import { examplePrompts } from '@/data/mock';
import type { AgentStep, Recommendation, Alternative, RecoveryOption, WorkflowStatus } from '@/types';
import {
  Bot,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertTriangle,
  GitBranch,
  ChevronRight,
  Sparkles,
  Info,
  Users,
  Clock3,
  Plane,
  Scale,
} from 'lucide-react';

interface AICrewLeadProps {
  initialQuery?: string;
}

export function AICrewLead({ initialQuery }: AICrewLeadProps) {
  const { push } = useToast();
  const [query, setQuery] = useState(initialQuery || examplePrompts[0]);
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [alternatives, setAlternatives] = useState<Alternative[]>([]);
  const [recoveryOptions, setRecoveryOptions] = useState<RecoveryOption[]>([]);
  const [completed, setCompleted] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [expandedDetail, setExpandedDetail] = useState<string | null>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  useEffect(() => {
    if (initialQuery) setQuery(initialQuery);
  }, [initialQuery]);

  const reset = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setSteps([]);
    setRecommendation(null);
    setAlternatives([]);
    setRecoveryOptions([]);
    setCompleted(false);
    setShowAlternatives(false);
    setExpandedDetail(null);
  };

  const run = async () => {
    if (!query.trim() || running) return;
    reset();
    setRunning(true);
    push('info', 'Backend decision-support analysis started.');

    const result = await runAnalysis(query);
    setSteps(result.steps);
    setAlternatives(result.alternatives);
    setRecoveryOptions(result.recoveryOptions);

    const stepDelay = 650;
    result.steps.forEach((_, idx) => {
      timers.current.push(setTimeout(() => {
        setSteps((previous) => previous.map((step, index) => (
          index === idx ? { ...step, status: 'Running' as WorkflowStatus, startedAt: new Date().toISOString() } : step
        )));
      }, idx * stepDelay));
      timers.current.push(setTimeout(() => {
        setSteps((previous) => previous.map((step, index) => (
          index === idx ? { ...step, status: 'Completed' as WorkflowStatus, completedAt: new Date().toISOString() } : step
        )));
        if (idx === result.steps.length - 1) {
          setRecommendation(result.recommendation);
          setCompleted(true);
          setRunning(false);
          push('success', 'Decision-support recommendation generated for review.');
        }
      }, idx * stepDelay + stepDelay * 0.72));
    });
  };

  const statusIcon = (status: WorkflowStatus) => {
    if (status === 'Completed') return <CheckCircle2 size={16} className="text-emerald-400" />;
    if (status === 'Running') return <Loader2 size={16} className="text-blue-400 animate-spin" />;
    if (status === 'Failed') return <XCircle size={16} className="text-red-400" />;
    return <div className="h-4 w-4 rounded-full border-2 border-console-600" />;
  };

  const riskClass = (risk: string) => risk === 'Low'
    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
    : risk === 'Medium'
      ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
      : 'bg-red-500/15 text-red-300 border-red-500/40';

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center">
            <Bot size={18} className="text-accent-soft" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-100">AI Crew Lead</h1>
            <p className="text-sm text-slate-400">Analyze crew operational issues and recommend the safest operational recovery.</p>
          </div>
        </div>
      </div>

      <div className="panel p-4">
        <label className="text-xs text-slate-400 uppercase tracking-wider font-medium">Query</label>
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          rows={3}
          placeholder="Describe the crew operational issue to analyze…"
          className="input w-full mt-2 resize-none"
          onKeyDown={(event) => {
            if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) run();
          }}
        />
        <div className="flex items-center justify-between mt-3 flex-wrap gap-2">
          <div className="flex flex-wrap gap-1.5">
            {examplePrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => setQuery(prompt)}
                className="text-xs px-2 py-1 rounded bg-console-800 border border-console-700 text-slate-400 hover:text-slate-200 hover:border-console-600 transition-colors max-w-xs truncate"
                title={prompt}
              >
                {prompt.length > 50 ? `${prompt.slice(0, 50)}…` : prompt}
              </button>
            ))}
          </div>
          <button onClick={run} disabled={running || !query.trim()} className="btn-primary">
            {running ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {running ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>
      </div>

      {steps.length > 0 && (
        <div className="panel">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <GitBranch size={14} className="text-accent-soft" /> Agent Workflow
            </h2>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">FastAPI workflow · no operational changes</span>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-y-5 overflow-x-auto scrollbar-thin pb-2">
              {steps.map((step, index) => (
                <div key={step.id} className="relative flex flex-col items-center min-w-[140px]">
                  {index < steps.length - 1 && <ChevronRight size={16} className={`hidden md:block absolute top-4 -right-2 ${step.status === 'Completed' ? 'text-emerald-500/50' : 'text-console-600'}`} />}
                  <div className={`flex items-center justify-center h-10 w-10 rounded-full border-2 transition-colors ${
                    step.status === 'Completed' ? 'border-emerald-500/50 bg-emerald-500/10' :
                    step.status === 'Running' ? 'border-blue-500/50 bg-blue-500/10' :
                    step.status === 'Failed' ? 'border-red-500/50 bg-red-500/10' :
                    'border-console-600 bg-console-800'
                  }`}>
                    {statusIcon(step.status)}
                  </div>
                  <p className="text-xs font-medium text-slate-200 text-center mt-2">{step.label}</p>
                  <p className="text-[10px] text-slate-500 text-center mt-0.5">{step.agent}</p>
                  <WorkflowStatusBadge status={step.status} />
                </div>
              ))}
            </div>
            <div className="mt-4 space-y-1.5 border-t border-console-800 pt-3">
              {steps.map((step) => (
                <div key={step.id} className="flex items-center gap-3 text-xs">
                  {statusIcon(step.status)}
                  <span className="text-slate-300 font-medium w-48 shrink-0">{step.label}</span>
                  <span className="text-slate-500">{step.description}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {steps.length === 0 && !running && (
        <div className="panel p-8 flex flex-col items-center text-center">
          <div className="h-12 w-12 rounded-full bg-console-800 border border-console-700 flex items-center justify-center mb-3">
            <Bot size={20} className="text-slate-500" />
          </div>
          <p className="text-sm font-medium text-slate-300">Ready to analyze</p>
          <p className="text-xs text-slate-500 mt-1 max-w-md">Enter a crew operational query above and click Analyze to run a simulated decision-support workflow. No operational change is executed automatically.</p>
        </div>
      )}

      {recoveryOptions.length > 0 && completed && (
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2"><Scale size={14} className="text-accent-soft" /> Recovery Options</h2>
            <span className="text-xs text-slate-500">Compare before deciding</span>
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-3 p-4">
            {recoveryOptions.map((option) => {
              const detailOpen = expandedDetail === option.id;
              return (
                <div key={option.id} className={`rounded-lg border p-4 ${option.recommended ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-console-700 bg-console-850'}`}>
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-100">{option.action}</p>
                    {option.recommended && <span className="chip bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shrink-0">Recommended</span>}
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
                    <div><p className="text-slate-500">Crew involved</p><p className="text-slate-200 font-mono mt-0.5">{option.crewIds.join(', ')}</p></div>
                    <div><p className="text-slate-500">Qualification</p><p className="text-emerald-300 mt-0.5">{option.qualificationStatus}</p></div>
                    <div><p className="text-slate-500">Duty remaining</p><p className="text-slate-200 font-mono mt-0.5">{Math.floor(option.dutyRemainingMinutes / 60)}h {option.dutyRemainingMinutes % 60}m</p></div>
                    <div><p className="text-slate-500">Rest status</p><p className="text-slate-200 mt-0.5">{option.restStatus}</p></div>
                    <div><p className="text-slate-500">Downstream impact</p><p className="text-slate-200 mt-0.5">{option.downstreamImpact.flightsProtected} protected</p></div>
                    <div><p className="text-slate-500">Operational risk</p><span className={`chip mt-0.5 ${riskClass(option.operationalRisk)}`}>{option.operationalRisk}</span></div>
                  </div>
                  <button onClick={() => setExpandedDetail(detailOpen ? null : option.id)} className="btn-ghost px-0 mt-4 text-xs text-accent-soft">
                    <Info size={13} /> {detailOpen ? 'Hide tradeoffs' : 'View tradeoffs'}
                  </button>
                  {detailOpen && <ul className="mt-2 space-y-1 border-t border-console-700 pt-2">{option.tradeoffs.map((tradeoff) => <li key={tradeoff} className="text-xs text-slate-400">• {tradeoff}</li>)}</ul>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {recommendation && completed && (
        <div className="panel border-emerald-500/30 animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2"><CheckCircle2 size={14} className="text-emerald-400" /> Final Recommendation</h2>
            <span className={`chip ${riskClass(recommendation.risk)}`}>Risk: {recommendation.risk}</span>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">Recommended Action</p>
              <p className="text-base font-semibold text-slate-100 mt-1">{recommendation.recommendedAction}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-console-850 border border-console-700 rounded-md p-3 space-y-2">
                <div className="flex gap-2 text-sm text-slate-200"><Plane size={14} className="text-accent-soft mt-0.5" /> <span><strong className="text-slate-400 font-normal">Affected flight:</strong> {recommendation.affectedFlight}</span></div>
                <div className="flex gap-2 text-sm text-slate-200"><Users size={14} className="text-accent-soft mt-0.5" /> <span><strong className="text-slate-400 font-normal">Affected crew:</strong> {recommendation.affectedCrew.join(', ')}</span></div>
                <div className="flex gap-2 text-sm text-slate-200"><Clock3 size={14} className="text-orange-300 mt-0.5" /> <span><strong className="text-slate-400 font-normal">Duty-time impact:</strong> {recommendation.dutyTimeImpact}</span></div>
                <div className="flex gap-2 text-sm text-slate-200"><GitBranch size={14} className="text-emerald-400 mt-0.5" /> <span><strong className="text-slate-400 font-normal">Downstream impact:</strong> {recommendation.downstreamImpactSummary}</span></div>
              </div>
              <div className="bg-console-850 border border-console-700 rounded-md p-3">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-medium mb-2">Why this action is recommended</p>
                <ul className="space-y-1.5">{recommendation.reason.map((reason) => <li key={reason} className="text-sm text-slate-300 flex items-start gap-2"><CheckCircle2 size={14} className="text-emerald-400 mt-0.5 shrink-0" /><span>{reason}</span></li>)}</ul>
              </div>
            </div>
            <div className="flex items-center gap-2 pt-1 flex-wrap">
              <button onClick={() => push('info', 'Recommendation acknowledged for crew lead review. No operational change was executed.')} className="btn-primary"><CheckCircle2 size={14} /> Accept Recommendation</button>
              <button onClick={() => { setShowAlternatives(true); push('info', 'Alternative recovery options are shown above.'); }} className="btn-outline">View Alternatives</button>
              <button onClick={() => { setRecommendation(null); push('warning', 'Recommendation rejected. No operational change was executed.'); }} className="btn-ghost text-slate-400">Reject</button>
            </div>
            {showAlternatives && <p className="text-xs text-slate-500">Review the Recovery Options above before making an operational decision.</p>}
          </div>
        </div>
      )}

      {alternatives.length > 0 && completed && (
        <div className="panel animate-fade-in">
          <div className="panel-header"><h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2"><AlertTriangle size={14} className="text-amber-400" /> Alternative Options</h2></div>
          <div className="divide-y divide-console-800">
            {alternatives.map((alternative) => (
              <div key={alternative.id} className="px-4 py-3 flex items-start justify-between gap-4">
                <div><p className="text-sm text-slate-200">{alternative.summary}</p><ul className="mt-2 space-y-1">{alternative.tradeoffs.map((tradeoff) => <li key={tradeoff} className="text-xs text-slate-400">• {tradeoff}</li>)}</ul></div>
                <span className={`chip shrink-0 ${riskClass(alternative.risk)}`}>Risk: {alternative.risk}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
