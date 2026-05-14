import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getStats, updateName, deleteAccount } from '../api'
import Spinner from '../components/Spinner'

export default function Profile({ user, onNameUpdate }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState(user?.name || '')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirm, setConfirm] = useState('')
  const [msg, setMsg] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    setName(user?.name || '')
    getStats().then(r => setStats(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [user])

  const handleSaveName = async (e) => {
    e.preventDefault(); setSaving(true); setMsg(null)
    try {
      await updateName(name)
      onNameUpdate?.(name)
      setMsg({ type: 'success', text: 'Display name updated!' })
    } catch {
      setMsg({ type: 'error', text: 'Could not update name.' })
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    if (confirm !== 'DELETE') { setMsg({ type: 'error', text: 'Type DELETE to confirm.' }); return }
    setDeleting(true)
    try {
      await deleteAccount()
      localStorage.removeItem('token')
      navigate('/')
    } catch {
      setMsg({ type: 'error', text: 'Could not delete account.' })
      setDeleting(false)
    }
  }

  if (loading) return <Spinner />

  const avatar = (user?.name || user?.email || 'U')[0].toUpperCase()
  const providers = stats?.providers || {}
  const total = stats?.total_bills || 0

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">My Profile</h1>
        <p className="text-textSub text-sm mt-1">Manage your account and view personal stats</p>
      </div>

      {msg && (
        <div className={`rounded-xl p-3 text-sm border
          ${msg.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
          {msg.text}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Account card */}
        <div className="card space-y-5">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-teal to-blue flex items-center justify-center text-2xl font-extrabold text-white flex-shrink-0">
              {avatar}
            </div>
            <div>
              <div className="font-semibold text-text">{user?.name || 'No name set'}</div>
              <div className="text-sm text-muted">{user?.email}</div>
              <span className={`text-[0.68rem] font-semibold px-2.5 py-0.5 rounded-full border mt-1.5 inline-block
                ${user?.is_admin ? 'bg-blue/10 border-blue/30 text-blue-400' : 'bg-teal/10 border-teal/25 text-teal'}`}>
                {user?.is_admin ? 'Admin' : 'Standard user'}
              </span>
            </div>
          </div>

          <form onSubmit={handleSaveName} className="space-y-3">
            <div className="sec-head">Edit Display Name</div>
            <input
              className="field-input"
              placeholder="Your name"
              value={name}
              onChange={e => setName(e.target.value)}
              required
            />
            <button type="submit" className="btn-primary w-full" disabled={saving}>
              {saving ? 'Saving…' : '💾 Save Name'}
            </button>
          </form>
        </div>

        {/* Stats */}
        <div className="space-y-4">
          <div className="card">
            <div className="sec-head mb-3">Your Stats</div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { icon: '📄', label: 'Bills Uploaded', value: total },
                { icon: '💷', label: 'Total Spend', value: `£${(stats?.total_spend || 0).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
                { icon: '⚡', label: 'Avg kWh/bill', value: (stats?.avg_monthly_kwh || 0).toFixed(0) },
                { icon: '🌿', label: 'Total CO₂', value: `${(stats?.total_carbon_kg || 0).toFixed(0)} kg` },
              ].map(({ icon, label, value }) => (
                <div key={label} className="bg-[#0A1018] border border-border rounded-xl p-3">
                  <div className="text-lg mb-1">{icon}</div>
                  <div className="text-[0.65rem] text-muted uppercase tracking-wider mb-0.5">{label}</div>
                  <div className="font-extrabold text-text">{value}</div>
                </div>
              ))}
            </div>
          </div>

          {Object.keys(providers).length > 0 && (
            <div className="card">
              <div className="sec-head mb-3">Providers Used</div>
              <div className="space-y-2">
                {Object.entries(providers).sort((a, b) => b[1] - a[1]).map(([prov, cnt]) => (
                  <div key={prov}>
                    <div className="flex justify-between text-xs text-textSub mb-1">
                      <span>{prov}</span><span>{cnt} bill{cnt !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="bg-[#0A1018] rounded-full h-1.5 overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-teal to-blue" style={{ width: `${(cnt / total) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Danger zone */}
      <div className="card border-red-500/20">
        <div className="text-xs font-bold uppercase tracking-widest text-red-400 mb-3">Danger Zone</div>
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4 mb-4 text-sm text-red-400">
          ⚠ Permanently deletes your account and all bills. This cannot be undone.
        </div>
        <div className="flex gap-3 items-center">
          <input
            className="field-input flex-1 border-red-500/20 focus:border-red-500/50"
            placeholder="Type DELETE to confirm"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
          />
          <button
            className="btn-danger flex-shrink-0"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? 'Deleting…' : '🗑 Delete Account'}
          </button>
        </div>
      </div>
    </div>
  )
}
