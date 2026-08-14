import type {
  Flight,
  Crew,
  Disruption,
  Issue,
  AgentStep,
  Recommendation,
  Alternative,
  RecoveryOption,
  AgentActivityEntry,
  Severity,
} from '@/types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let detail = `Backend request failed (${response.status})`;
    try {
      const body = await response.json() as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the HTTP status message when the backend did not return JSON.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export async function getFlights(): Promise<Flight[]> {
  return request<Flight[]>('/ui/flights');
}

export async function getCrew(): Promise<Crew[]> {
  return request<Crew[]>('/ui/crew');
}

export async function getDisruptions(): Promise<Disruption[]> {
  return request<Disruption[]>('/ui/disruptions');
}

export async function getIssues(): Promise<Issue[]> {
  return request<Issue[]>('/ui/issues');
}

export async function getAgentActivity(): Promise<AgentActivityEntry[]> {
  return request<AgentActivityEntry[]>('/ui/activity');
}

export interface RecentRecommendation {
  id: string;
  flight: string;
  text: string;
  severity: Severity;
  time: string;
}

export async function getRecentRecommendations(): Promise<RecentRecommendation[]> {
  return request<RecentRecommendation[]>('/ui/recommendations');
}

export async function getCrewAvailabilitySnapshot(): Promise<Record<string, number>> {
  return request<Record<string, number>>('/ui/availability-snapshot');
}

export interface AnalysisResult {
  flightId: string;
  steps: AgentStep[];
  recommendation: Recommendation;
  alternatives: Alternative[];
  recoveryOptions: RecoveryOption[];
}

export async function runAnalysis(query: string): Promise<AnalysisResult> {
  return request<AnalysisResult>('/ui/analyze', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}
