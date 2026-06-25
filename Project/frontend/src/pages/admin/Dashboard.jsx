import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { admin } from '../../api/client'

export default function AdminDashboard() {
  const [data, setData] = useState(null)

  useEffect(() => {
    admin.analytics().then((r) => setData(r.data))
  }, [])

  if (!data) return <div className="p-8">Loading analytics...</div>

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Admin Analytics</h1>

      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <p className="text-sm text-slate-500">Daily Revenue</p>
          <p className="text-3xl font-bold text-green-600">₹{data.daily_revenue}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Monthly Revenue</p>
          <p className="text-3xl font-bold text-brand-700">₹{data.monthly_revenue}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Total Prints</p>
          <p className="text-3xl font-bold">{data.total_prints}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Active Users</p>
          <p className="text-3xl font-bold">{data.active_users}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-4">Revenue (Last 7 Days)</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.revenue_by_day}>
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => [`₹${v}`, 'Revenue']} />
              <Bar dataKey="revenue" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-4">Jobs by Status</h2>
          <div className="space-y-3">
            {Object.entries(data.jobs_by_status).map(([status, count]) => (
              <div key={status} className="flex justify-between items-center">
                <span className="capitalize text-sm">{status}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-500 rounded-full" style={{ width: `${Math.min(100, count * 10)}%` }} />
                  </div>
                  <span className="font-medium w-8 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
