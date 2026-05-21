import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../utils/getErrorMessage'

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi' },
  { value: 'pa', label: 'Punjabi' },
  { value: 'bho', label: 'Bhojpuri' },
]

export default function Register() {
  const [form, setForm] = useState({
    username: '', email: '', password: '', full_name: '', preferred_language: 'en',
  })
  const [loading, setLoading] = useState(false)
  const [serverOnline, setServerOnline] = useState(null)
  const { register } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.ok && setServerOnline(true))
      .catch(() => setServerOnline(false))
  }, [])

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await register(form)
      toast.success('Account created!')
      navigate('/dashboard')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div className="min-h-screen flex items-center justify-center p-6">
      <motion.div className="glass-card w-full max-w-md p-8" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Link to="/" className="font-display font-bold text-xl bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
          Rural Edu AI
        </Link>
        <h2 className="text-2xl font-bold mt-6 mb-6">Create Account</h2>

        {serverOnline === false && (
          <motion.div className="mb-4 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
            <strong>Backend is not running.</strong>
            <br />
            1. Double-click <code className="bg-red-100 dark:bg-red-900 px-1 rounded">RUN-PROJECT.bat</code> in project folder
            <br />
            2. Or run: <code className="bg-red-100 dark:bg-red-900 px-1 rounded">cd backend</code> then <code className="bg-red-100 dark:bg-red-900 px-1 rounded">python run.py</code>
            <br />
            Keep that window open, then refresh this page.
          </motion.div>
        )}
        {serverOnline === true && (
          <p className="mb-4 text-sm text-green-600 dark:text-green-400">✓ Server connected — you can register</p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {['username', 'full_name', 'email', 'password'].map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium mb-1 capitalize">{field.replace('_', ' ')}</label>
              <input
                type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
                name={field}
                className="input-field"
                value={form[field]}
                onChange={handleChange}
                required
                minLength={field === 'password' ? 8 : field === 'username' ? 3 : undefined}
              />
            </div>
          ))}
          <div>
            <label className="block text-sm font-medium mb-1">Preferred Language</label>
            <select name="preferred_language" className="input-field" value={form.preferred_language} onChange={handleChange}>
              {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
          <button type="submit" className="gradient-btn w-full" disabled={loading}>
            {loading ? 'Creating...' : 'Register'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account? <Link to="/login" className="text-primary-600 font-medium">Login</Link>
        </p>
      </motion.div>
    </motion.div>
  )
}
