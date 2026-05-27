/**
 * Typed API client (Phase 5b).
 * All requests go through the Vite proxy → FastAPI backend.
 * Never exposes GROQ_API_KEY to the browser.
 */

import type { MetaResponse, RecommendRequest, RecommendResponse } from '../types/api'

const BASE = '/api/v1'

export class ApiClientError extends Error {
  public readonly status: number
  public readonly code: string

  constructor(
    status: number,
    code: string,
    message: string,
  ) {
    super(message)
    this.status = status
    this.code = code
    this.name = 'ApiClientError'
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.ok) {
    return res.json() as Promise<T>
  }

  // Try to parse structured error body
  let errorCode = 'unknown_error'
  let errorMessage = `Request failed with status ${res.status}`
  try {
    const body = await res.json()
    errorCode = body?.error ?? errorCode
    errorMessage = body?.message ?? errorMessage
    // FastAPI validation error format
    if (res.status === 422 && Array.isArray(body?.detail)) {
      const firstErr = body.detail[0]
      errorMessage = firstErr?.msg ?? errorMessage
    }
  } catch {
    // body was not JSON — keep defaults
  }

  throw new ApiClientError(res.status, errorCode, errorMessage)
}

/** POST /api/v1/recommendations */
export async function recommend(
  body: RecommendRequest,
  signal?: AbortSignal,
): Promise<RecommendResponse> {
  const res = await fetch(`${BASE}/recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  return handleResponse<RecommendResponse>(res)
}

/** GET /api/v1/meta */
export async function getMeta(signal?: AbortSignal): Promise<MetaResponse> {
  const res = await fetch(`${BASE}/meta`, { signal })
  return handleResponse<MetaResponse>(res)
}
