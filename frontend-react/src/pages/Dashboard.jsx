import { useEffect, useState } from 'react'
import LazyPlot from '../components/LazyPlot'
import { getStats, getBills, getRecommendations, getUpcomingDues, getGoal, getBudgetStatus } from '../api'
import KpiCard from '../components/KpiCard'
import Spinner from '../components/Spinner'

const CHART_LAYOUT = (height = 280) => ({
  height,
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#94A3B8', family: 'Inter, sans-serif', size: 11 },
  margin: { t: 10, r: 10, b: 40, l: 50 },
  xaxis: { gridcolor: '#1A2840', linecolor: '#1A2840', tickfont: { size: 10 } },
  yaxis: { gridcolor: '#1A2840', linecolor: '#1A2840', tickfont: { size: 10 } },
  showlegend: false,
})

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [bills, setBills] = useState([])
  const [recs, setRecs] = useState([])
  const [upcoming, setUpcoming] = useState([])
  const [goal, setGoal] = useState(null)
  const [budget, setBudget] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getStats(), getBills(), getRecommendations(), getUpcomingDues(), getGoal(), getBudgetStatus(),
    ]).then(([s, b, r, u, g, bst]) => {
      setStats(s.data)
      setBills(b.data)
      setRecs(r.data?.slice(0, 4) || [])
      setUpcoming(u.data || [])
      setGoal(g.data)
      setBudget(bst.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const kwhList = bills.filter(b => b.usage_kwh).map(b => b.usage_kwh)
  const costList = bills.filter(b => b.amount_due).map(b => b.amount_due)
  const dateList = bills.filter(b => b.usage_kwh).map(b => b.bill_date || `Bill ${b.id}`)
  const dateCost = bills.filter(b => b.amount_due).map(b => b.bill_date || `Bill ${b.id}`)

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Hero */}
      <div className="card bg-gradient-to-br from-[#080E1E] to-[#0C1525] border-teal/20">
        <div className="badge-teal mb-3 text-xs">⚡ AI-Powered Energy Analysis</div>
        <h1 className="text-2xl font-extrabold text-text mb-1">Your Energy Dashboard</h1>
        <p className="text-textSub text-sm">Real-time insights from your UK energy bills</p>
      </div>

      {/* Budget warning */}
      {budget && (budget.cost_status === 'exceeded' || budget.kwh_status === 'exceeded') && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm flex items-center gap-3">
          🚨 <span>
            {budget.cost_status === 'exceeded' ? `Latest bill (£${budget.latest_cost?.toFixed(2)}) exceeds your monthly budget of £${budget.budget_monthly_gbp?.toFixed(2)}` : ''}
            {budget.kwh_status === 'exceeded' ? ` Usage (${budget.latest_kwh} kWh) exceeds your ${budget.budget_monthly_kwh} kWh limit` : ''}
          </span>
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon="💷" label="Total Spend" value={`£${(stats?.total_spend || 0).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} sub={`${stats?.total_bills || 0} bills`} />
        <KpiCard icon="⚡" label="Avg Monthly kWh" value={(stats?.avg_monthly_kwh || 0).toLocaleString()} sub="kWh per bill" />
        <KpiCard icon="💳" label="Avg Bill Cost" value={`£${(stats?.avg_monthly_cost || 0).toFixed(2)}`} sub="per month" />
        <KpiCard icon="🌿" label="Total CO₂" value={`${(stats?.total_carbon_kg || 0).toFixed(0)} kg`} sub="CO₂ generated" valueColor="text-emerald-400" />
      </div>

      {/* Charts row */}
      {bills.length > 1 && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="card">
            <div className="sec-head mb-3">Usage Over Time</div>
            <LazyPlot
              data={[{
                type: 'bar', x: dateList, y: kwhList,
                marker: { color: 'rgba(0,201,184,0.7)', line: { color: '#00C9B8', width: 1 } },
              }]}
              layout={{ ...CHART_LAYOUT(240), yaxis: { ...CHART_LAYOUT().yaxis, title: 'kWh' } }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%' }}
            />
          </div>
          <div className="card">
            <div className="sec-head mb-3">Cost Over Time</div>
            <LazyPlot
              data={[{
                type: 'scatter', mode: 'lines+markers', x: dateCost, y: costList,
                line: { color: '#1D4ED8', width: 2 },
                marker: { color: '#00C9B8', size: 6 },
              }]}
              layout={{ ...CHART_LAYOUT(240), yaxis: { ...CHART_LAYOUT().yaxis, title: '£' } }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%' }}
            />

          </div>
        </div>
      )}

      {/* Bottom row */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Recommendations */}
        <div className="card">
          <div className="sec-head mb-3">Smart Recommendations</div>
          {recs.length > 0 ? (
            <div className="space-y-2">
              {recs.map((r, i) => (
                <div key={i} className="bg-[#0A1018] border-l-2 border-teal rounded-lg p-3 text-sm text-textSub leading-relaxed">
                  {r.title && <span className="font-semibold text-text">{r.title} — </span>}
                  {r.detail || r.message || ''}
                </div>
              ))}
            </div>
          ) : (
            <div className="info-box">Upload more bills to generate recommendations.</div>
          )}
        </div>

        <div className="space-y-4">
          {/* Upcoming dues */}
          {upcoming.length > 0 && (
            <div className="card">
              <div className="sec-head mb-3">Upcoming Payments</div>
              <div className="space-y-2">
                {upcoming.map((u) => (
                  <div key={u.bill_id} className="flex items-center justify-between text-sm">
                    <span className="text-textSub">{u.provider}</span>
                    <span className={`font-semibold ${u.days_left <= 1 ? 'text-red-400' : u.days_left <= 3 ? 'text-yellow-400' : 'text-blue-400'}`}>
                      {u.days_left === 0 ? 'Today' : u.days_left === 1 ? 'Tomorrow' : `${u.days_left} days`} · £{u.amount_due?.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Goal progress */}
          {goal?.goal_reduction_pct && (
            <div className="card">
              <div className="sec-head mb-3">Reduction Goal</div>
              <div className="flex items-center justify-between mb-2 text-sm">
                <span className="text-textSub">Target: {goal.goal_reduction_pct}% reduction</span>
                <span className={`font-semibold ${goal.on_track ? 'text-emerald-400' : 'text-yellow-400'}`}>
                  {goal.progress_pct != null ? `${goal.progress_pct.toFixed(0)}%` : 'No data'}
                </span>
              </div>
              {goal.progress_pct != null && (
                <div className="bg-[#0A1018] rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${goal.on_track ? 'bg-emerald-400' : 'bg-yellow-400'}`}
                    style={{ width: `${Math.min(goal.progress_pct, 100)}%` }}
                  />
                </div>
              )}
            </div>
          )}

          {/* Provider breakdown */}
          {stats?.providers && Object.keys(stats.providers).length > 0 && (
            <div className="card">
              <div className="sec-head mb-3">Providers</div>
              <div className="space-y-2">
                {Object.entries(stats.providers)
                  .sort((a, b) => b[1] - a[1])
                  .map(([prov, cnt]) => (
                    <div key={prov}>
                      <div className="flex justify-between text-xs text-textSub mb-1">
                        <span>{prov}</span>
                        <span>{cnt} bill{cnt !== 1 ? 's' : ''}</span>
                      </div>
                      <div className="bg-[#0A1018] rounded-full h-1.5 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-teal to-blue"
                          style={{ width: `${(cnt / stats.total_bills) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))
                }
              </div>
            </div>
          )}
        </div>
      </div>

      {/* No data */}
      {bills.length === 0 && (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">⚡</div>
          <div className="text-text font-semibold mb-2">No bills yet</div>
          <div className="text-textSub text-sm">Upload your first energy bill to see insights here.</div>
        </div>
      )}
    </div>
  )
}
