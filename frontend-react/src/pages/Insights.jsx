import { useEffect, useState } from 'react'
import LazyPlot from '../components/LazyPlot'
import {
  getPredictions, getAnomalies, getClassify,
  getRecommendations, getClusters, getChangepoints, getCostPrediction,
} from '../api'
import Spinner from '../components/Spinner'

const LAYOUT = (height = 280, extra = {}) => ({
  height,
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#94A3B8', family: 'Inter, sans-serif', size: 11 },
  margin: { t: 20, r: 16, b: 48, l: 52 },
  xaxis: { gridcolor: '#1A2840', linecolor: '#334155', tickfont: { size: 10 }, zeroline: false },
  yaxis: { gridcolor: '#1A2840', linecolor: '#334155', tickfont: { size: 10 }, zeroline: false },
  showlegend: true,
  legend: { font: { color: '#94A3B8', size: 10 }, bgcolor: 'transparent', orientation: 'h', y: -0.25 },
  bargap: 0.3,
  ...extra,
})

const UK_AVG_KWH = 258   // UK avg monthly kWh (3100/12)
const UK_AVG_COST = 130  // UK avg monthly £

export default function Insights() {
  const [pred, setPred]           = useState(null)
  const [anomalies, setAnomalies] = useState(null)
  const [classify, setClassify]   = useState(null)
  const [recs, setRecs]           = useState([])
  const [clusters, setClusters]   = useState(null)
  const [changepoints, setChangepoints] = useState(null)
  const [costPred, setCostPred]   = useState(null)
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    const safe = (p) => p.then(r => r.data).catch(() => null)
    Promise.all([
      safe(getPredictions()), safe(getAnomalies()), safe(getClassify()),
      safe(getRecommendations()), safe(getClusters()), safe(getChangepoints()), safe(getCostPrediction()),
    ]).then(([p, a, cl, r, clu, cp, co]) => {
      setPred(p); setAnomalies(a); setClassify(cl)
      setRecs(r || []); setClusters(clu); setChangepoints(cp); setCostPred(co)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const hasData  = pred?.status === 'ok' && pred?.predicted_kwh != null
  const history  = pred?.history || []
  const anomalyIds = new Set((anomalies?.anomalies || []).map(a => a.bill_id))

  // ── chart data ──────────────────────────────────────────────────────────────
  const histDates  = history.map(h => h.date)
  const histKwh    = history.map(h => h.kwh)
  const histCost   = history.map(h => h.cost)
  const histCarbon = history.map(h => h.carbon_kg)
  const allDates   = [...histDates, pred?.next_period].filter(Boolean)

  const usageChart = hasData ? [
    {
      type: 'bar', name: 'Actual Usage (kWh)',
      x: histDates, y: histKwh,
      marker: { color: histKwh.map((_, i) => anomalyIds.has(i + 1) ? '#F87171' : '#2DD4BF') },
      text: histKwh.map(v => `${v} kWh`), textposition: 'outside', textfont: { size: 10 },
    },
    {
      type: 'bar', name: `Predicted (${pred?.next_period})`,
      x: [pred?.next_period], y: [pred?.predicted_kwh],
      marker: { color: '#60A5FA', opacity: 0.75 },
      text: [`${pred?.predicted_kwh} kWh`], textposition: 'outside', textfont: { size: 10 },
    },
    {
      type: 'scatter', mode: 'lines', name: 'UK Avg',
      x: allDates, y: allDates.map(() => UK_AVG_KWH),
      line: { color: '#F59E0B', dash: 'dot', width: 1.5 },
    },
  ] : []

  const costChart = hasData && histCost.some(c => c > 0) ? [
    {
      type: 'bar', name: 'Actual Cost (£)',
      x: histDates, y: histCost,
      marker: { color: '#818CF8' },
      text: histCost.map(v => `£${v}`), textposition: 'outside', textfont: { size: 10 },
    },
    ...(pred?.predicted_cost != null ? [{
      type: 'bar', name: `Predicted (${pred?.next_period})`,
      x: [pred?.next_period], y: [pred?.predicted_cost],
      marker: { color: '#60A5FA', opacity: 0.75 },
      text: [`£${pred?.predicted_cost}`], textposition: 'outside', textfont: { size: 10 },
    }] : []),
    {
      type: 'scatter', mode: 'lines', name: 'UK Avg',
      x: allDates, y: allDates.map(() => UK_AVG_COST),
      line: { color: '#F59E0B', dash: 'dot', width: 1.5 },
    },
  ] : []

  const carbonChart = hasData && histCarbon.some(c => c > 0) ? [
    {
      type: 'scatter', mode: 'lines+markers', name: 'CO₂ (kg)',
      x: histDates, y: histCarbon,
      line: { color: '#34D399', width: 2 },
      marker: { size: 7, color: '#34D399' },
      fill: 'tozeroy', fillcolor: 'rgba(52,211,153,0.08)',
      text: histCarbon.map(v => `${v} kg`), hovertemplate: '%{text}',
    },
    ...(pred?.predicted_carbon_kg != null ? [{
      type: 'scatter', mode: 'markers', name: `Predicted`,
      x: [pred?.next_period], y: [pred?.predicted_carbon_kg],
      marker: { size: 10, color: '#60A5FA', symbol: 'diamond' },
      text: [`${pred?.predicted_carbon_kg} kg`], hovertemplate: '%{text}',
    }] : []),
  ] : []

  // ── efficiency score ─────────────────────────────────────────────────────────
  const avgKwh = history.length ? history.reduce((s, h) => s + h.kwh, 0) / history.length : null
  const efficiencyScore = avgKwh != null
    ? Math.max(0, Math.min(100, Math.round(100 - ((avgKwh - UK_AVG_KWH) / UK_AVG_KWH) * 50)))
    : null
  const effColor = efficiencyScore >= 70 ? '#34D399' : efficiencyScore >= 40 ? '#F59E0B' : '#F87171'

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">ML Insights</h1>
        <p className="text-textSub text-sm mt-1">AI-powered analysis of your energy usage patterns</p>
      </div>

      {!hasData && (
        <div className="info-box py-12 text-center">
          <div className="text-4xl mb-3">📊</div>
          <div className="font-semibold text-text mb-1">Not enough data yet</div>
          <div className="text-sm text-textSub">Upload at least 2 bills with dates and usage to unlock ML insights.</div>
        </div>
      )}

      {/* ── KPI row ── */}
      {hasData && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Predicted Next Month</div>
            <div className="text-2xl font-extrabold text-teal">{pred.predicted_kwh} <span className="text-sm font-normal">kWh</span></div>
            <div className="text-xs text-textSub mt-1">{pred.next_period}</div>
          </div>
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Predicted Cost</div>
            <div className="text-2xl font-extrabold text-blue-400">
              {pred.predicted_cost != null ? `£${pred.predicted_cost.toFixed(2)}` : '—'}
            </div>
            <div className="text-xs text-textSub mt-1">{pred.next_period}</div>
          </div>
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Trend</div>
            <div className={`text-2xl font-extrabold ${pred.trend === 'increasing' ? 'text-red-400' : 'text-emerald-400'}`}>
              {pred.trend === 'increasing' ? '↑' : '↓'}
            </div>
            <div className="text-xs text-textSub mt-1">{pred.monthly_change_kwh > 0 ? '+' : ''}{pred.monthly_change_kwh} kWh/mo</div>
          </div>
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Efficiency Score</div>
            <div className="text-2xl font-extrabold" style={{ color: effColor }}>{efficiencyScore ?? '—'}<span className="text-sm font-normal">/100</span></div>
            <div className="text-xs text-textSub mt-1">vs UK average</div>
          </div>
        </div>
      )}

      {/* ── Usage chart ── */}
      {hasData && usageChart.length > 0 && (
        <div className="card">
          <div className="sec-head mb-4">Usage History & Forecast</div>
          <LazyPlot
            data={usageChart}
            layout={{ ...LAYOUT(280), yaxis: { ...LAYOUT().yaxis, title: { text: 'kWh', font: { size: 10, color: '#64748B' } } } }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
          {anomalies?.anomalies?.length > 0 && (
            <p className="text-xs text-red-400 mt-2">⚠ Red bars indicate anomalous usage detected by the model.</p>
          )}
        </div>
      )}

      {/* ── Cost + Carbon charts ── */}
      {hasData && (costChart.length > 0 || carbonChart.length > 0) && (
        <div className="grid lg:grid-cols-2 gap-4">
          {costChart.length > 0 && (
            <div className="card">
              <div className="sec-head mb-4">Cost History & Forecast</div>
              <LazyPlot
                data={costChart}
                layout={{ ...LAYOUT(240), yaxis: { ...LAYOUT().yaxis, title: { text: '£', font: { size: 10, color: '#64748B' } } } }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%' }}
              />
            </div>
          )}
          {carbonChart.length > 0 && (
            <div className="card">
              <div className="sec-head mb-4">Carbon Footprint (kg CO₂)</div>
              <LazyPlot
                data={carbonChart}
                layout={{ ...LAYOUT(240), yaxis: { ...LAYOUT().yaxis, title: { text: 'kg CO₂', font: { size: 10, color: '#64748B' } } } }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%' }}
              />
            </div>
          )}
        </div>
      )}

      {/* ── Classification + Anomalies ── */}
      {hasData && (
        <div className="grid lg:grid-cols-2 gap-4">
          {classify?.label && (
            <div className="card">
              <div className="sec-head mb-3">Usage Classification</div>
              <div className="flex items-center gap-4">
                <div className={`text-4xl font-extrabold px-5 py-3 rounded-2xl border
                  ${classify.label === 'Low' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : classify.label === 'Medium' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                    : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                  {classify.label}
                </div>
                <div className="text-sm text-textSub space-y-1">
                  <div>Avg usage: <span className="text-text font-semibold">{classify.avg_kwh?.toFixed(0)} kWh/bill</span></div>
                  <div>UK average: <span className="text-text font-semibold">{UK_AVG_KWH} kWh/month</span></div>
                  {avgKwh && <div>Your avg: <span className="text-text font-semibold">{avgKwh.toFixed(0)} kWh/month</span></div>}
                </div>
              </div>
            </div>
          )}

          <div className="card">
            <div className="sec-head mb-3">Anomaly Detection</div>
            {anomalies?.anomalies?.length > 0 ? (
              <div className="space-y-2">
                {anomalies.anomalies.map((a, i) => (
                  <div key={i} className="flex items-center justify-between bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    <div>
                      <div className="text-xs text-red-400 font-semibold">⚠ Unusual spike</div>
                      <div className="text-sm text-text">{a.bill_date || `Bill #${a.bill_id}`} — {a.usage_kwh} kWh</div>
                    </div>
                    {a.deviation != null && (
                      <div className="text-sm font-bold text-red-400">{a.deviation > 0 ? '+' : ''}{a.deviation.toFixed(0)}%</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-emerald-400 flex items-center gap-2 py-2">
                <span>✓</span> No anomalies detected — usage looks consistent.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Changepoints ── */}
      {changepoints?.changepoints?.length > 0 && (
        <div className="card">
          <div className="sec-head mb-2">Behaviour Change Detected</div>
          <p className="text-sm text-textSub mb-3">Your usage pattern shifted significantly at these points:</p>
          <div className="flex flex-wrap gap-2">
            {changepoints.changepoints.map((cp, i) => (
              <div key={i} className="bg-yellow-500/10 border border-yellow-500/25 text-yellow-400 px-3 py-1.5 rounded-lg text-sm font-semibold">
                Bill #{cp}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Recommendations ── */}
      {recs.length > 0 && (
        <div className="card">
          <div className="sec-head mb-3">Smart Recommendations</div>
          <div className="grid sm:grid-cols-2 gap-3">
            {recs.map((r, i) => (
              <div key={i} className="bg-[#0A1018] border border-border rounded-xl p-4 text-sm text-textSub leading-relaxed hover:border-teal/40 transition-colors">
                {r.title && <div className="font-semibold text-text mb-1">{r.title}</div>}
                {r.detail || r.message || ''}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Clusters ── */}
      {clusters?.cluster_labels && (
        <div className="card">
          <div className="sec-head mb-3">Usage Clustering (KMeans)</div>
          <p className="text-sm text-textSub mb-3">Your bills have been grouped by usage level:</p>
          <div className="flex flex-wrap gap-3">
            {Object.entries(
              clusters.cluster_labels.reduce((acc, label) => { acc[label] = (acc[label] || 0) + 1; return acc }, {})
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
    </div>
  )
}
