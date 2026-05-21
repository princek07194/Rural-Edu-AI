import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { FiUsers, FiVideo, FiTrash2, FiToggleLeft } from 'react-icons/fi'
import { useAuth } from '../context/AuthContext'
import { adminAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function AdminPanel() {
  const { isAdmin } = useAuth()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [videos, setVideos] = useState([])
  const [logs, setLogs] = useState([])
  const [tab, setTab] = useState('users')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAdmin) return
    Promise.all([adminAPI.stats(), adminAPI.users(), adminAPI.videos(), adminAPI.logs()])
      .then(([s, u, v, l]) => {
        setStats(s.data)
        setUsers(u.data.users || [])
        setVideos(v.data.videos || [])
        setLogs(l.data.logs || [])
      })
      .finally(() => setLoading(false))
  }, [isAdmin])

  if (!isAdmin) return <Navigate to="/dashboard" replace />
  if (loading) return <LoadingSpinner fullScreen />

  const deleteUser = async (id) => {
    if (!confirm('Delete this user?')) return
    try {
      await adminAPI.deleteUser(id)
      setUsers((u) => u.filter((x) => x.id !== id))
      toast.success('User deleted')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed')
    }
  }

  const toggleUser = async (id) => {
    try {
      const res = await adminAPI.toggleUser(id)
      setUsers((u) => u.map((x) => x.id === id ? { ...x, is_active: res.data.is_active } : x))
      toast.success('User status updated')
    } catch {
      toast.error('Failed')
    }
  }

  const deleteVideo = async (id) => {
    if (!confirm('Delete this video?')) return
    try {
      await adminAPI.deleteVideo(id)
      setVideos((v) => v.filter((x) => x.id !== id))
      toast.success('Video deleted')
    } catch {
      toast.error('Failed')
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-display font-bold">Admin Panel</h1>

      <div className="grid sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Users', value: stats?.total_users, icon: FiUsers },
          { label: 'Active Users', value: stats?.active_users, icon: FiUsers },
          { label: 'Total Videos', value: stats?.total_videos, icon: FiVideo },
          { label: 'Completed', value: stats?.completed_videos, icon: FiVideo },
        ].map((s) => (
          <div key={s.label} className="glass-card p-4">
            <s.icon className="text-primary-500 mb-2" />
            <p className="text-2xl font-bold">{s.value}</p>
            <p className="text-sm text-slate-500">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        {['users', 'videos', 'logs'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-xl capitalize ${tab === t ? 'bg-primary-600 text-white' : 'bg-slate-100 dark:bg-slate-800'}`}>
            {t}
          </button>
        ))}
      </div>

      <motion.div className="glass-card overflow-hidden" key={tab} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {tab === 'users' && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr><th className="p-3 text-left">User</th><th className="p-3">Role</th><th className="p-3">Status</th><th className="p-3">Actions</th></tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="p-3">{u.username}<br /><span className="text-slate-500">{u.email}</span></td>
                  <td className="p-3 text-center">{u.role}</td>
                  <td className="p-3 text-center">{u.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="p-3 flex gap-2 justify-center">
                    <button onClick={() => toggleUser(u.id)} className="p-2 hover:bg-slate-100 rounded-lg"><FiToggleLeft /></button>
                    {u.role !== 'admin' && <button onClick={() => deleteUser(u.id)} className="p-2 text-red-500 hover:bg-red-50 rounded-lg"><FiTrash2 /></button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {tab === 'videos' && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr><th className="p-3 text-left">Title</th><th className="p-3">Status</th><th className="p-3">User</th><th className="p-3">Actions</th></tr>
            </thead>
            <tbody>
              {videos.map((v) => (
                <tr key={v.id} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="p-3">{v.title || v.video_id}</td>
                  <td className="p-3 text-center">{v.status}</td>
                  <td className="p-3 text-center">{v.user_id}</td>
                  <td className="p-3 text-center">
                    <button onClick={() => deleteVideo(v.id)} className="p-2 text-red-500"><FiTrash2 /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {tab === 'logs' && (
          <motion.div className="p-4 space-y-2 max-h-96 overflow-y-auto">
            {logs.map((l) => (
              <div key={l.id} className="text-sm p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="font-medium">{l.action}</span> — {l.details}
                <span className="text-slate-500 ml-2">{l.created_at?.slice(0, 10)}</span>
              </div>
            ))}
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
