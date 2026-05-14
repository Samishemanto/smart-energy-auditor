export default function KpiCard({ icon, label, value, sub, valueColor }) {
  return (
    <div className="kpi-card">
      <div className="text-xl mb-2">{icon}</div>
      <div className="text-[0.68rem] font-bold uppercase tracking-widest text-muted mb-1.5">{label}</div>
      <div className={`text-2xl font-extrabold leading-none mb-1.5 ${valueColor || 'text-text'}`}>
        {value}
      </div>
      {sub && <div className="text-xs text-muted mt-auto">{sub}</div>}
    </div>
  )
}
