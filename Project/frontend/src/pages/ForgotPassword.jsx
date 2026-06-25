import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PublicLayout } from '../components/Layout'
import { auth } from '../api/client'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    await auth.forgotPassword(email)
    setSent(true)
  }

  return (
    <PublicLayout>
      <form onSubmit={handleSubmit} className="card">
        <h2 className="text-2xl font-bold mb-6">Reset Password</h2>
        {sent ? (
          <p className="text-slate-600">If the email exists, a reset link has been sent. Check server logs in dev mode.</p>
        ) : (
          <>
            <div className="mb-6">
              <label className="label">Email</label>
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <button type="submit" className="btn-primary w-full">Send Reset Link</button>
          </>
        )}
        <p className="text-center text-sm text-slate-500 mt-4">
          <Link to="/login" className="text-brand-600">Back to Login</Link>
        </p>
      </form>
    </PublicLayout>
  )
}
