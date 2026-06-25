import { useEffect, useState } from 'react'
import { printCenter } from '../../api/client'

export default function PrintCenterDashboard() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)

  const load = () => printCenter.jobs().then((r) => setJobs(r.data))

  useEffect(() => { load() }, [])

  const handleAction = async (action, id) => {
    setLoading(true)
    try {
      await printCenter[action](id)
      await load()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Incoming Orders</h1>
          <p className="text-slate-500">Manage print jobs by priority</p>
        </div>
        <button onClick={() => handleAction('processQueue')} className="btn-primary" disabled={loading}>
          Process Next in Queue
        </button>
      </div>

      <div className="space-y-4">
        {jobs.map((job) => (
          <div key={job.id} className="card">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold">Job #{job.id} — {job.document?.filename}</h3>
                <p className="text-sm text-slate-500">
                  {job.pages_to_print} pages · {job.is_color ? 'Color' : 'B&W'} · Priority: {job.priority_score.toFixed(1)}
                </p>
                <span className={`inline-block mt-2 px-2 py-0.5 rounded text-xs font-medium capitalize ${
                  job.status === 'printing' ? 'bg-blue-100 text-blue-700' :
                  job.status === 'queued' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100'
                }`}>{job.status}</span>
              </div>
              <div className="flex gap-2">
                {job.status === 'queued' && (
                  <>
                    <button onClick={() => handleAction('assign', job.id)} className="btn-secondary text-sm" disabled={loading}>Assign</button>
                    <button onClick={() => handleAction('start', job.id)} className="btn-primary text-sm" disabled={loading}>Start</button>
                  </>
                )}
                {job.status === 'printing' && (
                  <>
                    <button onClick={() => handleAction('complete', job.id)} className="btn-primary text-sm" disabled={loading}>Complete</button>
                    <button onClick={() => handleAction('fail', job.id)} className="btn-secondary text-sm text-red-600" disabled={loading}>Fail & Retry</button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {jobs.length === 0 && <p className="text-slate-500">No pending jobs</p>}
      </div>
    </div>
  )
}
