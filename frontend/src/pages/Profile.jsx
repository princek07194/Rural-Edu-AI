import { useState } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../services/api'

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi' },
  { value: 'pa', label: 'Punjabi' },
  { value: 'bho', label: 'Bhojpuri' },
]

export default function Profile() {
  const { user, updateUser } = useAuth()
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    preferred_language: user?.preferred_language || 'en',
    avatar_url: user?.avatar_url || '',
  })
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '' })
  const [loading, setLoading] = useState(false)

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authAPI.updateProfile(form)
      updateUser(res.data.user)
      toast.success('Profile updated')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Update failed')
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    try {
      await authAPI.changePassword(passwords)
      toast.success('Password changed')
      setPasswords({ current_password: '', new_password: '' })
    } catch (err) {
      toast.error(err.response?.data?.error || 'Password change failed')
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-display font-bold">Profile</h1>

      <motion.div className="glass-card p-6 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-2xl font-bold">
          {(user?.full_name || user?.username || 'U')[0].toUpperCase()}
        </div>
        <h2 className="font-semibold mt-3">{user?.full_name}</h2>
        <p className="text-slate-500 text-sm">@{user?.username} • {user?.role}</p>
      </motion.div>

      <form onSubmit={handleProfileUpdate} className="glass-card p-6 space-y-4">
        <h3 className="font-semibold">Edit Profile</h3>
        <div>
          <label className="block text-sm font-medium mb-1">Full Name</label>
          <input className="input-field" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Preferred Language</label>
          <select className="input-field" value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}>
            {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Avatar URL</label>
          <input className="input-field" value={form.avatar_url} onChange={(e) => setForm({ ...form, avatar_url: e.target.value })} placeholder="https://..." />
        </div>
        <button type="submit" className="gradient-btn w-full" disabled={loading}>Save Changes</button>
      </form>

      <form onSubmit={handlePasswordChange} className="glass-card p-6 space-y-4">
        <h3 className="font-semibold">Change Password</h3>
        <input type="password" className="input-field" placeholder="Current password" value={passwords.current_password}
          onChange={(e) => setPasswords({ ...passwords, current_password: e.target.value })} required />
        <input type="password" className="input-field" placeholder="New password (min 8 chars)" value={passwords.new_password}
          onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })} required minLength={8} />
        <button type="submit" className="gradient-btn w-full">Change Password</button>
      </form>
    </div>
  )
}
