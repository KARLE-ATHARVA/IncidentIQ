import type { Investigation } from "../types";

import request from "./client";


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