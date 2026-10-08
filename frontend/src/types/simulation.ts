export interface SimulationResponse {
  scenario: string;
  status: string;
  incident_id: string | null;
  severity: string | null;
  incident_status: string | null;
  title: string | null;
}

export interface SimulationStateResponse {
  active: boolean;
  scenario: string | null;
  status: string | null;
  incident_id: string | null;
  severity: string | null;
  incident_status: string | null;
  title: string | null;
}

export interface SimulationResetResponse {
  status: string;
  deleted_run_id: string | null;
}
