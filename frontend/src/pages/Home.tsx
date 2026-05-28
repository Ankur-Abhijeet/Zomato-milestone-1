import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { getMeta } from '../api/client'
import { PreferenceForm } from '../components/PreferenceForm/PreferenceForm'
import { ResultsView } from '../components/ResultsView/ResultsView'
import { Toast, type ToastItem } from '../components/ui'
import { useRecommend } from '../hooks/useRecommend'
import type { MetaResponse, RecommendRequest } from '../types/api'
import './Home.css'

// ── SVG Delivery Rider ────────────────────────────────────────────────────────
function DeliveryRiderSVG() {
  return (
    <svg className="home__rider-svg" viewBox="0 0 120 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Back wheel */}
      <circle cx="25" cy="62" r="14" fill="#2d2d2d" stroke="#444" strokeWidth="2"/>
      <circle cx="25" cy="62" r="7" fill="#555"/>
      <circle cx="25" cy="62" r="3" fill="#e23744"/>
      {/* Spokes */}
      <line x1="25" y1="48" x2="25" y2="76" stroke="#777" strokeWidth="1.5"/>
      <line x1="11" y1="62" x2="39" y2="62" stroke="#777" strokeWidth="1.5"/>
      <line x1="15" y1="52" x2="35" y2="72" stroke="#777" strokeWidth="1.5"/>
      <line x1="35" y1="52" x2="15" y2="72" stroke="#777" strokeWidth="1.5"/>

      {/* Front wheel */}
      <circle cx="92" cy="62" r="14" fill="#2d2d2d" stroke="#444" strokeWidth="2"/>
      <circle cx="92" cy="62" r="7" fill="#555"/>
      <circle cx="92" cy="62" r="3" fill="#e23744"/>
      {/* Spokes */}
      <line x1="92" y1="48" x2="92" y2="76" stroke="#777" strokeWidth="1.5"/>
      <line x1="78" y1="62" x2="106" y2="62" stroke="#777" strokeWidth="1.5"/>
      <line x1="82" y1="52" x2="102" y2="72" stroke="#777" strokeWidth="1.5"/>
      <line x1="102" y1="52" x2="82" y2="72" stroke="#777" strokeWidth="1.5"/>

      {/* Bike frame */}
      <path d="M25 62 L55 38 L92 62" stroke="#c9202e" strokeWidth="3" strokeLinecap="round"/>
      <path d="M55 38 L75 38 L92 62" stroke="#e23744" strokeWidth="3" strokeLinecap="round" fill="none"/>
      <path d="M55 38 L48 48" stroke="#c9202e" strokeWidth="2.5" strokeLinecap="round"/>

      {/* Handlebar */}
      <rect x="84" y="30" width="14" height="3" rx="1.5" fill="#888"/>
      <rect x="82" y="29" width="4" height="10" rx="2" fill="#555"/>

      {/* Seat */}
      <rect x="50" y="34" width="16" height="4" rx="2" fill="#555"/>

      {/* Rider body */}
      <ellipse cx="62" cy="25" rx="10" ry="14" fill="#e23744"/>
      {/* Jacket detail */}
      <path d="M52 28 Q62 18 72 28" stroke="#c9202e" strokeWidth="1.5" fill="none"/>

      {/* Head with helmet */}
      <circle cx="62" cy="10" r="9" fill="#ff6b35"/>
      <path d="M53 9 Q62 0 71 9" fill="#e23744"/>
      {/* Visor */}
      <path d="M55 10 Q62 15 69 10" fill="none" stroke="#1a1a2e" strokeWidth="1.5"/>
      <rect x="54" y="8" width="16" height="4" rx="2" fill="rgba(0,0,0,0.3)"/>

      {/* Arm + food bag */}
      <path d="M72 22 L85 18" stroke="#ff6b35" strokeWidth="3" strokeLinecap="round"/>
      {/* Delivery box / bag */}
      <rect x="82" y="8" width="24" height="18" rx="3" fill="#e23744" stroke="#c9202e" strokeWidth="1"/>
      <text x="84" y="21" fontSize="10" fill="white" fontWeight="bold">🍕</text>

      {/* Legs */}
      <path d="M62 38 L55 55 L48 55" stroke="#2d2d2d" strokeWidth="3" strokeLinecap="round"/>
      <path d="M62 38 L68 55 L78 55" stroke="#2d2d2d" strokeWidth="3" strokeLinecap="round"/>

      {/* Exhaust puff */}
      <circle cx="15" cy="58" r="4" fill="rgba(255,255,255,0.15)"/>
      <circle cx="8" cy="54" r="3" fill="rgba(255,255,255,0.1)"/>
      <circle cx="3" cy="50" r="2" fill="rgba(255,255,255,0.06)"/>
    </svg>
  )
}

