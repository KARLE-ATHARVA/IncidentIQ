import type { Incident, IncidentListResponse } from "../types";

import type { TimelineResponse } from "../types/timeline";

import type { SimilarHistoricalIncident } from "../types/historicalRetrieval";

import type { InvestigationEvidence } from "../types/investigation";

import request from "./client";

export async function getIncidents(
  projectId: string,
): Promise<IncidentListResponse> {
  return request<IncidentListResponse>(`/api/projects/${projectId}/incidents`);
}

export async function getIncident(
  projectId: string,
  incidentId: string,
): Promise<Incident> {
  return request<Incident>(
    `/api/projects/${projectId}/incidents/${incidentId}`,
  );
}

export async function getIncidentTimeline(
  projectId: string,
  incidentId: string,
): Promise<TimelineResponse> {
  return request<TimelineResponse>(
    `/api/projects/${projectId}/incidents/${incidentId}/timeline`,
  );
}

export async function getSimilarHistoricalIncidents(
  projectId: string,
  incidentId: string,
  topK: number = 5,
  similarityThreshold: number = 0.65,
): Promise<SimilarHistoricalIncident[]> {
  const params = new URLSearchParams({
    top_k: String(topK),
    similarity_threshold: String(similarityThreshold),
  });

  return request<SimilarHistoricalIncident[]>(
    `/api/projects/${projectId}/incidents/${incidentId}/similar-incidents?${params.toString()}`,
  );
}

export async function getEvidenceInspection(
  projectId: string,
  incidentId: string,
  evidenceId: string,
): Promise<InvestigationEvidence> {
  return request<InvestigationEvidence>(
    `/api/projects/${projectId}/incidents/${incidentId}/evidence/${evidenceId}`,
  );
}
