import { useEffect, useState } from 'react'
import LazyPlot from '../components/LazyPlot'
import {
  getPredictions, getAnomalies, getClassify,
  getRecommendations, getClusters, getChangepoints, getCostPrediction,
} from '../api'
import Spinner from '../components/Spinner'

const LAYOUT = (height = 260) => ({
  height,
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#94A3B8', family: 'Inter, sans-serif', size: 11 },
  margin: { t: 10, r: 10, b: 40, l: 50 },
  xaxis: { gridcolor: '#1A2840', linecolor: '#1A2840', tickfont: { size: 10 } },
  yaxis: { gridcolor: '#1A2840', linecolor: '#1A2840', tickfont: { size: 10 } },
  showlegend: true,
  legend: { font: { color: '#94A3B8', size: 10 }, bgcolor: 'transparent' },
})

export default function Insights() {
  const [pred, setPred] = useState(null)
  const [anomalies, setAnomalies] = useState(null)
  const [classify, setClassify] = useState(null)
  const [recs, setRecs] = useState([])
  const [clusters, setClusters] = useState(null)
  const [changepoints, setChangepoints] = useState(null)
  const [costPred, setCostPred] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getPredictions(), getAnomalies(), getClassify(),
      getRecommendations(), getClusters(), getChangepoints(), getCostPrediction(),
    ]).then(([p, a, cl, r, clu, cp, co]) => {
      setPred(p.data); setAnomalies(a.data); setClassify(cl.data)
      setRecs(r.data || []); setClusters(clu.data); setChangepoints(cp.data); setCostPred(co.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const hasData = pred?.historical_kwh?.length > 0

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">ML Insights</h1>
        <p className="text-textSub text-sm mt-1">AI-powered analysis of your energy usage patterns</p>
      </div>

      {!hasData && (
        <div className="info-box py-12">
          Upload at least 3 bills with usage data to see ML insights.
        </div>
      )}

      {/* Prediction + Classification */}
      {hasData && (
        <div className="grid lg:grid-cols-2 gap-4">
          {/* Usage forecast */}
          <div className="card">
            <div className="sec-head mb-1">Usage Forecast</div>
            {pred?.predicted_kwh && (
              <div className="text-2xl font-extrabold text-teal mb-3">
                {pred.predicted_kwh} kWh <span className="text-sm text-muted font-normal">next month</span>
              </div>
            )}
            <LazyPlot
              data={[
                { type: 'scatter', mode: 'lines+markers', name: 'Historical',
                  x: pred.historical_dates || pred.historical_kwh.map((_, i) => `Bill ${i+1}`),
                  y: pred.historical_kwh,
                  line: { color: '#00C9B8', width: 2 }, marker: { size: 5 } },
                ...(pred.prophet_forecast ? [{
                  type: 'scatter', mode: 'lines', name: 'Prophet',
                  x: pred.prophet_dates || [], y: pred.prophet_forecast,
                  line: { color: '#1D4ED8', width: 2, dash: 'dot' },
                }] : []),
              ]}
              layout={{ ...LAYOUT(220), yaxis: { ...LAYOUT().yaxis, title: 'kWh' } }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%' }}
            />
            {pred?.model && <div className="text-xs text-muted mt-2">Model: {pred.model}</div>}
          </div>

          {/* Cost prediction */}
          {costPred?.predicted_cost != null && (
            <div className="card">
              <div className="sec-head mb-1">Cost Forecast</div>
              <div className="text-2xl font-extrabold text-blue-400 mb-3">
                £{costPred.predicted_cost.toFixed(2)} <span className="text-sm text-muted font-normal">next month</span>
              </div>
              <div className="space-y-2 text-sm">
                {costPred.r2_score != null && (
                  <div className="flex justify-between">
                    <span className="text-muted">Model accuracy (R²)</span>
                    <span className={`font-semibold ${costPred.r2_score > 0.7 ? 'text-emerald-400' : 'text-yellow-400'}`}>
                      {(costPred.r2_score * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {costPred.model && (
                  <div className="flex justify-between">
                    <span className="text-muted">Algorithm</span>
                    <span className="text-textSub">{costPred.model}</span>
                  </div>
                )}
              </div>

              {/* Classification badge */}
              {classify?.label && (
                <div className="mt-4 pt-4 border-t border-border">
                  <div className="sec-head mb-2">Usage Classification</div>
                  <div className={`inline-block text-sm font-semibold px-4 py-1.5 rounded-full border
                    ${classify.label === 'Low' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                      : classify.label === 'Medium' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                      : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                    {classify.label} Usage
                  </div>
                  {classify.avg_kwh && (
                    <p className="text-xs text-muted mt-2">Average: {classify.avg_kwh.toFixed(0)} kWh/bill</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Anomalies */}
      {anomalies?.anomalies?.length > 0 && (
        <div className="card">
          <div className="sec-head mb-3">Anomaly Detection</div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {anomalies.anomalies.map((a, i) => (
              <div key={i} className="bg-red-500/10 border border-red-500/25 rounded-xl p-3">
                <div className="text-xs text-red-400 font-semibold mb-1">⚠ Anomaly Detected</div>
                <div className="text-sm text-textSub">{a.bill_date || `Bill #${a.bill_id}`}</div>
                <div className="text-base font-bold text-text">{a.usage_kwh} kWh</div>
                {a.deviation && (
                  <div className="text-xs text-red-400 mt-1">{a.deviation > 0 ? '+' : ''}{a.deviation.toFixed(0)}% deviation</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {anomalies?.anomalies?.length === 0 && hasData && (
        <div className="card">
          <div className="sec-head mb-2">Anomaly Detection</div>
          <div className="text-sm text-emerald-400 flex items-center gap-2">
            <span>✓</span> No anomalies detected — your usage looks consistent.
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recs.length > 0 && (
        <div className="card">
          <div className="sec-head mb-3">Smart Recommendations</div>
          <div className="grid sm:grid-cols-2 gap-2">
            {recs.map((r, i) => (
              <div key={i} className="bg-[#0A1018] border-l-2 border-teal rounded-lg p-3 text-sm text-textSub leading-relaxed">
                {r.title && <span className="font-semibold text-text">{r.title} — </span>}
                {r.detail || r.message || ''}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clusters */}
      {clusters?.cluster_labels && (
        <div className="card">
          <div className="sec-head mb-3">Usage Clusters (KMeans)</div>
          <div className="flex flex-wrap gap-3">
            {Object.entries(
              clusters.cluster_labels.reduce((acc, label) => {
                acc[label] = (acc[label] || 0) + 1; return acc
              }, {})
            ).map(([label, count]) => (
              <div key={label} className={`px-4 py-2 rounded-xl border text-sm font-semibold
                ${label === 'Low' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : label === 'Medium' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                  : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                {label}: {count} bill{count !== 1 ? 's' : ''}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Changepoints */}
      {changepoints?.changepoints?.length > 0 && (
        <div className="card">
          <div className="sec-head mb-3">Changepoint Detection</div>
          <p className="text-sm text-textSub mb-3">Significant shifts detected in your usage pattern:</p>
          <div className="flex flex-wrap gap-2">
            {changepoints.changepoints.map((cp, i) => (
              <div key={i} className="bg-yellow-500/10 border border-yellow-500/25 text-yellow-400 px-3 py-1.5 rounded-lg text-sm">
                Bill #{cp}
              </div>
            ))}
          </div>
          {changepoints.method && (
            <div className="text-xs text-muted mt-3">Method: {changepoints.method}</div>
          )}
        </div>
      )}
    </div>
  )
}
