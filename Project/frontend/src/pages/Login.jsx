import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PublicLayout } from '../components/Layout'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(email, password)
      if (user.role === 'admin') navigate('/admin')
      else if (user.role === 'print_center') navigate('/print-center')
      else navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PublicLayout>
      <form onSubmit={handleSubmit} className="card">
        <h2 className="text-2xl font-bold mb-6">Sign In</h2>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        <div className="mb-4">
          <label className="label">Email</label>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="mb-6">
          <label className="label">Password</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
        <p className="text-center text-sm text-slate-500 mt-4">
          <Link to="/forgot-password" className="text-brand-600">Forgot password?</Link>
        </p>
        <p className="text-center text-sm text-slate-500 mt-2">
          No account? <Link to="/register" className="text-brand-600 font-medium">Register</Link>
        </p>
        <div className="mt-6 p-3 bg-slate-50 rounded-lg text-xs text-slate-500">
          Demo: student@demo.com / student123<br />
          Operator: operator@smartprintx.com / operator123<br />
          Admin: admin@smartprintx.com / admin12345
        </div>
      </form>
    </PublicLayout>
  )
}
