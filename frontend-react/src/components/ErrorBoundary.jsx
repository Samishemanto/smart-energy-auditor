import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="card max-w-lg w-full text-center space-y-4">
            <div className="text-4xl">⚠️</div>
            <div className="text-lg font-bold text-text">Something went wrong</div>
            <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-left font-mono break-all">
              {this.state.error.message}
            </div>
            <button
              className="btn-primary"
              onClick={() => { this.setState({ error: null }); window.location.href = '/' }}
            >
              Go to home
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
