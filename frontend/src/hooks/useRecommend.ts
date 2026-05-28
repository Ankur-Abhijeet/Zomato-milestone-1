/**
 * useRecommend — async state machine hook (Phase 5b).
 *
 * States:  idle → loading → success | error
 *
 * Aborts in-flight requests when a new one starts so there are
 * no stale-response races.
 */

import { useCallback, useRef, useState } from 'react'

import { ApiClientError, recommend } from '../api/client'
import type { RecommendRequest, RecommendResponse } from '../types/api'

// ── State type ────────────────────────────────────────────────────────────────

type IdleState = { status: 'idle' }
type LoadingState = { status: 'loading' }
type SuccessState = { status: 'success'; data: RecommendResponse }
type ErrorState = { status: 'error'; message: string; code: number }

export type RecommendState = IdleState | LoadingState | SuccessState | ErrorState

// ── Hook ─────────────────────────────────────────────────────────────────────

export function useRecommend() {
  const [state, setState] = useState<RecommendState>({ status: 'idle' })
  const abortRef = useRef<AbortController | null>(null)

  const fetch = useCallback(async (body: RecommendRequest) => {
    // Cancel any in-flight request
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ status: 'loading' })

    try {
      const data = await recommend(body, controller.signal)
      setState({ status: 'success', data })
    } catch (err: unknown) {
      if ((err as Error).name === 'AbortError') {
        // Request was intentionally cancelled — stay loading or revert to idle
        return
      }
      if (err instanceof ApiClientError) {
        const message = friendlyMessage(err)
        setState({ status: 'error', message, code: err.status })
      } else {
        const rawMsg = (err as Error).message || 'Unknown network error';
        setState({
          status: 'error',
          message: `${rawMsg} — This is usually caused by a CORS block. Ensure ALLOWED_ORIGINS in Render matches your exact Vercel URL!`,
          code: 0,
        })
      }
    }
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState({ status: 'idle' })
  }, [])

  return { state, fetch, reset }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function friendlyMessage(err: ApiClientError): string {
  switch (err.status) {
    case 422:
      return `Invalid input: ${err.message}`
    case 502:
      return 'The AI service is temporarily unavailable (quota exceeded). Results may be limited.'
    case 503:
      return 'The server is still warming up — please wait a moment and try again.'
    case 504:
      return 'The AI service timed out. Please try again.'
    default:
      return err.message || 'Something went wrong. Please try again.'
  }
}
