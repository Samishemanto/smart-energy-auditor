import { lazy, Suspense } from 'react'

const Plot = lazy(() => import('react-plotly.js'))

export default function LazyPlot(props) {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Loading chart…
      </div>
    }>
      <Plot {...props} />
    </Suspense>
  )
}
