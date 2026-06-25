import { useEffect, useState } from 'react'
import { admin } from '../../api/client'

export default function PrinterManagement() {
  const [printers, setPrinters] = useState([])
  const [form, setForm] = useState({ name: '', location: '', building: 'Main Campus' })

  const load = () => admin.printers().then((r) => setPrinters(r.data))
  useEffect(() => { load() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    await admin.addPrinter(form)
    setForm({ name: '', location: '', building: 'Main Campus' })
    load()
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Printer Management</h1>

      <form onSubmit={handleAdd} className="card mb-8 grid md:grid-cols-4 gap-4 items-end">
        <div>
          <label className="label">Name</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div>
          <label className="label">Location</label>
          <input className="input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} required />
        </div>
        <div>
          <label className="label">Building</label>
          <input className="input" value={form.building} onChange={(e) => setForm({ ...form, building: e.target.value })} />
        </div>
        <button type="submit" className="btn-primary">Add Printer</button>
      </form>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {printers.map((p) => (
          <div key={p.id} className="card">
            <div className="flex justify-between items-start mb-3">
              <h3 className="font-semibold">{p.name}</h3>
              <span className={`text-xs px-2 py-0.5 rounded capitalize ${
                p.status === 'online' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>{p.status}</span>
            </div>
            <p className="text-sm text-slate-500">{p.location}</p>
            <p className="text-sm text-slate-500">{p.building}</p>
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span>Health</span>
                <span>{p.health_score}%</span>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full">
                <div className="h-full bg-green-500 rounded-full" style={{ width: `${p.health_score}%` }} />
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-3">{p.jobs_completed} completed · {p.jobs_failed} failed</p>
            {!p.is_active && <p className="text-xs text-red-500 mt-1">Deactivated</p>}
          </div>
        ))}
      </div>
    </div>
  )
}
