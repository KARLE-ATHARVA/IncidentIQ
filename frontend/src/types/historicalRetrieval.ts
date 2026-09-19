export interface SimilarHistoricalIncident {
  historical_incident_id: string;
  title: string;
  summary: string;
  symptoms: string;
  root_cause: string | null;
  resolution: string | null;
  severity: string;
  service_id: string | null;
  occurred_at: string;
  similarity_score: number;
}