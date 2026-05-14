import { useState } from 'react'
import { downloadPdf } from '../api'

export default function Settings() {
  const [downloading, setDownloading] = useState(false)
  const [msg, setMsg] = useState(null)

  const handlePdf = async () => {
    setDownloading(true); setMsg(null)
    try {
      const r = await downloadPdf()
      const url = window.URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url; a.download = 'energy_report.pdf'; a.click()
      window.URL.revokeObjectURL(url)
      setMsg({ type: 'success', text: 'PDF report downloaded!' })
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Could not generate report.' })
    } finally { setDownloading(false) }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-text">Settings</h1>
        <p className="text-textSub text-sm mt-1">Configure your Smart Energy Auditor</p>
      </div>

      {msg && (
        <div className={`rounded-xl p-3 text-sm border
          ${msg.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
          {msg.text}
        </div>
      )}

      {/* Reports */}
      <div className="card space-y-3">
        <div className="sec-head">Reports</div>
        <p className="text-sm text-textSub">Download a branded PDF report with all your stats, charts and savings tips.</p>
        <button onClick={handlePdf} className="btn-primary" disabled={downloading}>
          {downloading ? '⏳ Generating…' : '📄 Download PDF Report'}
        </button>
      </div>

      {/* About */}
      <div className="card space-y-2">
        <div className="sec-head">About</div>
        <div className="text-sm text-textSub space-y-1.5">
          <div><span className="text-text font-semibold">Smart Energy Auditor</span> v0.3.0</div>
          <div>Backend: FastAPI · SQLAlchemy · Tesseract OCR · pdf2image</div>
          <div>Frontend: React · Vite · Tailwind CSS · Plotly.js</div>
          <div>ML: Prophet · Gradient Boosting · KMeans · IsolationForest · Ruptures PELT</div>
          <div>Providers: British Gas · Scottish Power · Octopus · E.ON Next · OVO · EDF · nPower · Utilita · Shell</div>
          <div className="pt-1">Carbon: <span className="text-emerald-400 font-medium">0.197 kg CO₂/kWh</span> (UK National Grid 2024)</div>
        </div>
      </div>
    </div>
  )
}
