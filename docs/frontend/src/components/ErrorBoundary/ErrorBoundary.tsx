import { Component, type ErrorInfo, type ReactNode } from 'react'
import './ErrorBoundary.css'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Class-based React error boundary (Phase 6).
 * Catches unhandled rendering errors anywhere in the subtree and shows
 * a styled fallback panel with a Reload button.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production this would ship to an observability sink (Sentry, Datadog)
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  private handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="eb" role="alert" aria-live="assertive">
          <div className="eb__card">
            <div className="eb__icon">⚠️</div>
            <h1 className="eb__title">Something went wrong</h1>
            <p className="eb__message">
              An unexpected error occurred in the application. Our team has been
              notified. Please try reloading the page.
            </p>
            {this.state.error && (
              <pre className="eb__detail">
                {this.state.error.message}
              </pre>
            )}
            <button
              id="eb-reload-btn"
              className="eb__btn"
              onClick={this.handleReload}
            >
              🔄 Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
