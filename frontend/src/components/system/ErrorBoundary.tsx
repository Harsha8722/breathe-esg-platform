import React from 'react'

type Props = {
  children: React.ReactNode
  title?: string
}

type State = {
  hasError: boolean
  error?: unknown
}

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: unknown): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: unknown) {
    // Keep a console breadcrumb for debugging. The UI shows a friendly fallback.
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary] Uncaught error', error)
  }

  render() {
    if (!this.state.hasError) return this.props.children

    const message =
      this.state.error instanceof Error
        ? this.state.error.message
        : 'A runtime error occurred while rendering this page.'

    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="card p-6 max-w-xl w-full">
          <div className="flex items-start gap-3">
            <div className="text-2xl">⚠️</div>
            <div className="flex-1">
              <div className="text-lg font-bold text-slate-800">
                {this.props.title ?? 'Something went wrong'}
              </div>
              <div className="text-sm text-slate-600 mt-1">
                The app hit an unexpected error instead of rendering a blank screen.
              </div>
              <div className="mt-3 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-3 text-slate-600 overflow-auto">
                {message}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="btn-primary" onClick={() => window.location.reload()}>
                  Reload
                </button>
                <button className="btn-secondary" onClick={() => this.setState({ hasError: false, error: undefined })}>
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

