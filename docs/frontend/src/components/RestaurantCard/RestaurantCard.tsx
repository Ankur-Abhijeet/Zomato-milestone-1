import { useState } from 'react'
import type { RecommendationItem } from '../../types/api'
import './RestaurantCard.css'

interface Props {
  item: RecommendationItem
  animationDelay?: number
}

// Beautiful fallback Unsplash food images based on cuisine type
const CUISINE_IMAGES: Record<string, string> = {
  'indian': 'https://images.unsplash.com/photo-1585938338392-50a59970d2ee?auto=format&fit=crop&w=600&h=400&q=80',
  'north indian': 'https://images.unsplash.com/photo-1585938338392-50a59970d2ee?auto=format&fit=crop&w=600&h=400&q=80',
  'south indian': 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&h=400&q=80',
  'italian': 'https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?auto=format&fit=crop&w=600&h=400&q=80',
  'pizza': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&h=400&q=80',
  'continental': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&h=400&q=80',
  'burger': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&h=400&q=80',
  'chinese': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&h=400&q=80',
  'ramen': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&h=400&q=80',
  'mexican': 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&h=400&q=80',
  'tacos': 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&h=400&q=80',
  'thai': 'https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=600&h=400&q=80',
  'fast food': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&h=400&q=80',
  'dessert': 'https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=600&h=400&q=80',
}

const DEFAULT_IMAGE = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&h=400&q=80'

export function RestaurantCard({ item, animationDelay = 0 }: Props) {
  const [expanded, setExpanded] = useState(false)

  // Choose image based on cuisine match
  const getCuisineImage = (): string => {
    if (!item.cuisine) return DEFAULT_IMAGE
    const list = item.cuisine.toLowerCase()
    for (const key of Object.keys(CUISINE_IMAGES)) {
      if (list.includes(key)) {
        return CUISINE_IMAGES[key]
      }
    }
    return DEFAULT_IMAGE
  }

  const imageUrl = getCuisineImage()
  const matchPct = item.rating ? Math.round(75 + (item.rating / 5) * 23) : 95
  const simulatedRatingsCount = item.rating ? Math.round((item.rating - 3) * 350 + (item.rank * 17) + 50) : 250
  const simulatedDistance = ((item.rank * 0.4) + 0.3).toFixed(1)

  return (
    <article
      className="rc"
      style={{ animation: `fadeIn 0.4s ease ${animationDelay}ms both` }}
      aria-label={`Recommendation ${item.rank}: ${item.name}`}
    >
      {/* Top Banner Image */}
      <div className="rc__image-wrap">
        <img
          className="rc__image"
          src={imageUrl}
          alt={item.name}
          loading="lazy"
        />
        <div className="rc__rank-badge" aria-label={`Rank ${item.rank}`}>
          #{item.rank}
        </div>
      </div>

      {/* Main Card Body */}
      <div className="rc__body">
        {/* Name and Rating row */}
        <div className="rc__title-row">
          <h3 className="rc__name">{item.name}</h3>
          
          <div className="rc__rating-container">
            {item.rating !== null && (
              <span className="rc__rating">
                {item.rating.toFixed(1)} <span className="rc__star">★</span>
              </span>
            )}
            <span className="rc__ratings-count">({simulatedRatingsCount} ratings)</span>
            <span className="rc__divider">•</span>
            {item.rank % 2 === 0 ? (
              <span className="rc__distance">{simulatedDistance} mi</span>
            ) : (
              <span className="rc__match-pct">{matchPct}% Match</span>
            )}
          </div>
        </div>

        {/* Cuisine Details */}
        <p className="rc__cuisines">{item.cuisine || 'Multi-Cuisine'}</p>

        {/* Info Row (Cost & Location) */}
        <div className="rc__meta">
          {item.estimated_cost && (
            <span className="rc__meta-item rc__cost">
              💰 ₹{item.estimated_cost} for two
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
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '16px', height: '16px', display: 'block', color: '#1f2937' }}>
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <path d="M9 9h6v6H9z" />
                  <path d="M9 1v2M15 1v2M9 21v2M15 21v2M21 9h2M21 15h2M1 9h2M1 15h2" />
                </svg>
              </span>
              <div className="rc__why-fits-content">
                <p className={`rc__explanation-text${expanded ? ' rc__explanation-text--expanded' : ''}`}>
                  <strong>Why this fits:</strong> {item.explanation}
                </p>
                {item.explanation.length > 130 && (
                  <button
                    className="rc__expand-btn"
                    onClick={() => setExpanded((v) => !v)}
                    aria-expanded={expanded}
                  >
                    {expanded ? 'View Less' : 'View Details'}
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
