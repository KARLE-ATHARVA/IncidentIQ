import request from "./client";

import type {
  SimulationResetResponse,
  SimulationResponse,
  SimulationStateResponse,
} from "../types/simulation";

export async function getSimulationState(
  projectId: string,
): Promise<SimulationStateResponse> {
  return request<SimulationStateResponse>(
    `/api/projects/${projectId}/simulation/state`,
  );
}

export async function runBadDeploymentSimulation(
  projectId: string,
): Promise<SimulationResponse> {
  return request<SimulationResponse>(
    `/api/projects/${projectId}/simulation/bad-deployment`,
    {
      method: "POST",
    },
  );
}

export async function resetSimulation(
  projectId: string,
): Promise<SimulationResetResponse> {
  return request<SimulationResetResponse>(
    `/api/projects/${projectId}/simulation/reset`,
    {
      method: "POST",
    },
  );
}