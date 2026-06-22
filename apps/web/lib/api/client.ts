import { createClient } from "../supabase/client"
import { ApiErrorSchema } from "./types"

export class ApiError extends Error {
  code: string

  constructor(message: string, code: string) {
    super(message)
    this.name = "ApiError"
    this.code = code
  }
}

export interface AskResponse {
  answer_id: string;
  session_id: string;
  summary: string;
  chart: any | null; 
  query_plan: any | null; 
  confidence: "high" | "medium" | "low";
  suggested_followups: string[];
  clarification_required: { code: string; message: string } | null;
  debug_sql?: string | null;
}

export interface UploadUrlResponse {
  dataset_id: string;
  upload_url: string;
  storage_path: string;
}

export interface DatasetColumn {
  name: string;
  display_name: string;
  data_type: "string" | "number" | "boolean" | "date" | "category";
  semantic_role: "time" | "metric" | "dimension" | "identifier" | null;
  missing_percent: number;
  unique_count?: number;
  sample_values?: any[];
  min_value?: any | null;
  max_value?: any | null;
}

export interface ProfileResponse {
  dataset_id: string;
  row_count: number;
  quality_score: number;
  warnings: string[];
  columns: DatasetColumn[];
}

export interface DatasetListItem {
  id: string;
  name: string;
  description: string | null;
  source_type: string;
  storage_bucket: string;
  storage_path: string;
  file_size_bytes: number;
  row_count: number;
  created_at: string;
  updated_at: string;
}

async function getAuthHeader(): Promise<HeadersInit> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (session?.access_token) {
    return {
      "Authorization": `Bearer ${session.access_token}`
    }
  }
  return {}
}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T> {
  const url = `${BASE_URL}${path}`
  const authHeader = await getAuthHeader()

  const headers = {
    ...authHeader,
    ...options.headers,
  }

  if (options.body && typeof options.body === 'string' && !('Content-Type' in headers)) {
    // @ts-expect-error Headers might not support string indexing directly depending on type
    headers['Content-Type'] = 'application/json'
  }

  try {
    const response = await fetch(url, { ...options, headers })

    if (response.status === 503 && !isRetry) {
      // Retry once for Render cold starts
      await new Promise(resolve => setTimeout(resolve, 2000))
      return apiFetch(path, options, true)
    }

    if (!response.ok) {
      let errorMessage = "An unknown API error occurred"
      let errorCode = "unknown_error"

      try {
        const rawBody = await response.json()
        const parsed = ApiErrorSchema.safeParse(rawBody)
        if (parsed.success) {
          errorMessage = parsed.data.error.message
          errorCode = parsed.data.error.code
        } else if (rawBody.detail) {
          // Fallback for standard FastAPI validation errors or standard detail strings
          errorMessage = Array.isArray(rawBody.detail) ? JSON.stringify(rawBody.detail) : rawBody.detail
          errorCode = "validation_error"
        }
      } catch {
        // Body was not JSON
        errorMessage = response.statusText
        errorCode = `http_${response.status}`
      }

      throw new ApiError(errorMessage, errorCode)
    }

    if (response.status === 204) {
      return undefined as unknown as T
    }

    return await response.json()
  } catch (error) {
    if (error instanceof TypeError && !isRetry) {
      // Network failure (could be cold start connection refused)
      await new Promise(resolve => setTimeout(resolve, 2000))
      return apiFetch(path, options, true)
    }
    throw error
  }
}

export const apiClient = {
  getDatasets: () => apiFetch<DatasetListItem[]>('/datasets'),
  
  askQuestion: (datasetId: string, question: string, sessionId?: string | null) => 
    apiFetch<AskResponse>('/ask', {
      method: 'POST',
      body: JSON.stringify({
        dataset_id: datasetId,
        question,
        session_id: sessionId || null
      })
    }),

  getUploadUrl: (filename: string, file_size_bytes: number, description?: string | null) =>
    apiFetch<UploadUrlResponse>('/datasets/upload-url', {
      method: 'POST',
      body: JSON.stringify({
        filename,
        file_size_bytes,
        description: description || null
      })
    }),

  profileDataset: (datasetId: string) =>
    apiFetch<ProfileResponse>(`/datasets/${datasetId}/profile`, {
      method: 'POST'
    }),

  getDatasetProfile: (datasetId: string) =>
    apiFetch<ProfileResponse>(`/datasets/${datasetId}/profile`),

  deleteDataset: (datasetId: string) =>
    apiFetch<void>(`/datasets/${datasetId}`, {
      method: 'DELETE'
    })
};
