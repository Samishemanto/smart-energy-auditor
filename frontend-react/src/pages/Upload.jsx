import { useState, useRef } from 'react'
import { uploadBill, createManual } from '../api'
import { MdCloudUpload, MdCheckCircle, MdError } from 'react-icons/md'

function Field({ label, ...props }) {
  return (
    <div>
      <label className="block text-xs font-medium text-muted mb-1.5">{label}</label>
      <input className="field-input" {...props} />
    </div>
  )
}

export default function Upload() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('file')
  const fileRef = useRef()

  const [manual, setManual] = useState({
    provider: '', bill_date: '', due_date: '', amount_due: '', usage_kwh: '',
    standing_charge: '', unit_rate: '', tariff_name: '', account_number: '', meter_serial: '',
  })

  const handleFile = async (file) => {
    if (!file) return
    setError(null); setResult(null); setUploading(true)
    try {
      const r = await uploadBill(file)
      setResult(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleManual = async (e) => {
    e.preventDefault()
    setError(null); setResult(null); setUploading(true)
    try {
      const payload = {
        ...manual,
        amount_due: manual.amount_due ? parseFloat(manual.amount_due) : null,
        usage_kwh:  manual.usage_kwh  ? parseInt(manual.usage_kwh) : null,
        standing_charge: manual.standing_charge ? parseFloat(manual.standing_charge) : null,
        unit_rate: manual.unit_rate ? parseFloat(manual.unit_rate) : null,
      }
      const r = await createManual(payload)
      setResult({ ...r.data, extracted_text: '' })
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save bill.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">Upload Bill</h1>
        <p className="text-textSub text-sm mt-1">Upload a PDF or image of your energy bill for AI analysis</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#0A1018] border border-border rounded-xl p-1 w-fit">
        {['file', 'manual'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${tab === t ? 'bg-surface text-teal border border-border' : 'text-muted hover:text-textSub'}`}
          >
            {t === 'file' ? '📎 Upload File' : '✏️ Manual Entry'}
          </button>
        ))}
      </div>

      {tab === 'file' ? (
        <div
          className={`card border-dashed border-2 text-center cursor-pointer transition-colors py-12
            ${dragging ? 'border-teal bg-teal/5' : 'border-border hover:border-teal/50'}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            className="hidden"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          <MdCloudUpload size={48} className={`mx-auto mb-4 ${dragging ? 'text-teal' : 'text-muted'}`} />
          <div className="text-text font-semibold mb-1">
            {dragging ? 'Drop to upload' : 'Drag & drop or click to choose'}
          </div>
          <div className="text-textSub text-sm">PDF, JPG, PNG · Max 20 MB</div>
          <div className="flex flex-wrap gap-2 justify-center mt-4">
            {['British Gas', 'Octopus', 'Scottish Power', 'E.ON Next', 'OVO', 'EDF', 'nPower', 'Utilita', 'Shell'].map(p => (
              <span key={p} className="badge-teal text-[0.65rem]">{p}</span>
            ))}
          </div>
        </div>
      ) : (
        <form className="card space-y-4" onSubmit={handleManual}>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Provider *" placeholder="e.g. British Gas" value={manual.provider} onChange={e => setManual({ ...manual, provider: e.target.value })} required />
            <Field label="Bill Date" type="date" value={manual.bill_date} onChange={e => setManual({ ...manual, bill_date: e.target.value })} />
            <Field label="Due Date" type="date" value={manual.due_date} onChange={e => setManual({ ...manual, due_date: e.target.value })} />
            <Field label="Amount Due (£)" type="number" step="0.01" placeholder="0.00" value={manual.amount_due} onChange={e => setManual({ ...manual, amount_due: e.target.value })} />
            <Field label="Usage (kWh)" type="number" placeholder="0" value={manual.usage_kwh} onChange={e => setManual({ ...manual, usage_kwh: e.target.value })} />
            <Field label="Standing Charge (p/day)" type="number" step="0.01" placeholder="0.00" value={manual.standing_charge} onChange={e => setManual({ ...manual, standing_charge: e.target.value })} />
            <Field label="Unit Rate (p/kWh)" type="number" step="0.01" placeholder="0.00" value={manual.unit_rate} onChange={e => setManual({ ...manual, unit_rate: e.target.value })} />
            <Field label="Tariff Name" placeholder="e.g. Flexible Tariff" value={manual.tariff_name} onChange={e => setManual({ ...manual, tariff_name: e.target.value })} />
            <Field label="Account Number" placeholder="optional" value={manual.account_number} onChange={e => setManual({ ...manual, account_number: e.target.value })} />
            <Field label="Meter Serial" placeholder="optional" value={manual.meter_serial} onChange={e => setManual({ ...manual, meter_serial: e.target.value })} />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={uploading}>
            {uploading ? 'Saving…' : 'Save Bill'}
          </button>
        </form>
      )}

      {/* Loading */}
      {uploading && tab === 'file' && (
        <div className="card text-center py-8">
          <div className="w-10 h-10 border-2 border-border border-t-teal rounded-full animate-spin mx-auto mb-4" />
          <div className="text-textSub text-sm">Extracting data with OCR…</div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
          <MdError size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-red-400 font-semibold text-sm">Upload failed</div>
            <div className="text-red-400/80 text-xs mt-1">{error}</div>
          </div>
        </div>
      )}

      {/* Success */}
      {result && (
        <div className="card border-emerald-500/30 bg-emerald-500/5">
          <div className="flex items-center gap-3 mb-4">
            <MdCheckCircle size={22} className="text-emerald-400" />
            <div className="font-semibold text-emerald-400">Bill analysed successfully!</div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[
              { label: 'Provider', value: result.provider },
              { label: 'Bill Date', value: result.bill_date || 'N/A' },
              { label: 'Amount Due', value: result.amount_due != null ? `£${result.amount_due.toFixed(2)}` : 'N/A' },
              { label: 'Usage', value: result.usage_kwh != null ? `${result.usage_kwh} kWh` : 'N/A' },
              { label: 'Unit Rate', value: result.unit_rate != null ? `${result.unit_rate}p/kWh` : 'N/A' },
              { label: 'CO₂', value: result.carbon_kg != null ? `${result.carbon_kg} kg` : 'N/A' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-[#0A1018] border border-border rounded-xl p-3">
                <div className="text-[0.65rem] text-muted uppercase tracking-wider mb-1">{label}</div>
                <div className="text-sm font-semibold text-text">{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
