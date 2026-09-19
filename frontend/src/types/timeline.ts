export type TimelineEventType = "metric" | "log" | "deployment";

export interface TimelineEvent {
  id: string;
  timestamp: string;
  event_type: TimelineEventType;
  service_id: string;
  title: string;
  description: string | null;
  source_id: string;
  severity: string | null;
  metadata: Record<string, unknown>;
}

export interface TimelineResponse {
  incident_id: string;
  start_time: string;
  end_time: string;
  events: TimelineEvent[];
}