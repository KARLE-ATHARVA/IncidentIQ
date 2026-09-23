import type {
  Investigation,
  InvestigationResult,
} from "../types";

import request from "./client";

export async function getInvestigations(
  projectId: string,
  incidentId: string,
): Promise<Investigation[]> {
  return request<Investigation[]>(
    `/api/projects/${projectId}/incidents/${incidentId}/investigations`,
  );
}

export async function createInvestigation(
  projectId: string,
  incidentId: string,
): Promise<Investigation> {
  return request<Investigation>(
    `/api/projects/${projectId}/incidents/${incidentId}/investigations`,
    {
      method: "POST",
    },
  );
}

export async function startInvestigation(
  projectId: string,
  incidentId: string,
  investigationId: string,
): Promise<Investigation> {
  return request<Investigation>(
    `/api/projects/${projectId}/incidents/${incidentId}/investigations/${investigationId}/start`,
    {
      method: "POST",
    },
  );
}

export async function generateInvestigationResult(
  projectId: string,
  incidentId: string,
  investigationId: string,
): Promise<InvestigationResult> {
  return request<InvestigationResult>(
    `/api/projects/${projectId}/incidents/${incidentId}/investigations/${investigationId}/generate-result`,
    {
      method: "POST",
    },
  );
}

export async function getInvestigationResult(
  projectId: string,
  incidentId: string,
  investigationId: string,
): Promise<InvestigationResult> {
  return request<InvestigationResult>(
    `/api/projects/${projectId}/incidents/${incidentId}/investigations/${investigationId}/result`,
  );
}