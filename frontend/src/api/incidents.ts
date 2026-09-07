import type {
  Incident,
  IncidentListResponse,
} from "../types";

import request from "./client";


export async function getIncidents(
  projectId: string,
): Promise<IncidentListResponse> {
  return request<IncidentListResponse>(
    `/api/projects/${projectId}/incidents`,
  );
}


export async function getIncident(
  projectId: string,
  incidentId: string,
): Promise<Incident> {
  return request<Incident>(
    `/api/projects/${projectId}/incidents/${incidentId}`,
  );
}