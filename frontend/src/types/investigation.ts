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

export interface InvestigationEvidence {
  evidence_id: string;
  incident_id: string;
  source_type: string;
  source_id: string;
  title: string;
  description: string;
  collected_at: string;
  service_id: string | null;
  timestamp: string | null;
  details: Record<string, unknown>;
}

export interface InvestigationEvaluation {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  evidence_count: number;
  supporting_evidence_count: number;
  evidence_coverage: number;
}

export interface InvestigationResult {
  id: string;
  investigation_id: string;
  created_at: string;
  reasoning_source: string;
  hypothesis: string;
  confidence: number;
  reasoning: string;
  alternative_explanations: string[];
  next_steps: string[];
  supporting_evidence: InvestigationEvidence[];
  evaluation?: InvestigationEvaluation;
}