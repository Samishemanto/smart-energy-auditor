import { useEffect, useState } from 'react'
import { getBudget, setBudget, getBudgetStatus, getGoal, setGoal, triggerSummary, checkDueDates, getUpcomingDues } from '../api'
import Spinner from '../components/Spinner'

function ProgressBar({ pct, status }) {
  const color = status === 'exceeded' ? 'bg-red-500' : status === 'warning' ? 'bg-yellow-400' : 'bg-teal'
  return (
    <div className="bg-[#0A1018] rounded-full h-2 overflow-hidden mt-1.5">
      <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.min(pct || 0, 100)}%` }} />
    </div>
  )
}

export default function Alerts() {
  const [budget, setBudgetData] = useState({ budget_monthly_gbp: '', budget_monthly_kwh: '', email_alerts: false })
  const [status, setStatus] = useState(null)
  const [goal, setGoalData] = useState({ goal_reduction_pct: '' })
  const [upcoming, setUpcoming] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savingGoal, setSavingGoal] = useState(false)
  const [sending, setSending] = useState(null)
  const [msg, setMsg] = useState(null)

  useEffect(() => {
    Promise.all([getBudget(), getBudgetStatus(), getGoal(), getUpcomingDues()])
      .then(([b, s, g, u]) => {
        setBudgetData(b.data)
        setStatus(s.data)
        setGoalData({ goal_reduction_pct: g.data?.goal_reduction_pct || '' })
        setUpcoming(u.data || [])
      }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleSaveBudget = async (e) => {
    e.preventDefault(); setSaving(true); setMsg(null)
    try {
      await setBudget({
        budget_monthly_gbp: budget.budget_monthly_gbp ? parseFloat(budget.budget_monthly_gbp) : null,
        budget_monthly_kwh: budget.budget_monthly_kwh ? parseInt(budget.budget_monthly_kwh) : null,
        email_alerts: budget.email_alerts,
      })
      const s = await getBudgetStatus()
      setStatus(s.data)
      setMsg({ type: 'success', text: 'Budget settings saved!' })
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Save failed.' })
    } finally { setSaving(false) }
  }

  const handleSaveGoal = async (e) => {
    e.preventDefault(); setSavingGoal(true); setMsg(null)
    try {
      await setGoal({ goal_reduction_pct: parseFloat(goal.goal_reduction_pct) })
      const g = await getGoal()
      setGoalData({ goal_reduction_pct: g.data?.goal_reduction_pct || '' })
      setMsg({ type: 'success', text: 'Goal saved!' })
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Save failed.' })
    } finally { setSavingGoal(false) }
  }

  const handleEmail = async (action) => {
    setSending(action); setMsg(null)
    try {
      if (action === 'summary') {
        await triggerSummary()
        setMsg({ type: 'success', text: 'Weekly summary sent to your email!' })
      } else {
        const r = await checkDueDates()
        setMsg({ type: 'success', text: `Checked ${r.data.checked} bills. Sent ${r.data.reminders_sent} reminder(s).` })
      }
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Email service not configured.' })
    } finally { setSending(null) }
  }

  if (loading) return <Spinner />

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">Alerts & Budget</h1>
        <p className="text-textSub text-sm mt-1">Set limits, track goals and manage email notifications</p>
      </div>

      {msg && (
        <div className={`rounded-xl p-3 text-sm flex items-center gap-2 border
          ${msg.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
          {msg.type === 'success' ? '✓' : '⚠'} {msg.text}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Budget limits */}
        <div className="card space-y-4">
          <div className="sec-head">Budget Limits</div>
          <form onSubmit={handleSaveBudget} className="space-y-3">
            <div>
              <label className="text-xs text-muted mb-1.5 block">Monthly spend limit (£)</label>
              <input
                type="number" step="0.01" placeholder="e.g. 150" className="field-input"
                value={budget.budget_monthly_gbp || ''}
                onChange={e => setBudgetData({ ...budget, budget_monthly_gbp: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs text-muted mb-1.5 block">Monthly usage limit (kWh)</label>
              <input
                type="number" placeholder="e.g. 350" className="field-input"
                value={budget.budget_monthly_kwh || ''}
                onChange={e => setBudgetData({ ...budget, budget_monthly_kwh: e.target.value })}
              />
            </div>
            <div className="flex items-center gap-3">
              <input
                type="checkbox" id="email_alerts" className="accent-teal w-4 h-4"
                checked={budget.email_alerts}
                onChange={e => setBudgetData({ ...budget, email_alerts: e.target.checked })}
              />
              <label htmlFor="email_alerts" className="text-sm text-textSub cursor-pointer">
                Enable email alerts (spike detection, reminders)
              </label>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={saving}>
              {saving ? 'Saving…' : '💾 Save Budget'}
            </button>
          </form>

          {/* Current status */}
          {status && (status.budget_monthly_gbp || status.budget_monthly_kwh) && (
            <div className="pt-3 border-t border-border space-y-3">
              <div className="sec-head">Current Status</div>
              {status.budget_monthly_gbp && (
                <div>
                  <div className="flex justify-between text-xs text-textSub mb-0.5">
                    <span>Spend</span>
                    <span>£{status.latest_cost?.toFixed(2) || '—'} / £{status.budget_monthly_gbp.toFixed(2)}</span>
                  </div>
                  <ProgressBar pct={status.cost_pct} status={status.cost_status} />
                </div>
              )}
              {status.budget_monthly_kwh && (
                <div>
                  <div className="flex justify-between text-xs text-textSub mb-0.5">
                    <span>Usage</span>
                    <span>{status.latest_kwh || '—'} / {status.budget_monthly_kwh} kWh</span>
                  </div>
                  <ProgressBar pct={status.kwh_pct} status={status.kwh_status} />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Usage Goal */}
          <div className="card">
            <div className="sec-head mb-3">Usage Reduction Goal</div>
            <form onSubmit={handleSaveGoal} className="space-y-3">
              <div>
                <label className="text-xs text-muted mb-1.5 block">Reduction target (%)</label>
                <input
                  type="number" step="0.5" min="1" max="100" placeholder="e.g. 15"
                  className="field-input"
                  value={goal.goal_reduction_pct}
                  onChange={e => setGoalData({ ...goal, goal_reduction_pct: e.target.value })}
                  required
                />
              </div>
              <button type="submit" className="btn-primary w-full" disabled={savingGoal}>
                {savingGoal ? 'Saving…' : '🎯 Set Goal'}
              </button>
            </form>
          </div>

          {/* Email actions */}
          <div className="card">
            <div className="sec-head mb-3">Email Actions</div>
            {!budget.email_alerts && (
              <div className="bg-yellow-500/10 border border-yellow-500/25 rounded-lg p-3 text-xs text-yellow-400 mb-3">
                Enable email alerts above to use these features.
              </div>
            )}
            <div className="space-y-2">
              <button
                className="btn-secondary w-full text-sm py-2.5"
                onClick={() => handleEmail('summary')}
                disabled={!budget.email_alerts || sending === 'summary'}
              >
                {sending === 'summary' ? '⏳ Sending…' : '📧 Send Weekly Summary Now'}
              </button>
              <button
                className="btn-secondary w-full text-sm py-2.5"
                onClick={() => handleEmail('dues')}
                disabled={!budget.email_alerts || sending === 'dues'}
              >
                {sending === 'dues' ? '⏳ Checking…' : '🔔 Check Due Date Reminders'}
              </button>
            </div>
          </div>

          {/* Upcoming dues */}
          {upcoming.length > 0 && (
            <div className="card">
              <div className="sec-head mb-3">Upcoming Payments</div>
              <div className="space-y-2">
                {upcoming.map((u) => (
                  <div key={u.bill_id} className="flex items-center justify-between text-sm bg-[#0A1018] border border-border rounded-lg px-3 py-2">
                    <div>
                      <div className="text-text font-medium">{u.provider}</div>
                      <div className="text-xs text-muted">Due: {u.due_date}</div>
                    </div>
                    <div className={`text-right font-semibold ${u.days_left <= 1 ? 'text-red-400' : u.days_left <= 3 ? 'text-yellow-400' : 'text-blue-400'}`}>
                      £{u.amount_due?.toFixed(2)}<br />
                      <span className="text-xs font-normal">{u.days_left === 0 ? 'Today' : u.days_left === 1 ? 'Tomorrow' : `${u.days_left} days`}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
