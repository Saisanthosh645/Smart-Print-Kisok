import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PublicLayout } from '../components/Layout'
import { auth } from '../api/client'

export default function ResetPassword() {
  const [params] = useSearchParams()
  const [password, setPassword] = useState('')
  const [done, setDone] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    await auth.resetPassword({ token: params.get('token'), new_password: password })
    setDone(true)
  }

  return (
    <PublicLayout>
      <form onSubmit={handleSubmit} className="card">
        <h2 className="text-2xl font-bold mb-6">New Password</h2>
        {done ? (
          <Link to="/login" className="btn-primary inline-block">Sign In</Link>
        ) : (
          <>
            <div className="mb-6">
              <label className="label">New Password</label>
              <input className="input" type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <button type="submit" className="btn-primary w-full">Reset Password</button>
          </>
        )}
      </form>
    </PublicLayout>
  )
}
