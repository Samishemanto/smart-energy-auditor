import { useEffect, useState } from 'react'
import { getBills, deleteBill, exportCsv } from '../api'
import Spinner from '../components/Spinner'
import { MdDelete, MdExpandMore, MdExpandLess, MdDownload } from 'react-icons/md'

function BillRow({ bill, onDelete }) {
  const [open, setOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
    if (!window.confirm(`Delete bill #${bill.id} from ${bill.provider}?`)) return
    setDeleting(true)
    try { await deleteBill(bill.id); onDelete(bill.id) } catch { setDeleting(false) }
  }

  return (
    <div className="card-sm mb-2">
      <div className="flex items-center gap-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
          <span className="font-semibold text-text">{bill.provider}</span>
          <span className="text-textSub">{bill.bill_date || 'No date'}</span>
          <span className="text-text">{bill.amount_due != null ? `£${bill.amount_due.toFixed(2)}` : 'N/A'}</span>
          <span className="text-textSub">{bill.usage_kwh != null ? `${bill.usage_kwh} kWh` : 'N/A'}</span>
        </div>
        <button onClick={(e) => { e.stopPropagation(); handleDelete() }} disabled={deleting}
          className="text-muted hover:text-red-400 transition-colors p-1 flex-shrink-0">
          <MdDelete size={16} />
        </button>
        <span className="text-muted flex-shrink-0">
          {open ? <MdExpandLess size={18} /> : <MdExpandMore size={18} />}
        </span>
      </div>

      {open && (
        <div className="mt-3 pt-3 border-t border-border grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[
            { label: 'Due Date', value: bill.due_date || 'N/A' },
            { label: 'Unit Rate', value: bill.unit_rate != null ? `${bill.unit_rate}p/kWh` : 'N/A' },
            { label: 'Standing Charge', value: bill.standing_charge != null ? `${bill.standing_charge}p/day` : 'N/A' },
            { label: 'Tariff', value: bill.tariff_name || 'N/A' },
            { label: 'Account No.', value: bill.account_number || 'N/A' },
            { label: 'CO₂', value: bill.carbon_kg != null ? `${bill.carbon_kg} kg` : 'N/A' },
          ].map(({ label, value }) => (
            <div key={label} className="bg-[#0A1018] border border-border rounded-lg p-2.5">
              <div className="text-[0.62rem] text-muted uppercase tracking-wider mb-0.5">{label}</div>
              <div className="text-xs font-medium text-text">{value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ComparePanel({ bills }) {
  const [a, setA] = useState('')
  const [b, setB] = useState('')

  const ba = bills.find(x => x.id === parseInt(a))
  const bb = bills.find(x => x.id === parseInt(b))

  const diff = (va, vb) => {
    if (va == null || vb == null) return null
    const pct = ((va - vb) / vb * 100).toFixed(1)
    return { pct, color: parseFloat(pct) > 0 ? 'text-red-400' : 'text-emerald-400' }
  }

  const fieldLabel = (label, va, vb, unit = '', invert = false) => {
    const d = diff(va, vb)
    return (
      <div className="bg-[#0A1018] border border-border rounded-xl p-3">
        <div className="text-[0.62rem] text-muted uppercase tracking-wider mb-2">{label}</div>
        <div className="flex items-end gap-2">
          <span className="font-semibold text-text">{va != null ? `${unit}${typeof va === 'number' ? va.toFixed(2) : va}` : 'N/A'}</span>
          {d && <span className={`text-xs font-medium ${invert ? (parseFloat(d.pct) > 0 ? 'text-emerald-400' : 'text-red-400') : d.color}`}>
            {parseFloat(d.pct) > 0 ? '+' : ''}{d.pct}%
          </span>}
        </div>
        <div className="text-xs text-muted mt-0.5">{vb != null ? `${unit}${typeof vb === 'number' ? vb.toFixed(2) : vb}` : 'N/A'}</div>
      </div>
    )
  }

  const opts = bills.map(b => (
    <option key={b.id} value={b.id}>
      #{b.id} · {b.provider} · {b.bill_date || 'No date'} {b.amount_due ? `· £${b.amount_due.toFixed(2)}` : ''}
    </option>
  ))

  return (
    <div className="card space-y-4 mb-4">
      <div className="sec-head">⚖️ Compare Bills</div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-muted mb-1.5 block">Bill A (current)</label>
          <select className="field-input" value={a} onChange={e => setA(e.target.value)}>
            <option value="">Select bill…</option>{opts}
          </select>
        </div>
        <div>
          <label className="text-xs text-muted mb-1.5 block">Bill B (compare to)</label>
          <select className="field-input" value={b} onChange={e => setB(e.target.value)}>
            <option value="">Select bill…</option>{opts}
          </select>
        </div>
      </div>
      {ba && bb && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {fieldLabel('Amount Due', ba.amount_due, bb.amount_due, '£')}
          {fieldLabel('Usage (kWh)', ba.usage_kwh, bb.usage_kwh, '', true)}
          {fieldLabel('Unit Rate (p)', ba.unit_rate, bb.unit_rate)}
          {fieldLabel('Standing Charge (p)', ba.standing_charge, bb.standing_charge)}
          {fieldLabel('CO₂ (kg)', ba.carbon_kg, bb.carbon_kg, '', true)}
        </div>
      )}
    </div>
  )
}

export default function History() {
  const [bills, setBills] = useState([])
  const [loading, setLoading] = useState(true)
  const [compare, setCompare] = useState(false)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    getBills().then(r => setBills(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleExport = async () => {
    setExporting(true)
    try {
      const r = await exportCsv()
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const a = document.createElement('a')
      a.href = url; a.download = 'energy_bills.csv'; a.click()
      window.URL.revokeObjectURL(url)
    } catch {} finally { setExporting(false) }
  }

  if (loading) return <Spinner />

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-text">Bill History</h1>
          <p className="text-textSub text-sm mt-1">{bills.length} bill{bills.length !== 1 ? 's' : ''} uploaded</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary text-sm py-2" onClick={() => setCompare(!compare)}>
            ⚖️ Compare
          </button>
          <button className="btn-secondary text-sm py-2 flex items-center gap-2" onClick={handleExport} disabled={exporting || bills.length === 0}>
            <MdDownload size={16} /> {exporting ? 'Exporting…' : 'Export CSV'}
          </button>
        </div>
      </div>

      {compare && bills.length >= 2 && <ComparePanel bills={bills} />}

      {bills.length === 0 ? (
        <div className="info-box py-12">
          No bills yet. Go to <strong>Upload Bill</strong> to get started.
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[0.65rem] text-muted uppercase tracking-wider px-1 mb-1">
            <span>Provider</span><span>Date</span><span>Amount</span><span>Usage</span>
          </div>
          {bills.map(b => (
            <BillRow key={b.id} bill={b} onDelete={(id) => setBills(prev => prev.filter(x => x.id !== id))} />
          ))}
        </div>
      )}
    </div>
  )
}
