export interface Incident {
  id: string;
  project_id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  detected_at: string;
  resolved_at: string | null;
}

export interface IncidentSummary {
  id: string;
  title: string;
  severity: string;
  status: string;
  detected_at: string;
}

export interface IncidentListResponse {
  items: IncidentSummary[];
  count: number;
}