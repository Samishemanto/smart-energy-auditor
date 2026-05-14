import { useEffect, useState } from 'react'
import { adminStats, adminUsers, adminBills, adminDeleteUser, adminDeleteBill } from '../api'
import KpiCard from '../components/KpiCard'
import Spinner from '../components/Spinner'
import { MdDelete, MdExpandMore, MdExpandLess } from 'react-icons/md'

function ExpandRow({ title, children }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card-sm mb-2">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="text-sm text-textSub">{title}</div>
        {open ? <MdExpandLess size={18} className="text-muted" /> : <MdExpandMore size={18} className="text-muted" />}
      </div>
      {open && <div className="mt-3 pt-3 border-t border-border">{children}</div>}
    </div>
  )
}

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [bills, setBills] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState(null)

  useEffect(() => {
    Promise.all([adminStats(), adminUsers(), adminBills()])
      .then(([s, u, b]) => { setStats(s.data); setUsers(u.data); setBills(b.data) })
      .catch(() => setMsg({ type: 'error', text: 'Access denied.' }))
      .finally(() => setLoading(false))
  }, [])

  const handleDeleteUser = async (id) => {
    if (!window.confirm('Delete this user and all their bills?')) return
    try {
      await adminDeleteUser(id)
      setUsers(prev => prev.filter(u => u.id !== id))
      setMsg({ type: 'success', text: `User #${id} deleted.` })
    } catch (e) {
      setMsg({ type: 'error', text: e.response?.data?.detail || 'Delete failed.' })
    }
  }

  const handleDeleteBill = async (id) => {
    if (!window.confirm(`Delete bill #${id}?`)) return
    try {
      await adminDeleteBill(id)
      setBills(prev => prev.filter(b => b.id !== id))
      setMsg({ type: 'success', text: `Bill #${id} deleted.` })
    } catch (e) {
      setMsg({ type: 'error', text: e.response?.data?.detail || 'Delete failed.' })
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">Admin Control Panel</h1>
        <p className="text-textSub text-sm mt-1">System-wide overview — visible only to admins</p>
      </div>

      {msg && (
        <div className={`rounded-xl p-3 text-sm border
          ${msg.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
          {msg.text}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard icon="👥" label="Total Users" value={stats.total_users} />
          <KpiCard icon="📄" label="Total Bills" value={stats.total_bills} />
          <KpiCard icon="💷" label="Total Spend" value={`£${(stats.total_spend || 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}`} />
          <KpiCard icon="🌿" label="Total CO₂" value={`${stats.total_carbon_kg} kg`} valueColor="text-emerald-400" />
        </div>
      )}

      {/* Users */}
      <div>
        <div className="sec-head mb-3">All Users ({users.length})</div>
        {users.length === 0 && <div className="info-box">No users found.</div>}
        {users.map(u => (
          <ExpandRow
            key={u.id}
            title={
              <span>
                <span className="font-semibold text-text">#{u.id} · {u.name || u.email}</span>
                {u.is_admin && <span className="text-[0.65rem] font-bold text-red-400 ml-2 uppercase">Admin</span>}
                <span className="text-muted ml-2">· {u.bill_count} bill(s) · Joined {u.created_at?.slice(0, 10) || 'N/A'}</span>
              </span>
            }
          >
            <div className="flex items-start justify-between">
              <div className="text-sm space-y-1 text-textSub">
                <div><span className="text-text font-medium">Email:</span> {u.email}</div>
                <div><span className="text-text font-medium">Name:</span> {u.name || 'N/A'}</div>
                <div><span className="text-text font-medium">Admin:</span> {u.is_admin ? 'Yes' : 'No'}</div>
                <div><span className="text-text font-medium">Bills:</span> {u.bill_count}</div>
              </div>
              {!u.is_admin && (
                <button className="btn-danger text-xs py-1.5 px-3 flex items-center gap-1" onClick={() => handleDeleteUser(u.id)}>
                  <MdDelete size={13} /> Delete
                </button>
              )}
            </div>
          </ExpandRow>
        ))}
      </div>

      {/* Bills */}
      <div>
        <div className="sec-head mb-3">All Bills ({bills.length})</div>
        {bills.length === 0 && <div className="info-box">No bills in the system.</div>}
        {bills.map(b => (
          <ExpandRow
            key={b.id}
            title={
              <span>
                <span className="font-semibold text-text">#{b.id} · {b.provider}</span>
                <span className="text-muted ml-2">
                  · {b.amount_due != null ? `£${b.amount_due.toFixed(2)}` : 'N/A'}
                  · {b.user_email}
                </span>
              </span>
            }
          >
            <div className="flex items-start justify-between">
              <div className="text-sm space-y-1 text-textSub">
                <div><span className="text-text font-medium">Provider:</span> {b.provider}</div>
                <div><span className="text-text font-medium">Amount:</span> {b.amount_due != null ? `£${b.amount_due.toFixed(2)}` : 'N/A'}</div>
                <div><span className="text-text font-medium">Usage:</span> {b.usage_kwh != null ? `${b.usage_kwh} kWh` : 'N/A'}</div>
                <div><span className="text-text font-medium">CO₂:</span> {b.carbon_kg != null ? `${b.carbon_kg} kg` : 'N/A'}</div>
                <div><span className="text-text font-medium">Owner:</span> {b.user_email}</div>
              </div>
              <button className="btn-danger text-xs py-1.5 px-3 flex items-center gap-1" onClick={() => handleDeleteBill(b.id)}>
                <MdDelete size={13} /> Delete
              </button>
            </div>
          </ExpandRow>
        ))}
      </div>
    </div>
  )
}
