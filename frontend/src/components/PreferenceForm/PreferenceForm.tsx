import { type KeyboardEvent, useEffect, useRef, useState } from 'react'
import type { BudgetChoice, RecommendRequest } from '../../types/api'
import { Spinner } from '../ui'
import './PreferenceForm.css'

interface Props {
  onSubmit: (req: RecommendRequest) => void
  isLoading: boolean
  locationCategories?: { label: string; query: string; count: number }[]
}

const BUDGET_OPTIONS: { value: BudgetChoice; label: string; desc: string }[] = [
  { value: 'low',    label: '💸 Low',    desc: '≤ ₹500' },
  { value: 'medium', label: '💳 Medium', desc: '≤ ₹1,500' },
  { value: 'high',   label: '💎 High',   desc: '> ₹1,500' },
]

export function PreferenceForm({ onSubmit, isLoading, locationCategories }: Props) {
  const [location, setLocation]     = useState('')
  const [budget, setBudget]         = useState<BudgetChoice>('medium')
  const [cuisines, setCuisines]     = useState<string[]>([])
  const [cuisineInput, setCuisineInput] = useState('')
  const [minRating, setMinRating]   = useState(3.0)
  const [additional, setAdditional] = useState('')
  const [topK, setTopK]             = useState(5)
  const [locationError, setLocationError] = useState('')

  const cuisineInputRef = useRef<HTMLInputElement>(null)

  // ── Auto-select first location when categories load ────────────────────────
  useEffect(() => {
    if (locationCategories && locationCategories.length > 0 && !location) {
      setLocation(locationCategories[0].query)
      setLocationError('')
    }
  }, [locationCategories, location])

  // ── Cuisine chip management ────────────────────────────────────────────────
  const addCuisine = (raw: string) => {
    const trimmed = raw.trim()
    if (!trimmed) return
    const parts = trimmed.split(',').map((s) => s.trim()).filter(Boolean)
    setCuisines((prev) => {
      const existing = new Set(prev.map((c) => c.toLowerCase()))
      const newOnes = parts.filter((p) => !existing.has(p.toLowerCase()))
      return [...prev, ...newOnes]
    })
    setCuisineInput('')
  }

  const removeCuisine = (idx: number) =>
    setCuisines((prev) => prev.filter((_, i) => i !== idx))

  const handleCuisineKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addCuisine(cuisineInput)
    } else if (e.key === 'Backspace' && cuisineInput === '' && cuisines.length > 0) {
      setCuisines((prev) => prev.slice(0, -1))
    }
  }

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!location.trim()) {
      setLocationError('Please enter a city or area.')
      return
    }
    setLocationError('')

    // Flush any partial cuisine input
    const finalCuisines = [...cuisines]
    if (cuisineInput.trim()) {
      cuisineInput
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
        .forEach((c) => {
          if (!finalCuisines.map((x) => x.toLowerCase()).includes(c.toLowerCase())) {
            finalCuisines.push(c)
          }
        })
    }

    onSubmit({
      location: location.trim(),
      budget,
      cuisines: finalCuisines,
      min_rating: minRating,
      additional: additional.trim() || undefined,
      top_k: topK,
    })
  }

  return (
    <form className="pf" onSubmit={handleSubmit} noValidate>
      <h2 className="pf__title">
        <span>🍽️</span> Find Your Restaurant
      </h2>
      <p className="pf__subtitle">
        Tell us what you're looking for — our AI will do the rest.
      </p>

      <div className="pf__grid">
        {/* Location */}
        <div className="pf__field pf__field--full">
          <label className="pf__label" htmlFor="pf-location">
            Location <span>*</span>
          </label>
          <select
            id="pf-location"
            className={`pf__input${locationError ? ' pf__input--error' : ''}`}
            value={location}
            onChange={(e) => {
              setLocation(e.target.value)
              if (e.target.value) setLocationError('')
            }}
            disabled={isLoading}
            style={{ cursor: 'pointer', appearance: 'auto' }}
          >
            <option value="" disabled>Select a location…</option>
            {locationCategories ? (
              locationCategories.map((c) => (
                <option key={c.query} value={c.query}>
                  {c.label} ({c.count.toLocaleString()})
                </option>
              ))
            ) : (
              <option value="" disabled>Loading locations…</option>
            )}
          </select>
          {locationError && (
            <span className="pf__error" role="alert">⚠ {locationError}</span>
          )}
        </div>

        {/* Budget */}
        <div className="pf__field pf__field--full">
          <label className="pf__label">Budget</label>
          <div className="pf__budget" role="group" aria-label="Budget selection">
            {BUDGET_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                id={`pf-budget-${opt.value}`}
                className={`pf__budget-btn${budget === opt.value ? ' pf__budget-btn--active' : ''}`}
                onClick={() => setBudget(opt.value)}
                disabled={isLoading}
                aria-pressed={budget === opt.value}
              >
                {opt.label}
                <br />
                <small style={{ opacity: 0.7, fontWeight: 400 }}>{opt.desc}</small>
              </button>
            ))}
          </div>
        </div>

        {/* Cuisines */}
        <div className="pf__field pf__field--full">
          <label className="pf__label" htmlFor="pf-cuisine-input">
            Cuisines <small style={{ fontWeight: 400, textTransform: 'none', opacity: 0.7 }}>
              (optional — any cuisine if empty)
            </small>
          </label>
          <div
            className="pf__cuisine-input-wrap"
            onClick={() => cuisineInputRef.current?.focus()}
            role="group"
            aria-label="Selected cuisines"
          >
            {cuisines.map((c, i) => (
              <span key={`${c}-${i}`} className="pf__chip">
                {c}
                <button
                  type="button"
                  className="pf__chip-remove"
                  onClick={(e) => { e.stopPropagation(); removeCuisine(i) }}
                  disabled={isLoading}
                  aria-label={`Remove ${c}`}
                >
                  ×
                </button>
              </span>
            ))}
            <input
              ref={cuisineInputRef}
              id="pf-cuisine-input"
              className="pf__cuisine-text-input"
              type="text"
              placeholder={cuisines.length === 0 ? 'Type a cuisine and press Enter…' : ''}
              value={cuisineInput}
              onChange={(e) => setCuisineInput(e.target.value)}
              onKeyDown={handleCuisineKeyDown}
              onBlur={() => addCuisine(cuisineInput)}
              disabled={isLoading}
            />
          </div>
          <span className="pf__cuisine-hint">
            Press Enter or comma to add • Backspace to remove last
          </span>
        </div>

        {/* Min Rating */}
        <div className="pf__field">
          <div className="pf__rating-wrap">
            <div className="pf__rating-header">
              <label className="pf__label" htmlFor="pf-rating">Min Rating</label>
              <span className="pf__rating-value">⭐ {minRating.toFixed(1)}</span>
            </div>
            <input
              id="pf-rating"
              className="pf__slider"
              type="range"
              min={0}
              max={5}
              step={0.5}
              value={minRating}
              onChange={(e) => setMinRating(parseFloat(e.target.value))}
              disabled={isLoading}
              aria-valuemin={0}
              aria-valuemax={5}
              aria-valuenow={minRating}
              aria-valuetext={`${minRating} stars`}
              style={{
                background: `linear-gradient(to right, var(--accent) ${(minRating / 5) * 100}%, var(--bg-input) ${(minRating / 5) * 100}%)`,
              }}
            />
          </div>
        </div>

        {/* Top K */}
        <div className="pf__field">
          <label className="pf__label">Results</label>
          <div className="pf__stepper" role="group" aria-label="Number of results">
            <button
              type="button"
              className="pf__stepper-btn"
              id="pf-topk-dec"
              onClick={() => setTopK((k) => Math.max(1, k - 1))}
              disabled={isLoading || topK <= 1}
              aria-label="Decrease results"
            >
              −
            </button>
            <span
              className="pf__stepper-value"
              id="pf-topk-value"
              aria-live="polite"
              aria-label={`${topK} results`}
            >
              {topK}
            </span>
            <button
              type="button"
              className="pf__stepper-btn"
              id="pf-topk-inc"
              onClick={() => setTopK((k) => Math.min(10, k + 1))}
              disabled={isLoading || topK >= 10}
              aria-label="Increase results"
            >
              +
            </button>
          </div>
        </div>

        {/* Additional (soft prefs) */}
        <div className="pf__field pf__field--full">
          <label className="pf__label" htmlFor="pf-additional">
            Special Preferences{' '}
            <small style={{ fontWeight: 400, textTransform: 'none', opacity: 0.7 }}>
              (optional — describe vibe, occasion, dietary needs…)
            </small>
          </label>
          <textarea
            id="pf-additional"
            className="pf__input pf__textarea"
            placeholder="e.g. family-friendly, outdoor seating, vegetarian-heavy menu, good for a date…"
            value={additional}
            onChange={(e) => setAdditional(e.target.value)}
            disabled={isLoading}
            maxLength={500}
          />
        </div>
      </div>

      {/* Submit */}
      <div className="pf__actions">
        <button
          type="submit"
          id="pf-submit"
          className="pf__submit"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Spinner size="sm" />
              Finding your perfect spots…
            </>
          ) : (
            <>✨ Find Restaurants</>
          )}
        </button>
      </div>
    </form>
  )
}
