import { useEffect, useState } from 'react'
import LazyPlot from '../components/LazyPlot'
import {
  getPredictions, getAnomalies, getClassify,
  getRecommendations, getClusters, getChangepoints, getCostPrediction, getBills,
} from '../api'
import Spinner from '../components/Spinner'

const LAYOUT = (height = 280, yTitle = '') => ({
  height,
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#94A3B8', family: 'Inter, sans-serif', size: 11 },
  margin: { t: 20, r: 16, b: 52, l: 56 },
  xaxis: { gridcolor: '#1A2840', linecolor: '#334155', tickfont: { size: 10 }, zeroline: false },
  yaxis: { gridcolor: '#1A2840', linecolor: '#334155', tickfont: { size: 10 }, zeroline: false, title: { text: yTitle, font: { size: 10, color: '#64748B' } } },
  showlegend: true,
  legend: { font: { color: '#94A3B8', size: 10 }, bgcolor: 'transparent', orientation: 'h', y: -0.3 },
  bargap: 0.35,
})

const UK_AVG_MONTHLY_KWH  = 258
const UK_AVG_MONTHLY_COST = 130
const UK_AVG_ANNUAL_KWH   = 3100
const UK_AVG_ANNUAL_COST  = 1568

function parseDate(str) {
  if (!str) return null
  const fmts = [
    [/^(\d{1,2})\s+(\w+)\s+(\d{4})$/, (m) => new Date(`${m[2]} ${m[1]} ${m[3]}`)],
    [/^(\d{4})-(\d{2})-(\d{2})$/, (m) => new Date(`${m[1]}-${m[2]}-${m[3]}`)],
  ]
  for (const [re, fn] of fmts) {
    const m = str.trim().match(re)
    if (m) { const d = fn(m); if (!isNaN(d)) return d }
  }
  return null
}