// ── Marquee items ─────────────────────────────────────────────────────────────
const MARQUEE_ITEMS = [
  '🍛 51,717+ Restaurants',
  '📍 Bangalore · Mumbai · Delhi · Hyderabad',
  '⭐ AI-Powered Rankings',
  '💸 All Budgets Welcome',
  '🤖 Groq Llama 3.3 70B',
  '🏆 Smart Deduplication',
  '🔍 Advanced Filters',
  '🎯 Personalised For You',
  '🍕 Every Cuisine Covered',
  '⚡ Results in Seconds',
]

// ── Food floats for hero ──────────────────────────────────────────────────────
const FOOD_FLOATS = ['🍛', '🍕', '🌮', '🍜']

export default function Home() {
  const { state, fetch } = useRecommend()
  const [meta, setMeta] = useState<MetaResponse | null>(null)
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const [lastTopK, setLastTopK] = useState(5)
  const [activeRequest, setActiveRequest] = useState<RecommendRequest | null>(null)
  const [showForm, setShowForm] = useState(true)
  const toastIdRef = useRef(0)
  const uniqueId = useId()
  const riderRef = useRef<HTMLDivElement>(null)
  const roadRef = useRef<HTMLDivElement>(null)

  // Load meta on mount with retries (Render backend might return 503 while warming up)
  useEffect(() => {
    const ctrl = new AbortController()
    
    const fetchMeta = async (retries = 20) => {
      try {
        const data = await getMeta(ctrl.signal)
        setMeta(data)
      } catch (err: any) {
        if (err.name === 'AbortError') return
        if (retries > 0) {
          setTimeout(() => fetchMeta(retries - 1), 3000)
        } else {
          // Exhausted retries, show the error to the user!
          const rawMsg = err.message || 'Unknown network error'
          const id = `toast-${uniqueId}-meta-fail`
          setToasts((prev) => [
            ...prev,
            {
              id,
              variant: 'error',
              title: 'Backend Unreachable',
              message: `Could not load location data: ${rawMsg}. If this is a CORS error, check your ALLOWED_ORIGINS.`,
            },
          ])
        }
      }
    }
    
    fetchMeta()
    
    return () => ctrl.abort()
  }, [])

  // ── Scroll-driven rider ─────────────────────────────────────────────────────
  useEffect(() => {
    const onScroll = () => {
      if (!riderRef.current || !roadRef.current) return
      const scrollY = window.scrollY
      const docH = document.documentElement.scrollHeight - window.innerHeight
      const pct = Math.min(Math.max(scrollY / (docH || 1), 0), 1)
      // Rider travels from 5% → 82% of road width
      const leftPct = 5 + pct * 77
      riderRef.current.style.left = `${leftPct}%`
      // Add moving class for speed lines
      if (scrollY > 20) {
        riderRef.current.classList.add('home__rider-wrap--moving')
      } else {
        riderRef.current.classList.remove('home__rider-wrap--moving')
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  useEffect(() => {
    if (state.status === 'error') {
      const id = `toast-${uniqueId}-${++toastIdRef.current}`
      const item: ToastItem = {
        id,
        variant: state.code >= 500 ? 'error' : 'warning',
        title: state.code >= 500 ? 'Service Error' : 'Could not fetch results',
        message: state.message,
      }
      setToasts((prev) => [...prev, item])
      setTimeout(() => dismissToast(id), 6000)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.status])

  const handleSubmit = useCallback(
    (req: RecommendRequest) => {
      setLastTopK(req.top_k ?? 5)
      setActiveRequest(req)
      setShowForm(false)
      fetch(req)
    },
    [fetch],
  )

  const isLoading = state.status === 'loading'
  const data = state.status === 'success' ? state.data : null
  const hasResults = state.status === 'success' || isLoading

  const getPriceSymbol = (budget?: string) => {
    if (budget === 'low') return '₹'
    if (budget === 'high') return '₹₹₹'
    return '₹₹'
  }

  return (
    <div className="home">

      {/* ── Glassmorphism Header ─────────────────────────────────────────── */}
      <header className="home__header-bar">
        <div className="home__header-left">
          <span className="home__header-logo">zomato</span>
          <span className="home__ai-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M9 9h6v6H9z" />
              <path d="M9 1v2M15 1v2M9 21v2M15 21v2M21 9h2M21 15h2M1 9h2M1 15h2" />
            </svg>
            AI
          </span>
        </div>

        <div className="home__header-center">
          <span className="home__search-icon">🔍</span>
          <input className="home__search-box" type="text" placeholder="Search restaurants, cuisines, locations…" disabled />
        </div>

        <div className="home__header-right">
          <button className="home__profile-btn" aria-label="User profile">👤</button>
        </div>
      </header>

      {/* ── Red Marquee Ticker ───────────────────────────────────────────── */}
      <div className="home__marquee-bar" aria-hidden="true">
        <div className="home__marquee-track">
          {/* Duplicate for seamless loop */}
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, i) => (
            <span key={i} className="home__marquee-item">
              <span className="home__marquee-dot" />
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* ── Hero Section (before first search) ──────────────────────────── */}
      {!hasResults && showForm && (
        <>
          <div className="home__hero">
            {/* Background orbs */}
            <div className="home__hero-orb home__hero-orb--1" />
            <div className="home__hero-orb home__hero-orb--2" />
            <div className="home__hero-orb home__hero-orb--3" />
            <div className="home__hero-orb home__hero-orb--4" />

            {/* Floating food emojis */}
            {FOOD_FLOATS.map((emoji) => (
              <div key={emoji} className="home__hero-food-float">{emoji}</div>
            ))}

            <div className="home__hero-content">
              <div className="home__hero-tag">
                <span className="home__hero-tag-dot" />
                Powered by Groq AI · llama-3.3-70b
              </div>

              <h1 className="home__hero-title">
                Find your next
                <span className="home__hero-title-accent">perfect meal</span>
              </h1>

              <p className="home__hero-subtitle">
                Tell us your city, budget, and cravings — our AI curates a personalised ranking from 51,717+ restaurants across India.
              </p>

              <div className="home__hero-cuisine-pills">
                {[
                  { emoji: '🍛', label: 'Indian' },
                  { emoji: '🍕', label: 'Italian' },
                  { emoji: '🍜', label: 'Chinese' },
                  { emoji: '🌮', label: 'Mexican' },
                  { emoji: '🍣', label: 'Japanese' },
                  { emoji: '🥘', label: 'Continental' },
                  { emoji: '🫕', label: 'Thai' },
                  { emoji: '🥗', label: 'Salads' },
                ].map(({ emoji, label }, i) => (
                  <span
                    key={label}
                    className="home__hero-cuisine-pill"
                    style={{ animationDelay: `${i * 60 + 300}ms` }}
                  >
                    {emoji} {label}
                  </span>
                ))}
              </div>
            </div>

            <div className="home__hero-form-wrapper">
              <PreferenceForm onSubmit={handleSubmit} isLoading={isLoading} locationCategories={meta?.location_categories} />
              {meta && (
                <div className="home__connected-badge" style={{ borderTop: 'none', marginTop: '12px' }}>
                  <span className="home__connected-dot" />
                  Connected · {(51717).toLocaleString()}+ restaurants ready
                </div>
              )}
            </div>
          </div>

          {/* ── Scroll-Driven Rider Road ─────────────────────────────────── */}
          <div className="home__rider-road" ref={roadRef}>
            {/* Road surface */}
            <div className="home__road-surface" />

            {/* Animated road dashes */}
            <div className="home__road-dashes">
              {Array.from({ length: 30 }).map((_, i) => (
                <div key={i} className="home__road-dash" style={{ animationDelay: `${i * -0.15}s` }} />
              ))}
            </div>

            {/* Rider — moves with scroll */}
            <div className="home__rider-wrap" ref={riderRef}>
              <div className="home__rider-speed-lines">
                <div className="home__rider-speed-line" style={{ width: 40 }} />
                <div className="home__rider-speed-line" style={{ width: 28 }} />
                <div className="home__rider-speed-line" style={{ width: 18 }} />
              </div>
              <DeliveryRiderSVG />
            </div>
          </div>

          {/* ── Stats Strip ─────────────────────────────────────────────── */}
          <div className="home__stats-strip">
            {[
              { icon: '🍽️', number: '51,717+', label: 'Restaurants' },
              { icon: '📍', number: '30+',     label: 'Cities covered' },
              { icon: '⭐', number: '4.2 avg', label: 'Avg. rating' },
              { icon: '🤖', number: 'Groq AI', label: 'AI engine' },
            ].map((stat, i) => (
              <div key={stat.label} className="home__stat-item" style={{ animationDelay: `${i * 90}ms` }}>
                <span className="home__stat-icon">{stat.icon}</span>
                <div>
                  <div className="home__stat-number">{stat.number}</div>
                  <div className="home__stat-label">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── Main Two-Column Layout ───────────────────────────────────────── */}
      <main className="home__main">
        <div className="home__layout" style={!hasResults ? { display: 'block' } : undefined}>

          {/* Left Sidebar (Only visible when results are loaded) */}
          {hasResults && (
            <aside className="home__sidebar">
              {showForm ? (
                <PreferenceForm onSubmit={handleSubmit} isLoading={isLoading} locationCategories={meta?.location_categories} />
              ) : (
                <>
                  <h2 className="home__sidebar-title">Your AI-Powered Picks</h2>

                  {/* Reasoning Bubble */}
                  <div className="home__reasoning-bubble">
                  <span className="home__reasoning-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '22px', height: '22px', display: 'block', color: '#e23744' }}>
                      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1 0-3.12 3 3 0 0 1 0-4.88 2.5 2.5 0 0 1 0-3.12A2.5 2.5 0 0 1 9.5 2z" />
                      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 0-3.12 3 3 0 0 0 0-4.88 2.5 2.5 0 0 0 0-3.12A2.5 2.5 0 0 0 14.5 2z" />
                    </svg>
                  </span>
                  <div className="home__reasoning-text">
                    <strong>Reasoning Summary:</strong> Here's why these are perfect for you:{' '}
                    {data?.summary ||
                      `Based on your preference for ${
                        activeRequest?.cuisines?.length ? activeRequest.cuisines.join(', ') : 'multi-cuisine'
                      } dining, a rating of ${
                        activeRequest?.min_rating?.toFixed(1) ?? '3.0'
                      }+, and a ${
                        activeRequest?.budget === 'low' ? 'budget under ₹500' : activeRequest?.budget === 'high' ? 'premium budget above ₹1,500' : 'medium budget ₹500–₹1,500'
                      }, I've curated these selections just for you.`}
                  </div>
                </div>

                {/* Active Filter Pills */}
                <div className="home__filter-pills">
                  {activeRequest?.cuisines && activeRequest.cuisines.length > 0 && (
                    <div className="home__filter-pill" style={{ animationDelay: '0ms' }}>
                      <strong>Cuisine:</strong>{activeRequest.cuisines.join(', ')}
                    </div>
                  )}
                  <div className="home__filter-pill" style={{ animationDelay: '50ms' }}>
                    <strong>Price:</strong>{getPriceSymbol(activeRequest?.budget)}
                  </div>
                  {activeRequest?.additional && (
                    <div className="home__filter-pill" style={{ animationDelay: '100ms' }}>
                      <strong>Vibe:</strong>{activeRequest.additional}
                    </div>
                  )}
                  <div className="home__filter-pill" style={{ animationDelay: '150ms' }}>
                    <strong>Location:</strong>{activeRequest?.location}
                  </div>
                  <div className="home__filter-pill" style={{ animationDelay: '200ms' }}>
                    <strong>Rating:</strong>{activeRequest?.min_rating?.toFixed(1) ?? '3.0'}+ ⭐
                  </div>
                </div>

                <button className="home__change-filters-btn" onClick={() => setShowForm(true)}>
                  <span>⚙️</span>
                  <span>Change Filters</span>
                </button>
              </>
              )}
            </aside>
          )}

          {/* Right Results */}
          <section className="home__content">
            {!hasResults && (
              <div className="home__content-watermark">
                <div className="home__watermark-plate">
                  <div className="home__watermark-inner-plate">🍽️</div>
                </div>
                <div className="home__watermark-text">
                  <h3>Hungry?</h3>
                  <p>Adjust your preferences on the left and let AI find your perfect meal.</p>
                </div>
                {/* Floating decor around plate */}
                <div className="home__watermark-decor home__watermark-decor--1">✨</div>
                <div className="home__watermark-decor home__watermark-decor--2">✨</div>
                <div className="home__watermark-decor home__watermark-decor--3">✨</div>
              </div>
            )}
            <ResultsView isLoading={isLoading} data={data} topK={lastTopK} />
          </section>
        </div>
      </main>

      {/* ── Sticky Footer Bar ────────────────────────────────────────────── */}
      <footer className="home__bottom-bar">
        <div className="home__chat-pill">
          <input
            className="home__chat-input"
            type="text"
            placeholder="Ask me about their best dish, ambience, or parking…"
            disabled
          />
          <button className="home__chat-send" disabled>Send</button>
        </div>

        <button
          className="home__book-btn"
          onClick={() => {
            const id = `toast-${uniqueId}-${++toastIdRef.current}`
            setToasts((prev) => [
              ...prev,
              {
                id,
                variant: 'success',
                title: '🎉 Table Booked!',
                message: 'Your reservation request was sent successfully. Enjoy your meal!',
              },
            ])
            setTimeout(() => dismissToast(id), 6000)
          }}
        >
          <span>🍽️</span>
          <span>Book a Table</span>
        </button>
      </footer>

      {/* ── Toasts ──────────────────────────────────────────────────────── */}
      <Toast items={toasts} onDismiss={dismissToast} />
    </div>
  )
}
