import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiVideo, FiFileText, FiHelpCircle, FiUpload, FiBell } from 'react-icons/fi'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js'
import { Bar, Doughnut } from 'react-chartjs-2'
import { dashboardAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement)

const statCards = [
  { key: 'total_videos', label: 'Videos Processed', icon: FiVideo, color: 'from-blue-500 to-cyan-500' },
  { key: 'total_notes', label: 'Notes Generated', icon: FiFileText, color: 'from-violet-500 to-purple-500' },
  { key: 'total_mcqs', label: 'MCQs Generated', icon: FiHelpCircle, color: 'from-emerald-500 to-teal-500' },
  { key: 'completed_videos', label: 'Completed', icon: FiUpload, color: 'from-orange-500 to-amber-500' },
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([dashboardAPI.stats(), dashboardAPI.notifications()])
      .then(([statsRes, notifRes]) => {
        setData(statsRes.data)
        setNotifications(notifRes.data.notifications || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner fullScreen text="Loading dashboard..." />
  const stats = data?.stats || {}

  const barData = {
    labels: data?.chart_data?.map((d) => d.month) || [],
    datasets: [{
      label: 'Videos Processed',
      data: data?.chart_data?.map((d) => d.videos) || [],
      backgroundColor: 'rgba(51, 150, 255, 0.7)',
      borderRadius: 8,
    }],
  }

  const doughnutData = {
    labels: ['Completed', 'Processing/Failed'],
    datasets: [{
      data: [stats.completed_videos || 0, (stats.total_videos || 0) - (stats.completed_videos || 0)],
      backgroundColor: ['#3396ff', '#e2e8f0'],
    }],
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-start gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-display font-bold">Dashboard</h1>
          <p className="text-slate-500 mt-1">Your AI-powered learning analytics</p>
        </div>
        <Link to="/process" className="gradient-btn inline-flex items-center gap-2">
          <FiUpload /> Process New Video
        </Link>
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <motion.div key={card.key} className="glass-card p-5" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center text-white mb-3`}>
              <card.icon size={20} />
            </div>
            <p className="text-2xl font-bold">{stats[card.key] || 0}</p>
            <p className="text-sm text-slate-500">{card.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Chart */}
        <motion.div className="lg:col-span-2 glass-card p-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <h3 className="font-semibold mb-4">Monthly Activity</h3>
          <Bar data={barData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
        </motion.div>

        {/* Doughnut + Recommendations */}
        <motion.div className="space-y-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="glass-card p-6">
            <h3 className="font-semibold mb-4">Completion Rate</h3>
            <div className="h-40 flex justify-center">
              <Doughnut data={doughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
          <div className="glass-card p-6">
            <h3 className="font-semibold mb-3">AI Recommendations</h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              {(data?.recommendations || []).map((r, i) => (
                <li key={i} className="flex gap-2"><span className="text-primary-500">•</span>{r}</li>
              ))}
            </ul>
          </div>
        </motion.div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent videos */}
        <div className="glass-card p-6">
          <h3 className="font-semibold mb-4">Recent Videos</h3>
          {data?.recent_videos?.length ? (
            <motion.div className="space-y-3">
              {data.recent_videos.map((v) => (
                <Link key={v.id} to={`/notes/${v.id}`} className="flex gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                  <img src={v.thumbnail_url} alt="" className="w-16 h-12 object-cover rounded-lg" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{v.title}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${v.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {v.status}
                    </span>
                  </div>
                </Link>
              ))}
            </motion.div>
          ) : (
            <p className="text-slate-500 text-sm">No videos yet. <Link to="/process" className="text-primary-600">Process your first video</Link></p>
          )}
        </div>

        {/* Notifications */}
        <div className="glass-card p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2"><FiBell /> Notifications</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {notifications.length ? notifications.map((n) => (
              <div key={n.id} className={`p-3 rounded-xl text-sm ${!n.is_read ? 'bg-primary-50 dark:bg-primary-900/20' : ''}`}>
                <p className="font-medium">{n.title}</p>
                <p className="text-slate-500">{n.message}</p>
              </div>
            )) : <p className="text-slate-500 text-sm">No notifications</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
