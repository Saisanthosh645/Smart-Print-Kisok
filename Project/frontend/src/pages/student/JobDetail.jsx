import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { student } from '../../api/client'
import JobTracker from '../../components/JobTracker'

export default function JobDetail() {
  const { id } = useParams()
  const [job, setJob] = useState(null)
  const [paying, setPaying] = useState(false)

  const loadJob = () => student.getJob(id).then((r) => setJob(r.data))

  useEffect(() => {
    loadJob()

    const token = localStorage.getItem('access_token')
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Construct the backend websocket URL. In dev environment, frontend is on port 5173 or 3000, backend is on 8000.
    const wsHost = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
    const wsUrl = `${protocol}//${wsHost}/api/v1/ws/jobs?token=${token}`

    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.event === 'job_status_update' && data.job_id === parseInt(id)) {
          loadJob()
        }
      } catch (err) {
        console.error("Error parsing WebSocket message:", err)
      }
    }

    ws.onerror = (err) => {
      console.error("WebSocket error:", err)
    }

    return () => {
      ws.close()
    }
  }, [id])

  const handlePay = async () => {
    setPaying(true)
    try {
      const order = await student.createPayment(id)
      if (order.data.mock) {
        await student.verifyPayment(id, {
          razorpay_order_id: order.data.order_id,
          razorpay_payment_id: `pay_mock_${Date.now()}`,
          razorpay_signature: 'mock_signature_valid',
          method: 'upi',
        })
        await loadJob()
      }
    } finally {
      setPaying(false)
    }
  }

  if (!job) return <div className="p-8">Loading...</div>

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">Job #{job.id}</h1>
      <p className="text-slate-500 mb-8">{job.document?.filename}</p>

      <div className="card mb-6">
        <JobTracker status={job.status} history={job.status_history} />
      </div>

      <div className="card grid grid-cols-2 gap-4 mb-6">
        <div><p className="text-sm text-slate-500">Pages</p><p className="font-semibold">{job.pages_to_print}</p></div>
        <div><p className="text-sm text-slate-500">Sheets</p><p className="font-semibold">{job.sheets_required}</p></div>
        <div><p className="text-sm text-slate-500">Type</p><p className="font-semibold">{job.is_color ? 'Color' : 'B&W'} · {job.is_double_sided ? 'Double' : 'Single'}</p></div>
        <div><p className="text-sm text-slate-500">Cost</p><p className="font-semibold text-brand-700">₹{job.cost}</p></div>
        <div><p className="text-sm text-slate-500">Payment</p><p className="font-semibold capitalize">{job.payment_status}</p></div>
        {job.collection_code && (
          <div><p className="text-sm text-slate-500">Collection Code</p><p className="font-bold text-2xl text-green-600">{job.collection_code}</p></div>
        )}
      </div>

      {job.payment_status === 'pending' && (
        <button onClick={handlePay} className="btn-primary w-full py-3" disabled={paying}>
          {paying ? 'Processing...' : `Pay ₹${job.cost} via Razorpay (Mock)`}
        </button>
      )}
    </div>
  )
}
