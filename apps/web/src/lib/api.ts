import type {
  AnalysisMode,
  AnalysisResponse,
  DatasetInfoResponse,
  HealthResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status}) for ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health");
}

export async function fetchDataset(): Promise<DatasetInfoResponse> {
  return getJson<DatasetInfoResponse>("/api/v1/dataset");
}

export async function runAnalysis(
  question: string,
  mode: AnalysisMode,
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/api/v1/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, mode }),
  });
  if (!response.ok) {
    let detail = `Analysis failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return response.json() as Promise<AnalysisResponse>;
}

export function chartImageUrl(imagePath?: string): string | null {
  if (!imagePath) return null;
  const parts = imagePath.split(/[/\\]/);
  const filename = parts[parts.length - 1];
  if (!filename) return null;
  return `${API_BASE}/charts/${encodeURIComponent(filename)}`;
}

export { API_BASE };
