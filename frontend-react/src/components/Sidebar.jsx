import { NavLink, useNavigate } from 'react-router-dom'
import {
  MdDashboard, MdCloudUpload, MdHistory, MdInsights,
  MdNotifications, MdPerson, MdSettings, MdAdminPanelSettings,
  MdLogout, MdMenu, MdClose,
} from 'react-icons/md'
import { useState } from 'react'

const NAV = [
  { to: '/dashboard',  label: 'Dashboard',   Icon: MdDashboard },
  { to: '/upload',     label: 'Upload Bill',  Icon: MdCloudUpload },
  { to: '/history',    label: 'History',      Icon: MdHistory },
  { to: '/insights',   label: 'Insights',     Icon: MdInsights },
  { to: '/alerts',     label: 'Alerts',       Icon: MdNotifications },
  { to: '/profile',    label: 'Profile',      Icon: MdPerson },
  { to: '/settings',   label: 'Settings',     Icon: MdSettings },
]

export default function Sidebar({ user }) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(true)

  const navItems = user?.is_admin
    ? [...NAV, { to: '/admin', label: 'Admin', Icon: MdAdminPanelSettings }]
    : NAV

  const handleSignOut = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="fixed top-3 left-3 z-50 lg:hidden bg-surface border border-border rounded-xl p-2 text-textSub hover:text-teal"
        onClick={() => setOpen(!open)}
      >
        {open ? <MdClose size={20} /> : <MdMenu size={20} />}
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full z-40 flex flex-col
          bg-[#080D1A] border-r border-border
          transition-transform duration-200
          w-56
          ${open ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:flex
        `}
      >
        {/* Logo */}
        <div className="px-5 pt-6 pb-5 text-center border-b border-border">
          <div className="text-3xl leading-none mb-1.5">⚡</div>
          <div className="text-sm font-bold text-text tracking-tight">Smart Energy</div>
          <div className="text-[0.65rem] text-muted tracking-widest uppercase mt-0.5">Auditor</div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors
                 ${isActive
                   ? 'bg-teal/10 text-teal font-semibold'
                   : 'text-subtle hover:text-textSub hover:bg-surface'
                 }`
              }
            >
              <Icon size={17} className="flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User block + sign out */}
        <div className="px-3 pb-5 border-t border-border pt-4 space-y-3">
          {user && (
            <div className="bg-[#0A1220] border border-border rounded-xl px-3 py-2.5">
              <div className="text-xs font-semibold text-textSub truncate">
                {user.name || user.email}
              </div>
              <div className="text-[0.68rem] text-muted truncate mt-0.5">{user.email}</div>
            </div>
          )}
          <button
            onClick={handleSignOut}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-subtle hover:text-red-400 hover:bg-red-500/5 transition-colors"
          >
            <MdLogout size={16} />
            Sign out
          </button>
        </div>
      </aside>
    </>
  )
}
