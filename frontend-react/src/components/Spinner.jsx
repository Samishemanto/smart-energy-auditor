export default function Spinner({ className = '' }) {
  return (
    <div className={`flex items-center justify-center py-12 ${className}`}>
      <div className="w-8 h-8 border-2 border-border border-t-teal rounded-full animate-spin" />
    </div>
  )
}
