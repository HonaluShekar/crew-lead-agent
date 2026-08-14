export type Severity = 'Critical' | 'High' | 'Medium' | 'Low';
export type IssueStatus = 'New' | 'Investigating' | 'Action Required' | 'Resolved';
export type DisruptionType = 'Delay' | 'Cancellation' | 'Crew Legality' | 'Replacement Required';
export type Availability =
  | 'Available'
  | 'Assigned'
  | 'On Duty'
  | 'Resting'
  | 'Unavailable'
  | 'At Risk';
export type RiskStatus = 'Safe' | 'Watch' | 'At Risk' | 'Critical';
export type WorkflowStatus = 'Waiting' | 'Running' | 'Completed' | 'Failed';

export interface Flight {
  id: string;
  number: string;
  origin: string;
  destination: string;
  aircraft: string;
  scheduledDeparture: string; // ISO
  estimatedDeparture: string; // ISO
  arrival: string; // ISO
  delayMinutes: number;
  assignedCrew: string[]; // crew ids
  crewStatus: 'Legal' | 'At Risk' | 'Illegal';
  disruptionStatus: 'None' | 'Delay' | 'Cancellation' | 'Crew Issue';
  downstreamImpact: number; // count of affected downstream flights
  downstreamFlights: string[]; // flight numbers
  route: string;
}

export interface Crew {
  id: string;
  role: 'Captain' | 'First Officer' | 'Senior Cabin Crew' | 'Cabin Crew';
  base: string;
  qualification: string;
  currentFlight: string | null;
  dutyStart: string | null; // ISO
  dutyElapsedMinutes: number;
  dutyRemainingMinutes: number;
  restStatus: 'Rested' | 'Resting' | 'Rest Required' | 'Insufficient';
  availability: Availability;
  riskStatus: RiskStatus;
  upcoming: { flightNumber: string; departure: string; route: string }[];
  conflicts: string[];
}

export interface Disruption {
  id: string;
  flightNumber: string;
  origin: string;
  destination: string;
  scheduledDeparture: string;
  estimatedDeparture: string;
  delayMinutes: number;
  type: DisruptionType;
  assignedCrew: string[];
  crewLegality: 'Legal' | 'At Risk' | 'Illegal';
  downstreamFlights: string[];
  severity: Severity;
  status: 'Active' | 'Monitoring' | 'Resolved';
  reason: string;
}

export interface Issue {
  id: string;
  type:
    | 'Duty Time'
    | 'Replacement Required'
    | 'Qualification Conflict'
    | 'Downstream Impact'
    | 'Crew Shortage'
    | 'Rest Violation';
  flight: string;
  severity: Severity;
  crewAffected: number;
  crewIds: string[];
  createdTime: string;
  status: IssueStatus;
  owner: string;
  recommendedAction: string;
  description: string;
}

export interface AgentStep {
  id: string;
  label: string;
  agent: string;
  description: string;
  status: WorkflowStatus;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
  details?: ExplainabilityDetail;
}

export interface Recommendation {
  id: string;
  title: string;
  recommendedAction: string;
  reason: string[];
  affectedFlight: string;
  affectedCrew: string[];
  dutyTimeImpact: string;
  downstreamImpactSummary: string;
  impact: { downstreamProtected: number; reassignments: number };
  risk: 'Low' | 'Medium' | 'High';
  crewId?: string;
  flightNumber: string;
}

export interface Alternative {
  id: string;
  summary: string;
  tradeoffs: string[];
  risk: 'Low' | 'Medium' | 'High';
}

export interface RecoveryOption {
  id: string;
  action: string;
  crewIds: string[];
  qualificationStatus: 'Qualified' | 'Partial' | 'Not Qualified';
  dutyRemainingMinutes: number;
  restStatus: 'Rested' | 'Resting' | 'Rest Required' | 'Insufficient';
  downstreamImpact: { flightsProtected: number; flightsAtRisk: string[] };
  operationalRisk: 'Low' | 'Medium' | 'High';
  tradeoffs: string[];
  recommended: boolean;
}

export interface ExplainabilityDetail {
  kind: 'duty-risk' | 'replacement-candidate';
  dutyRisk?: {
    currentDutyElapsed: string;
    projectedDuty: string;
    maxAllowed: string;
    projectedViolation: string;
  };
  replacementCandidate?: {
    qualification: string;
    availableAtBase: boolean;
    restSatisfied: boolean;
    dutyRemainingSufficient: boolean;
    noConflictingAssignment: boolean;
  };
}

export interface AgentActivityEntry {
  id: string;
  step: number;
  label: string;
  agent: string;
  tool: string;
  description: string;
  timestamp: string;
  status: WorkflowStatus;
  durationMs: number;
}
