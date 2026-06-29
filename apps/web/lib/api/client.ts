import { z, type ZodType } from "zod";
import { createClient } from "@/lib/supabase/client";
import * as S from "./types";
export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public cause?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
const DEFAULT_API_BASE_URL = "https://rana-m-ahmed-readout.hf.space";
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
let coldStart: ((active: boolean) => void) | undefined;
export const onColdStart = (listener: (active: boolean) => void) => {
  coldStart = listener;
  return () => {
    coldStart = undefined;
  };
};
const pause = () => new Promise((r) => setTimeout(r, 1200));
export async function apiFetch<T>(
  path: string,
  schema: ZodType<T>,
  options: RequestInit = {},
  attempt = 0,
): Promise<T> {
  let token: string | undefined;
  try {
    token = (await createClient().auth.getSession()).data.session?.access_token;
  } catch {}
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { ...options, headers });
  } catch (error) {
    if (attempt === 0) {
      coldStart?.(true);
      await pause();
      const result = await apiFetch(path, schema, options, 1);
      coldStart?.(false);
      return result;
    }
    throw new ApiError(
      "Unable to reach Readout. Please try again.",
      "network_error",
      0,
      error,
    );
  }
  if (response.status === 503 && attempt === 0) {
    coldStart?.(true);
    await pause();
    const result = await apiFetch(path, schema, options, 1);
    coldStart?.(false);
    return result;
  }
  if (!response.ok) {
    let code = `http_${response.status}`,
      message = response.statusText || "Request failed";
    try {
      const parsed = S.ApiErrorBody.safeParse(await response.json());
      if (parsed.success) {
        code = parsed.data.error.code;
        message = parsed.data.error.message;
      }
    } catch {}
    throw new ApiError(message, code, response.status);
  }
  if (response.status === 204) return undefined as T;
  const body = await response.json();
  const parsed = schema.safeParse(body);
  if (!parsed.success)
    throw new ApiError(
      "The server returned an unexpected response.",
      "invalid_response",
      502,
      parsed.error,
    );
  return parsed.data;
}
const body = (value: unknown) => JSON.stringify(value);
export const api = {
  getDatasets: () => apiFetch("/datasets", z.array(S.Dataset)),
  getSchema: (id: string) => apiFetch(`/datasets/${id}/schema`, S.Schema),
  getProfile: (id: string) => apiFetch(`/datasets/${id}/profile`, S.Profile),
  getAnalysisConfig: (id: string) => apiFetch(`/datasets/${id}/analysis-config`, S.AnalysisConfig),
  saveAnalysisConfig: (id: string, input: S.AnalysisConfigInputT) => apiFetch(`/datasets/${id}/analysis-config`, S.AnalysisConfig, {method:"PUT",body:body(input)}),
  previewAnalysisConfig: (id: string, input: S.AnalysisConfigInputT) => apiFetch(`/datasets/${id}/analysis-config/preview`, S.DatasetOverview, {method:"POST",body:body(input)}),
  getOverview: (id: string) => apiFetch(`/datasets/${id}/overview`, S.DatasetOverview),
  profile: (id: string) =>
    apiFetch(`/datasets/${id}/profile`, S.Profile, { method: "POST" }),
  uploadUrl: (input: {
    filename: string;
    file_size_bytes: number;
    description?: string | null;
  }) =>
    apiFetch("/datasets/upload-url", S.UploadUrl, {
      method: "POST",
      body: body({ ...input, description: input.description ?? null }),
    }),
  deleteDataset: (id: string) =>
    apiFetch(`/datasets/${id}`, z.void(), { method: "DELETE" }),
  ask: (input: {
    dataset_id: string;
    question: string;
    session_id: string | null;
    persist?: boolean;
  }) => apiFetch("/ask", S.Ask, { method: "POST", body: body(input) }),
  createWidget: (input: {
    dashboard_id: string;
    source_type: "ask_message" | "insight" | "anomaly";
    source_id: string;
    title?: string;
    position?: number;
  }) => apiFetch("/widgets", S.Widget, { method: "POST", body: body(input) }),
  getWidgets: (id: string) =>
    apiFetch(`/dashboards/${id}/widgets`, z.array(S.Widget)),
  updateWidget: (id: string, input: { title?: string; position?: number }) =>
    apiFetch(`/widgets/${id}`, S.Widget, {
      method: "PATCH",
      body: body(input),
    }),
  deleteWidget: (id: string) =>
    apiFetch(`/widgets/${id}`, z.void(), { method: "DELETE" }),
  updateLayout: (
    id: string,
    widgets: { widget_id: string; position: number }[],
  ) =>
    apiFetch(`/dashboards/${id}/layout`, S.Layout, {
      method: "PATCH",
      body: body({ widgets }),
    }),
  getInsights: (id: string) =>
    apiFetch(`/datasets/${id}/insights`, z.array(S.Insight)),
  generateInsights: (id: string) =>
    apiFetch(`/datasets/${id}/insights/generate`, z.array(S.Insight), {
      method: "POST",
    }),
  getAnomalies: (id: string) =>
    apiFetch(`/datasets/${id}/anomalies`, z.array(S.Anomaly)),
  scanAnomalies: (id: string) =>
    apiFetch(`/datasets/${id}/anomalies/scan`, z.array(S.Anomaly), {
      method: "POST",
    }),
  deleteAnomaly: (id: string) =>
    apiFetch(`/anomalies/${id}`, z.void(), { method: "DELETE" }),
};
export function uploadBinary(
  url: string,
  file: File,
  onProgress: (percent: number) => void,
) {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    xhr.setRequestHeader("Content-Type", "text/csv");
    xhr.upload.onprogress = (e) =>
      e.lengthComputable && onProgress(Math.round((e.loaded / e.total) * 100));
    xhr.onload = () =>
      xhr.status >= 200 && xhr.status < 300
        ? resolve()
        : reject(
            new ApiError(
              "The file upload failed.",
              "upload_failed",
              xhr.status,
            ),
          );
    xhr.onerror = () =>
      reject(
        new ApiError("The file upload was interrupted.", "network_error", 0),
      );
    xhr.send(file);
  });
}
