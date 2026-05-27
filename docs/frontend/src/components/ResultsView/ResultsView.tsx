import type { FilterStats, RecommendResponse } from '../../types/api'
import { RestaurantCard } from '../RestaurantCard/RestaurantCard'
import { SkeletonCard } from '../ui'
import './ResultsView.css'

// ── Sub-components ────────────────────────────────────────────────────────────

function FilterStatsStrip({ stats, dedupRemoved }: { stats: FilterStats; dedupRemoved: number }) {
  const steps = [
    { label: 'Total', value: stats.initial },
    { label: 'Location', value: stats.after_location },
    { label: 'Rating', value: stats.after_rating },
    { label: 'Budget', value: stats.after_budget },
    { label: 'Cuisine', value: stats.after_cuisine },
    { label: 'Sent to AI', value: stats.capped_for_llm },
  ]

  return (
    <div className="rv__stats" aria-label="Filter statistics">
      <span className="rv__stats-label">Filter:</span>
      {steps.map((step, i) => (
        <span key={step.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span className="rv__stat-chip">
            {step.label}: <strong>{step.value.toLocaleString()}</strong>
          </span>
          {i < steps.length - 1 && <span className="rv__stat-arrow">→</span>}
        </span>
      ))}
      {dedupRemoved > 0 && (
        <span className="rv__stat-chip rv__stat-chip--dedup" title="Duplicate outlets at the same location were collapsed">
          🔁 {dedupRemoved} duplicate{dedupRemoved !== 1 ? 's' : ''} hidden
        </span>
      )}
    </div>
  )
}

// ── Loading ───────────────────────────────────────────────────────────────────

function LoadingSkeleton({ count }: { count: number }) {
  return (
    <div className="rv__skeletons" aria-label="Loading recommendations…" aria-busy="true">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState({ message }: { message: string | null }) {
  return (
    <div className="rv__empty" role="status">
      <div className="rv__empty-icon">🍽️</div>
      <h2 className="rv__empty-title">No restaurants found</h2>
      <p className="rv__empty-message">
        We couldn't find any restaurants matching your filters.
      </p>
      {message && (
        <p className="rv__empty-hint">{message}</p>
      )}
    </div>
  )
}

// ── Main ResultsView ──────────────────────────────────────────────────────────

interface Props {
  isLoading: boolean
  data: RecommendResponse | null
  topK?: number
}

export function ResultsView({ isLoading, data, topK = 5 }: Props) {
  if (isLoading) {
    return (
      <section className="rv" aria-live="polite">
        <LoadingSkeleton count={topK} />
      </section>
    )
  }

  if (!data) return null

  // Empty filter result
  if (data.skip_llm || data.recommendations.length === 0) {
    return (
      <section className="rv" aria-live="polite">
        {data.filter_stats && <FilterStatsStrip stats={data.filter_stats} dedupRemoved={0} />}
        <EmptyState message={data.message} />
      </section>
    )
  }

  return (
    <section className="rv" aria-live="polite" aria-label="Recommendations">
      {/* Alert fallback notice if AI fails */}
      {data.used_fallback && (
        <div className="rv__summary" role="status" style={{ backgroundColor: '#fffbeb', borderColor: '#fde68a', color: '#b45309', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px' }}>
          ⚠️ AI unavailable — results are ranked by rating
        </div>
      )}

      {data.filter_stats && <FilterStatsStrip stats={data.filter_stats} dedupRemoved={data.dedup_removed} />}

      {/* Result count */}
      <p className="rv__count">
        Showing <strong>{data.recommendations.length}</strong> recommendation
        {data.recommendations.length !== 1 ? 's' : ''}
      </p>

      {/* Cards grid */}
      <div className="rv__grid">
        {data.recommendations.map((item, i) => (
          <RestaurantCard
            key={item.id}
            item={item}
            animationDelay={i * 70}
          />
        ))}
      </div>
    </section>
  )
}
