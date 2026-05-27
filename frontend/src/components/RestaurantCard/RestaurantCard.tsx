import { useState } from 'react'
import type { RecommendationItem } from '../../types/api'
import './RestaurantCard.css'

interface Props {
  item: RecommendationItem
  animationDelay?: number
}

export function RestaurantCard({ item, animationDelay = 0 }: Props) {
  const [expanded, setExpanded] = useState(false)

  const matchPct = item.rating ? Math.round(75 + (item.rating / 5) * 23) : 95
  const simulatedRatingsCount = item.rating ? Math.round((item.rating - 3) * 350 + (item.rank * 17) + 50) : 250
  const simulatedDistance = ((item.rank * 0.4) + 0.3).toFixed(1)

  // Split cuisines for chips
  const cuisines = item.cuisine ? item.cuisine.split(',').map(c => c.trim()) : ['Multi-Cuisine']

  // Gradient based on rank for top banner
  const getBannerGradient = (rank: number) => {
    if (rank === 1) return 'linear-gradient(90deg, #ffd700, #ff8c00)'
    if (rank === 2) return 'linear-gradient(90deg, #e2e8f0, #94a3b8)'
    if (rank === 3) return 'linear-gradient(90deg, #fbcfe8, #f43f5e)'
    return 'linear-gradient(90deg, #feeceb, #e23744)'
  }

  return (
    <article
      className="rc"
      style={{ animation: `fadeIn 0.4s ease ${animationDelay}ms both` }}
      aria-label={`Recommendation ${item.rank}: ${item.name}`}
    >
      <div className="rc__banner" style={{ background: getBannerGradient(item.rank) }} />
      
      {/* Card Body */}
      <div className="rc__body">
        {/* Name, Rank Badge and Rating row */}
        <div className="rc__title-row">
          <div className="rc__name-wrap">
            <span className="rc__rank-badge" aria-label={`Rank ${item.rank}`}>#{item.rank}</span>
            <h3 className="rc__name" title={item.name}>{item.name}</h3>
          </div>

          <div className="rc__rating-container">
            {item.rating !== null && (
              <span className="rc__rating">
                {item.rating.toFixed(1)} <span className="rc__star">★</span>
              </span>
            )}
            <span className="rc__ratings-count">({simulatedRatingsCount})</span>
            <span className="rc__divider">•</span>
            {item.rank % 2 === 0 ? (
              <span className="rc__distance">{simulatedDistance} mi</span>
            ) : (
              <span className="rc__match-pct">{matchPct}%</span>
            )}
          </div>
        </div>

        {/* Cuisine Details */}
        <div className="rc__cuisine-chips">
          {cuisines.map(c => (
            <span key={c} className="rc__cuisine-chip">{c}</span>
          ))}
        </div>

        {/* Info Row (Cost & Location) */}
        <div className="rc__meta">
          {item.estimated_cost && (
            <span className="rc__meta-item rc__cost">
              💵 ₹{item.estimated_cost} for two
            </span>
          )}
          <span className="rc__meta-item rc__location">
            📍 {item.location}
          </span>
        </div>

        {/* "Why this fits" Bubble */}
        {item.explanation && (
          <div className="rc__explanation">
            <div className="rc__why-fits-box">
              <span className="rc__ai-icon" title="AI Recommendation logic">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: '15px', height: '15px', display: 'block', color: '#e23744' }}>
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <path d="M9 9h6v6H9z" />
                  <path d="M9 1v2M15 1v2M9 21v2M15 21v2M21 9h2M21 15h2M1 9h2M1 15h2" />
                </svg>
              </span>
              <div className="rc__why-fits-content">
                <p className={`rc__explanation-text${expanded ? ' rc__explanation-text--expanded' : ''}`}>
                  {item.explanation}
                </p>
                {item.explanation.length > 110 && (
                  <button
                    className="rc__expand-btn"
                    onClick={() => setExpanded((v) => !v)}
                    aria-expanded={expanded}
                  >
                    {expanded ? 'Hide' : 'Read more'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </article>
  )
}
