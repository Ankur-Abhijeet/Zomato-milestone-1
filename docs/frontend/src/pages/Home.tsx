import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { getMeta } from '../api/client'
import { PreferenceForm } from '../components/PreferenceForm/PreferenceForm'
import { ResultsView } from '../components/ResultsView/ResultsView'
import { Toast, type ToastItem } from '../components/ui'
import { useRecommend } from '../hooks/useRecommend'
import type { MetaResponse, RecommendRequest } from '../types/api'
import './Home.css'

export default function Home() {
  const { state, fetch } = useRecommend()
  const [meta, setMeta] = useState<MetaResponse | null>(null)
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const [lastTopK, setLastTopK] = useState(5)
  const [activeRequest, setActiveRequest] = useState<RecommendRequest | null>(null)
  const [showForm, setShowForm] = useState(true)
  const toastIdRef = useRef(0)
  const uniqueId = useId()

  // Load meta on mount
  useEffect(() => {
    const ctrl = new AbortController()
    getMeta(ctrl.signal)
      .then(setMeta)
      .catch(() => { /* non-fatal — use defaults */ })
    return () => ctrl.abort()
  }, [])

  // Show toast on error state
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
      // Auto-dismiss after 6 s
      setTimeout(() => dismissToast(id), 6000)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.status])

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const handleSubmit = useCallback(
    (req: RecommendRequest) => {
      setLastTopK(req.top_k ?? 5)
      setActiveRequest(req)
      setShowForm(false) // Hide form and show reasoning panel
      fetch(req)
    },
    [fetch],
  )

  const isLoading = state.status === 'loading'
  const data = state.status === 'success' ? state.data : null
  const hasResults = state.status === 'success' || isLoading

  // Helper to map budget choices to Zomato price indicators
  const getPriceSymbol = (budget?: string) => {
    if (budget === 'low') return '$'
    if (budget === 'high') return '$$$'
    return '$$'
  }

  return (
    <div className="home">
      {/* ── Top Sticky Header Bar ────────────────────────────────────────── */}
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
          <input
            className="home__search-box"
            type="text"
            placeholder="Search"
            disabled
          />
        </div>

        <div className="home__header-right">
          <button className="home__profile-btn" aria-label="User profile">
            👤
          </button>
        </div>
      </header>

      {/* ── Main content layout ─────────────────────────────────────────── */}
      <main className="home__main">
        <div className="home__layout">
          {/* Left Column (Sticky Sidebar) */}
          <aside className="home__sidebar">
            {showForm || !hasResults ? (
              // Option search form
              <>
                <PreferenceForm onSubmit={handleSubmit} isLoading={isLoading} />
                
                {/* Visual statistics for warm cache loaded state */}
                {meta && (
                  <div style={{ fontSize: '12px', color: '#9ca3af', textAlign: 'center', marginTop: '8px' }}>
                    ✦ Connected to {(51717).toLocaleString()}+ active restaurants in database
                  </div>
                )}
              </>
            ) : (
              // Screenshots reasoning summary & active filters
              <>
                <h2 className="home__sidebar-title">Your AI-Powered Picks</h2>

                {/* Peach Reasoning Bubble */}
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
                      } dining, a rating preference of ${
                        activeRequest?.min_rating?.toFixed(1) ?? '3.0'
                      }+, and a budget of ${
                        activeRequest?.budget === 'low' ? 'under ₹500' : activeRequest?.budget === 'high' ? 'above ₹1,500' : '₹500 to ₹1,500'
                      } per person, I've curated these selections just for you.`}
                  </div>
                </div>

                {/* Filter tags panel */}
                <div className="home__filter-pills">
                  {activeRequest?.cuisines && activeRequest.cuisines.length > 0 && (
                    <div className="home__filter-pill">
                      <strong>Cuisine:</strong> &nbsp;{activeRequest.cuisines.join(', ')}
                    </div>
                  )}
                  <div className="home__filter-pill">
                    <strong>Price:</strong> &nbsp;{getPriceSymbol(activeRequest?.budget)}
                  </div>
                  {activeRequest?.additional && (
                    <div className="home__filter-pill">
                      <strong>Vibe:</strong> &nbsp;{activeRequest.additional}
                    </div>
                  )}
                  <div className="home__filter-pill">
                    <strong>Location:</strong> &nbsp;{activeRequest?.location}
                  </div>
                  <div className="home__filter-pill">
                    <strong>Rating:</strong> &nbsp;{activeRequest?.min_rating?.toFixed(1) ?? '3.0'}+
                  </div>
                </div>

                {/* Edit Filters Button */}
                <button
                  className="home__change-filters-btn"
                  onClick={() => setShowForm(true)}
                >
                  ⚙️ Change Filters / Search
                </button>
              </>
            )}
          </aside>

          {/* Right Column (Scrollable Results) */}
          <section className="home__content">
            <ResultsView isLoading={isLoading} data={data} topK={lastTopK} />
          </section>
        </div>
      </main>

      {/* ── Sticky Bottom Bar ──────────────────────────────────────────── */}
      <footer className="home__bottom-bar">
        <div className="home__chat-pill">
          <input
            className="home__chat-input"
            type="text"
            placeholder="Ask me about their best dish..."
            disabled
          />
          <button className="home__chat-send" disabled>
            Send
          </button>
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
                title: 'Table Booked',
                message: 'Your table reservation request was sent to the restaurant successfully!',
              },
            ])
            setTimeout(() => dismissToast(id), 6000)
          }}
        >
          Book a Table
        </button>
      </footer>

      {/* ── Toasts ───────────────────────────────────────────────────────── */}
      <Toast items={toasts} onDismiss={dismissToast} />
    </div>
  )
}
