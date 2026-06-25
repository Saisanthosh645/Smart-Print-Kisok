import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Upload, IndianRupee, Bell } from 'lucide-react'
import { student } from '../api/client'

export default function StudentDashboard() {
  const [jobs, setJobs] = useState([])
  const [docs, setDocs] = useState([])
  const [notifications, setNotifications] = useState([])

  useEffect(() => {
    student.listJobs().then((r) => setJobs(r.data.slice(0, 5)))
    student.listDocuments().then((r) => setDocs(r.data.slice(0, 3)))
    student.notifications().then((r) => setNotifications(r.data.slice(0, 5)))
  }, [])

  const activeJobs = jobs.filter((j) => !['completed', 'cancelled'].includes(j.status))

  return (
    <div className="p-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-2">Student Dashboard</h1>
      <p className="text-slate-500 mb-8">Upload, pay, and track your print jobs</p>

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-brand-100 rounded-lg"><FileText className="w-6 h-6 text-brand-600" /></div>
          <div>
            <p className="text-2xl font-bold">{docs.length}</p>
            <p className="text-sm text-slate-500">Documents</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-lg"><Upload className="w-6 h-6 text-green-600" /></div>
          <div>
            <p className="text-2xl font-bold">{activeJobs.length}</p>
            <p className="text-sm text-slate-500">Active Jobs</p>
          </div>
        </div>
        <Link to="/upload" className="card flex items-center gap-4 hover:border-brand-300 transition cursor-pointer">
          <div className="p-3 bg-amber-100 rounded-lg"><IndianRupee className="w-6 h-6 text-amber-600" /></div>
          <div>
            <p className="font-semibold text-brand-600">New Print Job</p>
            <p className="text-sm text-slate-500">Upload & calculate cost</p>
          </div>
        </Link>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-4">Recent Jobs</h2>
          {jobs.length === 0 ? (
            <p className="text-slate-500 text-sm">No jobs yet. <Link to="/upload" className="text-brand-600">Upload a document</Link></p>
          ) : (
            <ul className="space-y-3">
              {jobs.map((job) => (
                <li key={job.id} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                  <div>
                    <Link to={`/jobs/${job.id}`} className="font-medium text-brand-600 hover:underline">
                      Job #{job.id}
                    </Link>
                    <p className="text-xs text-slate-500 capitalize">{job.status}</p>
                  </div>
                  <span className="font-medium">₹{job.cost}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="font-semibold mb-4 flex items-center gap-2"><Bell className="w-4 h-4" /> Notifications</h2>
          {notifications.length === 0 ? (
            <p className="text-slate-500 text-sm">No notifications</p>
          ) : (
            <ul className="space-y-3">
              {notifications.map((n) => (
                <li key={n.id} className="text-sm">
                  <p className="font-medium">{n.title}</p>
                  <p className="text-slate-500">{n.message}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
