import { useEffect, useState } from 'react'
import { getAuthUrl } from '../api'

const GOOGLE_ICON = (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
    <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.859-3.048.859-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
    <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
  </svg>
)

const FEATURES = [
  { icon: '⚡', title: 'Instant OCR Extraction', desc: 'Upload PDF, JPG or PNG — AI reads kWh, rates, dates and costs in seconds.' },
  { icon: '📊', title: 'ML-Powered Forecasting', desc: 'Prophet + Gradient Boosting predict next month\'s usage and cost before the bill arrives.' },
  { icon: '🔔', title: 'Smart Alerts', desc: 'Spike detection, due-date reminders and weekly summaries sent straight to your inbox.' },
  { icon: '🌿', title: 'Carbon Tracking', desc: 'Every bill auto-calculates CO₂ using the UK National Grid factor (0.197 kg/kWh).' },
  { icon: '🎯', title: 'Usage Goals', desc: 'Set a reduction target — the app tracks your progress bill by bill.' },
  { icon: '📄', title: 'PDF Reports', desc: 'One-click branded report with all your stats, charts and savings tips.' },
]

const STEPS = [
  { n: '1', color: 'from-teal to-cyan-500', title: 'Upload your bill', sub: 'PDF, JPG or PNG from any UK provider' },
  { n: '2', color: 'from-blue to-violet-600', title: 'AI extracts the data', sub: 'OCR + smart parsers pull kWh, cost, rates & dates' },
  { n: '3', color: 'from-emerald-500 to-green-600', title: 'Get ML insights', sub: 'Forecasts, anomalies, carbon & personalised tips' },
]

export default function Landing() {
  const [authUrl, setAuthUrl] = useState(null)
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    getAuthUrl()
      .then((r) => setAuthUrl(r.data.url))
      .catch(() => setOffline(true))
  }, [])

  return (
    <div className="min-h-screen bg-bg text-text">
      {/* Animated background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-1/4 -left-1/4 w-1/2 h-1/2 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(0,201,184,0.06) 0%, transparent 70%)', animation: 'pulse 6s ease-in-out infinite' }} />
        <div className="absolute -bottom-1/4 -right-1/4 w-1/2 h-1/2 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(29,78,216,0.06) 0%, transparent 70%)', animation: 'pulse 8s ease-in-out 2s infinite' }} />
        <div className="absolute inset-0 opacity-30"
          style={{ backgroundImage: 'radial-gradient(circle, #1A2840 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:.5;transform:scale(1)} 50%{opacity:.8;transform:scale(1.04)} }`}</style>

      {/* ── HERO ────────────────────────────────────────────────────── */}
      <div className="relative z-10 max-w-6xl mx-auto px-6 pt-20 pb-8 text-center">
        <div className="inline-flex items-center gap-2 bg-teal/10 border border-teal/25 text-teal text-xs font-bold tracking-widest uppercase px-4 py-1.5 rounded-full mb-6">
          ⚡ AI-Powered · UK Energy · Free
        </div>
        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-5 leading-tight">
          Stop overpaying<br />
          <span className="text-teal">for energy.</span>
        </h1>
        <p className="text-textSub text-lg max-w-xl mx-auto mb-10 leading-relaxed">
          Upload your UK electricity or gas bills. AI extracts the data, ML models predict your next bill,
          and personalised tips show you exactly how to cut costs.
        </p>

        {offline ? (
          <div className="inline-block bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-6 py-3 rounded-xl">
            ⚠ Backend offline — start the FastAPI server first.
          </div>
        ) : authUrl ? (
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <a
              href={authUrl}
              className="flex items-center gap-3 bg-white text-gray-900 font-semibold px-6 py-3 rounded-xl text-sm shadow-lg hover:shadow-xl transition-shadow"
            >
              {GOOGLE_ICON} Sign in with Google
            </a>
            <a
              href={authUrl}
              className="flex items-center gap-3 bg-teal/10 border border-teal/30 text-text font-semibold px-6 py-3 rounded-xl text-sm hover:bg-teal/15 transition-colors"
            >
              {GOOGLE_ICON} Create free account
            </a>
          </div>
        ) : (
          <div className="w-8 h-8 border-2 border-border border-t-teal rounded-full animate-spin mx-auto" />
        )}

        <p className="text-muted text-xs mt-4">Free forever · No credit card · UK bills only</p>
      </div>

      {/* ── STATS BAR ───────────────────────────────────────────────── */}
      <div className="relative z-10 max-w-3xl mx-auto px-6 mb-16">
        <div className="grid grid-cols-4 border border-border rounded-2xl overflow-hidden bg-surface">
          {[
            { val: '9', label: 'UK Providers' },
            { val: '5+', label: 'ML Models' },
            { val: '71', label: 'Tests Passing' },
            { val: 'Free', label: 'Always', color: 'text-teal' },
          ].map(({ val, label, color }, i) => (
            <div key={i} className={`py-4 text-center ${i < 3 ? 'border-r border-border' : ''}`}>
              <div className={`text-xl font-extrabold ${color || 'text-text'}`}>{val}</div>
              <div className="text-[0.65rem] text-muted mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── HOW IT WORKS ────────────────────────────────────────────── */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 mb-20">
        <div className="text-center mb-10">
          <div className="sec-head mb-2">How it works</div>
          <h2 className="text-2xl font-extrabold text-text">Three steps to energy clarity</h2>
        </div>
        <div className="grid sm:grid-cols-3 gap-5">
          {STEPS.map(({ n, color, title, sub }) => (
            <div key={n} className="card text-center">
              <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${color} flex items-center justify-center text-white font-extrabold text-sm mx-auto mb-4`}>
                {n}
              </div>
              <div className="font-semibold text-text mb-1.5">{title}</div>
              <div className="text-sm text-textSub leading-relaxed">{sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── FEATURES GRID ───────────────────────────────────────────── */}
      <div className="relative z-10 max-w-5xl mx-auto px-6 mb-20">
        <div className="text-center mb-10">
          <div className="sec-head mb-2">Features</div>
          <h2 className="text-2xl font-extrabold text-text">Everything you need to take control</h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map(({ icon, title, desc }) => (
            <div key={title} className="card hover:border-teal/40 transition-colors">
              <div className="text-2xl mb-3">{icon}</div>
              <div className="font-semibold text-text mb-1.5">{title}</div>
              <div className="text-sm text-textSub leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── CTA FOOTER ──────────────────────────────────────────────── */}
      <div className="relative z-10 max-w-2xl mx-auto px-6 pb-20 text-center">
        <div className="card border-teal/20">
          <div className="text-3xl mb-4">⚡</div>
          <h2 className="text-xl font-extrabold text-text mb-2">Ready to start saving?</h2>
          <p className="text-textSub text-sm mb-6 leading-relaxed">
            Join and upload your first bill in under 60 seconds. 100% free, always.
          </p>
          {authUrl && (
            <a
              href={authUrl}
              className="inline-flex items-center gap-3 btn-primary text-base px-8 py-3"
            >
              {GOOGLE_ICON} Get started free
            </a>
          )}
        </div>
        <p className="text-muted text-xs mt-6">
          Smart Energy Auditor · Built with FastAPI, React, Prophet & ❤
        </p>
      </div>
    </div>
  )
}
