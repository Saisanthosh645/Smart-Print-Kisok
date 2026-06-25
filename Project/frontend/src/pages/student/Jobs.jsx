import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { student } from '../../api/client'
import JobTracker from '../../components/JobTracker'

export default function Jobs() {
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    student.listJobs().then((r) => setJobs(r.data))
  }, [])

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">My Print Jobs</h1>
        <Link to="/upload" className="btn-primary">New Job</Link>
      </div>

      <div className="space-y-4">
        {jobs.map((job) => (
          <Link key={job.id} to={`/jobs/${job.id}`} className="card block hover:border-brand-300 transition">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold">Job #{job.id}</h3>
                <p className="text-sm text-slate-500">{job.document?.filename}</p>
              </div>
              <span className="font-bold text-brand-700">₹{job.cost}</span>
            </div>
            <JobTracker status={job.status} history={job.status_history} />
          </Link>
        ))}
        {jobs.length === 0 && <p className="text-slate-500">No print jobs yet.</p>}
      </div>
    </div>
  )
}
