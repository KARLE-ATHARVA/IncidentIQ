import type { Project } from "../types";
import request from "./client";

export async function getProjects(): Promise<Project[]> {
  return request<Project[]>("/api/projects");
}