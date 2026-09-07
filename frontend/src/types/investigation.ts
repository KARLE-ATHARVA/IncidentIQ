export type InvestigationStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export interface Investigation {
  id: string;
  incident_id: string;
  status: InvestigationStatus;
  started_at: string | null;
  completed_at: string | null;
}