export default function Insights() {
  const [pred, setPred]           = useState(null)
  const [anomalies, setAnomalies] = useState(null)
  const [classify, setClassify]   = useState(null)
  const [recs, setRecs]           = useState([])
  const [clusters, setClusters]   = useState(null)
  const [changepoints, setChangepoints] = useState(null)
  const [costPred, setCostPred]   = useState(null)
  const [bills, setBills]         = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    const safe = (p) => p.then(r => r.data).catch(() => null)
    Promise.all([
      safe(getPredictions()), safe(getAnomalies()), safe(getClassify()),
      safe(getRecommendations()), safe(getClusters()), safe(getChangepoints()),
      safe(getCostPrediction()), safe(getBills()),
    ]).then(([p, a, cl, r, clu, cp, co, b]) => {
      setPred(p); setAnomalies(a); setClassify(cl)
      setRecs(r || []); setClusters(clu); setChangepoints(cp)
      setCostPred(co); setBills(Array.isArray(b) ? b : [])
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const hasData = pred?.status === 'ok' && pred?.predicted_kwh != null

  // ── derive history from bills when backend history not available ──────────────
  const backendHistory = pred?.history || []
  const billsWithDate = bills
    .filter(b => b.usage_kwh && b.bill_date && parseDate(b.bill_date))
    .sort((a, b) => parseDate(a.bill_date) - parseDate(b.bill_date))

  const history = backendHistory.length > 0
    ? backendHistory
    : billsWithDate.map(b => ({
        date: b.bill_date,
        kwh: b.usage_kwh,
        cost: b.amount_due || 0,
        carbon_kg: b.carbon_kg || 0,
      }))

  const histDates  = history.map(h => h.date)
  const histKwh    = history.map(h => h.kwh)
  const histCost   = history.map(h => h.cost)
  const histCarbon = history.map(h => h.carbon_kg)
  const allDates   = [...histDates, pred?.next_period].filter(Boolean)

  // ── derived stats ─────────────────────────────────────────────────────────────
  const avgKwh     = history.length ? history.reduce((s, h) => s + h.kwh, 0) / history.length : null
  const avgCost    = history.length ? history.reduce((s, h) => s + h.cost, 0) / history.length : null
  const totalCarbon = history.reduce((s, h) => s + (h.carbon_kg || 0), 0)

  const annualKwh  = avgKwh  ? Math.round(avgKwh  * 12) : null
  const annualCost = avgCost ? Math.round(avgCost * 12) : null

  const savingsKwh  = avgKwh  ? Math.round((avgKwh  - UK_AVG_MONTHLY_KWH)  * 12) : null
  const savingsCost = avgCost ? Math.round((avgCost - UK_AVG_MONTHLY_COST) * 12) : null

  const efficiencyScore = avgKwh != null
    ? Math.max(0, Math.min(100, Math.round(100 - ((avgKwh - UK_AVG_MONTHLY_KWH) / UK_AVG_MONTHLY_KWH) * 50)))
    : null
  const effColor = efficiencyScore >= 70 ? '#34D399' : efficiencyScore >= 40 ? '#F59E0B' : '#F87171'

  const anomalyBillIds = new Set((anomalies?.anomalies || []).map(a => a.bill_id))

  // ── charts ────────────────────────────────────────────────────────────────────
  const usageChart = history.length > 0 ? [
    {
      type: 'bar', name: 'Your Usage',
      x: histDates, y: histKwh,
      marker: { color: histKwh.map((_, i) => anomalyBillIds.has(bills[i]?.id) ? '#F87171' : '#2DD4BF') },
      text: histKwh.map(v => `${v} kWh`), textposition: 'outside', textfont: { size: 10, color: '#94A3B8' },
    },
    ...(hasData && pred.predicted_kwh > 0 ? [{
      type: 'bar', name: `Forecast (${pred.next_period})`,
      x: [pred.next_period], y: [pred.predicted_kwh],
      marker: { color: '#60A5FA', opacity: 0.75 },
      text: [`${pred.predicted_kwh} kWh`], textposition: 'outside', textfont: { size: 10, color: '#94A3B8' },
    }] : []),
    {
      type: 'scatter', mode: 'lines', name: `UK Avg (${UK_AVG_MONTHLY_KWH} kWh)`,
      x: allDates.length ? allDates : histDates,
      y: (allDates.length ? allDates : histDates).map(() => UK_AVG_MONTHLY_KWH),
      line: { color: '#F59E0B', dash: 'dot', width: 2 },
    },
  ] : []

  const costChart = histCost.some(c => c > 0) ? [
    {
      type: 'bar', name: 'Your Cost (£)',
      x: histDates, y: histCost,
      marker: { color: '#818CF8' },
      text: histCost.map(v => `£${v}`), textposition: 'outside', textfont: { size: 10, color: '#94A3B8' },
    },
    ...(hasData && pred.predicted_cost > 0 ? [{
      type: 'bar', name: `Forecast (${pred.next_period})`,
      x: [pred.next_period], y: [pred.predicted_cost],
      marker: { color: '#60A5FA', opacity: 0.75 },
      text: [`£${pred.predicted_cost}`], textposition: 'outside', textfont: { size: 10, color: '#94A3B8' },
    }] : []),
    {
      type: 'scatter', mode: 'lines', name: `UK Avg (£${UK_AVG_MONTHLY_COST})`,
      x: allDates.length ? allDates : histDates,
      y: (allDates.length ? allDates : histDates).map(() => UK_AVG_MONTHLY_COST),
      line: { color: '#F59E0B', dash: 'dot', width: 2 },
    },
  ] : []

  const carbonChart = histCarbon.some(c => c > 0) ? [
    {
      type: 'scatter', mode: 'lines+markers', name: 'CO₂ (kg)',
      x: histDates, y: histCarbon,
      line: { color: '#34D399', width: 2.5 },
      marker: { size: 8, color: '#34D399' },
      fill: 'tozeroy', fillcolor: 'rgba(52,211,153,0.07)',
    },
    ...(hasData && pred.predicted_carbon_kg > 0 ? [{
      type: 'scatter', mode: 'markers', name: 'Forecast',
      x: [pred.next_period], y: [pred.predicted_carbon_kg],
      marker: { size: 11, color: '#60A5FA', symbol: 'diamond' },
    }] : []),
  ] : []

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">ML Insights</h1>
        <p className="text-textSub text-sm mt-1">AI-powered analysis of your energy usage patterns</p>
      </div>

      {!hasData && bills.length < 2 && (
        <div className="info-box py-12 text-center">
          <div className="text-4xl mb-3">📊</div>
          <div className="font-semibold text-text mb-1">Not enough data yet</div>
          <div className="text-sm text-textSub">Upload at least 2 bills with dates and usage to unlock ML insights.</div>
        </div>
      )}

      {/* ── KPI row ── */}
      {(hasData || history.length > 0) && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Avg Monthly Usage</div>
            <div className="text-2xl font-extrabold text-teal">{avgKwh ? Math.round(avgKwh) : '—'}<span className="text-sm font-normal"> kWh</span></div>
            <div className="text-xs text-textSub mt-1">UK avg: {UK_AVG_MONTHLY_KWH} kWh</div>
          </div>
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Avg Monthly Cost</div>
            <div className="text-2xl font-extrabold text-blue-400">{avgCost ? `£${Math.round(avgCost)}` : '—'}</div>
            <div className="text-xs text-textSub mt-1">UK avg: £{UK_AVG_MONTHLY_COST}</div>
          </div>
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Projected Annual Cost</div>
            <div className="text-2xl font-extrabold text-purple-400">{annualCost ? `£${annualCost}` : '—'}</div>
            <div className="text-xs text-textSub mt-1">UK avg: £{UK_AVG_ANNUAL_COST}</div>
          </div>
          <div className="card text-center">
            <div className="text-xs text-muted mb-1">Efficiency Score</div>
            <div className="text-2xl font-extrabold" style={{ color: effColor }}>
              {efficiencyScore ?? '—'}<span className="text-sm font-normal">/100</span>
            </div>
            <div className="text-xs text-textSub mt-1">vs UK average</div>
          </div>
        </div>
      )}

      {/* ── Savings + Forecast row ── */}
      {(hasData || history.length > 0) && (
        <div className="grid lg:grid-cols-3 gap-4">
          {/* Savings potential */}
          <div className="card lg:col-span-2">
            <div className="sec-head mb-3">Savings Potential vs UK Average</div>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-muted mb-1">Annual energy saving if at UK avg</div>
                <div className={`text-3xl font-extrabold ${savingsKwh > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {savingsKwh != null ? `${savingsKwh > 0 ? '+' : ''}${savingsKwh.toLocaleString()} kWh` : '—'}
                </div>
                <div className="text-xs text-textSub mt-1">
                  {savingsKwh > 0 ? 'above UK average — room to improve' : 'below UK average — great work!'}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted mb-1">Annual cost saving if at UK avg</div>
                <div className={`text-3xl font-extrabold ${savingsCost > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {savingsCost != null ? `${savingsCost > 0 ? '+' : ''}£${Math.abs(savingsCost)}` : '—'}
                </div>
                <div className="text-xs text-textSub mt-1">
                  {savingsCost > 0 ? 'potential annual saving by reducing usage' : 'already saving vs UK average'}
                </div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-border grid grid-cols-3 text-center text-xs gap-2">
              <div>
                <div className="text-muted">Your annual</div>
                <div className="font-bold text-text">{annualKwh ? `${annualKwh.toLocaleString()} kWh` : '—'}</div>
              </div>
              <div>
                <div className="text-muted">UK average</div>
                <div className="font-bold text-text">{UK_AVG_ANNUAL_KWH.toLocaleString()} kWh</div>
              </div>
              <div>
                <div className="text-muted">Total CO₂</div>
                <div className="font-bold text-text">{totalCarbon > 0 ? `${totalCarbon.toFixed(1)} kg` : '—'}</div>
              </div>
            </div>
          </div>

          {/* Forecast + classification */}
          <div className="card">
            <div className="sec-head mb-3">Next Period Forecast</div>
            {hasData ? (
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-muted">Period</div>
                  <div className="font-semibold text-text">{pred.next_period}</div>
                </div>
                <div>
                  <div className="text-xs text-muted">Predicted Usage</div>
                  <div className="text-xl font-extrabold text-teal">
                    {pred.predicted_kwh > 0 ? `${pred.predicted_kwh} kWh` : <span className="text-yellow-400 text-sm">Need more bills for accurate forecast</span>}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted">Predicted Cost</div>
                  <div className="text-xl font-extrabold text-blue-400">
                    {pred.predicted_cost > 0 ? `£${pred.predicted_cost.toFixed(2)}` : '—'}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-xs text-muted">Trend</div>
                  <span className={`text-sm font-bold ${pred.trend === 'increasing' ? 'text-red-400' : 'text-emerald-400'}`}>
                    {pred.trend === 'increasing' ? '↑ Increasing' : '↓ Decreasing'} ({pred.monthly_change_kwh > 0 ? '+' : ''}{pred.monthly_change_kwh} kWh/mo)
                  </span>
                </div>
                {pred.model_r2 != null && (
                  <div className="text-xs text-muted">Model R²: {(pred.model_r2 * 100).toFixed(1)}% accuracy</div>
                )}
              </div>
            ) : (
              <div className="text-sm text-textSub">Upload more bills to enable forecasting.</div>
            )}
            {classify?.label && (
              <div className="mt-4 pt-3 border-t border-border">
                <div className="text-xs text-muted mb-2">Usage Band</div>
                <div className={`inline-block text-sm font-bold px-4 py-1.5 rounded-full border
                  ${classify.label === 'Low' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : classify.label === 'Medium' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                    : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                  {classify.label} Usage
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Usage chart ── */}
      {usageChart.length > 0 && (
        <div className="card">
          <div className="sec-head mb-4">Usage History & Forecast</div>
          <LazyPlot data={usageChart} layout={LAYOUT(300, 'kWh')}
            config={{ responsive: true, displayModeBar: false }} style={{ width: '100%' }} />
          {anomalies?.anomalies?.length > 0 && (
            <p className="text-xs text-red-400 mt-2">⚠ Red bars = anomalous usage detected by Isolation Forest model</p>
          )}
        </div>
      )}

      {/* ── Cost + Carbon ── */}
      {(costChart.length > 0 || carbonChart.length > 0) && (
        <div className="grid lg:grid-cols-2 gap-4">
          {costChart.length > 0 && (
            <div className="card">
              <div className="sec-head mb-4">Cost History & Forecast</div>
              <LazyPlot data={costChart} layout={LAYOUT(260, '£')}
                config={{ responsive: true, displayModeBar: false }} style={{ width: '100%' }} />
            </div>
          )}
          {carbonChart.length > 0 && (
            <div className="card">
              <div className="sec-head mb-4">Carbon Footprint Over Time</div>
              <LazyPlot data={carbonChart} layout={LAYOUT(260, 'kg CO₂')}
                config={{ responsive: true, displayModeBar: false }} style={{ width: '100%' }} />
              {totalCarbon > 0 && (
                <p className="text-xs text-textSub mt-2">
                  🌳 Equivalent to planting {Math.round(totalCarbon / 21)} trees to offset
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Bill comparison table ── */}
      {billsWithDate.length > 0 && (
        <div className="card overflow-x-auto">
          <div className="sec-head mb-3">Bill-by-Bill Comparison</div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-muted text-xs border-b border-border">
                <th className="text-left py-2 pr-4">Bill Date</th>
                <th className="text-left py-2 pr-4">Provider</th>
                <th className="text-right py-2 pr-4">Usage (kWh)</th>
                <th className="text-right py-2 pr-4">Cost (£)</th>
                <th className="text-right py-2 pr-4">CO₂ (kg)</th>
                <th className="text-right py-2">vs UK avg</th>
              </tr>
            </thead>
            <tbody>
              {billsWithDate.map((b, i) => {
                const diff = b.usage_kwh - UK_AVG_MONTHLY_KWH
                return (
                  <tr key={b.id} className="border-b border-border/40 hover:bg-white/[0.02]">
                    <td className="py-2 pr-4 text-text font-medium">{b.bill_date}</td>
                    <td className="py-2 pr-4 text-textSub">{b.provider}</td>
                    <td className="py-2 pr-4 text-right font-semibold text-text">{b.usage_kwh.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-textSub">{b.amount_due ? `£${b.amount_due.toFixed(2)}` : '—'}</td>
                    <td className="py-2 pr-4 text-right text-textSub">{b.carbon_kg ? b.carbon_kg.toFixed(1) : '—'}</td>
                    <td className={`py-2 text-right text-xs font-semibold ${diff > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {diff > 0 ? '+' : ''}{diff} kWh
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Anomaly + Changepoints ── */}
      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card">
          <div className="sec-head mb-3">Anomaly Detection <span className="text-xs text-muted font-normal">(Isolation Forest)</span></div>
          {anomalies?.anomalies?.length > 0 ? (
            <div className="space-y-2">
              {anomalies.anomalies.map((a, i) => (
                <div key={i} className="flex items-center justify-between bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  <div>
                    <div className="text-xs text-red-400 font-semibold">⚠ Unusual spike detected</div>
                    <div className="text-sm text-text">{a.bill_date || `Bill #${a.bill_id}`} — {a.usage_kwh} kWh</div>
                  </div>
                  {a.deviation != null && (
                    <div className="text-sm font-bold text-red-400">{a.deviation > 0 ? '+' : ''}{a.deviation.toFixed(0)}%</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-emerald-400 flex items-center gap-2 py-2">✓ No anomalies — usage looks consistent.</div>
          )}
        </div>

        <div className="card">
          <div className="sec-head mb-3">Usage Clusters <span className="text-xs text-muted font-normal">(KMeans)</span></div>
          {clusters?.cluster_labels ? (
            <>
              <p className="text-xs text-textSub mb-3">Bills grouped by usage level:</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(
                  clusters.cluster_labels.reduce((acc, l) => { acc[l] = (acc[l] || 0) + 1; return acc }, {})
                ).map(([label, count]) => (
                  <div key={label} className={`px-4 py-2 rounded-xl border text-sm font-semibold
                    ${label === 'Low' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                      : label === 'Medium' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                      : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                    {label}: {count} bill{count !== 1 ? 's' : ''}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="text-sm text-textSub py-2">Upload more bills to enable clustering.</div>
          )}
          {changepoints?.changepoints?.length > 0 && (
            <div className="mt-4 pt-3 border-t border-border">
              <div className="text-xs text-muted mb-2">Behaviour shifts detected <span className="font-normal">(PELT)</span></div>
              <div className="flex flex-wrap gap-2">
                {changepoints.changepoints.map((cp, i) => (
                  <div key={i} className="bg-yellow-500/10 border border-yellow-500/25 text-yellow-400 px-3 py-1 rounded-lg text-xs font-semibold">
                    Bill #{cp}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

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
    </div>
  )
}
