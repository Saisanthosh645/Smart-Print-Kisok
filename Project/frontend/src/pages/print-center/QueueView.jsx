import { useEffect, useState } from 'react'
import { printCenter } from '../../api/client'

export default function QueueView() {
  const [queue, setQueue] = useState({ queue_size: 0, jobs: [] })

  useEffect(() => {
    printCenter.queue().then((r) => setQueue(r.data))
    const interval = setInterval(() => printCenter.queue().then((r) => setQueue(r.data)), 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">Priority Queue</h1>
      <p className="text-slate-500 mb-8">Heap-based queue — lower priority score = higher priority</p>

      <div className="card mb-6">
        <p className="text-4xl font-bold text-brand-700">{queue.queue_size}</p>
        <p className="text-slate-500">Jobs in queue</p>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-4">Queue Order</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="pb-2">#</th>
              <th className="pb-2">Job ID</th>
              <th className="pb-2">Priority Score</th>
            </tr>
          </thead>
          <tbody>
            {queue.jobs.map((item, idx) => (
              <tr key={item.job_id} className="border-b border-slate-50">
                <td className="py-3">{idx + 1}</td>
                <td className="py-3 font-medium">#{item.job_id}</td>
                <td className="py-3">{item.priority.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {queue.jobs.length === 0 && <p className="text-slate-500 py-4">Queue is empty</p>}
      </div>
    </div>
  )
}
