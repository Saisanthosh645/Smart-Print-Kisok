import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PublicLayout } from '../components/Layout'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <PublicLayout>
        <div className="card text-center">
          <h2 className="text-2xl font-bold mb-4">Check your email</h2>
          <p className="text-slate-600 mb-6">We sent a verification link. Check server logs in dev mode for the token.</p>
          <Link to="/login" className="btn-primary inline-block">Go to Login</Link>
        </div>
      </PublicLayout>
    )
  }

  return (
    <PublicLayout>
      <form onSubmit={handleSubmit} className="card">
        <h2 className="text-2xl font-bold mb-6">Create Account</h2>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        <div className="mb-4">
          <label className="label">Full Name</label>
          <input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        </div>
        <div className="mb-4">
          <label className="label">Email</label>
          <input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </div>
        <div className="mb-6">
          <label className="label">Password</label>
          <input className="input" type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? 'Creating...' : 'Register'}
        </button>
        <p className="text-center text-sm text-slate-500 mt-4">
          Already have an account? <Link to="/login" className="text-brand-600 font-medium">Sign In</Link>
        </p>
      </form>
    </PublicLayout>
  )
}
