/**
 * TypeScript mirrors of the FastAPI response DTOs (Phase 5b).
 * Keep in sync with api/schemas/request.py and api/schemas/response.py.
 */

export type BudgetChoice = 'low' | 'medium' | 'high'

// ── Request ──────────────────────────────────────────────────────────────────

export interface RecommendRequest {
  location: string
  budget?: BudgetChoice
  cuisines?: string[]
  min_rating?: number
  additional?: string
  top_k?: number
}

// ── Response ─────────────────────────────────────────────────────────────────

export interface FilterStats {
  initial: number
  after_location: number
  after_rating: number
  after_budget: number
  after_cuisine: number
  capped_for_llm: number
}

export interface RecommendationItem {
  rank: number
  id: string
  name: string
  cuisine: string
  rating: number | null
  estimated_cost: string | null
  location: string
  explanation: string
  is_ai_generated: boolean
}

export interface RecommendResponse {
  summary: string | null
  used_fallback: boolean
  skip_llm: boolean
  message: string | null
  filter_stats: FilterStats | null
  recommendations: RecommendationItem[]
  /** Number of duplicate name+location outlets removed server-side. */
  dedup_removed: number
}

// ── Meta ─────────────────────────────────────────────────────────────────────

export interface MetaResponse {
  budget_bands: Record<BudgetChoice, string>
  default_top_k: number
  default_min_rating: number
  default_budget: BudgetChoice
  example_locations: string[]
  location_categories: {
    label: string
    query: string
    count: number
  }[]
}

// ── API Error shape ───────────────────────────────────────────────────────────

export interface ApiError {
  error: string
  message: string
  detail?: unknown
}
