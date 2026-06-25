import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LogOut, Printer } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navByRole = {
  student: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/upload', label: 'Upload' },
    { to: '/jobs', label: 'My Jobs' },
  ],
  print_center: [
    { to: '/print-center', label: 'Incoming Orders' },
    { to: '/print-center/queue', label: 'Priority Queue' },
  ],
  admin: [
    { to: '/admin', label: 'Analytics' },
    { to: '/admin/users', label: 'Users' },
    { to: '/admin/printers', label: 'Printers' },
    { to: '/print-center', label: 'Print Center' },
  ],
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const links = navByRole[user?.role] || navByRole.student

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-brand-900 text-white flex flex-col">
        <div className="p-6 flex items-center gap-3 border-b border-brand-700">
          <Printer className="w-8 h-8" />
          <div>
            <h1 className="font-bold text-lg">SmartPrintX</h1>
            <p className="text-xs text-brand-100">Campus Printing</p>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `block px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive ? 'bg-brand-600 text-white' : 'text-brand-100 hover:bg-brand-800'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-brand-700">
          <p className="text-sm text-brand-100 truncate">{user?.full_name}</p>
          <p className="text-xs text-brand-200 truncate">{user?.email}</p>
          <button
            onClick={handleLogout}
            className="mt-3 flex items-center gap-2 text-sm text-brand-100 hover:text-white"
          >
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

export function PublicLayout({ children }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2 text-white mb-8">
          <Printer className="w-10 h-10" />
          <span className="text-2xl font-bold">SmartPrintX</span>
        </Link>
        {children}
      </div>
    </div>
  )
}
