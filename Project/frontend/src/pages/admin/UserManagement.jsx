import { useEffect, useState } from 'react'
import { admin } from '../../api/client'

export default function UserManagement() {
  const [users, setUsers] = useState([])

  const load = () => admin.users().then((r) => setUsers(r.data))
  useEffect(() => { load() }, [])

  const handleBan = async (id) => { await admin.banUser(id); load() }
  const handleUnban = async (id) => { await admin.unbanUser(id); load() }
  const handlePremium = async (id) => { await admin.togglePremium(id); load() }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">User Management</h1>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="pb-3 pr-4">Name</th>
              <th className="pb-3 pr-4">Email</th>
              <th className="pb-3 pr-4">Role</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-slate-50">
                <td className="py-3 pr-4 font-medium">{u.full_name}</td>
                <td className="py-3 pr-4">{u.email}</td>
                <td className="py-3 pr-4 capitalize">{u.role.replace('_', ' ')}</td>
                <td className="py-3 pr-4">
                  {u.is_banned ? <span className="text-red-600">Banned</span> : <span className="text-green-600">Active</span>}
                  {u.is_premium && <span className="ml-2 text-amber-600 text-xs">Premium</span>}
                </td>
                <td className="py-3 flex gap-2">
                  {u.is_banned ? (
                    <button onClick={() => handleUnban(u.id)} className="btn-secondary text-xs">Unban</button>
                  ) : (
                    <button onClick={() => handleBan(u.id)} className="btn-secondary text-xs text-red-600">Ban</button>
                  )}
                  <button onClick={() => handlePremium(u.id)} className="btn-secondary text-xs">Toggle Premium</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
