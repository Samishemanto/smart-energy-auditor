import { useEffect, useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { getMe } from './api'

import Sidebar from './components/Sidebar'
import Spinner from './components/Spinner'

import Landing    from './pages/Landing'
import Dashboard  from './pages/Dashboard'
import Upload     from './pages/Upload'
import History    from './pages/History'
import Insights   from './pages/Insights'
import Alerts     from './pages/Alerts'
import Profile    from './pages/Profile'
import Settings   from './pages/Settings'
import Admin      from './pages/Admin'

function AppLayout({ user, onNameUpdate }) {
  return (
    <div className="flex min-h-screen w-full">
      <Sidebar user={user} />
      <main className="flex-1 min-w-0 overflow-y-auto">
        <Routes>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload"    element={<Upload />} />
          <Route path="history"   element={<History />} />
          <Route path="insights"  element={<Insights />} />
          <Route path="alerts"    element={<Alerts />} />
          <Route path="profile"   element={<Profile user={user} onNameUpdate={onNameUpdate} />} />
          <Route path="settings"  element={<Settings />} />
          {user?.is_admin && <Route path="admin" element={<Admin />} />}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)

  useEffect(() => {
    // Capture token from Google OAuth redirect: backend sends /?token=...
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    if (urlToken) {
      localStorage.setItem('token', urlToken)
      window.history.replaceState({}, '', '/')
    }

    const token = urlToken || localStorage.getItem('token')
    if (!token) { setAuthLoading(false); return }
    getMe()
      .then(r => setUser(r.data))
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setAuthLoading(false))
  }, [])

  const handleNameUpdate = useCallback((name) => {
    setUser(prev => ({ ...prev, name }))
  }, [])

  if (authLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="w-10 h-10 border-2 border-border border-t-teal rounded-full animate-spin" />
    </div>
  )

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Landing />} />
        <Route
          path="/*"
          element={
            user
              ? <AppLayout user={user} onNameUpdate={handleNameUpdate} />
              : <Navigate to="/" replace />
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
