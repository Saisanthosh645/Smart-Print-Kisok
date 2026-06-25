import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PublicLayout } from '../components/Layout'
import { auth } from '../api/client'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const [status, setStatus] = useState('loading')
  const token = params.get('token')

  useEffect(() => {
    if (!token) { setStatus('error'); return }
    auth.verifyEmail(token)
      .then(() => setStatus('success'))
      .catch(() => setStatus('error'))
  }, [token])

  return (
    <PublicLayout>
      <div className="card text-center">
        {status === 'loading' && <p>Verifying email...</p>}
        {status === 'success' && (
          <>
            <h2 className="text-2xl font-bold text-green-600 mb-4">Email Verified!</h2>
            <Link to="/login" className="btn-primary inline-block">Sign In</Link>
          </>
        )}
        {status === 'error' && (
          <>
            <h2 className="text-2xl font-bold text-red-600 mb-4">Verification Failed</h2>
            <Link to="/register" className="btn-secondary inline-block">Try Again</Link>
          </>
        )}
      </div>
    </PublicLayout>
  )
}
