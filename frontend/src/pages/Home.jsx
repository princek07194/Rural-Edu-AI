import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiPlay, FiBook, FiGlobe, FiMessageCircle, FiArrowRight } from 'react-icons/fi'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { FiSun, FiMoon } from 'react-icons/fi'

const features = [
  { icon: FiPlay, title: 'YouTube Processing', desc: 'Paste any educational video URL and get instant AI-generated study material.' },
  { icon: FiBook, title: 'Smart Notes & MCQs', desc: 'Detailed notes, summaries, MCQs, and practice questions auto-generated.' },
  { icon: FiGlobe, title: 'Multi-Language', desc: 'Learn in English, Hindi, or Punjabi with built-in translation support.' },
  { icon: FiMessageCircle, title: 'AI Tutor Chatbot', desc: 'Ask questions about video content and get intelligent contextual answers.' },
]

export default function Home() {
  const { user } = useAuth()
  const { dark, toggle } = useTheme()

  return (
    <div className="min-h-screen overflow-hidden">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 glass-card border-0 border-b border-white/10 rounded-none">
        <motion.div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <span className="font-display font-bold text-xl bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
            Rural Edu AI
          </span>
          <div className="flex items-center gap-4">
            <button onClick={toggle} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">
              {dark ? <FiSun /> : <FiMoon />}
            </button>
            {user ? (
              <Link to="/dashboard" className="gradient-btn text-sm py-2 px-4">Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="text-slate-600 dark:text-slate-300 hover:text-primary-600 font-medium">Login</Link>
                <Link to="/register" className="gradient-btn text-sm py-2 px-4">Get Started</Link>
              </>
            )}
          </div>
        </motion.div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6">
        <motion.div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-primary-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl" />
        </motion.div>

        <motion.div className="max-w-4xl mx-auto text-center" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <span className="inline-block px-4 py-1 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm font-medium mb-6">
            AI-Powered Rural Education
          </span>
          <h1 className="font-display text-4xl md:text-6xl font-bold leading-tight mb-6">
            Regional Language Based{' '}
            <span className="bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
              Digital Education
            </span>
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-8 max-w-2xl mx-auto">
            Transform YouTube educational videos into notes, summaries, MCQs, and an AI tutor — in English, Hindi, and Punjabi for rural communities.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to={user ? '/process' : '/register'} className="gradient-btn inline-flex items-center gap-2">
              Start Learning <FiArrowRight />
            </Link>
            <Link to="/login" className="px-6 py-3 rounded-xl border border-slate-300 dark:border-slate-600 font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition">
              Sign In
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 max-w-7xl mx-auto">
        <motion.h2 className="text-3xl font-display font-bold text-center mb-12" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
          Everything You Need to Learn
        </motion.h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => (
            <motion.div key={f.title} className="glass-card p-6 hover:scale-105 transition-transform duration-300"
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white mb-4">
                <f.icon size={24} />
              </div>
              <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <motion.div className="max-w-3xl mx-auto glass-card p-12 text-center bg-gradient-to-br from-primary-600/10 to-accent-500/10"
          initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}>
          <h2 className="text-2xl font-display font-bold mb-4">Ready to empower rural education?</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">Join thousands of learners accessing quality education through AI.</p>
          <Link to="/register" className="gradient-btn inline-flex items-center gap-2">
            Create Free Account <FiArrowRight />
          </Link>
        </motion.div>
      </section>

      <footer className="py-8 text-center text-slate-500 text-sm border-t border-slate-200 dark:border-slate-800">
        © 2026 Rural Digital Education System. Built for rural communities.
      </footer>
    </div>
  )
}
