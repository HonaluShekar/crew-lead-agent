import { useEffect, useState } from 'react';
import { Sidebar, type Page } from '@/components/Sidebar';
import { Header } from '@/components/Header';
import { ToastProvider } from '@/components/Toast';
import { Dashboard } from '@/pages/Dashboard';
import { Disruptions } from '@/pages/Disruptions';
import { CrewPage } from '@/pages/CrewPage';
import { Flights } from '@/pages/Flights';
import { Issues } from '@/pages/Issues';
import { AICrewLead } from '@/pages/AICrewLead';
import { AgentActivity } from '@/pages/AgentActivity';
import { SystemStatus } from '@/pages/SystemStatus';
import { Settings } from '@/pages/Settings';
import { CrewDetailModal } from '@/components/CrewDetailModal';
import { FlightDetailModal } from '@/components/FlightDetailModal';
import { DisruptionDetailModal } from '@/components/DisruptionDetailModal';
import { getCrew, getDisruptions, getIssues } from '@/services/api';
import type { Crew, Disruption, Flight } from '@/types';

function AppInner() {
  const [page, setPage] = useState<Page>('dashboard');
  const [search, setSearch] = useState('');
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [now, setNow] = useState(new Date());

  const [crewList, setCrewList] = useState<Crew[]>([]);
  const [disruptionList, setDisruptionList] = useState<Disruption[]>([]);
  const [issueCount, setIssueCount] = useState(0);
  const [crewMap, setCrewMap] = useState<Record<string, Crew>>({});

  // modal state
  const [openCrew, setOpenCrew] = useState<Crew | null>(null);
  const [openFlight, setOpenFlight] = useState<Flight | null>(null);
  const [openDisruption, setOpenDisruption] = useState<Disruption | null>(null);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      const [c, d, i] = await Promise.all([getCrew(), getDisruptions(), getIssues()]);
      if (!active) return;
      setCrewList(c);
      setDisruptionList(d);
      setIssueCount(i.filter((x) => x.status !== 'Resolved').length);
      setCrewMap(Object.fromEntries(c.map((x) => [x.id, x])));
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleNavigate = (p: Page) => {
    setPage(p);
    setOpenCrew(null);
    setOpenFlight(null);
    setOpenDisruption(null);
  };

  const handleAnalyzeDisruption = (d: Disruption) => {
    setOpenDisruption(null);
    setAnalysisQuery(
      `Analyze the crew disruption for flight ${d.flightNumber}. Check duty time, replacement options, and downstream impact.`,
    );
    setPage('ai');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-console-950">
      <Sidebar active={page} onNavigate={handleNavigate} counts={{ disruptions: disruptionList.length, issues: issueCount, crew: crewList.length }} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header now={now} onSearch={setSearch} search={search} />
        <main className="flex-1 overflow-y-auto scrollbar-thin p-4 md:p-6">
          {page === 'dashboard' && (
            <Dashboard
              onOpenDisruption={(d) => setOpenDisruption(d)}
              onNavigate={(p) => setPage(p)}
            />
          )}
          {page === 'disruptions' && (
            <Disruptions onOpenDisruption={(d) => setOpenDisruption(d)} />
          )}
          {page === 'crew' && (
            <CrewPage onCrewClick={(c) => setOpenCrew(c)} />
          )}
          {page === 'flights' && (
            <Flights onFlightClick={(f, cm) => { setOpenFlight(f); setCrewMap((prev) => ({ ...prev, ...cm })); }} />
          )}
          {page === 'issues' && <Issues />}
          {page === 'ai' && <AICrewLead initialQuery={analysisQuery || undefined} />}
          {page === 'activity' && <AgentActivity />}
          {page === 'system' && <SystemStatus />}
          {page === 'settings' && <Settings />}
        </main>
      </div>

      <CrewDetailModal crew={openCrew} open={!!openCrew} onClose={() => setOpenCrew(null)} />
      <FlightDetailModal flight={openFlight} crewMap={crewMap} open={!!openFlight} onClose={() => setOpenFlight(null)} onCrewClick={(c) => setOpenCrew(c)} />
      <DisruptionDetailModal
        disruption={openDisruption}
        crewMap={crewMap}
        flightMap={{}}
        open={!!openDisruption}
        onClose={() => setOpenDisruption(null)}
        onCrewClick={(c) => setOpenCrew(c)}
        onAnalyze={handleAnalyzeDisruption}
      />
    </div>
  );
}

function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  );
}

export default App;
